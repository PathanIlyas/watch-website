import os
import subprocess
import sys


def run_step(command, label):
    print(f"\n--- {label} ---", flush=True)
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"Step failed: {' '.join(command)}", flush=True)
        sys.exit(result.returncode)


python = sys.executable

run_step([python, "manage.py", "migrate", "--noinput"], "Applying database migrations")
run_step([python, "manage.py", "create_admin"], "Creating admin user if needed")
run_step([python, "manage.py", "seed_watches"], "Seeding default watch collection")

port = os.environ.get("PORT", "8000")
os.execvp(
    "gunicorn",
    [
        "gunicorn",
        "core.wsgi:application",
        "--bind",
        f"0.0.0.0:{port}",
        "--log-file",
        "-",
    ],
)
