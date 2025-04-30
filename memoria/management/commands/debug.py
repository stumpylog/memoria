from django.core.management.base import BaseCommand


def merge_tree(data):
    """Merges child nodes and removes duplicate keywords while preserving structure.

    Args:
      data: The input dictionary.

    Returns:
      The modified dictionary.
    """

    seen_keywords = set()

    def helper(node):
        children = node.get("Children", [])
        filtered_children = []
        for child in children:
            helper(child)
            if child["Keyword"] not in seen_keywords:
                seen_keywords.add(child["Keyword"])
                filtered_children.append(child)
        node["Children"] = filtered_children

    helper(data)
    return data


class Command(BaseCommand):
    help = "Debug command to do stuff"

    def handle(self, *args, **options) -> None:  # noqa: ARG002
        data = {
            "Children": [
                {"Children": [], "Keyword": "Outdoors"},
                {
                    "Children": [{"Children": [], "Keyword": "Mountains"}],
                    "Keyword": "Outdoors",
                },
            ],
            "Keyword": "Themes",
        }

        result = merge_tree(data)
        print(result)  # noqa: T201
