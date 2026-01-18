from django.shortcuts import render
from django.db.models import Q
from .models import Nutritionist


def nutritionists(request):
    search = request.GET.get("search", "").strip()
    city = request.GET.get("city", "").strip()
    specialty = request.GET.get("specialty", "").strip()

    queryset = Nutritionist.objects.all()

    # Build search filters progressively depending on input length:
    # - name matches when user types at least 2 characters
    # - specialty, category, clinic name/address included when user types at least 3 characters
    if search:
        s_len = len(search)
        q = Q()
        if s_len >= 2:
            q |= Q(name__icontains=search)
        if s_len >= 3:
            q |= Q(specialty__icontains=search)
            q |= Q(category__icontains=search)
            q |= Q(clinic_name__icontains=search)
            q |= Q(clinic_address__icontains=search)

        if q:
            queryset = queryset.filter(q)

    # Only filter by city when user provides at least 2 characters (avoid overly broad matches)
    if city and len(city) >= 2:
        queryset = queryset.filter(city__icontains=city)

    # Allow direct specialty filter (select box keywords). Match case-insensitively
    # against both the `specialty` text and the `category` key so options like
    # "weight" or "sports" match either field.
    if specialty and len(specialty) >= 2:
        queryset = queryset.filter(
            Q(specialty__icontains=specialty) | Q(category__icontains=specialty)
        )

    queryset = queryset[:10]

    context = {
        "nutritionists": queryset,
        "search": search,
        "city": city,
        "specialty": specialty,
    }
    return render(request, "nutritionists/nutritionists.html", context)
