# Architecture

## Database Relations

```mermaid
erDiagram
    User ||--o{ UserProfile : "has"
    Group {
        string name
    }
    UserProfile {
        int items_per_page
        string timezone
        string bio
    }

    AbstractTimestampMixin {
        datetime created_at
        datetime updated_at
    }

    AbstractSimpleNamedModelMixin {
        string name
        string description
    }

    AbstractBoxInImage {
        float center_x
        float center_y
        float height
        float width
        string description
    }

    ObjectPermissionModelMixin {
        string dummy "Placeholder for M2M"
    }
    ObjectPermissionModelMixin ||--|{ Group : "view_groups (%(class)ss_viewable)"
    ObjectPermissionModelMixin ||--|{ Group : "edit_groups (%(class)ss_editable)"

    Image {
        string original_checksum PK
        string phash
        bigint file_size
        int original_height
        int original_width
        smallint thumbnail_height
        smallint thumbnail_width
        smallint orientation
        string title
        string description
        string original
        bool is_dirty
        datetime deleted_at
        bool is_starred
    }
    Image --|> AbstractTimestampMixin : "inherits"
    Image --|> ObjectPermissionModelMixin : "inherits"
    Image ||--o{ ImageSource : "source (images)"
    Image ||--o{ RoughLocation : "location (images)"
    Image ||--o{ RoughDate : "date (images)"
    Image ||--|{ ImageFolder : "folder (images)"

    Album {
        string name
        string description
    }
    Album --|> AbstractSimpleNamedModelMixin : "inherits"
    Album --|> AbstractTimestampMixin : "inherits"
    Album --|> ObjectPermissionModelMixin : "inherits"
    Album ||--|{ ImageInAlbum : "contains"
    Image ||--|{ ImageInAlbum : "part of"

    ImageInAlbum {
        bigint sort_order
    }
    ImageInAlbum --|> AbstractTimestampMixin : "inherits"
    ImageInAlbum }|..|| Album : "album"
    ImageInAlbum }|..|| Image : "image"

    ImageFolder {
        string name
        string description
    }
    ImageFolder --|> AbstractTimestampMixin : "inherits"
    ImageFolder --|> AbstractSimpleNamedModelMixin : "inherits"
    ImageFolder --|> ObjectPermissionModelMixin : "inherits"
    ImageFolder --|> TreeNodeModel : "inherits"
    ImageFolder ||--o{ ImageFolder : "parent (children)"

    Tag {
        string name
        string description
    }
    Tag --|> AbstractTimestampMixin : "inherits"
    Tag --|> AbstractSimpleNamedModelMixin : "inherits"
    Tag --|> TreeNodeModel : "inherits"
    Tag ||--o{ Tag : "parent (children)"


    TagOnImage {
        bool applied
    }
    TagOnImage }|..|| Tag : "tag"
    TagOnImage }|..|| Image : "image"
    Image ||--|{ TagOnImage : "has_tags"
    Tag ||--|{ TagOnImage : "on_images"


    Person {
        string name
        string description
    }
    Person --|> AbstractSimpleNamedModelMixin : "inherits"
    Person --|> AbstractTimestampMixin : "inherits"
    Person --|> ObjectPermissionModelMixin : "inherits"

    PersonInImage {
        bool exclude_from_training
    }
    PersonInImage --|> AbstractBoxInImage : "inherits"
    PersonInImage }|..|| Person : "person (images/appearances)"
    PersonInImage }|..|| Image : "image"
    Image ||--|{ PersonInImage : "has_people_boxes"
    Person ||--|{ PersonInImage : "appears_in_images_boxes"


    Pet {
        string name
        string description
        string pet_type
    }
    Pet --|> AbstractSimpleNamedModelMixin : "inherits"
    Pet --|> AbstractTimestampMixin : "inherits"
    Pet --|> ObjectPermissionModelMixin : "inherits"

    PetInImage {
        string name "property"
    }
    PetInImage --|> AbstractBoxInImage : "inherits"
    PetInImage }|..|| Pet : "pet (images/appearances)"
    PetInImage }|..|| Image : "image"
    Image ||--|{ PetInImage : "has_pet_boxes"
    Pet ||--|{ PetInImage : "appears_in_images_boxes"

    ImageSource {
        string name
        string description
    }
    ImageSource --|> AbstractTimestampMixin : "inherits"
    ImageSource --|> AbstractSimpleNamedModelMixin : "inherits"
    ImageSource --|> ObjectPermissionModelMixin : "inherits"

    RoughDate {
        date date PK
        bool month_valid
        bool day_valid
    }
    RoughDate --|> AbstractTimestampMixin : "inherits"
    RoughDate --|> ObjectPermissionModelMixin : "inherits"

    RoughLocation {
        string country_code PK
        string subdivision_code
        string city
        string sub_location
    }
    RoughLocation --|> AbstractTimestampMixin : "inherits"
    RoughLocation --|> ObjectPermissionModelMixin : "inherits"

    %% Placeholder for TreeNodeModel if you want to visualize it
    TreeNodeModel {
        string tn_ancestors_pks
        string tn_ancestors_count
        string tn_children_pks
        string tn_children_count
        string tn_depth
        string tn_descendants_pks
        string tn_descendants_count
        string tn_index
        string tn_level
        string tn_priority
        string tn_order
        string tn_siblings_pks
        string tn_siblings_count
    }

    %% Notes on relationships for ObjectPermissionModelMixin
    %% Since it's abstract, the M2M to Group is actually on concrete models.
    %% Mermaid doesn't directly support abstract inheritance for ERD M2M like this.
    %% So, Album, Image, ImageFolder, ImageSource, Person, Pet, RoughDate, RoughLocation
    %% would each have their own M2M to Group.
    %% Example for one:
    %% Image ||--|{ Group : "view_groups"
    %% Image ||--|{ Group : "edit_groups"
    %% (Repeat for other models inheriting ObjectPermissionModelMixin)
```
