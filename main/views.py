from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm

# model counts for homepage
from meals.models import FoodItem
from exercises.models import Exercise
from nutritionists.models import Nutritionist
from django.contrib.auth import get_user_model


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            form.save()  # Save message into ContactMessage table
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')

    else:
        form = ContactForm()

    return render(request, 'main/contact.html', {'form': form})


def home(request):
    User = get_user_model()

    meals_count = FoodItem.objects.count()
    exercises_count = Exercise.objects.filter(is_active=True).count()
    nutritionists_count = Nutritionist.objects.count()
    users_count = User.objects.filter(is_active=True).count()

    context = {
        'meals_count': meals_count,
        'exercises_count': exercises_count,
        'nutritionists_count': nutritionists_count,
        'users_count': users_count,
    }

    return render(request, 'main/Home.html', context)


def about(request):
    return render(request, 'main/about.html')
