"""Test mağaza önizleme şablon bağlamı."""

from __future__ import annotations


def test_store_inspection_context(request):
    from common.brand_scope import get_active_brand
    from common.platform_test_access import is_inspecting_test_store

    if not is_inspecting_test_store(request):
        return {
            'test_store_inspection_active': False,
            'test_store_brand_name': '',
        }
    brand = get_active_brand(request)
    return {
        'test_store_inspection_active': True,
        'test_store_brand_name': brand.name if brand else '',
    }
