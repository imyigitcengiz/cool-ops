# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core_settings.models import ProductOption, ServiceTypeOption

products = ["Pergola", "Zip Perde", "Giyotin Cam", "Radius Pergola", "Bioklimatik Pergola", "Rolling Roof"]
service_types = ["İzolasyon", "Motor Arızası", "Led Arıza", "Kayış Kopması", "Kumaş Değişimi", "Genel Bakım", "Kumanda Tanıtma"]

print("Seeding products...")
for p in products:
    obj, created = ProductOption.objects.get_or_create(name=p)
    if created: print(f"Added: {p}")

print("\nSeeding service types...")
for s in service_types:
    obj, created = ServiceTypeOption.objects.get_or_create(name=s)
    if created: print(f"Added: {s}")

print("\nDone!")
