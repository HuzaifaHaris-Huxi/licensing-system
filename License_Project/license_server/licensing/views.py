import json
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import LicenseKey, ClientProfile
from .forms import LicenseKeyForm, ClientProfileForm

# Dashboard Views
class DashboardHomeView(LoginRequiredMixin, View):
    def get(self, request):
        licenses = LicenseKey.objects.all().select_related('client')
        
        active_count = sum(1 for l in licenses if l.status == "Active")
        expired_count = sum(1 for l in licenses if l.status == "Expired")
        pending_count = sum(1 for l in licenses if l.status == "Pending Activation")
        
        context = {
            'total_licenses': licenses.count(),
            'active_count': active_count,
            'expired_count': expired_count,
            'pending_count': pending_count,
            'recent_licenses': licenses.order_by('-created_at')[:10],
        }
        return render(request, 'dashboard/index.html', context)

# Client Profile Management
class ClientListView(LoginRequiredMixin, View):
    def get(self, request):
        clients = ClientProfile.objects.all()
        return render(request, 'dashboard/clients.html', {'clients': clients})
    
    def post(self, request):
        form = ClientProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
        return render(request, 'dashboard/clients.html', {
            'clients': ClientProfile.objects.all(),
            'form': form
        })

class GenerateLicenseView(LoginRequiredMixin, View):
    def get(self, request):
        form = LicenseKeyForm()
        return render(request, 'dashboard/generate.html', {'form': form})
    
    def post(self, request):
        form = LicenseKeyForm(request.POST)
        if form.is_valid():
            license_obj = form.save(commit=False)
            
            # Generate the offline payload token
            payload_data = {
                "d": license_obj.duration_days,
                "g": license_obj.grace_period_days,
                "p": license_obj.product_name or "General",
                "c": license_obj.client.name,
                "ref": license_obj.reference_id
            }
            
            fernet = Fernet(settings.LICENSE_ENCRYPTION_KEY.encode())
            encrypted_payload = fernet.encrypt(json.dumps(payload_data).encode()).decode()
            
            # Set the massive encrypted string as the key to hand to the user
            license_obj.key = encrypted_payload
            license_obj.save()
            
            return redirect('dashboard_home')
        return render(request, 'dashboard/generate.html', {'form': form})

class ResetHWIDView(LoginRequiredMixin, View):
    def post(self, request, pk):
        license_obj = get_object_or_404(LicenseKey, pk=pk)
        license_obj.hwid = None
        license_obj.save()
        return redirect('dashboard_home')

# API Validation View
class ValidateLicenseView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            key = data.get('license_key')
            hwid = data.get('hwid')
            
            if not key or not hwid:
                return JsonResponse({'error': 'Missing required fields (license_key, hwid)'}, status=400)
            
            license_obj = LicenseKey.objects.filter(key=key, is_active=True).first()
            
            if not license_obj:
                return JsonResponse({'status': 'invalid', 'message': 'License key not found or inactive'}, status=404)
            
            # HWID Locking Logic
            if not license_obj.hwid:
                license_obj.hwid = hwid
                license_obj.activation_date = timezone.now()
                license_obj.save()
            elif license_obj.hwid != hwid:
                return JsonResponse({'status': 'unauthorized', 'message': 'Device not authorized'}, status=403)
            
            # Check Status
            status = license_obj.status
            if status == "Expired":
                return JsonResponse({'status': 'expired', 'message': 'License has expired'}, status=403)
            
            # Preparation of Success Response Data
            response_data = {
                'status': 'valid',
                'license_key': license_obj.key,
                'product_name': license_obj.product_name or "General License",
                'client_name': license_obj.client.name,
                'client_email': license_obj.client.email,
                'expiry_date': license_obj.expiry_date.isoformat() if license_obj.expiry_date else None,
                'grace_period_end': license_obj.grace_period_end.isoformat() if license_obj.grace_period_end else None,
                'server_time': timezone.now().isoformat()
            }
            
            # Encryption logic
            fernet = Fernet(settings.LICENSE_ENCRYPTION_KEY.encode())
            encrypted_response = fernet.encrypt(json.dumps(response_data).encode()).decode()
            
            return JsonResponse({'payload': encrypted_response})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON Payload'}, status=400)
        except Exception as e:
            print(f"API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
