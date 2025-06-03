from collections import defaultdict
from typing import Annotated

from django.db import transaction
from django_typer.management import TyperCommand
from typer import Option

from memoria.models import RoughLocation


class Command(TyperCommand):
    help = "Clean up duplicate RoughLocation records and reassign foreign key references"

    def handle(
        self,
        *,
        dry_run: Annotated[bool, Option(help="Show what would be deleted without actually deleting")] = True,
    ) -> None:
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Group locations by their unique key (all 4 fields)
        groups = defaultdict(list)

        for location in RoughLocation.objects.all().order_by("pk"):  # Order by pk to keep earliest
            key = (
                location.country_code,
                location.subdivision_code,
                location.city,
                location.sub_location,
            )
            groups[key].append(location)

        # Find groups with duplicates
        duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}

        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicates found!"))
            return

        self.stdout.write(f"Found {len(duplicate_groups)} groups with duplicates:")

        total_duplicates_removed = 0
        total_images_reassigned = 0

        for key, locations in duplicate_groups.items():
            # Keep the record with the most images, or earliest if tied
            canonical = max(locations, key=lambda loc: (loc.images.count(), -loc.pk))
            duplicates = locations[1:]  # Delete the rest

            self.stdout.write(f"\nGroup: {key}")
            self.stdout.write(f"  Keeping: pk={canonical.pk} (has {canonical.images.count()} images)")

            images_to_reassign = 0
            for duplicate in duplicates:
                image_count = duplicate.images.count()
                images_to_reassign += image_count
                self.stdout.write(f"  Removing: pk={duplicate.pk} (has {image_count} images)")

            if not dry_run:
                with transaction.atomic():
                    # Reassign all images from duplicates to the canonical location
                    for duplicate in duplicates:
                        # Update all images that reference this duplicate
                        updated_count = duplicate.images.update(location=canonical)
                        total_images_reassigned += updated_count

                        # Now safe to delete the duplicate
                        duplicate.delete()
                        total_duplicates_removed += 1
            else:
                total_duplicates_removed += len(duplicates)
                total_images_reassigned += images_to_reassign

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\nWould remove {total_duplicates_removed} duplicate locations"))
            self.stdout.write(self.style.WARNING(f"Would reassign {total_images_reassigned} image references"))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nRemoved {total_duplicates_removed} duplicate locations"))
            self.stdout.write(self.style.SUCCESS(f"Reassigned {total_images_reassigned} image references"))

            # Verify no duplicates remain
            remaining_groups = defaultdict(list)
            for location in RoughLocation.objects.all():
                key = (
                    location.country_code,
                    location.subdivision_code,
                    location.city,
                    location.sub_location,
                )
                remaining_groups[key].append(location)

            remaining_duplicates = {k: v for k, v in remaining_groups.items() if len(v) > 1}
            if remaining_duplicates:
                self.stdout.write(
                    self.style.ERROR(f"WARNING: {len(remaining_duplicates)} duplicate groups still remain!"),
                )
            else:
                self.stdout.write(self.style.SUCCESS("All duplicates successfully cleaned up!"))
