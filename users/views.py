from django.shortcuts import render, redirect
from authentication.decorators import profile_required
from .models import UserProfile
from .forms import UserProfileForm
from django.contrib import messages

@profile_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    edit_mode = request.GET.get("edit") == "true"

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        else:
            messages.error(
                request,
                "Please complete all required fields before saving changes."
            )
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "users/profile.html", {
        "profile": profile,
        "form": form,
        "edit_mode": edit_mode
    })


@profile_required
def dashboard(request):
    return render(request, 'users/dashboard.html')
