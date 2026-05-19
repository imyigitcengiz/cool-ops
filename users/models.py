from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Yönetici'),
        ('operation', 'Operasyon'),
        ('service', 'Servis Personeli'),
        ('sales', 'Satış Temsilcisi'),
        ('accounting', 'Muhasebe'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales', verbose_name='Kullanıcı Rolü')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
