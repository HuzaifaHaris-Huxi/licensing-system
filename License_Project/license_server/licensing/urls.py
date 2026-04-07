from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import DashboardHomeView, GenerateLicenseView, ResetHWIDView, ValidateLicenseView, ClientListView

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard_home'),
    path('generate/', GenerateLicenseView.as_view(), name='generate_license'),
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('reset-hwid/<int:pk>/', ResetHWIDView.as_view(), name='reset_hwid'),
    
    # Internal API
    path('api/validate/', csrf_exempt(ValidateLicenseView.as_view()), name='api_validate'),
]
