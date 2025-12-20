from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import UserProfile
from .forms import UserProfileForm


@login_required
def profile_view(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    # determine mode edit/view
    edit_mode = request.GET.get("edit") == "true"

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect("profile")  # return to view mode
    else:
        form = UserProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
        "edit_mode": edit_mode,
    }
    return render(request, "users/profile.html", context)

def dashboard(request):
    return render(request, 'users/dashboard.html')
