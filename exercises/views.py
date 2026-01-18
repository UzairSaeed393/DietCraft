from django.shortcuts import render
from authentication.decorators import profile_required

# Create your views here.
@profile_required
def exercises(request):
    return render(request, 'exercises/exercises.html')
