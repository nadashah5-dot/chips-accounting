import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accounting_project.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME")
email = os.getenv("DJANGO_SUPERUSER_EMAIL")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email or "", password=password)
        print("✅ Superuser created")
    else:
        print("ℹ️ Superuser already exists")
else:
    print("⚠️ Missing DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD")
