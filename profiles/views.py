from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Profile

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if created:
        print(f"Profile created for {request.user.username}")

    return render(request, 'profile.html', {'profile': profile})
