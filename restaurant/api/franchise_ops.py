from restaurant.compat import get_api_profile, serialize_brand_for_api, ensure_restaurant_tenant, get_tenant_profile
"""Franchise panel sipariş ve masa işlemleri — şube kapsamında."""

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from restaurant.models import (
    CashRegister, CashTransaction, Category, Customer, MenuItem,
    Order, OrderItem, Payment, RestaurantProfile, Table, WhatsAppConfig,
)
from restaurant.api.serializers import CategorySerializer, MenuItemSerializer, OrderSerializer


def franchise_table_for_branch(branch, table_id):
    try:
        return Table.objects.select_related('brand').get(
            id=table_id, brand_id=branch.brand_id, branch=branch,
        ), None
    except Table.DoesNotExist:
        return None, Response(
            {'error': 'Masa bulunamadı veya bu şubeye ait değil.'},
            status=status.HTTP_404_NOT_FOUND,
        )


def franchise_order_for_branch(branch, order_id):
    try:
        return Order.objects.select_related('table', 'branch').prefetch_related('items').get(
            id=order_id, brand_id=branch.brand_id, branch=branch,
        ), None
    except Order.DoesNotExist:
        return None, Response(
            {'error': 'Sipariş bulunamadı veya bu şubeye ait değil.'},
            status=status.HTTP_404_NOT_FOUND,
        )


def create_franchise_order(branch, table_id, items_data):
    table, err = franchise_table_for_branch(branch, table_id)
    if err:
        return None, err

    if not items_data:
        return None, Response({'error': 'En az bir ürün gereklidir.'}, status=status.HTTP_400_BAD_REQUEST)

    brand = branch.brand
    table.status = 'occupied'
    table.save()

    active_order = Order.objects.filter(table=table).exclude(
        status__in=['completed', 'cancelled'],
    ).first()
    order = active_order or Order.objects.create(
        table=table, status='preparing', brand=brand, branch=branch,
    )

    total_amount = float(order.total_amount)
    for item in items_data:
        menu_item_id = item.get('menu_item')
        try:
            menu_item = MenuItem.objects.get(id=menu_item_id, brand=brand)
        except MenuItem.DoesNotExist:
            return None, Response(
                {'error': f'Menü ürünü geçersiz: {menu_item_id}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quantity = int(item.get('quantity', 1))
        note = item.get('note', '')
        modifier_text = item.get('modifier_text', '')
        modifier_extra = float(item.get('modifier_extra', 0))
        price = float(menu_item.price) + modifier_extra

        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            price=price,
            note=note,
            modifier_text=modifier_text,
            modifier_extra=modifier_extra,
            status='preparing',
        )
        total_amount += price * quantity

    order.total_amount = total_amount
    order.save()
    return order, None


def pay_and_close_franchise_order(branch, order_id, payment_method, amount):
    order, err = franchise_order_for_branch(branch, order_id)
    if err:
        return None, err

    if not payment_method or amount is None:
        return None, Response(
            {'error': 'Ödeme yöntemi ve tutar gereklidir'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        amount_decimal = float(amount)
    except (TypeError, ValueError):
        return None, Response({'error': 'Geçersiz tutar'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        Payment.objects.create(
            order=order,
            amount=amount_decimal,
            payment_method=payment_method,
        )
        order.status = 'completed'
        order.save()

        for item in order.items.all():
            if hasattr(item.menu_item, 'recipe'):
                recipe = item.menu_item.recipe
                for recipe_ingredient in recipe.ingredients.all():
                    ingredient = recipe_ingredient.ingredient
                    deduction_qty = float(recipe_ingredient.quantity) * item.quantity
                    ingredient.stock_quantity = float(ingredient.stock_quantity) - deduction_qty
                    ingredient.save()

        table = order.table
        table.status = 'empty'
        table.save()

        brand = order.brand
        register = CashRegister.objects.filter(brand=brand, branch=branch).first()
        if not register:
            register = CashRegister.objects.filter(brand=brand, branch__isnull=True).first()
        if not register:
            register = CashRegister.objects.create(
                brand=brand, branch=branch, name=f'{branch.name} Kasası',
                balance=0.00, location=branch.name,
            )

        CashTransaction.objects.create(
            register=register,
            transaction_type='in',
            amount=amount_decimal,
            description=(
                f"Franchise Masa Ödemesi ({table.name}) - Sipariş #{order.id} "
                f"({'Nakit' if payment_method == 'cash' else 'Kredi Kartı'})"
            ),
        )

    whatsapp_simulated = None
    try:
        profile = RestaurantProfile.objects.filter(brand=brand).first()
        if profile and profile.ext_whatsapp_enabled:
            wa_config = WhatsAppConfig.objects.filter(brand=brand).first()
            if wa_config and wa_config.is_auto_message_enabled:
                customer = Customer.objects.filter(brand=brand).first()
                cust_name = customer.name if customer else 'Değerli Müşterimiz'
                cust_phone = customer.phone if customer else '0555 555 55 55'
                msg = wa_config.message_template.replace(
                    '{customer_name}', cust_name,
                ).replace('{order_id}', str(order.id))
                whatsapp_simulated = {
                    'to': f'{cust_name} ({cust_phone})',
                    'message': msg,
                }
    except Exception:
        pass

    return {
        'message': 'Ödeme alındı ve masa kapatıldı',
        'order': OrderSerializer(order).data,
        'whatsapp_simulated': whatsapp_simulated,
    }, None


def change_franchise_table_status(branch, table_id, new_status):
    table, err = franchise_table_for_branch(branch, table_id)
    if err:
        return None, err

    valid = dict(Table.STATUS_CHOICES)
    if new_status not in valid:
        return None, Response({'error': 'Geçersiz durum'}, status=status.HTTP_400_BAD_REQUEST)

    table.status = new_status
    table.save()
    return table, None


def get_franchise_menu(branch):
    brand = branch.brand
    categories = Category.objects.filter(brand=brand).order_by('name')
    menu_items = MenuItem.objects.filter(brand=brand, is_available=True).order_by('name')
    return {
        'categories': CategorySerializer(categories, many=True).data,
        'menu_items': MenuItemSerializer(menu_items, many=True).data,
    }
