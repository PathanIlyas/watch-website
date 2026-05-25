"""
CHRONOS startup script.
Run once after cloning or deploying:
    python startup.py
"""
import subprocess, sys

python = sys.executable

steps = [
    ([python, 'manage.py', 'migrate'],             'Applying migrations...'),
    ([python, 'manage.py', 'create_admin'],         'Creating admin user...'),
    ([python, 'manage.py', 'seed_watches'],         'Seeding watch collection...'),
    ([python, 'manage.py', 'collectstatic',
      '--noinput', '--clear'],                       'Collecting static files...'),
]

for cmd, label in steps:
    print(f'\n{"─"*50}\n  {label}\n{"─"*50}')
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f'  ✗ Step failed: {" ".join(cmd)}')
        sys.exit(result.returncode)

print('\n' + '═'*50)
print('  ✓ CHRONOS is ready.')
print('  Run:       python manage.py runserver')
print('  Site:      http://127.0.0.1:8000/')
print('  Register:  http://127.0.0.1:8000/accounts/register/')
print('  Login:     http://127.0.0.1:8000/accounts/login/')
print('  Dashboard: http://127.0.0.1:8000/dashboard/')
print('═'*50 + '\n')
