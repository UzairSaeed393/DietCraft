from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

def signup_view(request):
    return render(request, "auth/register.html")
def login_view(request):
    return render(request, "auth/login.html")
