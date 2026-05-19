import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core_settings.models import ProductOption

products = [
    {'name': 'Pergola'},
    {'name': 'Zip Perde'},
    {'name': 'Giyotin Cam'},
    {'name': 'Kış Bahçesi'},
]

for p in products:
    ProductOption.objects.get_or_create(name=p['name'])

print("Default products seeded successfully.")
