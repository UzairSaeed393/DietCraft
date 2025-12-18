from django.shortcuts import render
from django.db.models import Q
from .models import Nutritionist


def nutritionists(request):
    search = request.GET.get("search", "").strip()
    city = request.GET.get("city", "").strip()

    queryset = Nutritionist.objects.all()

    if search and len(search) >= 2:
        queryset = queryset.filter(
            Q(name__icontains=search)
        )

    if city:
        queryset = queryset.filter(city__icontains=city)

    queryset = queryset[:10]

    context = {
        "nutritionists": queryset,
        "search": search,
        "city": city,
    }
    return render(request, "nutritionists/nutritionists.html", context)
