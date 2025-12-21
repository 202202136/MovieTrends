Docker usage

Build the image (example):

```bash
docker build -t your_dockerhub_username/movietrends:latest .
```

Run with Docker (example):

```bash
docker run -p 5000:5000 -e TMDB_API_KEY=your_key -v "${PWD}/data:/app/data" your_dockerhub_username/movietrends:latest
```

Or use docker-compose:

```bash
TMDB_API_KEY=your_key docker-compose up --build
```

Render notes:

- For Render's Docker deployment, point the service to this repo or push the image to Docker Hub and reference the image in Render.
- Ensure you set `TMDB_API_KEY` and `SECRET_KEY` in Render's environment settings. Render provides `$PORT`; the container uses that env.

Persistence note:

- The SQLite file is stored in `data/database.db` and is mounted into the container via a volume when using Docker Compose or the `-v` flag. On Render, use a Persistent Disk or switch to a hosted Postgres for production.
- To reinitialize the DB, remove `data/database.db` and restart the container; `init_db()` runs at container start.
