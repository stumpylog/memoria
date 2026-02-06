# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Memoria** is a full-stack web application for organizing, categorizing, and enriching metadata for scanned pre-digital images (slides, photos). It helps families sort and catalog scanned images with rich metadata including people, pets, locations, dates, and albums.

**Tech Stack:**
- **Backend**: Django 5.2 + Django Ninja (REST API), PostgreSQL, Valkey/Redis, Huey (task queue)
- **Frontend**: React 19 + TypeScript, Vite, TanStack Query, React Bootstrap
- **Package Managers**: uv (Python), pnpm (Node.js)
- **Task Runner**: Go Task (taskfile.dev)

## Common Commands

### Development

```bash
# Install all dependencies (Python + Node.js)
task deps:install

# Start all development servers (backend, frontend, docs)
task dev

# Start individual servers
task backend:dev              # Django server at http://localhost:8000
task src-frontend:dev         # Vite dev server at http://localhost:5173
task docs:dev                 # MkDocs server at http://localhost:8001
```

### Testing

```bash
# Run backend tests with pytest
task test
task backend:test

# Run a single test file
cd src-backend
uv run pytest tests/test_specific.py

# Run a single test function
cd src-backend
uv run pytest tests/test_specific.py::test_function_name

# Run with verbose output
cd src-backend
uv run pytest -v
```

### Linting

```bash
# Lint everything (backend + frontend)
task lint

# Backend only (ruff + mypy)
task backend:lint
cd src-backend
uv run ruff check . --fix
uv run mypy .

# Frontend only (ESLint + Prettier + stylelint)
task src-frontend:lint
cd src-frontend
pnpm lint
pnpm format
pnpm lint:styles
```

### Building

```bash
# Build all project artifacts
task build

# Build individual components
task backend:build
task src-frontend:build
task docs:build
```

### Database Migrations

```bash
# Create new migrations
task backend:migrations:makemigrations
cd src-backend
uv run python manage.py makemigrations

# Apply migrations
task backend:migrations:migrate
cd src-backend
uv run python manage.py migrate
```

### API Client Generation

The frontend uses an auto-generated TypeScript client from the backend's OpenAPI schema:

```bash
# Export OpenAPI schema from backend + generate frontend client
task api:update-client

# Or run steps individually:
task backend:api:export-schema    # Exports to api-spec.json
task src-frontend:api:generate-client  # Generates TypeScript client
```

**When to run**: After changing Django Ninja schemas, routes, or endpoint signatures.

### Image Indexing (Management Commands)

```bash
cd src-backend

# Index images with permission groups
uv run python manage.py index \
  --root-dir /path/to/photos \
  --view-group "Family Viewers" \
  --edit-group "Family Editors" \
  /path/to/photos/vacation

# Options:
# --hash-threads N      # Parallel hashing threads (default: 4)
# --overwrite          # Replace existing groups instead of merging
# --synchronous        # Run immediately instead of queuing to Huey
```

## High-Level Architecture

### Backend Architecture (Django + Django Ninja)

#### API Organization

Routes are organized by feature in `src-backend/memoria/routes/`:

```
routes/
├── albums/        # Album CRUD, image ordering
├── authentication/# Login, logout, CSRF token
├── folders/       # Hierarchical folder structure
├── groups/        # Permission group management
├── images/        # Core image operations, metadata
├── locations/     # Geographic location data
├── people/        # Person management, face regions
├── pets/          # Pet management, pet regions
├── system/        # Settings, statistics
└── users/         # User profiles

Each feature folder contains:
├── api.py         # Django Ninja endpoints
├── schemas.py     # Pydantic request/response schemas
└── filters.py     # (Optional) FilterSchema classes
```

#### Permission System

**Group-Based Access Control**: All protected entities (Image, Album, Person, Pet, Folder) have two M2M relationships:
- `view_groups` - Users can view but not edit
- `edit_groups` - Users can edit (implies view access)

**Permission Filtering Pattern** (CRITICAL):
```python
# ALWAYS filter querysets at database level
images = Image.objects.permitted(request.user)  # or .viewable_by(user)
image = get_object_or_404(Image.objects.editable_by(request.user), pk=id)

# NEVER fetch then check - use queryset filtering
```

**Custom QuerySets**: All models with permissions inherit from `PermittedQueryset` with methods:
- `.permitted(user)` or `.viewable_by(user)` - View access
- `.editable_by(user)` - Edit access
- Superusers bypass all checks

#### Core Models

**Image** (`models/image.py`):
- **Deduplication**: `original_checksum` (blake3) for exact content match, `phash` for perceptual similarity
- **Relationships**: Folder (hierarchy), RoughDate, RoughLocation, People (M2M with bounding boxes), Pets (M2M with bounding boxes), Tags (hierarchical)
- **Metadata Sync**: `is_dirty` flag marks images needing sync back to files (via signals)
- **Soft Delete**: `deleted_at` timestamp instead of hard deletion

**RoughDate** (`models/metadata.py`):
- Flexible precision: year (required), month (optional), day (optional)
- `comparison_date` field for sorting (fills missing parts with 1)
- Unique constraints per precision level

**RoughLocation** (`models/metadata.py`):
- Hierarchical: country_code (required), subdivision_code, city, sub_location
- Uses ISO 3166 codes with `simpleiso3166` library for resolution
- Human-readable names via properties

**Person/Pet with Bounding Boxes**:
- Through models: `PersonInImage`, `PetInImage` (inherit from `AbstractBoxInImage`)
- Normalized coordinates (0.0-1.0): `center_x`, `center_y`, `height`, `width`
- Created from MWG Region metadata

#### Image Processing Pipeline

**Indexing Flow** (`imageops/index.py`):
1. **Hash Calculation**: blake3 (content) + phash (perceptual)
2. **Three Scenarios**:
   - **New Image**: Extract metadata, generate WebP derivatives (thumbnail + large), create DB records
   - **Moved Image**: Same checksum, different path → update path, rebuild folder structure
   - **Replaced Image**: Same path, different checksum → clear metadata, re-extract, regenerate derivatives
3. **Metadata Extraction** (`imageops/metadata.py`):
   - MWG fields (face/pet regions, location)
   - Hierarchical keywords (tags, dates, locations as fallback)
   - Uses `exifmwg` library for reading
4. **Output**:
   - `MEDIA_ROOT/thumbnails/{image_fs_id}.webp` (max 512px by default)
   - `MEDIA_ROOT/larger-size/{image_fs_id}.webp` (max 2560px, quality 90)
   - `image_fs_id` = zero-padded 10-digit PK (e.g., `0000000042`)

**File Locking**: Tree operations (folders, tags) use file locks (`utils/locking.py`) to prevent race conditions.

#### Task Queue (Huey)

**Configuration**:
- Immediate (synchronous) mode in DEBUG for testing
- Redis-backed in production
- Tasks in `tasks/images.py`: `@db_task()` for single execution, `@db_periodic_task()` for cron

**Invocation**:
```python
if synchronous:
    task_function.call_local(args)  # Immediate execution
else:
    task_function(args)  # Queue to Huey
```

**Batch Processing**: Images processed in configurable batches (default 10) to avoid overwhelming the queue.

#### Authentication

Multiple auth levels in `common/auth.py`:
- `active_user_auth` - Authenticated + active
- `active_staff_auth` - Staff only (403 if not staff)
- `active_superuser_auth` - Superuser only
- Async variants: `async_active_user_auth`, etc.

**Pattern**: 401 for unauthenticated, 403 for authenticated but unauthorized.

#### Database Considerations

- **SQLite**: Configured with WAL mode, IMMEDIATE transactions, optimized for concurrent access
- **PostgreSQL**: Production default with connection pooling
- **Indexes**: On foreign keys, common filters (`original_checksum`, `phash`, `folder_id`, `date__comparison_date`)

### Frontend Architecture (React + TypeScript)

#### Auto-Generated API Client

**Generation**: `@hey-api/openapi-ts` generates TypeScript client from `api-spec.json`:
```
src/api/
├── @tanstack/
│   └── react-query.gen.ts    # Query hooks, mutation factories
├── client/
│   └── client.gen.ts         # Axios client
├── sdk.gen.ts                # Direct API functions
└── types.gen.ts              # All TypeScript types
```

**Usage Patterns**:
```typescript
// TanStack Query hook (preferred)
const { data, isLoading } = useQuery(
  getSingleAlbumInfoOptions({ path: { album_id: id } })
);

// Mutation
const mutation = useMutation(createAlbumMutation());
mutation.mutate({ body: { name: "Album" } });

// Direct SDK call (no React Query)
const response = await getSingleAlbumInfo({ path: { album_id: 1 } });
```

**CSRF Handling** (`api-config.ts`):
- Token fetched on app initialization (`initializeCsrfToken()`)
- Axios interceptor auto-injects token for POST/PUT/DELETE/PATCH
- Dual-sourced: in-memory variable + cookie fallback

#### Component Organization

```
components/
├── album/              # Album-specific components
├── common/             # Reusable components (ErrorToast, ProtectedRoute, ThemedSelect)
├── folder/             # Folder management
├── image/              # Image display, editing (14 components)
├── layout/             # NavigationBar
├── people/             # Person management
├── pets/               # Pet management
└── user-management/    # User CRUD

pages/                  # 15 page components (lazy-loaded)
├── HomePage.tsx
├── ImageGalleryPage.tsx
├── ImageDetail.tsx
├── AlbumsPage.tsx
├── PeoplePage.tsx
└── ...
```

**Component Patterns**:
- Typed props interfaces: `interface ComponentProps { ... }`
- Presentational vs. Container: Pages fetch data, components receive via props
- Modal pattern: `show`, `onHide`, `onUpdated` props with `useForm` integration

#### State Management (No Redux/Zustand)

**Layered Approach**:
1. **Server State**: TanStack Query (all API data)
   - Configured with 5-minute stale time, no auto-refetch on window focus
   - Query invalidation on mutations instead of optimistic updates
2. **Authentication**: `AuthContext` (user, profile, login/logout, global error state)
3. **Theme**: `ThemeContext` (light/dark/system with localStorage persistence)
4. **URL State**: Filter parameters, pagination via `useSearchParams`
5. **Local State**: UI state (modals, forms) via `useState`, `useForm`

**Query Pattern**:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["resource", id, filters],
  queryFn: async ({ signal }) => {
    const response = await apiFunction({ query: { ...filters }, signal });
    return response.data;
  },
  enabled: !!id,
  placeholderData: keepPreviousData,  // Smooth pagination
});
```

**Mutation Pattern**:
```typescript
const mutation = useMutation({
  mutationFn: (data) => updateApiFunction({ path: { id }, body: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["resource", id] });
    queryClient.invalidateQueries({ queryKey: ["resources"] });
    onComplete();
  },
});
```

#### React Router Structure

- **Lazy Loading**: All pages lazy-loaded for code splitting
- **Nested Layout**: `AppLayout` wraps protected routes with `NavigationBar`
- **Protected Routes**: `ProtectedRoute` HOC checks `AuthContext.isAuthenticated`
- **URL State**: Pagination and filters in URL query params for shareability

#### Form Handling (React Hook Form)

**Standard Pattern**:
```typescript
const { register, handleSubmit, formState, reset } = useForm<FormType>({
  defaultValues: { /* initial values */ },
});

// Reset when modal opens
useEffect(() => {
  if (show) {
    reset({ name: entity.name, description: entity.description || "" });
  }
}, [show, reset, entity]);

<Form onSubmit={handleSubmit(onSubmit)}>
  <Form.Control
    {...register("fieldName", { required: "Field is required" })}
    isInvalid={!!formState.errors.fieldName}
  />
</Form>
```

**Controller Pattern** (for custom inputs like react-select):
```typescript
<Controller
  name="people_ids"
  control={control}
  render={({ field }) => (
    <ThemedSelect
      {...field}
      isMulti
      options={options}
      onChange={(selected) => field.onChange(selected.map(o => o.value))}
    />
  )}
/>
```

**Partial Updates**: Only send changed fields using `formState.isDirty` and `formState.dirtyFields`.

#### Bootstrap Integration + Theming

- **Bootstrap 5.3.8**: Uses `data-bs-theme` attribute on `<html>` for theming
- **react-bootstrap 2.10**: Component library for all UI
- **Theme System**: `ThemeContext` manages light/dark/system with localStorage persistence
- **ThemedSelect**: Custom wrapper for `react-select` with Bootstrap-consistent styling

#### Key Conventions

**Naming**:
- Components: PascalCase (e.g., `ImageDetailPage`)
- Files: Match component name (e.g., `ImageDetailPage.tsx`)
- Hooks: camelCase with `use` prefix (e.g., `useAuth`, `useDebounce`)
- Props: `{ComponentName}Props`
- Generated files: `*.gen.ts` suffix

**Import Order**:
```typescript
// Type imports first
import type { TypeA } from "...";

// External libraries
import React, { useState } from "react";
import { Button } from "react-bootstrap";

// API and generated code
import { apiFunction } from "../api";

// Internal components
import ComponentA from "./ComponentA";
```

## Key Architectural Patterns

### Backend: Permission Filtering is Database-Level

Always filter at queryset level, never fetch then check:
```python
# CORRECT
images = Image.objects.permitted(request.user).filter(...)

# WRONG - security risk and performance issue
images = Image.objects.all()
return [img for img in images if user can view img]
```

### Backend: Dirty Flag + Signals

- Metadata changes automatically mark images dirty via Django signals
- Use `.update()` to bypass signals when marking clean
- Sync task (TODO: incomplete) will write dirty metadata back to files

### Backend: Hash-Based Deduplication

- `original_checksum` (blake3) for exact content matching
- Path is secondary; checksum is the true unique identifier
- Moved images detected by checksum match with different path

### Backend: Tree Models Need Locking

- `django-treenode` maintains adjacency lists
- Concurrent folder/tag creation needs file locks (`file_lock_with_cleanup`)
- Per-parent uniqueness constraints

### Frontend: Generated-First API

- 100% type-safe API client auto-generated from OpenAPI spec
- TanStack Query hooks generated alongside SDK functions
- Run `task api:update-client` after backend schema changes

### Frontend: Query Invalidation Over Optimistic Updates

- Mutations invalidate related queries on success
- Simplicity and correctness prioritized over perceived performance
- `placeholderData: keepPreviousData` for smooth pagination UX

### Frontend: URL as State

- Filter parameters and pagination in URL for shareability
- Uses `useSearchParams` hook
- Browser back/forward and refresh work correctly

### Frontend: Two Contexts Only

- `AuthContext` for authentication and global error state
- `ThemeContext` for UI theme
- Everything else is local state or TanStack Query

## Common Development Workflows

### Adding a New API Endpoint

1. **Backend**:
   - Add endpoint to appropriate `routes/{feature}/api.py`
   - Create Pydantic schemas in `schemas.py` if needed
   - Test with pytest
   - Export schema: `task backend:api:export-schema`

2. **Frontend**:
   - Generate client: `task src-frontend:api:generate-client`
   - Use generated hooks/functions in components
   - TypeScript will catch any breaking changes

### Adding a New Model Field

1. **Backend**:
   - Add field to model in `models/`
   - Create migration: `task backend:migrations:makemigrations`
   - Apply migration: `task backend:migrations:migrate`
   - Update schemas in `routes/{feature}/schemas.py`
   - Update metadata extraction if needed (`imageops/metadata.py`)

2. **Frontend**:
   - Regenerate client: `task api:update-client`
   - Update components to display/edit new field

### Debugging Permission Issues

1. Check queryset filtering:
   ```python
   # Add logging
   qs = Image.objects.permitted(request.user)
   print(qs.query)  # See generated SQL
   ```

2. Verify group membership:
   ```python
   print(user.groups.all())
   print(image.view_groups.all())
   print(image.edit_groups.all())
   ```

3. Check if superuser bypass is active:
   ```python
   print(user.is_superuser)  # Should bypass all checks
   ```

### Running Image Processing Tasks

```bash
cd src-backend

# Synchronous (immediate, good for testing)
uv run python manage.py index --synchronous --root-dir /photos /photos/vacation

# Asynchronous (queued to Huey, production)
uv run python manage.py index --root-dir /photos /photos/vacation

# Monitor Huey workers (separate terminal)
uv run python manage.py run_huey
```

## Important Files

### Backend
- `src-backend/memoria/api.py` - Main API router configuration
- `src-backend/memoria/models/` - Database models
- `src-backend/memoria/routes/` - Feature-based API endpoints
- `src-backend/memoria/common/auth.py` - Authentication levels
- `src-backend/memoria/imageops/` - Image processing pipeline
- `src-backend/memoria/tasks/` - Huey background tasks
- `src-backend/memoria/settings.py` - Django configuration

### Frontend
- `src-frontend/src/App.tsx` - Router setup, QueryClient config
- `src-frontend/src/api-config.ts` - CSRF handling, client config
- `src-frontend/src/contexts/` - AuthContext, ThemeContext
- `src-frontend/src/pages/` - Page components (lazy-loaded)
- `src-frontend/src/api/` - Auto-generated API client (DO NOT EDIT)
- `src-frontend/openapi-ts.config.ts` - API generation config

### Configuration
- `Taskfile.yml` - Root task definitions
- `src-backend/Taskfile.yml` - Backend-specific tasks
- `src-frontend/Taskfile.yml` - Frontend-specific tasks
- `pyproject.toml` (root) - Python workspace configuration
- `src-backend/pyproject.toml` - Backend dependencies
- `src-frontend/package.json` - Frontend dependencies
- `api-spec.json` - Generated OpenAPI schema (updated by backend)

## Gotchas and Common Mistakes

### Backend

1. **Forgetting `.permitted(user)` on querysets** - Always filter at database level
2. **Using `.save()` to mark images clean** - Use `.update()` to bypass signals
3. **Forgetting `.distinct()` after M2M filters** - Can return duplicate rows
4. **Not using file locks for tree operations** - Can corrupt adjacency lists
5. **Creating thousands of single-item tasks** - Batch operations instead
6. **Checking permissions after fetching** - Filter queryset before retrieval

### Frontend

1. **Editing generated files** - Never edit files in `src/api/*.gen.ts`
2. **Not invalidating queries after mutations** - Data becomes stale
3. **Using nested objects in queryKey** - Use stable primitives instead
4. **Forgetting to debounce filter inputs** - Can spam API
5. **Not handling loading/error states** - Poor UX
6. **Putting server state in Context** - Use TanStack Query instead

## Version Synchronization

The project uses a single VERSION file at the root:
```bash
# Update version across all files
task version:sync
```

This synchronizes version to:
- `src-backend/pyproject.toml`
- `src-docs/pyproject.toml`
- `src-frontend/package.json`
