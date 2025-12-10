from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from .forms import RegisterForm, LoginForm


#   SIGNUP VIEW

def signup_view(request):
    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data["user_name"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            confirm_password = form.cleaned_data["confirm_password"]

            # Check passwords match
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, "auth/register.html", {"form": form})

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered.")
                return render(request, "auth/register.html", {"form": form})

            # Check if username already exists
            if User.objects.filter(username=name).exists():
                messages.error(request, "Username already exists.")
                return render(request, "auth/register.html", {"form": form})

            # Create the user
            user = User.objects.create_user(
                username=name,
                email=email,
                password=password,
                is_active = False
            )

            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")

    return render(request, "auth/register.html", {"form": form})

#   LOGIN VIEW

def login_view(request):
    form = LoginForm()

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            # Check if email exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
                return render(request, "auth/login.html", {"form": form})

            # Authenticate using username 
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully!","Welcome {{user.username}}")
                # messages.success(request, "Welcome {{user.username}}")
                return redirect("/")  
            else:
                messages.error(request, "Incorrect password.")
                return render(request, "auth/login.html", {"form": form})

    return render(request, "auth/login.html", {"form": form})

#   LOGOUT VIEW

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    # messages.success(request, "Good bye {{user.username}}")

    return redirect("/")
