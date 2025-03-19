from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('editor', 'Editor'), ('viewer', 'Viewer')], default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
