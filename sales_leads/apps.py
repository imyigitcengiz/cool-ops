from django.apps import AppConfig


class SalesLeadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_leads'
    verbose_name = 'Satış Kayıtları'

    def ready(self):
        import sales_leads.signals  # noqa: F401
