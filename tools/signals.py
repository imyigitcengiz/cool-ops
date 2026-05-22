from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save, sender='core_settings.SolutionPartner')
def sync_solution_partner_directory(sender, instance, **kwargs):
    from tools.firm_directory import sync_partner_to_directory

    sync_partner_to_directory(instance)


@receiver(post_delete, sender='core_settings.SolutionPartner')
def remove_solution_partner_directory(sender, instance, **kwargs):
    from tools.firm_directory import remove_partner_from_directory

    remove_partner_from_directory(instance.pk)
