import csv
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from customers.models import Customer
from services.models import ServiceRecord
from core_settings.models import StatusOption, PriorityOption, ProductOption, ServiceTypeOption


class Command(BaseCommand):
    help = 'Import services from JSON or CSV exported by export_services command'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Path to JSON or CSV file')
        parser.add_argument('--format', choices=['json', 'csv'], default=None, help='Format of the file (auto-detected by extension if omitted)')

    def handle(self, *args, **options):
        file_path = options['file']
        fmt = options['format']
        if not fmt:
            if file_path.lower().endswith('.json'):
                fmt = 'json'
            elif file_path.lower().endswith('.csv'):
                fmt = 'csv'
            else:
                self.stdout.write(self.style.ERROR('Unable to detect file format. Provide --format json|csv'))
                return

        try:
            with transaction.atomic():
                count = 0
                if fmt == 'json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            customer_name = item.get('customer_name') or 'Bilinmeyen Müşteri'
                            phone = item.get('customer_phone') or ''
                            customer, _ = Customer.objects.get_or_create(name=customer_name, phone=phone)

                            status_name = item.get('status') or 'Beklemede'
                            priority_name = item.get('priority') or 'Normal'

                            status_obj, _ = StatusOption.objects.get_or_create(name=status_name)
                            priority_obj, _ = PriorityOption.objects.get_or_create(name=priority_name)

                            s = ServiceRecord.objects.create(
                                customer=customer,
                                status=status_obj,
                                priority=priority_obj,
                                notes=item.get('notes', ''),
                                warranty_status=item.get('warranty_status', 'active')
                            )

                            # Products and service types
                            for pname in item.get('products', []):
                                p, _ = ProductOption.objects.get_or_create(name=pname)
                                s.products.add(p)
                            for tname in item.get('service_types', []):
                                t, _ = ServiceTypeOption.objects.get_or_create(name=tname)
                                s.service_types.add(t)

                            count += 1
                else:  # csv
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            customer_name = row.get('customer_name') or row.get('Kişi') or 'Bilinmeyen Müşteri'
                            phone = row.get('customer_phone') or row.get('Telefon') or ''
                            customer, _ = Customer.objects.get_or_create(name=customer_name, phone=phone)

                            status_name = row.get('status') or row.get('Durum') or 'Beklemede'
                            priority_name = row.get('priority') or row.get('Öncelik') or 'Normal'

                            status_obj, _ = StatusOption.objects.get_or_create(name=status_name)
                            priority_obj, _ = PriorityOption.objects.get_or_create(name=priority_name)

                            s = ServiceRecord.objects.create(
                                customer=customer,
                                status=status_obj,
                                priority=priority_obj,
                                notes=row.get('notes') or row.get('Servis Notu') or '',
                                warranty_status=row.get('warranty_status') or 'active'
                            )

                            products_field = row.get('products') or row.get('Ürün') or ''
                            service_types_field = row.get('service_types') or row.get('Arıza Tipi') or ''

                            for pname in [p.strip() for p in products_field.split('|') if p.strip()]:
                                p, _ = ProductOption.objects.get_or_create(name=pname)
                                s.products.add(p)
                            for tname in [t.strip() for t in service_types_field.split('|') if t.strip()]:
                                t, _ = ServiceTypeOption.objects.get_or_create(name=tname)
                                s.service_types.add(t)

                            count += 1

                self.stdout.write(self.style.SUCCESS(f'Imported {count} service records.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File "{file_path}" not found.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
