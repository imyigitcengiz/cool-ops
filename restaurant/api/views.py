import logging

from restaurant.compat import get_api_profile, serialize_brand_for_api, ensure_restaurant_tenant, get_tenant_profile

logger = logging.getLogger(__name__)
from rest_framework.permissions import IsAuthenticated
from restaurant.api.permissions import IsRestaurantFinanceRole
from restaurant.api.security import is_api_superuser
from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, F, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from restaurant.models import (
    Table, Category, MenuItem, MenuItemModifier, Order, OrderItem, Payment,
    OrderChannel, CashRegister, Ingredient, Recipe, RecipeIngredient,
    StaffMember, Expense, Courier, CourierLog, RestaurantProfile,
    CashTransaction, StockAudit, StockAuditItem, Customer, WhatsAppConfig,
    Branch,
)
from restaurant.api.tenant_scope import filter_by_tenant, resolve_branch_for_user
from restaurant.api.tenant_helpers import (
    get_tenant_table, get_tenant_menu_item, get_tenant_ingredient,
    get_tenant_order, get_tenant_register, get_user_brand,
)
from restaurant.api.serializers import (
    TableSerializer, CategorySerializer, MenuItemSerializer, MenuItemModifierSerializer,
    OrderSerializer, OrderItemSerializer, PaymentSerializer,
    OrderChannelSerializer, CashRegisterSerializer, IngredientSerializer,
    RecipeSerializer, RecipeIngredientSerializer, StaffMemberSerializer,
    ExpenseSerializer, CourierSerializer, CourierLogSerializer,
    RestaurantProfileSerializer, CashTransactionSerializer, StockAuditSerializer,
    CustomerSerializer, WhatsAppConfigSerializer, BranchSerializer,
)

def filter_by_brand(queryset, request, brand_field='brand'):
    user = request.user
    if not user.is_authenticated:
        return queryset.none()
    profile = get_api_profile(user, request)
    if not is_api_superuser(user):
        if profile.brand:
            filter_kwargs = {brand_field: profile.brand}
            return queryset.filter(**filter_kwargs)
        else:
            return queryset.model.objects.none()
    return queryset

def assign_brand(serializer, request):
    from rest_framework.exceptions import PermissionDenied
    user = request.user
    profile = get_api_profile(user, request)
    if profile and profile.brand:
        serializer.save(brand=profile.brand)
    elif is_api_superuser(user):
        brand_id = request.data.get('brand')
        if brand_id:
            serializer.save(brand_id=brand_id)
        else:
            serializer.save()
    else:
        raise PermissionDenied('Marka bilgisi bulunamadı. Kayıt oluşturulamadı.')

DEFAULT_BRANCH_TABLES = [
    ('Masa 1', 4), ('Masa 2', 2), ('Masa 3', 6), ('Masa 4', 4),
    ('Paket Servis', 1), ('Teras 1', 4),
]


def _seed_branch_tables(branch):
    for name, capacity in DEFAULT_BRANCH_TABLES:
        Table.objects.get_or_create(
            brand=branch.brand, branch=branch, name=name,
            defaults={'capacity': capacity, 'status': 'empty'},
        )
    CashRegister.objects.get_or_create(
        brand=branch.brand, branch=branch, name=f'{branch.name} Kasası',
        defaults={'balance': 0.00, 'location': branch.name},
    )


class TableViewSet(viewsets.ModelViewSet):
    serializer_class = TableSerializer

    def get_queryset(self):
        return filter_by_tenant(Table.objects.all().order_by('name'), self.request)

    def perform_create(self, serializer):
        user = self.request.user
        profile = get_api_profile(user, self.request)
        branch_id = self.request.data.get('branch')
        branch = resolve_branch_for_user(self.request, branch_id) if branch_id else None
        if profile and profile.brand:
            serializer.save(brand=profile.brand, branch=branch)
        else:
            assign_brand(serializer, self.request)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        table = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Table.STATUS_CHOICES):
            table.status = new_status
            table.save()
            return Response(TableSerializer(table).data)
        return Response({'error': 'Geçersiz durum'}, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return filter_by_brand(Category.objects.all().order_by('name'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        queryset = MenuItem.objects.all().order_by('name')
        queryset = filter_by_brand(queryset, self.request)
        category_id = self.request.query_params.get('category', None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related('table', 'branch').order_by('-id')
        queryset = filter_by_tenant(queryset, self.request)
        table_id = self.request.query_params.get('table', None)
        active_only = self.request.query_params.get('active', None)
        
        if table_id is not None:
            queryset = queryset.filter(table_id=table_id)
        if active_only == 'true':
            queryset = queryset.exclude(status='completed').exclude(status='cancelled')
        return queryset

    def create(self, request, *args, **kwargs):
        table_id = request.data.get('table')
        items_data = request.data.get('items', [])

        table, err = get_tenant_table(request.user, table_id, request)
        if err:
            return err

        table.status = 'occupied'
        table.save()

        profile = get_api_profile(request.user, request)
        brand = table.brand or (profile.brand if profile else None)

        active_order = Order.objects.filter(table=table).exclude(status__in=['completed', 'cancelled']).first()
        if active_order:
            order = active_order
        else:
            order = Order.objects.create(
                table=table, status='preparing', brand=brand, branch=table.branch,
            )

        total_amount = order.total_amount
        for item in items_data:
            menu_item, item_err = get_tenant_menu_item(request.user, item.get('menu_item'), request)
            if item_err:
                continue
            if not menu_item:
                continue
            
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
                status='preparing'
            )
            total_amount += price * quantity
            
        order.total_amount = total_amount
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def pay_and_close(self, request, pk=None):
        order = self.get_object()
        payment_method = request.data.get('payment_method')
        amount = request.data.get('amount')
        
        if not payment_method or not amount:
            return Response({'error': 'Ödeme yöntemi ve tutar gereklidir'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount_decimal = float(amount)
        except ValueError:
            return Response({'error': 'Geçersiz tutar'}, status=status.HTTP_400_BAD_REQUEST)
 
        # Atomically record payment, register transaction, update order/table
        with transaction.atomic():
            # Record payment
            Payment.objects.create(
                order=order,
                amount=amount_decimal,
                payment_method=payment_method
            )
            
            # Update order status to completed
            order.status = 'completed'
            order.save()

            # Deduct ingredient stocks automatically based on recipes
            for item in order.items.all():
                if hasattr(item.menu_item, 'recipe'):
                    recipe = item.menu_item.recipe
                    for recipe_ingredient in recipe.ingredients.all():
                        ingredient = recipe_ingredient.ingredient
                        deduction_qty = float(recipe_ingredient.quantity) * item.quantity
                        ingredient.stock_quantity = float(ingredient.stock_quantity) - deduction_qty
                        ingredient.save()
            
            # Empty the table
            table = order.table
            table.status = 'empty'
            table.save()

            brand = order.brand
            branch = order.branch or table.branch
            register = None
            if branch:
                register = CashRegister.objects.filter(brand=brand, branch=branch).first()
            if not register:
                register = CashRegister.objects.filter(brand=brand, branch__isnull=True).first()
            if not register:
                register = CashRegister.objects.create(
                    brand=brand, branch=branch, name='Ana Kasa', balance=0.00, location='Merkez',
                )
            
            # Log CashTransaction (which will automatically increment the register balance!)
            CashTransaction.objects.create(
                register=register,
                transaction_type='in',
                amount=amount_decimal,
                description=f"Masa Ödemesi ({table.name}) - Sipariş #{order.id} ({payment_method == 'cash' and 'Nakit' or 'Kredi Kartı'})"
            )
        
        # Check WhatsApp Auto Message
        whatsapp_simulated = None
        try:
            brand = order.brand
            profile = RestaurantProfile.objects.filter(brand=brand).first()
            if profile and profile.ext_whatsapp_enabled:
                wa_config = WhatsAppConfig.objects.filter(brand=brand).first()
                if wa_config and wa_config.is_auto_message_enabled:
                    # Select a customer (either first customer or mock name)
                    customer = Customer.objects.filter(brand=brand).first()
                    cust_name = customer.name if customer else "Değerli Müşterimiz"
                    cust_phone = customer.phone if customer else "0555 555 55 55"
                    
                    msg = wa_config.message_template.replace('{customer_name}', cust_name).replace('{order_id}', str(order.id))
                    
                    logger.debug(
                        'WhatsApp auto message simulation to=%s message=%s',
                        cust_phone,
                        msg[:120],
                    )
                    
                    whatsapp_simulated = {
                        'to': f"{cust_name} ({cust_phone})",
                        'message': msg
                    }
        except Exception:
            logger.exception('WhatsApp auto message simulation failed')
        
        return Response({
            'message': 'Ödeme alındı ve masa kapatıldı',
            'order': OrderSerializer(order).data,
            'whatsapp_simulated': whatsapp_simulated
        })

    @action(detail=True, methods=['post'])
    def apply_discount(self, request, pk=None):
        """Apply or remove discount on an active order."""
        order = self.get_object()
        if order.status in ['completed', 'cancelled']:
            return Response({'error': 'Tamamlanmış sipairişe indirim uygulanamaz'}, status=status.HTTP_400_BAD_REQUEST)

        discount_type = request.data.get('discount_type', 'none')
        discount_value = float(request.data.get('discount_value', 0))
        discount_reason = request.data.get('discount_reason', '')

        if discount_type not in ['none', 'percent', 'fixed']:
            return Response({'error': 'Geçersiz indirim tipi'}, status=status.HTTP_400_BAD_REQUEST)
        if discount_type == 'percent' and not (0 <= discount_value <= 100):
            return Response({'error': 'Yüzde 0-100 arasında olmalıdır'}, status=status.HTTP_400_BAD_REQUEST)

        order.discount_type = discount_type
        order.discount_value = discount_value
        order.discount_reason = discount_reason
        order.save()
        return Response(OrderSerializer(order).data)

class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        return filter_by_brand(OrderItem.objects.all().order_by('-id'), self.request, brand_field='order__brand')

    def perform_create(self, serializer):
        order_id = self.request.data.get('order')
        order, err = get_tenant_order(self.request.user, order_id, self.request)
        if err:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(err.data.get('error', 'Yetkisiz erişim.'))
        serializer.save(order=order)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        item = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(OrderItem.STATUS_CHOICES):
            item.status = new_status
            item.save()
            
            # Check if all items in order are ready/served, if so, update order status
            order = item.order
            all_items = order.items.all()
            
            if not all_items.filter(status='preparing').exists():
                order.status = 'ready'
                order.save()
                
            return Response(OrderItemSerializer(item).data)
        return Response({'error': 'Geçersiz durum'}, status=status.HTTP_400_BAD_REQUEST)

class DashboardStatsView(views.APIView):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Kimlik doğrulaması gerekli'}, status=401)
        profile = get_api_profile(user, request)
        brand = profile.brand if profile else None

        today = timezone.localtime().date()
        start_of_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        
        # Total revenue today
        payments_qs = Payment.objects.all()
        tables_qs = Table.objects.all()
        orders_qs = Order.objects.all()
        order_items_qs = OrderItem.objects.all()
        
        if not is_api_superuser(user):
            payments_qs = payments_qs.filter(order__brand=brand)
            tables_qs = tables_qs.filter(brand=brand)
            orders_qs = orders_qs.filter(brand=brand)
            order_items_qs = order_items_qs.filter(order__brand=brand)

        branch_id = request.query_params.get('branch_id')
        if branch_id:
            try:
                bid = int(branch_id)
                branch = resolve_branch_for_user(request, bid)
                if branch:
                    payments_qs = payments_qs.filter(order__branch_id=bid)
                    tables_qs = tables_qs.filter(branch_id=bid)
                    orders_qs = orders_qs.filter(branch_id=bid)
                    order_items_qs = order_items_qs.filter(order__branch_id=bid)
            except (TypeError, ValueError):
                pass

        today_payments = payments_qs.filter(created_at__gte=start_of_today)
        today_revenue = today_payments.aggregate(total=Sum('amount'))['total'] or 0.00
        
        # Active tables
        active_tables = tables_qs.exclude(status='empty').count()
        empty_tables = tables_qs.filter(status='empty').count()
        
        # Active orders (preparing or ready)
        active_orders = orders_qs.filter(status__in=['preparing', 'ready']).count()
        
        # Popular items (top 5)
        popular = order_items_qs.filter(
            order__status='completed'
        ).values(
            name=F('menu_item__name')
        ).annotate(
            count=Sum('quantity')
        ).order_by('-count')[:5]
        
        # Revenue by payment method
        payment_methods = today_payments.values('payment_method').annotate(total=Sum('amount'))
        methods_data = {
            'cash': 0.00,
            'card': 0.00
        }
        for pm in payment_methods:
            methods_data[pm['payment_method']] = pm['total']
            
        # Last 7 days daily sales
        daily_sales = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.max.time()))
            
            day_revenue = payments_qs.filter(
                created_at__range=(day_start, day_end)
            ).aggregate(total=Sum('amount'))['total'] or 0.00
            
            daily_sales.append({
                'date': day.strftime('%d.%m'),
                'revenue': float(day_revenue)
            })

        return Response({
            'today_revenue': float(today_revenue),
            'active_tables': active_tables,
            'empty_tables': empty_tables,
            'active_orders': active_orders,
            'popular_items': list(popular),
            'payment_methods': methods_data,
            'daily_sales': daily_sales
        })

class OrderChannelViewSet(viewsets.ModelViewSet):
    serializer_class = OrderChannelSerializer

    def get_queryset(self):
        return filter_by_brand(OrderChannel.objects.all().order_by('name'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class CashRegisterViewSet(viewsets.ModelViewSet):
    serializer_class = CashRegisterSerializer

    def get_queryset(self):
        return filter_by_tenant(CashRegister.objects.select_related('branch').order_by('name'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer

    def get_queryset(self):
        return filter_by_brand(Ingredient.objects.all().order_by('name'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer

    def get_queryset(self):
        return filter_by_brand(Recipe.objects.all().order_by('id'), self.request, brand_field='menu_item__brand')

class RecipeIngredientViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeIngredientSerializer

    def get_queryset(self):
        return filter_by_brand(RecipeIngredient.objects.all().order_by('id'), self.request, brand_field='recipe__menu_item__brand')

class StaffMemberViewSet(viewsets.ModelViewSet):
    serializer_class = StaffMemberSerializer

    def get_queryset(self):
        return filter_by_brand(StaffMember.objects.all().order_by('id'), self.request, brand_field='user__profile__brand')

class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsRestaurantFinanceRole]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        return filter_by_brand(Expense.objects.all().order_by('-date'), self.request, brand_field='staff_member__user__profile__brand')

    def perform_create(self, serializer):
        with transaction.atomic():
            expense = serializer.save()
            
            # Find default cash register for user's brand
            user = self.request.user
            profile = get_api_profile(user, request)
            brand = profile.brand if profile else None
            register = CashRegister.objects.filter(brand=brand).first()
            if not register:
                register = CashRegister.objects.create(brand=brand, name='Ana Kasa', balance=0.00, location='Merkez')
            
            # Log CashTransaction (which will automatically deduct the register balance!)
            CashTransaction.objects.create(
                register=register,
                transaction_type='out',
                amount=expense.amount,
                description=f"Gider: {expense.title} ({expense.category or 'Genel'})"
            )

class CashTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsRestaurantFinanceRole]
    serializer_class = CashTransactionSerializer

    def get_queryset(self):
        queryset = CashTransaction.objects.all().order_by('-id')
        queryset = filter_by_brand(queryset, self.request, brand_field='register__brand')
        register_id = self.request.query_params.get('register', None)
        if register_id is not None:
            queryset = queryset.filter(register_id=register_id)
        return queryset

    def perform_create(self, serializer):
        register_id = self.request.data.get('register')
        register, err = get_tenant_register(self.request.user, register_id, self.request)
        if err:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(err.data.get('error', 'Yetkisiz erişim.'))
        serializer.save(register=register)

class StockAuditViewSet(viewsets.ModelViewSet):
    serializer_class = StockAuditSerializer

    def get_queryset(self):
        queryset = StockAudit.objects.all().order_by('-date').distinct()
        return filter_by_brand(queryset, self.request, brand_field='items__ingredient__brand')

    def create(self, request, *args, **kwargs):
        items_data = request.data.get('items', [])
        notes = request.data.get('notes', '')

        if not items_data:
            return Response({'error': 'Sayım yapılacak malzeme bulunamadı'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                audit = StockAudit.objects.create(notes=notes, total_variance_amount=0)
                total_variance = 0

                for item in items_data:
                    ing_id = item.get('ingredient')
                    actual_stock = float(item.get('actual_stock', 0))

                    ingredient, ing_err = get_tenant_ingredient(request.user, ing_id, request)
                    if ing_err or not ingredient:
                        continue

                    system_stock = float(ingredient.stock_quantity)
                    variance = actual_stock - system_stock
                    unit_price = float(ingredient.unit_price)
                    cost_difference = variance * unit_price

                    # Save Audit Item
                    StockAuditItem.objects.create(
                        audit=audit,
                        ingredient=ingredient,
                        system_stock=system_stock,
                        actual_stock=actual_stock,
                        variance=variance,
                        unit_price=unit_price,
                        cost_difference=cost_difference
                    )

                    # Update ingredient stock quantity in database
                    ingredient.stock_quantity = actual_stock
                    ingredient.save()

                    total_variance += cost_difference

                # Save the total variance on audit
                audit.total_variance_amount = total_variance
                audit.save()

            return Response(StockAuditSerializer(audit).data, status=status.HTTP_201_CREATED)
        except (ValueError, TypeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CourierViewSet(viewsets.ModelViewSet):
    serializer_class = CourierSerializer

    def get_queryset(self):
        return filter_by_brand(Courier.objects.all().order_by('name'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class CourierLogViewSet(viewsets.ModelViewSet):
    serializer_class = CourierLogSerializer

    def get_queryset(self):
        return filter_by_brand(CourierLog.objects.all().order_by('-timestamp'), self.request, brand_field='courier__brand')

class RestaurantProfileViewSet(viewsets.ModelViewSet):
    serializer_class = RestaurantProfileSerializer

    def get_queryset(self):
        return filter_by_brand(RestaurantProfile.objects.all(), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        profile = get_api_profile(request.user, request)
        if not is_api_superuser(request.user) and profile and profile.brand:
            from restaurant.api.plan_limits import check_feature
            from rest_framework.exceptions import PermissionDenied
            ok, err = check_feature(profile.brand, 'crm')
            if not ok:
                raise PermissionDenied(err)

    def get_queryset(self):
        return filter_by_brand(Customer.objects.all().order_by('-id'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

class WhatsAppConfigViewSet(viewsets.ModelViewSet):
    serializer_class = WhatsAppConfigSerializer

    def get_queryset(self):
        return filter_by_brand(WhatsAppConfig.objects.all().order_by('-id'), self.request)

    def perform_create(self, serializer):
        assign_brand(serializer, self.request)

    @action(detail=False, methods=['post'])
    def send_campaign(self, request):
        profile = get_api_profile(request.user, request)
        if profile and profile.brand:
            from restaurant.api.plan_limits import check_feature
            ok, err = check_feature(profile.brand, 'whatsapp')
            if not ok:
                return Response({'error': err}, status=status.HTTP_403_FORBIDDEN)

        message = request.data.get('message', '')
        recipients = request.data.get('recipients', [])
        
        if not message or not recipients:
            return Response({'error': 'Mesaj ve alıcı listesi gereklidir'}, status=status.HTTP_400_BAD_REQUEST)
        
        logs = []
        for index, r in enumerate(recipients):
            logs.append({
                'id': index + 1,
                'customer': r.get('name'),
                'phone': r.get('phone'),
                'status': 'Gönderildi',
                'message_preview': message.replace('{customer_name}', r.get('name', 'Müşteri'))
            })
        
        return Response({
            'status': 'success',
            'message': f'{len(recipients)} müşteriye kampanya gönderimi simüle edildi.',
            'logs': logs
        })

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by('name')
    serializer_class = BranchSerializer

    def _get_profile(self):
        return get_api_profile(self.request.user, self.request)

    def _can_manage_franchise(self):
        profile = self._get_profile()
        if not profile:
            return False
        return profile.role == 'store_owner' or is_api_superuser(self.request.user)

    def get_queryset(self):
        queryset = Branch.objects.all().order_by('name')
        user = self.request.user
        if not user.is_authenticated:
            return Branch.objects.none()
        profile = self._get_profile()
        if not is_api_superuser(user):
            if profile.brand:
                queryset = queryset.filter(brand=profile.brand)
            else:
                queryset = Branch.objects.none()
        return queryset

    def create(self, request, *args, **kwargs):
        if not self._can_manage_franchise():
            return Response(
                {'error': 'Franchise oluşturma yalnızca kurum yöneticisine aittir.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = self._get_profile()
        brand = profile.brand if profile and profile.role == 'store_owner' else None
        if not brand and is_api_superuser(request.user):
            from core_settings.models import BusinessBrand as Brand
            brand_id = request.data.get('brand')
            brand = Brand.objects.filter(panel_kind=Brand.PANEL_HQ).filter(id=brand_id).first() if brand_id else Brand.objects.filter(panel_kind=Brand.PANEL_HQ).first()
        if brand:
            from restaurant.api.plan_limits import check_limit, check_feature
            ok, err = check_feature(brand, 'multi_branch')
            if not ok and Branch.objects.filter(brand=brand).count() >= 1:
                return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
            ok, err = check_limit(brand, 'branches')
            if not ok:
                return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._can_manage_franchise():
            return Response(
                {'error': 'Franchise yönetimi yalnızca kurum yöneticisine aittir.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._can_manage_franchise():
            return Response(
                {'error': 'Franchise silme yalnızca kurum yöneticisine aittir.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        from .franchise_views import _generate_panel_slug
        user = self.request.user
        profile = get_api_profile(user, request)
        if profile and profile.brand and profile.role == 'store_owner':
            branch = serializer.save(brand=profile.brand)
        else:
            brand_id = self.request.data.get('brand')
            if brand_id:
                branch = serializer.save(brand_id=brand_id)
            else:
                from core_settings.models import BusinessBrand as Brand
                brand = Brand.objects.filter(panel_kind=Brand.PANEL_HQ).first()
                if brand:
                    branch = serializer.save(brand=brand)
                else:
                    raise Exception('Bir marka bulunamadı.')
        if not branch.panel_slug:
            branch.panel_slug = _generate_panel_slug(branch)
            branch.save(update_fields=['panel_slug'])
        _seed_branch_tables(branch)


class MenuItemModifierViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemModifierSerializer

    def get_queryset(self):
        queryset = MenuItemModifier.objects.all().order_by('id')
        queryset = filter_by_brand(queryset, self.request, brand_field='menu_item__brand')
        menu_item_id = self.request.query_params.get('menu_item', None)
        if menu_item_id is not None:
            queryset = queryset.filter(menu_item_id=menu_item_id)
        return queryset

class LowStockView(views.APIView):
    """Returns all ingredients where stock_quantity <= minimum_stock (and minimum_stock > 0)."""
    def get(self, request):
        low = Ingredient.objects.filter(
            minimum_stock__gt=0,
            stock_quantity__lte=F('minimum_stock')
        ).order_by('name')
        low = filter_by_brand(low, request)
        from restaurant.api.serializers import IngredientSerializer
        data = IngredientSerializer(low, many=True).data
        return Response({
            'count': low.count(),
            'items': data
        })


class ReportStatsView(views.APIView):
    """Comprehensive report stats with date range filtering."""
    def get(self, request):
        from datetime import datetime as dt

        today = timezone.localtime().date()

        # Parse date range
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')

        if start_str:
            try:
                start_date = dt.strptime(start_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = today
        else:
            start_date = today

        if end_str:
            try:
                end_date = dt.strptime(end_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = today
        else:
            end_date = today

        # Make timezone-aware datetimes
        start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))

        # Previous period for comparison (same duration before start_date)
        period_days = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date - timedelta(days=1)
        prev_start_dt = timezone.make_aware(timezone.datetime.combine(prev_start, timezone.datetime.min.time()))
        prev_end_dt = timezone.make_aware(timezone.datetime.combine(prev_end, timezone.datetime.max.time()))

        brand = get_user_brand(request.user)
        profile = get_api_profile(request.user, request)

        orders = Order.objects.filter(created_at__range=(start_dt, end_dt))
        payments = Payment.objects.filter(created_at__range=(start_dt, end_dt))
        expenses = Expense.objects.filter(date__range=(start_date, end_date))

        if not is_api_superuser(user):
            if brand:
                orders = orders.filter(brand=brand)
                payments = payments.filter(order__brand=brand)
                expenses = expenses.filter(staff_member__user__profile__brand=brand)
            else:
                orders = Order.objects.none()
                payments = Payment.objects.none()
                expenses = Expense.objects.none()

        completed_orders = orders.filter(status='completed')

        total_revenue = payments.aggregate(t=Sum('amount'))['t'] or 0
        total_expense = expenses.aggregate(t=Sum('amount'))['t'] or 0
        net_profit = float(total_revenue) - float(total_expense)
        order_count = completed_orders.count()
        avg_order = float(total_revenue) / order_count if order_count > 0 else 0

        # Payment method breakdown
        payment_methods = payments.values('payment_method').annotate(total=Sum('amount'))
        methods_data = {'cash': 0.0, 'card': 0.0}
        for pm in payment_methods:
            methods_data[pm['payment_method']] = float(pm['total'])

        prev_payments = Payment.objects.filter(created_at__range=(prev_start_dt, prev_end_dt))
        prev_expenses = Expense.objects.filter(date__range=(prev_start, prev_end))
        prev_completed = Order.objects.filter(created_at__range=(prev_start_dt, prev_end_dt), status='completed')
        if not is_api_superuser(request.user) and brand:
            prev_payments = prev_payments.filter(order__brand=brand)
            prev_expenses = prev_expenses.filter(staff_member__user__profile__brand=brand)
            prev_completed = prev_completed.filter(brand=brand)
        elif not is_api_superuser(request.user):
            prev_payments = Payment.objects.none()
            prev_expenses = Expense.objects.none()
            prev_completed = Order.objects.none()

        prev_revenue = float(prev_payments.aggregate(t=Sum('amount'))['t'] or 0)
        prev_expense_total = float(prev_expenses.aggregate(t=Sum('amount'))['t'] or 0)
        prev_order_count = prev_completed.count()

        def pct_change(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 1)

        # ── Daily sales series ──
        daily_sales = []
        for i in range((end_date - start_date).days + 1):
            day = start_date + timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.max.time()))
            day_pay_qs = Payment.objects.filter(created_at__range=(day_start, day_end))
            day_ord_qs = Order.objects.filter(created_at__range=(day_start, day_end), status='completed')
            if not is_api_superuser(request.user) and brand:
                day_pay_qs = day_pay_qs.filter(order__brand=brand)
                day_ord_qs = day_ord_qs.filter(brand=brand)
            elif not is_api_superuser(request.user):
                day_pay_qs = Payment.objects.none()
                day_ord_qs = Order.objects.none()
            day_revenue = float(day_pay_qs.aggregate(t=Sum('amount'))['t'] or 0)
            day_orders = day_ord_qs.count()
            daily_sales.append({
                'date': day.strftime('%d.%m'),
                'full_date': day.strftime('%Y-%m-%d'),
                'revenue': day_revenue,
                'orders': day_orders,
            })

        # ── Hourly distribution ──
        hourly = [0] * 24
        for order in completed_orders:
            h = timezone.localtime(order.created_at).hour
            hourly[h] += 1

        # ── Top 10 products ──
        top_products = OrderItem.objects.filter(
            order__in=completed_orders
        ).values(
            name=F('menu_item__name')
        ).annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        ).order_by('-total_qty')[:10]

        # ── Channel breakdown ──
        channel_breakdown = {}
        for o in completed_orders:
            channel = 'Masa Satışları'
            if o.table and o.table.name:
                for ch in ['Yemeksepeti', 'Getir', 'Trendyol', 'Migros', 'WebSitesi']:
                    if o.table.name.startswith(ch):
                        channel = ch
                        break
            channel_breakdown[channel] = channel_breakdown.get(channel, 0) + float(o.total_amount)

        # ── Expense category breakdown ──
        expense_breakdown = {}
        for e in expenses:
            cat = e.category or 'Diğer'
            expense_breakdown[cat] = expense_breakdown.get(cat, 0) + float(e.amount)

        # ── Recent orders ──
        recent_orders = []
        for o in orders.order_by('-created_at')[:20]:
            payment = o.payments.first()
            recent_orders.append({
                'id': o.id,
                'table': o.table.name if o.table else '—',
                'total': float(o.total_amount),
                'status': o.get_status_display(),
                'status_key': o.status,
                'payment_method': payment.get_payment_method_display() if payment else '—',
                'date': timezone.localtime(o.created_at).strftime('%d.%m.%Y %H:%M'),
                'item_count': o.items.count(),
            })

        return Response({
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': period_days,
            },
            'summary': {
                'total_revenue': float(total_revenue),
                'total_expense': float(total_expense),
                'net_profit': net_profit,
                'order_count': order_count,
                'avg_order': round(avg_order, 2),
                'cash_total': methods_data['cash'],
                'card_total': methods_data['card'],
            },
            'comparison': {
                'revenue_change': pct_change(float(total_revenue), prev_revenue),
                'expense_change': pct_change(float(total_expense), prev_expense_total),
                'profit_change': pct_change(net_profit, prev_revenue - prev_expense_total),
                'order_change': pct_change(order_count, prev_order_count),
            },
            'daily_sales': daily_sales,
            'hourly_distribution': hourly,
            'top_products': list(top_products),
            'channel_breakdown': channel_breakdown,
            'expense_breakdown': expense_breakdown,
            'recent_orders': recent_orders,
        })


def public_website_view(request, slug, page_slug=None):
    import json
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    import datetime

    profile = get_object_or_404(RestaurantProfile, website_slug=slug)
    
    # Template configuration
    template_val = profile.website_template or 'Modern Dark'
    parts = template_val.split('|')
    tpl_id = parts[0] if parts else 'Modern Dark'
    typography = parts[1] if len(parts) > 1 else 'Sans-serif'
    
    if tpl_id == 'Elegant Gold':
        bg = '#0f0e0c'
        text = '#f3e5c8'
        default_accent = '#d4af37'
        card_bg = '#1a1815'
    elif tpl_id == 'Cozy Retro':
        bg = '#f4ede4'
        text = '#2c221e'
        default_accent = '#d96a3b'
        card_bg = '#ede5dc'
    elif tpl_id == 'Minimal Light':
        bg = '#ffffff'
        text = '#111827'
        default_accent = '#10b981'
        card_bg = '#f9fafb'
    else: # Modern Dark
        bg = '#0b0c10'
        text = '#ffffff'
        default_accent = '#6366f1'
        card_bg = '#111218'
        
    accent = profile.website_theme_color or default_accent
    
    if typography == 'Serif':
        font = "'Playfair Display', Georgia, serif"
    elif typography == 'Monospace':
        font = "'Courier New', monospace"
    else:
        font = "'Outfit', 'Inter', system-ui, sans-serif"
        
    is_light = bg in ['#ffffff', '#f4ede4']
    border_color = 'rgba(0,0,0,0.08)' if is_light else 'rgba(255,255,255,0.06)'
    text_muted = 'rgba(0,0,0,0.6)' if is_light else 'rgba(255,255,255,0.6)'
    year = datetime.datetime.now().year

    # Load modular blocks
    about_raw = profile.website_about_text or ''
    blocks = []
    seo_data = {}
    pages_list = []
    
    if about_raw.strip().startswith('{'):
        try:
            parsed = json.loads(about_raw)
            pages_list = parsed.get('pages', [])
            blocks_fallback = parsed.get('blocks', [])
            seo_fallback = parsed.get('seo', {})
            
            # Convert blocks-only format to pages format
            if not pages_list and blocks_fallback:
                pages_list = [{
                    'id': 'home',
                    'title': 'Ana Sayfa',
                    'slug': 'home',
                    'blocks': blocks_fallback,
                    'seo': seo_fallback
                }]
        except Exception:
            pass
    elif about_raw.strip().startswith('['):
        try:
            blocks_fallback = json.loads(about_raw)
            pages_list = [{
                'id': 'home',
                'title': 'Ana Sayfa',
                'slug': 'home',
                'blocks': blocks_fallback,
                'seo': {}
            }]
        except Exception:
            pass

    # Resolve target page
    target_slug = page_slug or 'home'
    active_page = None
    if pages_list:
        for p in pages_list:
            if p.get('slug') == target_slug or (target_slug == 'home' and p.get('id') == 'home'):
                active_page = p
                break
        if not active_page:
            # Fallback to home page or first page
            for p in pages_list:
                if p.get('id') == 'home':
                    active_page = p
                    break
            if not active_page:
                active_page = pages_list[0]

    if active_page:
        blocks = active_page.get('blocks', [])
        seo_data = active_page.get('seo', {})
    else:
        blocks = []
        seo_data = {}

    # Build Navigation Links dynamically
    nav_links = []
    if pages_list:
        for p in pages_list:
            p_slug = p.get('slug', 'home')
            p_title = p.get('title', 'Sayfa')
            if p_slug == 'home' or p.get('id') == 'home':
                url = f"/w/{slug}/"
            else:
                url = f"/w/{slug}/{p_slug}/"
            
            is_active = p_slug == target_slug or (target_slug == 'home' and p_slug == 'home')
            style_attr = f'style="color:{accent}; font-weight:bold;"' if is_active else ''
            nav_links.append(f'<a href="{url}" {style_attr}>{p_title}</a>')
    else:
        nav_links = [
            f'<a href="/w/{slug}/">Anasayfa</a>',
            '<a href="#about">Hikayemiz</a>',
            '<a href="#menu">Menü</a>',
            '<a href="#hours">İletişim</a>'
        ]
    nav_links_html = "".join(nav_links)

    seo_title = seo_data.get('title') or (f"{profile.name} - Tanıtım Web Sitesi" if target_slug == 'home' else f"{active_page.get('title', 'Sayfa')} | {profile.name}")
    seo_desc = seo_data.get('description') or "Taze malzemeler ve usta ellerden çıkan eşsiz lezzetlerle dolu restoranımıza hoş geldiniz!"
    seo_keywords = seo_data.get('keywords') or f"{profile.name}, restoran, menü, yemek siparişi, rezervasyon"

    # If no blocks loaded, use default fallback structure
    if not blocks:
        blocks = [
            {
                'id': 'hero-1',
                'type': 'hero',
                'title': 'Giriş',
                'content': {
                    'banner': profile.website_banner_text or 'Eşsiz Lezzetlerin Buluşma Noktası',
                    'subtitle': 'Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.',
                    'button_text': 'Masa Rezervasyonu Yap',
                    'button_url': '#reservation',
                    'layout': 'center'
                }
            },
            {
                'id': 'about-1',
                'type': 'about',
                'title': 'Hikayemiz',
                'content': {
                    'text': about_raw or 'Yılların getirdiği tecrübe ve mutfak aşkıyla, misafirlerimize en taze ve en lezzetli yemekleri sunmak için her gün aynı heyecanla çalışıyoruz.',
                    'image': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80',
                    'layout': 'left'
                }
            },
            {
                'id': 'menu-1',
                'type': 'menu',
                'title': 'Öne Çıkan Lezzetler',
                'content': {
                    'layout': 'grid',
                    'items': [
                        {'name': 'Bidolu Kebap', 'description': 'Özel marine edilmiş kuzu kıyması, lavaş ve közlenmiş garnitür ile', 'price': '280', 'image': ''},
                        {'name': 'Taş Fırın Lahmacun', 'description': 'Bol kıymalı harç, taze yeşillik ve limon ile', 'price': '85', 'image': ''},
                        {'name': 'Ev Yapımı Künefe', 'description': 'Sıcak şerbet, eritilmiş peynir ve Antep fıstığı ile', 'price': '150', 'image': ''}
                    ]
                }
            },
            {
                'id': 'hours-1',
                'type': 'hours',
                'title': 'İletişim & Çalışma Saatleri',
                'content': {
                    'layout': 'split',
                    'address': 'Atatürk Mah. Fatih Cad. No:42, Ataşehir/İstanbul',
                    'phone': '0216 555 44 33',
                    'times': [
                        {'day': 'Pazartesi - Cuma', 'hours': '11:00 - 23:00'},
                        {'day': 'Cumartesi - Pazar', 'hours': '11:00 - 00:00'}
                    ]
                }
            },
            {
                'id': 'reservation-1',
                'type': 'reservation',
                'title': 'Online Masa Rezervasyonu',
                'content': {}
            }
        ]

    # Generate sections html
    sections_html = []
    
    for block in blocks:
        b_type = block.get('type')
        b_title = block.get('title', '')
        b_content = block.get('content', {})
        
        if b_type == 'hero':
            layout = b_content.get('layout', 'center')
            banner = b_content.get('banner', 'Eşsiz Lezzetlerin Buluşma Noktası')
            subtitle = b_content.get('subtitle', 'Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.')
            btn_text = b_content.get('button_text', 'Masa Rezervasyonu Yap')
            image_url = b_content.get('image', 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80')
            
            res_btn = ''
            if profile.website_enable_reservation and btn_text:
                res_btn = f'''
                <button onclick="document.getElementById('res-modal').style.display='flex'" class="btn-primary-custom" style="border:none; background:{accent}; color:{'#000000' if is_light else '#ffffff'}; padding:12px 28px; font-size:14px; border-radius:30px; font-weight:750; cursor:pointer; display:inline-flex; gap:8px; align-items:center; margin-top:16px; box-shadow: 0 4px 14px {accent}40; transition: transform 0.2s ease;">
                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                     {btn_text}
                </button>
                '''
                
            if layout == 'split':
                sections_html.append(f'''
                <section style="padding: 60px 0; border-bottom: 1px solid {border_color};">
                    <div class="container" style="display:flex; flex-direction:row; flex-wrap:wrap; gap:40px; align-items:center;">
                        <div style="flex: 1; min-width: 300px; text-align: left;">
                            <h1 style="font-size:36px; font-weight:800; line-height:1.2; margin: 0 0 20px 0;">{banner}</h1>
                            <p style="font-size:16px; opacity:0.8; line-height:1.6; margin-bottom:24px;">{subtitle}</p>
                            {res_btn}
                        </div>
                        <div style="flex: 1; min-width: 300px;">
                            <img src="{image_url}" style="width:100%; height:380px; object-fit:cover; border-radius:20px; box-shadow:0 20px 40px rgba(0,0,0,0.15);" alt="Hero" />
                        </div>
                    </div>
                </section>
                ''')
            elif layout == 'glass':
                sections_html.append(f'''
                <section style="padding: 100px 0; background-image: url('{image_url}'); background-size: cover; background-position: center; position:relative; border-bottom: 1px solid {border_color};">
                    <div style="position:absolute; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.5); z-index:1;"></div>
                    <div class="container" style="position:relative; z-index:2; display:flex; justify-content:center;">
                        <div style="background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.1); border-radius:24px; padding:60px 40px; max-width: 700px; width: 100%; text-align: center; box-shadow: 0 30px 60px rgba(0,0,0,0.35);">
                            <h1 style="font-size:36px; font-weight:800; line-height:1.2; color:#ffffff; margin: 0 0 20px 0;">{banner}</h1>
                            <p style="font-size:16px; color:rgba(255,255,255,0.9); line-height:1.6; margin-bottom:24px;">{subtitle}</p>
                            {res_btn}
                        </div>
                    </div>
                </section>
                ''')
            else: # center layout
                sections_html.append(f'''
                <section style="padding: 80px 0; text-align: center; background: linear-gradient(to bottom, {accent}08, transparent); border-bottom: 1px solid {border_color};">
                    <div class="container" style="display:flex; flex-direction:column; align-items:center; justify-content:center;">
                        <h1 style="font-size:42px; font-weight:800; line-height:1.2; max-width:800px; margin: 0 auto 20px auto;">{banner}</h1>
                        <div style="width:60px; height:3px; background:{accent}; margin:0 auto 24px auto; border-radius:2px;"></div>
                        <p style="font-size:16px; opacity:0.8; max-width:600px; margin:0 auto 24px auto; line-height:1.6;">{subtitle}</p>
                        <div style="display:flex; justify-content:center; width:100%;">{res_btn}</div>
                    </div>
                </section>
                ''')
                
        elif b_type == 'about':
            layout = b_content.get('layout', 'left')
            text = b_content.get('text', '')
            image = b_content.get('image', 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80')
            
            if layout == 'minimal':
                sections_html.append(f'''
                <section id="about" style="padding: 60px 0; background: {card_bg if is_light else 'transparent'}; border-bottom: 1px solid {border_color};">
                    <div class="container" style="max-width:800px; text-align:center;">
                        <h2 style="font-size:28px; font-weight:800; margin-bottom:12px; color:{accent};">{b_title}</h2>
                        <div style="width:40px; height:2px; background:{accent}; margin: 0 auto 20px auto;"></div>
                        <p style="font-size:15px; line-height:1.8; opacity:0.85; margin:0;">{text}</p>
                    </div>
                </section>
                ''')
            else: # left or right
                flex_dir = 'row' if layout == 'left' else 'row-reverse'
                sections_html.append(f'''
                <section id="about" style="padding: 60px 0; background: {card_bg if is_light else 'transparent'}; border-bottom: 1px solid {border_color};">
                    <div class="container" style="display:flex; flex-direction:{flex_dir}; flex-wrap:wrap; gap:40px; align-items:center;">
                        <div style="flex: 1.2; min-width: 300px; text-align: left;">
                            <h2 style="font-size:28px; font-weight:800; margin-top:0; margin-bottom:16px; color:{accent};">{b_title}</h2>
                            <div style="width:40px; height:2px; background:{accent}; margin-bottom:20px;"></div>
                            <p style="font-size:15px; line-height:1.75; opacity:0.85; margin:0;">{text}</p>
                        </div>
                        <div style="flex: 1; min-width: 300px;">
                            <img src="{image}" style="width:100%; height:320px; object-fit:cover; border-radius:16px; box-shadow:0 12px 30px rgba(0,0,0,0.1);" alt="About" />
                        </div>
                    </div>
                </section>
                ''')
                
        elif b_type == 'menu':
            layout = b_content.get('layout', 'grid')
            items = b_content.get('items', [])
            
            items_cards = []
            
            if layout == 'list':
                for item in items:
                    name = item.get('name', '')
                    price = item.get('price', '0')
                    desc = item.get('description', '')
                    items_cards.append(f'''
                    <div style="margin-bottom:20px; text-align:left;">
                        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:4px;">
                            <span style="font-size:16px; font-weight:700; color:{text};">{name}</span>
                            <div style="flex-grow:1; border-bottom:1px dotted {border_color}; margin:0 12px; height:1px;"></div>
                            <span style="font-size:16px; font-weight:800; color:{accent};">{price} ₺</span>
                        </div>
                        {f'<p style="font-size:13px; color:{text_muted}; margin:0; line-height:1.4;">{desc}</p>' if desc else ''}
                    </div>
                    ''')
                items_container = f'<div style="max-width:800px; margin:0 auto;">{"".join(items_cards)}</div>'
            elif layout == 'minimal':
                for item in items:
                    name = item.get('name', '')
                    price = item.get('price', '0')
                    desc = item.get('description', '')
                    items_cards.append(f'''
                    <div style="background:{card_bg}; border:1px solid {border_color}; border-radius:12px; padding:20px; text-align:left;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-weight:700; font-size:15px;">{name}</span>
                            <span style="color:{accent}; font-weight:800; font-size:15px;">{price} ₺</span>
                        </div>
                        {f'<p style="font-size:12px; color:{text_muted}; margin:0; line-height:1.4;">{desc}</p>' if desc else ''}
                    </div>
                    ''')
                items_container = f'<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:20px;">{"".join(items_cards)}</div>'
            else: # grid with images
                for item in items:
                    name = item.get('name', '')
                    price = item.get('price', '0')
                    desc = item.get('description', '')
                    img = item.get('image', '')
                    
                    img_html = f'<img src="{img}" style="width:100%; height:160px; object-fit:cover; border-radius:8px 8px 0 0;" alt="" />' if img else f'<div style="width:100%; height:120px; background:{accent}15; display:flex; align-items:center; justify-content:center; color:{accent}; font-size:24px; font-weight:bold; border-radius:8px 8px 0 0;">🍽️</div>'
                    
                    items_cards.append(f'''
                    <div style="background:{card_bg}; border:1px solid {border_color}; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; text-align:left;">
                        {img_html}
                        <div style="padding:16px; display:flex; flex-direction:column; gap:6px; flex-grow:1;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:700; font-size:14px;">{name}</span>
                                <span style="color:{accent}; font-weight:800; font-size:14px;">{price} ₺</span>
                            </div>
                            {f'<p style="font-size:12px; color:{text_muted}; margin:0; line-height:1.4; flex-grow:1;">{desc}</p>' if desc else ''}
                        </div>
                    </div>
                    ''')
                items_container = f'<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:24px;">{"".join(items_cards)}</div>'
                
            sections_html.append(f'''
            <section id="menu" style="padding: 60px 0; border-bottom: 1px solid {border_color};">
                <div class="container">
                    <h2 style="font-size:28px; font-weight:800; margin-bottom:12px; color:{accent}; text-align:center;">{b_title}</h2>
                    <div style="width:40px; height:2px; background:{accent}; margin:0 auto 40px auto;"></div>
                    {items_container}
                </div>
            </section>
            ''')
            
        elif b_type == 'testimonials':
            layout = b_content.get('layout', 'grid')
            quotes = b_content.get('quotes', [])
            
            quotes_html = []
            
            if layout == 'spotlight':
                if quotes:
                    q = quotes[0]
                    stars = '⭐' * int(q.get('rating', 5))
                    quotes_html.append(f'''
                    <div style="max-width:700px; margin:0 auto; background:{card_bg}; padding:40px; border-radius:20px; border:1px solid {border_color}; box-shadow:0 15px 35px rgba(0,0,0,0.05); text-align:center; position:relative;">
                        <span style="font-size:80px; color:{accent}15; position:absolute; top:20px; left:30px; font-family:serif; line-height:0; pointer-events:none;">“</span>
                        <div style="color:{accent}; font-size:14px; margin-bottom:16px;">{stars}</div>
                        <p style="font-size:18px; font-style:italic; line-height:1.7; margin:0 0 20px 0; position:relative; z-index:2;">"{q.get('text', '')}"</p>
                        <span style="font-size:14px; font-weight:750; color:{accent}; display:block;">- {q.get('name', '')}</span>
                    </div>
                    ''')
                quotes_container = "".join(quotes_html)
            else: # grid layout
                for q in quotes:
                    stars = '⭐' * int(q.get('rating', 5))
                    quotes_html.append(f'''
                    <div style="background:{card_bg}; border:1px solid {border_color}; border-radius:12px; padding:24px; text-align:left; box-shadow:0 4px 15px rgba(0,0,0,0.02);">
                        <div style="color:{accent}; font-size:11px; margin-bottom:10px;">{stars}</div>
                        <p style="font-size:13.5px; font-style:italic; line-height:1.6; margin:0 0 12px 0; opacity:0.9;">"{q.get('text', '')}"</p>
                        <span style="font-size:12px; font-weight:700; color:{accent}; display:block;">- {q.get('name', '')}</span>
                    </div>
                    ''')
                quotes_container = f'<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px;">{"".join(quotes_html)}</div>'
                
            sections_html.append(f'''
            <section id="testimonials" style="padding: 60px 0; border-bottom: 1px solid {border_color};">
                <div class="container">
                    <h2 style="font-size:28px; font-weight:800; margin-bottom:12px; color:{accent}; text-align:center;">{b_title}</h2>
                    <div style="width:40px; height:2px; background:{accent}; margin:0 auto 36px auto;"></div>
                    {quotes_container}
                </div>
            </section>
            ''')
            
        elif b_type == 'hours':
            layout = b_content.get('layout', 'split')
            address = b_content.get('address', '')
            phone = b_content.get('phone', '')
            times = b_content.get('times', [])
            
            times_rows = []
            for t in times:
                times_rows.append(f'''
                <div style="display:flex; justify-content:space-between; font-size:14px; padding:8px 0; border-bottom: 1px solid {border_color};">
                    <span style="font-weight:600;">{t.get('day', '')}</span>
                    <span>{t.get('hours', '')}</span>
                </div>
                ''')
            times_table = f'<div style="background:{card_bg}; border:1px solid {border_color}; border-radius:12px; padding:20px;">{"".join(times_rows)}</div>'
            
            contact_info = ''
            if address:
                contact_info += f'<p style="font-size:15px; margin: 0 0 12px 0; display:flex; gap:10px; align-items:center;"><span>📍</span> <span>{address}</span></p>'
            if phone:
                contact_info += f'<p style="font-size:15px; margin: 0 0 12px 0; display:flex; gap:10px; align-items:center;"><span>📞</span> <a href="tel:{phone}" style="color:{text}; text-decoration:none; font-weight:600;">{phone}</a></p>'
                
            if layout == 'center':
                sections_html.append(f'''
                <section id="hours" style="padding: 60px 0; border-bottom: 1px solid {border_color};">
                    <div class="container" style="max-width:700px; text-align:center;">
                        <h2 style="font-size:28px; font-weight:800; margin-bottom:12px; color:{accent};">{b_title}</h2>
                        <div style="width:40px; height:2px; background:{accent}; margin: 0 auto 30px auto;"></div>
                        <div style="margin-bottom:24px; display:inline-block; text-align:center;">
                            {contact_info}
                        </div>
                        {times_table}
                    </div>
                </section>
                ''')
            else: # split layout
                sections_html.append(f'''
                <section id="hours" style="padding: 60px 0; border-bottom: 1px solid {border_color};">
                    <div class="container" style="display:flex; flex-direction:row; flex-wrap:wrap; gap:40px;">
                        <div style="flex:1; min-width:280px; text-align:left;">
                            <h2 style="font-size:28px; font-weight:800; margin-top:0; margin-bottom:16px; color:{accent};">{b_title}</h2>
                            <div style="width:40px; height:2px; background:{accent}; margin-bottom:24px;"></div>
                            <div style="display:flex; flex-direction:column; gap:8px;">
                                {contact_info}
                            </div>
                        </div>
                        <div style="flex:1.2; min-width:280px;">
                            {times_table}
                        </div>
                    </div>
                </section>
                ''')
                
        elif b_type == 'reservation':
            if profile.website_enable_reservation:
                sections_html.append(f'''
                <section id="reservation" style="padding: 60px 0; text-align:center; background: linear-gradient(to top, {accent}08, transparent); border-bottom: 1px solid {border_color};">
                    <div class="container" style="max-width:700px;">
                        <h2 style="font-size:28px; font-weight:800; margin-bottom:12px; color:{accent};">{b_title}</h2>
                        <div style="width:40px; height:2px; background:{accent}; margin:0 auto 20px auto;"></div>
                        <p style="font-size:15px; opacity:0.8; line-height:1.6; margin-bottom:24px;">Harika bir yemek deneyimi için masanızı şimdiden ayırtın. Talebiniz anında tarafımıza ulaşacaktır.</p>
                        <button onclick="document.getElementById('res-modal').style.display='flex'" style="border:none; background:{accent}; color:{'#000000' if is_light else '#ffffff'}; padding:14px 36px; font-size:15px; border-radius:30px; font-weight:750; cursor:pointer; display:inline-flex; gap:8px; align-items:center; box-shadow: 0 4px 14px {accent}40;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            Masa Rezervasyonu Yap
                        </button>
                    </div>
                </section>
                ''')

    # Socials
    socials_html = []
    if profile.website_instagram:
        socials_html.append(f'<a href="https://instagram.com/{profile.website_instagram}" target="_blank" style="color:{text}; margin-left:16px; opacity:0.8; text-decoration:none; font-size:14px;">📸 Instagram</a>')
    if profile.website_facebook:
        socials_html.append(f'<a href="https://facebook.com/{profile.website_facebook}" target="_blank" style="color:{text}; margin-left:16px; opacity:0.8; text-decoration:none; font-size:14px;">👤 Facebook</a>')
    
    # Reservation form HTML
    reservation_form = f'''
    <div id="res-modal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.85); z-index:9999; align-items:center; justify-content:center; padding:16px; backdrop-filter:blur(5px);">
        <div style="background:{card_bg}; color:{text}; border:1px solid {border_color}; border-radius:20px; max-width:480px; width:100%; padding:32px; position:relative; box-shadow:0 15px 40px rgba(0,0,0,0.6); text-align:left;">
            <button onclick="document.getElementById('res-modal').style.display='none'" style="position:absolute; top:20px; right:20px; background:none; border:none; color:{text}; font-size:28px; cursor:pointer; opacity:0.6;">&times;</button>
            <h2 style="font-size:24px; font-weight:800; margin-top:0; margin-bottom:20px; color:{accent};">Masa Rezervasyonu</h2>
            <form id="reservation-form" onsubmit="submitReservation(event)">
                <div style="margin-bottom:16px;">
                    <label style="display:block; font-size:12.5px; font-weight:600; margin-bottom:6px; opacity:0.75;">Adınız Soyadınız</label>
                    <input type="text" required style="width:100%; padding:12px; border-radius:10px; border:1px solid {border_color}; background:{bg}; color:{text}; font-size:14.5px; outline:none;" />
                </div>
                <div style="margin-bottom:16px;">
                    <label style="display:block; font-size:12.5px; font-weight:600; margin-bottom:6px; opacity:0.75;">Telefon Numaranız</label>
                    <input type="tel" required placeholder="05xx xxx xx xx" style="width:100%; padding:12px; border-radius:10px; border:1px solid {border_color}; background:{bg}; color:{text}; font-size:14.5px; outline:none;" />
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
                    <div>
                        <label style="display:block; font-size:12.5px; font-weight:600; margin-bottom:6px; opacity:0.75;">Tarih</label>
                        <input type="date" required style="width:100%; padding:12px; border-radius:10px; border:1px solid {border_color}; background:{bg}; color:{text}; font-size:14.5px; outline:none;" />
                    </div>
                    <div>
                        <label style="display:block; font-size:12.5px; font-weight:600; margin-bottom:6px; opacity:0.75;">Saat</label>
                        <input type="time" required style="width:100%; padding:12px; border-radius:10px; border:1px solid {border_color}; background:{bg}; color:{text}; font-size:14.5px; outline:none;" />
                    </div>
                </div>
                <div style="margin-bottom:20px;">
                    <label style="display:block; font-size:12.5px; font-weight:600; margin-bottom:6px; opacity:0.75;">Kişi Sayısı</label>
                    <select style="width:100%; padding:12px; border-radius:10px; border:1px solid {border_color}; background:{bg}; color:{text}; font-size:14.5px; outline:none;">
                        <option>1 Kişi</option>
                        <option selected>2 Kişi</option>
                        <option>3 Kişi</option>
                        <option>4 Kişi</option>
                        <option>5 Kişi</option>
                        <option>6 Kişi</option>
                        <option>7+ Kişi</option>
                    </select>
                </div>
                <button type="submit" style="width:100%; border:none; background:{accent}; color:{'#000000' if is_light else '#ffffff'}; padding:14px; font-size:15px; border-radius:10px; font-weight:750; cursor:pointer; box-shadow:0 4px 12px {accent}30;">Rezervasyonu Tamamla</button>
            </form>
        </div>
    </div>
    '''

    html_content = f'''<!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{seo_title}</title>
        <meta name="description" content="{seo_desc}">
        <meta name="keywords" content="{seo_keywords}">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Outfit:wght@100..900&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                background: {bg};
                color: {text};
                font-family: {font};
                margin: 0;
                padding: 0;
                transition: background 0.3s, color 0.3s;
            }}
            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 0 24px;
            }}
            header {{
                border-bottom: 1px solid {border_color};
                padding: 20px 0;
            }}
            header .nav-flex {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            header .logo {{
                font-weight: 800;
                font-size: 22px;
                color: {accent};
                text-decoration: none;
            }}
            nav a {{
                color: {text};
                text-decoration: none;
                margin-left: 24px;
                font-size: 14px;
                opacity: 0.8;
                transition: opacity 0.2s;
            }}
            nav a:hover {{
                opacity: 1;
                color: {accent};
            }}
            footer {{
                border-top: 1px solid {border_color};
                padding: 30px 0;
                margin-top: 40px;
            }}
            .footer-flex {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 16px;
                font-size: 13.5px;
                opacity: 0.7;
            }}
            .btn-primary-custom:hover {{
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="container nav-flex">
                <a href="/w/{slug}/" class="logo">{profile.name}</a>
                <nav>
                    {nav_links_html}
                </nav>
            </div>
        </header>

        {"".join(sections_html)}

        <footer>
            <div class="container footer-flex">
                <span>© {year} {profile.name}. Tüm Hakları Saklıdır.</span>
                <div>
                    {"".join(socials_html)}
                </div>
            </div>
        </footer>

        {reservation_form}

        <script>
            function submitReservation(event) {{
                event.preventDefault();
                alert('Rezervasyon talebiniz başarıyla alındı! En kısa sürede telefon ile onay için sizinle iletişime geçeceğiz.');
                document.getElementById('res-modal').style.display = 'none';
                document.getElementById('reservation-form').reset();
            }}
        </script>
    </body>
    </html>
    '''
    return HttpResponse(html_content)
