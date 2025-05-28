# Memoria

<img src="src-frontend\public\brand.svg" width="150" height="150" alt="project logo">

**Memoria** is a tool to help you sort, categorize, and generally assist with making sense of scanned images. It focusses on
dealing with scanned, pre-digital images, such as slides and photos, which are lacking the detailed EXIF metadata
(like precise GPS coordinates or exact capture dates) that many modern photo library applications rely upon.

Memoria provides the tools to manually enrich this metadata, allowing you to catalogue, rediscover, and share your memories with the context they deserve.

## Naming

**Memoria** can be translated from Latin as "memory", as that is what the project aims to help preserve and share with your family.

## Inspiration

This project was born out of another project I embarked on in late 2023, the scanning of thousands of slides from my
parents' and grandparents' trips and life. As I accumulated more and more images, with pictures of my family, their trips, and general life,
I found it hard to keep track of the images of people in particular. Then I
wanted to know where the picture was taken, roughly what it was about, an idea of the year, and maybe even month.

But I wasn't around for most of the images, so I had no idea about most of that. And so, this project was
born with the goal to assist one or more family members in sorting out all that information.

It allows one or more users (probably other family members) to view, sort, categorize old photographs,
slides, etc and then share with more users to view, remember and enjoy a little bit of history no one might have ever seen before. Because, after all,
who has a slide projector anymore?

## Features

- **Metadata Working Group Support**
  - **Face & Pet Support**
    - Uses the MWG Face & Pet regions, ties people and pets to the images where they are found
    - Includes the bounding box, which is displayed in the frontend
  - **Rough Location**:
    - Associate images with geographical locations—from broad country data down to specific sub-locations. This is ideal for images where only approximate places are known.
    - Uses the MWG location tags to build a rough idea of location for the image
    - If the MWG locations are not set, falls back to a tag based attempt to gather location information
  - **Rough Date**
    - Assign approximate or exact dates (year, month, day) with validity flags, perfect for when only a general timeframe is recalled.
    - Uses a tag based structure to store a rough idea of when the image was originally captured.
  - **Description**: Allows users to add image descriptions, stored per the MWG
  - **Title**: Although the MWG doesn't specify a title field, it is possible to set an image's title as well, delegating to EXIFTool what that sets
- **Albums**:
  - Group your images into thematic albums.
  - Crucially, **manually order images within albums**. This feature is perfect for reconstructing the original sequence of digitized slide carousels or the narrative flow of physical photo albums.
- **Multi-User & Multi-Family Support:**
  - Securely manage access for multiple individual users or distinct family groups.
  - Utilizes a robust **group-based permissions system** for images, albums, and other metadata, ensuring that private collections remain private and accessible only to authorized individuals or groups.
- **Robust Image Handling:**
  - Efficiently indexes your image library.
  - Generates and serves optimized image versions (thumbnails, larger web-display copies) for fast and responsive viewing, while preserving your originals.
  - Ensures metadata consistency by synchronizing database information with physical image files where appropriate, adhering to MWG standards.
- **Modern & Intuitive Interface:**
  - Experience a clean, responsive user interface built with React Bootstrap.
  - Choose between light and dark themes, with an option to follow your system's preference.
  - Navigate and manage your photos with ease

## Roadmap

### Markdown Support

- Make descriptions treated as Markdown text, with rendering and editor support
- Allows more robust descriptions, links, etc

### More Region Support

- Add, edit and delete boxes for faces and pets in images

### Frontend Error Handling

- Standardize error handling, using toasts or similar
- Break out the problem fields on forms to display more helpful text

### Advanced Searching

- Text based searching over description and captions
- Filter on images containing any people or all people
- Filter for images containing Person A & Person B IN Place between YEAR & YEAR
- Consider Mellisearch or similar tools

### AI Integration

- Semantic searching over descriptions and titles
- Automatic face tagging and recognition
  - Using either local or cloud AI models to find and recognize faces

### Task Status

- Integrate with Huey signals to provide task status and tracking
- Consider integrating websockets for more real-time status

### Tasks from Frontend

- Allow users to start an index, sync, etc task manually via the frontend

### Next & Previous

- Allow walking through all images in an album or folder using next and previous
- Potentially extend to include paginated all images display

### Documentation

- Add documentation for getting started
- Document the capabilities of each type of user, group, etc

### Async Support

- Given Django's current async support, look for opportunities to utilize it, either in the current state or future releases

### Testing

- Currently have PoC for testing the backend, needs to be expanded
- Determine how to test the frontend
- Integrate code coverage, including branches

## Tech Stack

- **Backend:**
  - Python
  - Django & Django Ninja (for REST APIs)
  - PostgreSQL (Database)
  - Valkey (Redis fork, for caching/Huey broker)
  - Huey (Task Queue)
- **Frontend:**
  - TypeScript
  - React
  - Vite (Build Tool)
  - pnpm (Package Manager)
  - React Bootstrap & Bootstrap Icons (UI)
  - Axios (HTTP Client)
- **DevOps & Tooling:**
  - Docker & Docker Compose
  - MkDocs (Documentation)
  - Go Task (Task Runner)
