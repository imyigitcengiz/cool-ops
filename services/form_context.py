from django.contrib.auth import get_user_model

from core_settings.models import (
    PriorityOption,
    ProductOption,
    ServiceTypeOption,
    StatusOption,
)


def build_service_form_context(service=None):
    products = ProductOption.objects.prefetch_related('service_types').order_by('name')
    service_types = ServiceTypeOption.objects.prefetch_related('products').order_by('name')

    def service_type_color(st):
        first_product = next(iter(st.products.all()), None)
        return first_product.color_hex if first_product else st.color_hex

    catalog = {
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'color': p.color_hex,
                'service_type_ids': list(p.service_types.values_list('id', flat=True)),
            }
            for p in products
        ],
        'service_types': [
            {'id': s.id, 'name': s.name, 'color': service_type_color(s)}
            for s in service_types
        ],
        'statuses': [
            {'id': s.id, 'name': s.name, 'color': s.color_hex}
            for s in StatusOption.objects.order_by('name')
        ],
        'priorities': [
            {'id': p.id, 'name': p.name, 'color': p.color_hex}
            for p in PriorityOption.objects.order_by('name')
        ],
    }
    ctx = {
        'options_catalog': catalog,
        'users_for_assign': get_user_model().objects.filter(is_active=True).order_by('username'),
    }
    if service:
        ctx['initial_product_ids'] = list(service.products.values_list('id', flat=True))
        ctx['initial_service_type_ids'] = list(service.service_types.values_list('id', flat=True))
    else:
        ctx['initial_product_ids'] = []
        ctx['initial_service_type_ids'] = []
    return ctx
