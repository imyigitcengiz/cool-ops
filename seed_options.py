import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core_settings.models import StatusOption, PriorityOption

def seed():
    statuses = [
        ('Servis', '#3b82f6'),
        ('Beklemede', '#f59e0b'),
        ('İptal', '#ef4444'),
        ('Ücretli Tamamlandı', '#a855f7'),
        ('İptal Ücretli', '#f43f5e'),
    ]
    for name, color in statuses:
        obj, _ = StatusOption.objects.get_or_create(name=name, defaults={'color': color})
        if obj.color != color and not str(obj.color).startswith('#'):
            obj.color = color
            obj.save(update_fields=['color'])

    priorities = [
        ('Düşük', '#10b981'),
        ('Orta', '#f59e0b'),
        ('Acil', '#ef4444'),
    ]
    for name, color in priorities:
        obj, _ = PriorityOption.objects.get_or_create(name=name, defaults={'color': color})
        if obj.color != color and not str(obj.color).startswith('#'):
            obj.color = color
            obj.save(update_fields=['color'])

    print("Seed completed!")

if __name__ == "__main__":
    seed()
