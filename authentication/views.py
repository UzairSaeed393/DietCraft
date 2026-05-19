from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.utils import formataddr
from users.models import UserProfile
from users.forms import UserProfileForm
from users.utils import delete_user_plans
from .forms import RegisterForm, LoginForm
from .models import UserOTP, PendingSignup
from django.contrib.auth.decorators import login_required


def send_verification_email(to_email, otp_code):
    """Send a verification email and return the mail send count."""
    sender = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    recipient = (to_email or "").strip()
    subject = "DietCraft verification code"
    text_body = (
        f"Hello,\n\n"
        f"Your DietCraft verification code is: {otp_code}\n\n"
        f"This code expires in 5 minutes.\n\n"
        f"If you did not request this email, you can ignore it.\n"
    )
    html_body = (
        f"<p>Hello,</p>"
        f"<p>Your DietCraft verification code is <strong>{otp_code}</strong>.</p>"
        f"<p>This code expires in 5 minutes.</p>"
        f"<p>If you did not request this email, you can ignore it.</p>"
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=formataddr(("DietCraft", sender)),
        to=[recipient],
    )
    message.attach_alternative(html_body, "text/html")
    return message.send(fail_silently=False)

def signup_view(request):
    # Pre-fill email/username if provided via query (e.g., from verify Change Email)
    initial_email = request.GET.get('email') if request.method == 'GET' else None
    initial_username = request.GET.get('username') if request.method == 'GET' else None
    initial = {}
    if initial_email:
        initial['email'] = initial_email
    if initial_username:
        initial['user_name'] = initial_username
    form = RegisterForm(initial=initial if initial else None)
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please enter a valid username, email, and password.")
            return render(request, "auth/register.html", {"form": form})

        user_name = form.cleaned_data["user_name"].strip()
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]
        confirm_password = form.cleaned_data["confirm_password"]

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/register.html", {"form": form})

        if len(password) < 5:
            messages.error(request, "Password must contain at least one number & 5 characters long.")
            return render(request, "auth/register.html", {"form": form})

        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one number & 5 characters long.")
            return render(request, "auth/register.html", {"form": form})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "auth/register.html", {"form": form})

        # Replace any previous pending signup for same username/email.
        PendingSignup.objects.filter(username=user_name).delete()
        PendingSignup.objects.filter(email=email).delete()

        pending_signup = PendingSignup.objects.create(
            username=user_name,
            email=email,
            password_hash=make_password(password),
            otp_code="000000",
        )
        pending_signup.generate_otp()

        try:
            send_verification_email(email, pending_signup.otp_code)
        except Exception as exc:
            pending_signup.delete()
            messages.error(request, f"Could not send verification email: {exc}")
            return redirect("signup")

        messages.success(request, "OTP sent to your email. Please verify your account.")
        return redirect("verify", pending_id=pending_signup.id)
    return render(request, "auth/register.html", {"form": form})

def verify_otp_view(request, pending_id):
    pending_signup = PendingSignup.objects.filter(id=pending_id).first()

    if not pending_signup:
        messages.error(request, "Signup session not found. Please register again.")
        return redirect("signup")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        if pending_signup.is_expired():
            messages.error(request, "OTP expired. Please request a new OTP.")
            return redirect("verify", pending_id=pending_signup.id)

        if entered_otp == pending_signup.otp_code:
            if User.objects.filter(username=pending_signup.username).exists():
                messages.error(request, "Username already exists. Please sign up again.")
                pending_signup.delete()
                return redirect("signup")

            if User.objects.filter(email=pending_signup.email).exists():
                messages.error(request, "Email already registered. Please log in.")
                pending_signup.delete()
                return redirect("login")

            with transaction.atomic():
                user = User.objects.create(
                    username=pending_signup.username,
                    email=pending_signup.email,
                    password=pending_signup.password_hash,
                    is_active=True,
                )
                pending_signup.delete()

            messages.success(request, "Account verified! You can now log in.")
            return redirect("login")

        messages.error(request, "Invalid OTP. Try again.")

    return render(request, "auth/verify.html", {"pending_id": pending_id, "pending_email": pending_signup.email, "pending_username": pending_signup.username})


def resend_otp(request, pending_id):
    pending_signup = PendingSignup.objects.filter(id=pending_id).first()

    if not pending_signup:
        messages.error(request, "Signup session not found. Please register again.")
        return redirect("signup")

    pending_signup.generate_otp()

    try:
        send_verification_email(pending_signup.email, pending_signup.otp_code)
    except Exception as exc:
        messages.error(request, f"Could not resend verification email: {exc}")
        return redirect("verify", pending_id=pending_id)

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify", pending_id=pending_id)


def change_pending_email(request, pending_id):
    """Update the email on a PendingSignup and resend OTP."""
    pending_signup = PendingSignup.objects.filter(id=pending_id).first()

    if not pending_signup:
        messages.error(request, "Signup session not found. Please register again.")
        return redirect("signup")

    if request.method != "POST":
        return redirect("verify", pending_id=pending_id)

    new_email = request.POST.get("email")
    if not new_email:
        messages.error(request, "Please provide a new email address.")
        return redirect("verify", pending_id=pending_id)

    # Ensure new email is not already used by a real user
    if User.objects.filter(email=new_email).exists():
        messages.error(request, "That email is already registered. Please log in instead.")
        return redirect("login")

    # Remove any other pending signup for the new email to avoid duplicates
    PendingSignup.objects.filter(email=new_email).exclude(id=pending_id).delete()

    pending_signup.email = new_email
    pending_signup.generate_otp()

    try:
        send_verification_email(new_email, pending_signup.otp_code)
    except Exception as exc:
        messages.error(request, f"Could not send verification email: {exc}")
        return redirect("signup")

    messages.success(request, "Email updated and a new OTP has been sent.")
    return redirect("verify", pending_id=pending_signup.id)


#   LOGIN VIEW

def login_view(request):
    form = LoginForm()
    if not request.user.is_authenticated and request.GET.get('next'):
        messages.info(request, "Please log in to access that page.")
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            # Check if email exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pending = PendingSignup.objects.filter(email=email).first()
                if pending:
                    messages.error(request, "Account not verified yet. Please verify your email.")
                    return redirect("verify", pending_id=pending.id)
                messages.error(request, "User with this email does not exist.")
                return render(request, "auth/login.html", {"form": form})
                
            if not user.is_active:
                messages.error(request, "Account inactive. Please verify your email.")
                return redirect("login")

            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome {user.username}!")
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

        reset_message = EmailMultiAlternatives(
            subject="DietCraft password reset code",
            body=(
                f"Hello,\n\n"
                f"Your DietCraft password reset code is: {otp_obj.otp_code}\n\n"
                f"This code expires in 5 minutes.\n\n"
                f"If you did not request this email, you can ignore it.\n"
            ),
            from_email=formataddr(("DietCraft", settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER)),
            to=[email.strip()],
        )
        reset_message.attach_alternative(
            (
                f"<p>Hello,</p>"
                f"<p>Your DietCraft password reset code is <strong>{otp_obj.otp_code}</strong>.</p>"
                f"<p>This code expires in 5 minutes.</p>"
                f"<p>If you did not request this email, you can ignore it.</p>"
            ),
            "text/html",
        )
        reset_message.send(fail_silently=False)

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
        was_existing_profile = profile is not None
        # {% csrf_token %}
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            if was_existing_profile:
                delete_user_plans(request.user)
            # MealPlan.objects.create(user=request.user)
            messages.success(request, "Profile created successfully.")
            return redirect("home")
        else:
            messages.error(
                request,
                "Please complete all required fields before submitting your profile."
            )
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "auth/profileform.html", {
        "form": form
    })