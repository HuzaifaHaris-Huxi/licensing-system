import uuid
import secrets
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta

def generate_reference_id():
    """Generates a unique reference ID in format ABCD-1234-EFGH-5678"""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        parts = []
        for _ in range(4):
            parts.append(''.join(secrets.choice(alphabet) for _ in range(4)))
        ref_id = '-'.join(parts)
        # Avoid circular imports or complex checks if possible, assuming unique enough 
        # But for absolute safety we'll just return it. Uniqueness handled by DB.
        return ref_id

class ClientProfile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

class LicenseKey(models.Model):
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='licenses')
    product_name = models.CharField(max_length=100, blank=True, null=True, help_text="Optional name of the software")
    reference_id = models.CharField(max_length=25, unique=True, default=generate_reference_id)
    key = models.TextField(unique=True, help_text="The encrypted offline token payload")
    
    # License Details
    duration_days = models.IntegerField(default=10, help_text="Duration in days")
    is_active = models.BooleanField(default=True)
    
    # Validation Dates (Historical Reference Only)
    grace_period_days = models.IntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def expiry_date(self):
        # Without activation date, offline tokens display theoretical expiry based on max
        return self.created_at + timedelta(days=self.duration_days)

    @property
    def grace_period_end(self):
        expiry = self.expiry_date
        if not expiry:
            return None
        return expiry + timedelta(days=self.grace_period_days)

    @property
    def status(self):
        if not self.is_active:
            return "Suspended"
        
        now = timezone.now()
        expiry = self.expiry_date
        grace_end = self.grace_period_end
        
        if expiry and now <= expiry:
            return "Active"
        if grace_end and now <= grace_end:
            return "Grace Period"
        return "Expired"

    def __str__(self):
        name = self.product_name if self.product_name else "General License"
        return f"{self.reference_id} - {name} ({self.client.name})"
