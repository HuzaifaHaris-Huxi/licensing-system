# Barkat Offline License Integration Guide

This guide details exactly how to implement the **Offline Payload License System** into any other generic Django software you build, ensuring complete reusability of the standalone Central Brain architecture.

## 1. Prerequisites 

Install the required library for securely decrypting the Central Brain payload tokens on the client software.
```bash
pip install cryptography
```

Add your shared secret key to `settings.py`. This **must match** what your Central Brain uses:
```python
# settings.py
LICENSE_ENCRYPTION_KEY = "YOUR-FERNET-KEY"
```

---

## 2. Model Structure

Add a local tracking table to store the offline duration timestamps and track the history array to prevent Replay Attacks.

```python
# models.py
from django.db import models

class LicenseSetting(models.Model):
    license_key = models.TextField(blank=True, null=True)
    client_name = models.CharField(max_length=100, blank=True, null=True)
    product_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Offline Dates
    expiry_date = models.DateTimeField(blank=True, null=True)
    grace_period_end = models.DateTimeField(blank=True, null=True)
    
    # Replay Attack Prevention Vault
    activation_history = models.TextField(
        blank=True, 
        default="", 
        help_text="Comma-separated used reference IDs"
    )
    is_active = models.BooleanField(default=False)
```

Run `python manage.py makemigrations` and `python manage.py migrate` after adding this model.

---

## 3. Cryptography Engine (`utils/licensing.py`)

Create a `licensing.py` utility that mathmatically extracts the token without communicating with any external servers.

```python
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
from .models import LicenseSetting

def validate_license_offline(key):
    """
    Validates the massive offline token without internet access.
    """
    encryption_key = getattr(settings, 'LICENSE_ENCRYPTION_KEY', None)
    if not encryption_key:
        return False, "License encryption configuration missing."

    try:
        # Decrypt offline locally
        fernet = Fernet(encryption_key.encode())
        decrypted_json = fernet.decrypt(key.encode()).decode()
        decrypted_data = json.loads(decrypted_json)
        
        # Read or Create Settings
        license_obj = LicenseSetting.objects.first()
        if not license_obj:
            license_obj = LicenseSetting()
            
        # 1. Replay Attack Prevention
        ref_id = decrypted_data.get('ref')
        if ref_id:
            used_refs = [r.strip() for r in license_obj.activation_history.split(',') if r.strip()]
            if ref_id in used_refs:
                return False, "This exact License Token has already been used on this machine."
            
            used_refs.append(ref_id)
            license_obj.activation_history = ','.join(used_refs)
        
        # 2. Extract Duration Metrics
        duration_days = int(decrypted_data.get('d', 0))
        grace_days = int(decrypted_data.get('g', 0))
        
        # 3. Calculate Offline Expiration limits from exact current moment
        now = timezone.now()
        license_obj.expiry_date = now + timedelta(days=duration_days)
        license_obj.grace_period_end = license_obj.expiry_date + timedelta(days=grace_days)
        
        license_obj.license_key = key
        license_obj.is_active = True
        license_obj.save()
        
        return True, "Software activated successfully."
            
    except Exception as e:
        return False, "Invalid License Token. Validation failed."


def check_license_local():
    """
    Checks if the local system is currently valid to operate.
    Returns: 'valid', 'grace', 'expired', or 'missing'
    """
    license_obj = LicenseSetting.objects.first()
    if not license_obj or not license_obj.is_active:
        return 'missing', "No active license."
        
    now = timezone.now()
    
    # Check absolute limit
    if license_obj.expiry_date and now <= license_obj.expiry_date:
        return 'valid', {"expiry": license_obj.expiry_date}
        
    # Check grace period extension
    if license_obj.grace_period_end and now <= license_obj.grace_period_end:
        days_left = (license_obj.grace_period_end - now).days
        return 'grace', {"days_left": max(0, days_left)}
        
    return 'expired', "Your license has completely expired."
```

---

## 4. Middleware Routing Lockout

To ensure that expired clients are strictly trapped inside the "Activation Page" until they upgrade, you inject this middleware into `settings.py` (`MIDDLEWARE` array).

```python
# middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from .utils.licensing import check_license_local

class EnforcementMiddleware:
    """
    Traps expired users on the Activation page, while allowing SuperUsers 
    to bypass restrictions so you don't lock administrators out.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        status, info = check_license_local()
        
        # Share status universally with every template rendering so UI headers can display "Grace Period" warning banners.
        request.license_data = {
            'status': status,
            'info': info
        }
        
        # Always allow users trying to access Activation pages, Login, Admin, or static resources
        allowed_paths = [
            reverse('activate_license'), # Ensure you set the route name correctly
            reverse('login'),
            '/admin/',
            '/static/',
            '/__reload__/'
        ]
        
        is_allowed_path = any(request.path.startswith(p) for p in allowed_paths)
        
        if not is_allowed_path:
            # Trap them if expired or missing, UNLESS they are SuperUser
            if status in ['expired', 'missing']:
                if request.user.is_authenticated and not request.user.is_superuser:
                    # Enforce Lockout - redirect everything to the activation page
                    return redirect('activate_license')
                
        return self.get_response(request)
```

**Workflow Results:**
1. A user attempts to view a secure dashboard page.
2. The Middleware checks the local database timestamp silently.
3. If `< today()`, they are kicked instantly to `activate_license.html`.
4. The user pastes the huge Fernet Token you generated from your Central Brain.
5. The `validate_license_offline` utility unpackages the token, mathematically pushes the expiry boundaries mathematically based on the `duration_days` string, writes the Token Hash to the history log, and lets the user proceed!
