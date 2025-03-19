from django.apps import AppConfig
from django.contrib.auth import get_user_model
import os

class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiles'

    def ready(self):
        # Run only in production to avoid local issues
        if os.getenv("CREATE_SUPERUSER", "False") == "True":
            User = get_user_model()
            if not User.objects.filter(username=os.getenv("DJANGO_SUPERUSER_USERNAME")).exists():
                User.objects.create_superuser(
                    username=os.getenv("DJANGO_SUPERUSER_USERNAME"),
                    email=os.getenv("DJANGO_SUPERUSER_EMAIL"),
                    password=os.getenv("DJANGO_SUPERUSER_PASSWORD")
                )
                print("✅ Superuser created successfully!")