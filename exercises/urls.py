from django.urls import path
from .views import (
    exercise_plan_view,
    generate_exercise_plan,
    mark_done
)

urlpatterns = [
    path('', exercise_plan_view, name='exercise_plan_view'),
    path('generate/', generate_exercise_plan, name='generate_exercise_plan'),
    path('done/<int:item_id>/', mark_done, name='mark_done'),
]
