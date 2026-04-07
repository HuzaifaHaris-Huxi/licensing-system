from django.db import connection

def drop_tables():
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS licensing_licensekey CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS licensing_project CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS licensing_clientprofile CASCADE;")
        print("Dropped licensing tables.")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'license_server.settings')
    django.setup()
    try:
        drop_tables()
    except Exception as e:
        print(f"Error dropping tables: {e}")
