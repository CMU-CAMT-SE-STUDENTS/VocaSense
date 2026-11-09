# VocaSense

## Project Overview

VocaSense is a browser-based voice analysis application. The repository contains two deployable services:

| Service | Technology | Container role |
| --- | --- | --- |
| Frontend | Vue 3, Vite, Node.js 24 | Builds static assets and serves them with unprivileged Nginx on port 8080. Nginx proxies `/api/*` and `/health` to the backend. |
| Backend | FastAPI, Uvicorn, Python 3.11 | Provides voice analysis and recommendation APIs on port 8000. |

Supabase provides managed authentication and Postgres access. This Compose setup does not run a database container. Gemini wording enhancement is optional; deterministic recommendations remain available without a Gemini key.

## Prerequisites

- Git 2.30 or later.
- Docker Engine 24 or later, or current Docker Desktop.
- Docker Compose v2 (`docker compose`, included with Docker Desktop and the Docker Engine plugin).
- For native development outside Docker: Node.js 22.12 or later and npm, or Python 3.11 with pip.
- A Supabase project for authentication and database-backed features.

## Environment Configuration

Copy the root example file to `.env` and fill in the values for your environment:

```sh
cp .env.example .env
```

PowerShell equivalent:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`. The Supabase publishable key and project URL are public browser configuration. Protect database access with Supabase Row Level Security. The Supabase secret/service-role key and Gemini API key are sensitive backend credentials and must never be added to a `VITE_` variable or frontend image build argument.

| Variable | Required? | Purpose / example | Where to obtain it | Exposure |
| --- | --- | --- | --- | --- |
| `FRONTEND_PORT` | Optional | Host port for the frontend; `8080` | Choose an unused port on the host | Public port setting |
| `BACKEND_PORT` | Optional | Host port for direct local API access; `8000` | Choose an unused port on the host | Public port setting; production example does not publish it |
| `VITE_SUPABASE_URL` | Required to build the frontend | Supabase project URL, e.g. `https://your-project.supabase.co` | Supabase Dashboard → Project Settings → API | Public; embedded in browser assets |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Required to build the frontend | Supabase publishable/anon key | Supabase Dashboard → Project Settings → API Keys | Public by design; embedded in browser assets; secure data with RLS |
| `VITE_API_BASE_URL` | Optional build-time value | API base URL; leave blank to use the same-origin `/api` Nginx proxy | Set only when serving the API at another URL | Public; embedded in browser assets |
| `SUPABASE_URL` | Required at runtime for database-backed backend features | Supabase project URL | Supabase Dashboard → Project Settings → API | Public configuration, backend runtime only |
| `SUPABASE_SECRET_KEY` | Required at runtime for database-backed backend features | Server-side Supabase secret key | Supabase Dashboard → Project Settings → API Keys | Sensitive; backend runtime only |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional legacy alternative | Legacy server-side service-role key | Supabase Dashboard → Project Settings → API | Sensitive; backend runtime only; use instead of the secret key only when needed |
| `GEMINI_API_KEY` | Optional | Enables Gemini wording enhancement; blank disables it | Google AI Studio → API keys | Sensitive; backend runtime only |
| `GEMINI_MODEL` | Optional | Model name; defaults to `gemini-3.5-flash-lite` | Use a model available to your Google AI Studio project | Backend runtime setting |
| `CORS_ORIGINS` | Optional | Comma-separated allowed browser origins | Set to the exact public frontend origins; local default is in `.env.example` | Public URLs; backend runtime setting |
| `IMAGE_TAG` | Production Compose only, optional | GHCR tag to pull; defaults to `latest` | A workflow-generated `v*` or `sha-*` tag | Public image version setting |

The two `VITE_` Supabase variables are read when Vite builds the frontend. Changing them requires rebuilding the frontend image. Backend credentials are supplied only when the backend container starts.

## Local Development

Clone the repository and configure environment variables:

```sh
git clone https://github.com/muanpee/VocaSense.git
cd VocaSense
cp .env.example .env
```

Set the Supabase frontend and backend values in `.env`. You can run the frontend and backend containers before entering server credentials, but database-backed API routes will require the server-side Supabase key.

Build and start the application:

```sh
docker compose build
docker compose up -d
```

Open <http://localhost:8080>. The direct backend API and interactive docs are available at <http://localhost:8000/docs> for local development. Check status and logs with:

```sh
docker compose ps
docker compose logs -f
docker compose logs -f backend
```

After changing application code, rebuild and recreate the services:

```sh
docker compose up --build -d
```

Stop the local stack with:

```sh
docker compose down
```

## Production Deployment

The production example pulls prebuilt images and does not publish the backend port. On a Linux host with Docker Compose v2:

1. Create a deployment directory, copy `docker-compose.example.yml` into it, and create `.env` from `.env.example`. Keep `.env` readable only by the deployment operator.
2. Set `SUPABASE_URL` and `SUPABASE_SECRET_KEY`. Add `GEMINI_API_KEY` only if Gemini wording is enabled. Set `FRONTEND_PORT` if port 8080 is already in use.
3. If the GHCR packages are private, authenticate using an account that can read both packages:

   ```sh
   printf '%s' "$GHCR_READ_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

   The token needs `read:packages` access to both packages. Do not save it in `.env` or shell history.
4. Validate and pull the images, then start the services:

   ```sh
   docker compose -f docker-compose.example.yml config
   docker compose -f docker-compose.example.yml pull
   docker compose -f docker-compose.example.yml up -d
   ```

5. Verify both container health and the frontend endpoint:

   ```sh
   docker compose -f docker-compose.example.yml ps
   curl --fail http://localhost:8080/healthz
   curl --fail http://localhost:8080/health
   ```

6. View service logs:

   ```sh
   docker compose -f docker-compose.example.yml logs -f
   ```

7. To update to the latest default-branch build, pull and recreate:

   ```sh
   docker compose -f docker-compose.example.yml pull
   docker compose -f docker-compose.example.yml up -d
   ```

   For a versioned or commit image, set `IMAGE_TAG=v1.0.0` or `IMAGE_TAG=sha-<short-commit>` in `.env`, then pull and recreate.
8. To roll back, set `IMAGE_TAG` to a previously published `v*` or `sha-*` tag, then run the pull and `up -d` commands again.

The GHCR images are not made public by this workflow. If packages remain private, the server must authenticate before pulling.

## GitHub Actions

`.github/workflows/docker-publish.yml` builds and publishes the frontend and backend images independently. It runs on pushes to `main`, tags matching `v*`, and manual `workflow_dispatch` runs. It uses Buildx, OCI metadata, and GitHub Actions BuildKit cache. Image tags include `latest` on the default branch, the original version tag (for example `v1.0.0`), and `sha-<commit>`.

Image names:

- `ghcr.io/cmu-camt-se-students/vocasense-frontend`
- `ghcr.io/cmu-camt-se-students/vocasense-backend`

The workflow grants `contents: read` and `packages: write`, and logs in to GHCR with the repository's `GITHUB_TOKEN`. Add these **repository Actions variables** for the frontend build:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- Optional `VITE_API_BASE_URL` (leave unset for the Nginx proxy)

These are public client configuration values, not backend secrets. Runtime backend credentials belong in the deployment host's `.env` or secret manager and are not needed by the image publishing workflow. The images are published under `ghcr.io/cmu-camt-se-students`; once this branch is synced to the fork in that organization, the workflow authenticates with that repository's `GITHUB_TOKEN`. If the workflow fails, inspect the failed run under the repository's **Actions** tab and check the named step.

## Troubleshooting

- **Docker build fails:** run `docker compose build --no-cache backend` or `docker compose build --no-cache frontend`; inspect the first failed install/build command. Confirm network access to PyPI/npm and enough disk space.
- **Missing environment values:** check that `.env` is in the project root and was copied from `.env.example`. Build-time `VITE_` values require rebuilding the frontend.
- **Container startup or health check fails:** inspect `docker compose logs backend frontend` and `docker compose ps`. The backend may need up to a minute to become healthy on first startup.
- **Port conflict:** change `FRONTEND_PORT` or `BACKEND_PORT` in `.env`, then recreate the services.
- **Database connection or authorization fails:** verify `SUPABASE_URL`, the backend server-side key, Supabase network availability, schema migrations, and Row Level Security policies. Do not use the public publishable key as the backend server key.
- **GHCR authentication or permission error:** confirm the workflow has `packages: write`, the fork is in the expected organization, and the package name matches the image namespace.
- **Image pull fails:** confirm the image tag exists, package visibility/access allows the host to pull it, and `docker login ghcr.io` used an account/token with `read:packages`.
- **GitHub Actions failure:** check workflow permissions, the frontend repository variables, the GHCR package access settings, and the detailed logs in the Actions run. Never print tokens while debugging.
