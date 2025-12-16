from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegisterForm, LoginForm
from .models import UserOTP
#   SIGNUP VIEW


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
            messages.error(request, "Password must be at least 5 characters long.")
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
            message=f"Your OTP is {otp_obj.otp_code}",
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
        message=f"Your new OTP is {otp_obj.otp_code}. It expires in 5 minutes.",
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
