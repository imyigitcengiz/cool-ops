from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from .models import Customer
from .forms import CustomerForm
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core_settings.models import ProductOption

class CustomerListView(ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('products')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(phone__icontains=q) |
                Q(region__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = ProductOption.objects.order_by('name')
        return context

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers')

class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers')

class CustomerDeleteView(DeleteView):
    model = Customer
    success_url = reverse_lazy('customers')

def bulk_delete_customers(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids')
        Customer.objects.filter(id__in=ids).delete()
    return redirect('customers')


@require_http_methods(["POST"])
def bulk_manage_customers(request):
    ids = [int(x) for x in request.POST.getlist('ids') if str(x).isdigit()]
    action = (request.POST.get('bulk_action') or '').strip()
    queryset = Customer.objects.filter(id__in=ids)

    if not ids:
        return JsonResponse({'ok': False, 'error': 'Toplu işlem için müşteri seçin.'}, status=400)
    if not action:
        return JsonResponse({'ok': False, 'error': 'Toplu işlem türü seçin.'}, status=400)

    if action == 'delete':
        count = queryset.count()
        queryset.delete()
        return JsonResponse({'ok': True, 'message': f'{count} müşteri silindi.'})

    if action == 'set_region':
        region = request.POST.get('bulk_region', '').strip()
        queryset.update(region=region or None)
        return JsonResponse({'ok': True, 'message': f'{queryset.count()} müşterinin bölgesi güncellendi.'})

    if action == 'set_contract_date':
        contract_date = request.POST.get('bulk_contract_date', '').strip()
        queryset.update(contract_date=contract_date or None)
        return JsonResponse({'ok': True, 'message': f'{queryset.count()} müşterinin sözleşme tarihi güncellendi.'})

    if action == 'add_product':
        product_id = request.POST.get('bulk_product_id')
        if not product_id or not str(product_id).isdigit():
            return JsonResponse({'ok': False, 'error': 'Ürün seçin.'}, status=400)
        product = get_object_or_404(ProductOption, pk=int(product_id))
        for customer in queryset:
            customer.products.add(product)
        return JsonResponse({'ok': True, 'message': f'{queryset.count()} müşteriye {product.name} eklendi.'})

    if action == 'remove_product':
        product_id = request.POST.get('bulk_product_id')
        if not product_id or not str(product_id).isdigit():
            return JsonResponse({'ok': False, 'error': 'Ürün seçin.'}, status=400)
        product = get_object_or_404(ProductOption, pk=int(product_id))
        for customer in queryset:
            customer.products.remove(product)
        return JsonResponse({'ok': True, 'message': f'{queryset.count()} müşteriden {product.name} kaldırıldı.'})

    return JsonResponse({'ok': False, 'error': 'Geçersiz toplu işlem.'}, status=400)

def quick_customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        region = request.POST.get('region')
        location_link = request.POST.get('location_link')
        contract_date = request.POST.get('contract_date')
        if name:
            customer = Customer.objects.create(
                name=name, phone=phone, region=region, 
                location_link=location_link, contract_date=contract_date or None
            )
            return JsonResponse({'id': customer.id, 'name': customer.name})
    return JsonResponse({'error': 'Geçersiz veri'}, status=400)

def customer_detail_api(request, pk):
    try:
        c = Customer.objects.get(pk=pk)
        return JsonResponse({
            'name': c.name,
            'phone': c.phone or '-',
            'whatsapp_link': c.whatsapp_link or '',
            'region': c.region or '-',
            'address': c.address or '-',
            'location_link': c.location_link or '',
            'contract_date': c.contract_date.strftime('%d.%m.%Y') if c.contract_date else '-',
            'contract_age': f"({c.contract_age} önce)" if c.contract_age else '',
            'product_ids': list(c.products.values_list('id', flat=True)),
            'product_names': list(c.products.values_list('name', flat=True)),
        })
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Müşteri bulunamadı'}, status=404)

@require_http_methods(["POST"])
def update_customer_products(request, pk):
    import json
    data = json.loads(request.body)
    product_ids = data.get('product_ids', [])
    c = Customer.objects.get(pk=pk)
    c.products.set(product_ids)
    return JsonResponse({'status': 'ok'})


@require_http_methods(["GET", "POST"])
def customer_quick_edit_api(request, pk):
    customer = get_object_or_404(Customer.objects.prefetch_related('products'), pk=pk)
    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone or '',
                'region': customer.region or '',
                'address': customer.address or '',
                'location_link': customer.location_link or '',
                'contract_date': customer.contract_date.isoformat() if customer.contract_date else '',
                'product_ids': list(customer.products.values_list('id', flat=True)),
            }
        })

    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Müşteri adı zorunlu.'}, status=400)

    customer.name = name
    customer.phone = request.POST.get('phone', '').strip() or None
    customer.region = request.POST.get('region', '').strip() or None
    customer.address = request.POST.get('address', '').strip() or None
    customer.location_link = request.POST.get('location_link', '').strip() or None
    customer.contract_date = request.POST.get('contract_date', '').strip() or None
    customer.save(update_fields=['name', 'phone', 'region', 'address', 'location_link', 'contract_date', 'updated_at'])

    product_ids = [int(x) for x in request.POST.getlist('product_ids') if str(x).isdigit()]
    customer.products.set(product_ids)

    return JsonResponse({'ok': True})
