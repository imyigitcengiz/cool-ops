from restaurant.compat import get_api_profile, serialize_brand_for_api, ensure_restaurant_tenant, get_tenant_profile
from rest_framework import serializers
from restaurant.models import (
    Table, Category, MenuItem, MenuItemModifier, Order, OrderItem, Payment,
    OrderChannel, CashRegister, Ingredient, Recipe, RecipeIngredient,
    StaffMember, Expense, Courier, CourierLog, RestaurantProfile,
    CashTransaction, StockAudit, StockAuditItem, Customer, WhatsAppConfig,
    Branch,
)

class TableSerializer(serializers.ModelSerializer):
    branch_name = serializers.ReadOnlyField(source='branch.name')

    class Meta:
        model = Table
        fields = '__all__'
        read_only_fields = ['brand', 'branch']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['brand']

class MenuItemModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItemModifier
        fields = '__all__'

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    image = serializers.ImageField(required=False, allow_null=True)
    modifiers = MenuItemModifierSerializer(many=True, read_only=True)

    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ['brand']

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.ReadOnlyField(source='menu_item.name')
    menu_item_price = serializers.ReadOnlyField(source='menu_item.price')

    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_name = serializers.ReadOnlyField(source='table.name')
    branch_name = serializers.ReadOnlyField(source='branch.name')
    discounted_total = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['brand', 'branch']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['order']

class OrderChannelSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = OrderChannel
        fields = '__all__'
        read_only_fields = ['brand']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.api_key:
            data['api_key_masked'] = instance.api_key[:4] + '****' if len(instance.api_key) > 4 else '****'
        return data

class CashRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashRegister
        fields = '__all__'
        read_only_fields = ['brand', 'branch']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ['brand']

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'

class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = '__all__'

class StaffMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMember
        fields = '__all__'

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'

class CourierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = '__all__'
        read_only_fields = ['brand']

class CourierLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourierLog
        fields = '__all__'

class RestaurantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantProfile
        fields = '__all__'
        read_only_fields = ['brand']

class CashTransactionSerializer(serializers.ModelSerializer):
    register_name = serializers.ReadOnlyField(source='register.name')

    class Meta:
        model = CashTransaction
        fields = '__all__'
        read_only_fields = ['register']

class StockAuditItemSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.ReadOnlyField(source='ingredient.name')
    ingredient_unit = serializers.ReadOnlyField(source='ingredient.unit')

    class Meta:
        model = StockAuditItem
        fields = '__all__'

class StockAuditSerializer(serializers.ModelSerializer):
    items = StockAuditItemSerializer(many=True, read_only=True)

    class Meta:
        model = StockAudit
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['brand']

class WhatsAppConfigSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = WhatsAppConfig
        fields = '__all__'
        read_only_fields = ['brand']


class BranchSerializer(serializers.ModelSerializer):
    brand_name = serializers.ReadOnlyField(source='brand.name')
    has_panel_password = serializers.SerializerMethodField()
    panel_url = serializers.SerializerMethodField()
    brand_plan = serializers.SerializerMethodField()
    table_count = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            'id', 'brand', 'brand_name', 'brand_plan', 'name', 'city', 'address', 'phone',
            'is_active', 'panel_slug', 'panel_enabled', 'has_panel_password', 'panel_url',
            'panel_password_updated_at', 'created_at', 'table_count',
        ]
        read_only_fields = ['panel_slug', 'panel_password_updated_at', 'created_at', 'brand']

    def get_brand_plan(self, obj):
        from restaurant.compat import get_tenant_profile
        return get_tenant_profile(obj.brand).plan_tier

    def get_has_panel_password(self, obj):
        return bool(obj.panel_password)

    def get_panel_url(self, obj):
        from common.panel_registry import franchise_panel_url
        return franchise_panel_url(obj.panel_slug)

    def get_table_count(self, obj):
        return obj.tables.count()
