# Deploy Online

This app is now deployment-ready as a single FastAPI web service. The backend serves both:

- The UI at `/`
- The API at `/docs`, `/signals`, `/portfolio`, `/risk`, `/report/daily`

## Recommended Simple Path: Render

1. Push this folder to a GitHub repository.
2. In Render, create a new Web Service from that repository.
3. Choose Docker as the runtime. Render will use the root `Dockerfile`.
4. Add an environment variable:

   ```text
   QUANT_DB_PATH=/data/quant.db
   ```

5. To make SQLite data persist across deploys, add a persistent disk mounted at:

   ```text
   /data
   ```

   Recommended settings:

   ```text
   Disk name: quant-data
   Mount path: /data
   Size: 1 GB or larger
   ```

   Only files under the disk mount path are preserved by Render, so the SQLite database must live at `/data/quant.db`.

6. Deploy.
7. Open `/health` on your Render URL and confirm:

   ```json
   "database": {
     "path": "/data/quant.db",
     "parent_writable": true
   }
   ```

8. Open your public Render URL and click `刷新市场数据`.

This repository also includes `render.yaml` with the same disk and environment variable settings for Blueprint-based Render configuration.

## Railway

1. Push to GitHub.
2. Create a Railway project from the repository.
3. Railway will detect the `Dockerfile`.
4. Add:

   ```text
   QUANT_DB_PATH=/data/quant.db
   ```

5. Ensure the service exposes HTTP traffic. The Docker command listens on `0.0.0.0:$PORT`.
6. Deploy and open the generated public URL.

## Fly.io

1. Install and log in to `flyctl`.
2. From the project root:

   ```bash
   fly launch
   fly deploy
   ```

3. For persistent SQLite storage, create and mount a volume at `/data`.
4. Open the generated Fly URL and refresh market data.

## Important Notes

- The cloud URL is public. Do not add real broker credentials or private account data without authentication.
- SQLite is fine for a personal dashboard. For a production multi-user app, move holdings and price history to Postgres.
- `yfinance` depends on Yahoo Finance availability and can occasionally rate-limit or fail. The UI refresh button can be retried.
- The app listens on the platform-provided `PORT`, which is required by common PaaS providers.
