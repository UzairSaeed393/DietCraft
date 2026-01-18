from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from users.models import UserProfile
from users.forms import UserProfileForm
from .forms import RegisterForm, LoginForm
from .models import UserOTP
#   SIGNUP VIEW
from django.contrib.auth.decorators import login_required

def signup_view(request):
    form = RegisterForm()
    # form = RegisterForm()
    if request.method == "POST":
        user_name = request.POST.get("user_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")
                
        if len(password) < 5:
            messages.error(request, "Password must contain at least one number & 5 characters long.")
            return redirect("signup")
        
        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one number & 5 characters long.")
            return redirect("signup")
        
        if User.objects.filter(username=user_name).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        # Create inactive user
        user = User.objects.create_user(
            username=user_name,
            email=email,
            password=password,
            is_active=False
        )

        # Create OTP
        otp_obj = UserOTP.objects.create(user=user)
        otp_obj.generate_otp()

        # Send OTP email
        send_mail(
            subject="Your DietCraft Verification Code",
            message=f"Your OTP For DietCraft is {otp_obj.otp_code}.It will expire in 5 min. If you did not ask for otp ignore it",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )

        messages.success(request, "OTP sent to your email. Please verify your account.")
        return redirect("verify", user_id=user.id)
    return render(request, "auth/register.html", {"form": form})

def verify_otp_view(request, user_id):
    user = User.objects.get(id=user_id)
    otp_obj = UserOTP.objects.get(user=user)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        if entered_otp == otp_obj.otp_code:
            user.is_active = True
            user.save()
            otp_obj.delete()

            messages.success(request, "Account verified! You can now log in.")
            return redirect("login")

        messages.error(request, "Invalid OTP. Try again.")

    return render(request, "auth/verify.html", {"user_id": user_id})
def resend_otp(request, user_id):
    user = User.objects.get(id=user_id)
    otp_obj = UserOTP.objects.get(user=user)

    otp_obj.generate_otp()

    send_mail(
        subject="Your New DietCraft Verification Code",
        message=f"Your new OTP for DietCraft is {otp_obj.otp_code}. It expires in 5 minutes.",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
    )

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify", user_id=user_id)


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
                
            if not user.is_active:
                messages.error(request, "Account inactive. Please verify your email.")
                return redirect("login")
            # Authenticate using username 
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome {user.username}!")
                # If user already has a profile, send them to home; otherwise prompt profile form
                try:
                    has_profile = UserProfile.objects.filter(user=user).exists()
                except Exception:
                    has_profile = False

                if has_profile:
                    return redirect("home")
                return redirect("profileform")
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

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not registered.")
            return redirect("forgot_password")

        otp_obj, created = UserOTP.objects.get_or_create(user=user)
        otp_obj.generate_otp()

        send_mail(
            subject="DietCraft Password Reset OTP",
            message=f"Your password reset OTP from DietCraft is {otp_obj.otp_code}.OTP code will expire in 5 min .If you did not ask for otp ignore it",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )

        messages.success(request, "OTP sent to your email.")
        return redirect("forgot_verify", user_id=user.id)

    return render(request, "auth/forgot_password.html")

def forgot_verify_view(request, user_id):
    user = User.objects.get(id=user_id)
    otp_obj = UserOTP.objects.get(user=user)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        if otp_obj.is_expired():
            messages.error(request, "OTP expired.")
            return redirect("forgot_password")

        if entered_otp == otp_obj.otp_code:
            return redirect("reset_password", user_id=user.id)

        messages.error(request, "Invalid OTP.")

    return render(request, "auth/verify.html", {"user_id": user_id})

def reset_password_view(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password", user_id=user.id)

        if len(password) < 5:
            messages.error(request, "Password must be at least 5 characters.")
            return redirect("reset_password", user_id=user.id)
        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one number & 5 characters long.")
            return redirect("signup")
        # IMPORTANT: This hashes the password
        user.set_password(password)
        user.save()

        # Cleanup OTP
        UserOTP.objects.filter(user=user).delete()

        messages.success(request, "Password updated successfully. You can now log in.")
        return redirect("login")

    return render(request, "auth/new_password.html")

@login_required
def profile_form(request):

    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == "POST":
        # {% csrf_token %}
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            # MealPlan.objects.create(user=request.user)
            messages.success(request, "Profile created successfully.")
            return redirect("home")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "auth/profileform.html", {
        "form": form
    })