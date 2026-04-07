import requests
import json
import base64
from cryptography.fernet import Fernet

# Configuration
SERVER_URL = "http://127.0.0.1:8000/api/validate/"
ENCRYPTION_KEY = "7S6Z-P1X-yG6R5z-YVp-S7Q8P4N2M1L0K9J8I7H6G5F4E3D2C1B0A==" # Matches settings.py

def validate_license(license_key, project_id, hwid):
    print(f"--- Validating Key: {license_key} for Project: {project_id} ---")
    payload = {
        "license_key": license_key,
        "project_id": project_id,
        "hwid": hwid
    }
    
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            encrypted_payload = data.get('payload')
            
            # Decrypt response
            fernet = Fernet(ENCRYPTION_KEY.encode())
            decrypted_data = fernet.decrypt(encrypted_payload.encode()).decode()
            
            print("\n[SUCCESS] Decrypted Response:")
            print(json.dumps(json.loads(decrypted_data), indent=4))
        else:
            print(f"\n[FAILED] Error: {response.json().get('message', 'Unknown Error')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("DEMO SCRIPT: Ensure Django server is running first (python manage.py runserver)")
    # Example usage (Replace with actual key generated from dashboard)
    # validate_license("ABCD-1234-EFGH-5678", 1, "HWID-TEST-001")
