# OmniBot Architectural Roadmap & Future Plans

Hey team,

I've been reviewing the current state of the OmniBot codebase. While it's functional and modular, as we start adding more computationally intensive tasks (like face recognition, video rendering, and AI media generation), we're going to hit some serious scaling and performance bottlenecks. Here is the roadmap for how we should refactor and evolve the project over the next couple of sprints.

## 1. Decoupling Heavy Workloads (Task Queues)
Right now, commands like `/comparar_rostros` (using `face_recognition`) and `/crear_meme` (using `moviepy`) are running directly in the bot's process. These are CPU-bound operations. Even though we are deferring the Discord interactions, blocking the main thread or running heavy synchronous libraries without a proper thread pool will degrade the bot's responsiveness to other commands.
- **Action Item**: We need to introduce a message broker and task queue. I recommend standing up **Redis** and using **Celery** (or **RQ** if we want something lighter). The bot will simply dispatch the job to the queue and a separate pool of worker processes will handle the heavy lifting. We can then ping the user back via webhooks when the job completes.

## 2. Media Storage & Cleanup Strategies
We're currently saving temporary files directly to the local filesystem before uploading them to Discord. This is extremely brittle. If a command fails mid-execution, we leave orphaned `.mp4` and `.jpg` files lying around, which will eventually eat up all our disk space.
- **Action Item**: Move to an ephemeral object storage strategy. At the very least, we need robust `try/finally` blocks and Python's `tempfile` module to ensure temporary directories are nuked. Long term, if we plan to host generated content, we should push it to an S3 bucket with a 24-hour lifecycle deletion policy instead of attaching large files directly to Discord messages.

## 3. Containerization and Environment Consistency
Managing dependencies like `ffmpeg` (required by `spotdl` and `moviepy`) and `dlib` / `cmake` (required by `face_recognition`) directly on the host OS is a nightmare for onboarding new devs and deploying.
- **Action Item**: We must Dockerize this application. We need a multi-stage `Dockerfile` that installs all system-level dependencies. We also need a `docker-compose.yml` to spin up the bot along with the Redis instance and worker nodes.

## 4. State Persistence and Rate Limiting
We don't have a solid persistence layer yet. As we integrate expensive APIs or heavy compute tasks, we need to implement rate limiting per user and per guild to prevent abuse.
- **Action Item**: Let's integrate PostgreSQL. We can use `SQLAlchemy` (with async drivers) or `Prisma` for Python. This will let us track usage metrics, quotas, and handle guild-specific configurations cleanly.

Let's sync up on Monday to prioritize these items. I want to tackle the worker queue setup before we introduce any more heavy ML models.

Cheers,
Senior Developer
