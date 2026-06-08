"""Herkese açık restoran vitrin sitesi — /w/<slug>/"""

from django.shortcuts import get_object_or_404, render

from restaurant.models import RestaurantCategory, RestaurantMenuItem, RestaurantProfile, RestaurantTenantProfile


def public_website_view(request, slug, page_slug=None):
    tenant = get_object_or_404(RestaurantTenantProfile, public_slug=slug)
    brand = tenant.brand
    profile = get_object_or_404(RestaurantProfile, brand=brand)
    categories = RestaurantCategory.objects.filter(brand=brand, is_active=True).prefetch_related('items')
    menu = []
    for cat in categories:
        items = RestaurantMenuItem.objects.filter(category=cat, is_available=True)
        menu.append({
            'category': cat.name,
            'items': [{'name': i.name, 'description': i.description, 'price': float(i.price)} for i in items],
        })
    return render(request, 'restaurant/public_website.html', {
        'profile': profile,
        'brand': brand,
        'menu': menu,
        'page_slug': page_slug,
    })
