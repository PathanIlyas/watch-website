# Render Setup

Use this project as a Render Python web service with the included `render.yaml`.

## Required Render environment values

Keep these values in Render:

```env
DEBUG=False
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
SMS_PROVIDER=console
ADMIN_USERNAME=admin
ADMIN_EMAIL=your-email@gmail.com
ADMIN_PASSWORD=change-this-password
```

Do not manually set:

```env
DATABASE_URL=sqlite:///db.sqlite3
```

Render should provide `DATABASE_URL` automatically from the `chronos-db` PostgreSQL database in `render.yaml`.

## Deploy steps

1. Push this code to GitHub.
2. In Render, connect the repository.
3. Use the Blueprint / `render.yaml` setup.
4. After the first deploy, update `SITE_URL` to your real Render URL.
5. Change `ADMIN_EMAIL` and `ADMIN_PASSWORD`.
6. Use "Clear build cache and deploy" once after changing environment values.

On startup, `startup_render.py` automatically runs migrations, creates the admin user if needed, seeds the watch collection, and starts Gunicorn.
