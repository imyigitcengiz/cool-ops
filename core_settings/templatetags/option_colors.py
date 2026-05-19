from django import template

from core_settings.color_utils import badge_styles, dot_style, normalize_hex

register = template.Library()


@register.filter
def option_hex(value):
    return normalize_hex(value)


@register.filter
def option_badge_bg(value):
    return badge_styles(value)['background']


@register.filter
def option_badge_text(value):
    return badge_styles(value)['color']


@register.filter
def option_badge_border(value):
    return badge_styles(value)['border']


@register.filter
def option_dot(value):
    return dot_style(value)


@register.filter
def service_type_primary_color(service_type):
    """Use first linked product color; fallback to service type color."""
    products = service_type.products.all().order_by('name')
    first = products.first()
    if first:
        return first.color_hex
    return service_type.color_hex


@register.filter
def service_type_color_for_products(service_type, products):
    """Resolve service type color from current service's products."""
    first_product = None
    for product in products:
        if first_product is None:
            first_product = product
        if any(st.id == service_type.id for st in product.service_types.all()):
            return product.color_hex
    if first_product is not None:
        return first_product.color_hex
    return service_type_primary_color(service_type)
