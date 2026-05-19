import csv
import json
from django.core.management.base import BaseCommand
from services.models import ServiceRecord

class Command(BaseCommand):
    help = 'Export services to JSON or CSV (includes related products and service types)'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='Path to output file')
        parser.add_argument('--format', choices=['json', 'csv'], default=None, help='Output format (auto by extension if omitted)')
        parser.add_argument('--filter-status', dest='status', type=int, help='Filter by status id')

    def handle(self, *args, **options):
        path = options['output_file']
        fmt = options['format']
        if not fmt:
            if path.lower().endswith('.json'):
                fmt = 'json'
            elif path.lower().endswith('.csv'):
                fmt = 'csv'
            else:
                self.stdout.write(self.style.ERROR('Unable to detect output format. Provide --format json|csv'))
                return

        qs = ServiceRecord.objects.all().select_related('customer', 'status', 'priority').prefetch_related('products', 'service_types')
        if options.get('status'):
            qs = qs.filter(status_id=options['status'])

        data = []
        for s in qs:
            item = {
                'id': s.id,
                'customer_name': s.customer.name if s.customer else '',
                'customer_phone': s.customer.phone if s.customer else '',
                'status': s.status.name if s.status else '',
                'priority': s.priority.name if s.priority else '',
                'products': [p.name for p in s.products.all()],
                'service_types': [t.name for t in s.service_types.all()],
                'notes': s.notes or '',
                'warranty_status': s.warranty_status,
                'created_at': s.created_at.isoformat() if s.created_at else '',
            }
            data.append(item)

        try:
            if fmt == 'json':
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # write csv with products/service_types as pipe-separated
                fieldnames = ['id', 'customer_name', 'customer_phone', 'status', 'priority', 'products', 'service_types', 'notes', 'warranty_status', 'created_at']
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in data:
                        item_copy = item.copy()
                        item_copy['products'] = '|'.join(item_copy['products'])
                        item_copy['service_types'] = '|'.join(item_copy['service_types'])
                        writer.writerow(item_copy)

            self.stdout.write(self.style.SUCCESS(f'Exported {len(data)} services to {path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while writing file: {str(e)}'))
