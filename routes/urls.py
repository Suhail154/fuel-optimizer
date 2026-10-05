from django.urls import path

from .views import FuelStopsView, HealthCheckView, RouteOptimizationView

urlpatterns = [
    path('health/', HealthCheckView.as_view()),
    path('optimize-route/', RouteOptimizationView.as_view()),
    path('fuel-stops/', FuelStopsView.as_view()),
]
