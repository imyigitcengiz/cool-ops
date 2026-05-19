from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q, Min
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from urllib.parse import quote
from django.views.decorators.http import require_POST, require_http_methods
import csv
from .models import ServiceRecord, ServiceImage, ServiceHistory
from .forms import ServiceRecordForm
from .form_context import build_service_form_context
from core_settings.models import ServiceTeam, ServicePersonnel, StatusOption, PriorityOption


def _normalize_phone_for_wa(phone_raw):
    clean_phone = ''.join(ch for ch in (phone_raw or '') if ch.isdigit())
    if clean_phone.startswith('0'):
        clean_phone = '9' + clean_phone
    elif not clean_phone.startswith('90') and len(clean_phone) == 10:
        clean_phone = '90' + clean_phone
    return clean_phone


def _build_service_summary_message(target_label, services):
    lines = [f"{target_label} için servis özeti ({len(services)} kayıt):", ""]
    for index, s in enumerate(services, start=1):
        service_types = ", ".join([st.name for st in s.service_types.all()]) or "-"
        note = (s.notes or "-").strip() or "-"
        lines.append(f"{index}. Kayıt")
        lines.append(f"Müşteri Adı: {s.customer.name}")
        lines.append(f"Müşteri Telefonu: {s.customer.phone or '-TELEFON YOK- (Müşteriden telefon isteyin)'}")
        lines.append(f"Bölge: {s.customer.region or '-'}")
        lines.append(f"Arıza Tipi: {service_types}")
        lines.append(f"Servis Notu: {note}")
        if s.customer.location_link:
            lines.append(f"Konum URL: {s.customer.location_link}")
        else:
            lines.append("Konum URL: -URL Konum Yok- (Müşteriden konum isteyin)")
        lines.append("")
    return "\n".join(lines)


def _apply_service_filters(qs, request):
    q = request.GET.get('q')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    product = request.GET.get('product')
    warranty = request.GET.get('warranty')

    if q:
        qs = qs.filter(
            Q(customer__name__icontains=q) |
            Q(customer__phone__icontains=q) |
            Q(customer__region__icontains=q) |
            Q(notes__icontains=q) |
            Q(products__name__icontains=q) |
            Q(service_types__name__icontains=q)
        )
    if status:
        qs = qs.filter(status_id=status)
    if priority:
        qs = qs.filter(priority_id=priority)
    if product:
        qs = qs.filter(products__id=product)
    if warranty == 'expired':
        qs = qs.filter(Q(warranty_status='expired') | Q(status__name__icontains='ücretli'))
    elif warranty == 'active':
        qs = qs.filter(warranty_status='active').exclude(status__name__icontains='ücretli')
    return qs.distinct()


def _build_service_snapshot(service):
    customer = service.customer
    return {
        'service': {
            'status_id': service.status_id,
            'priority_id': service.priority_id,
            'solution_partner_id': service.solution_partner_id,
            'assigned_to_id': service.assigned_to_id,
            'service_personnel_id': service.service_personnel_id,
            'warranty_status': service.warranty_status,
            'notes': service.notes or '',
            'product_ids': list(service.products.values_list('id', flat=True)),
            'service_type_ids': list(service.service_types.values_list('id', flat=True)),
        },
        'customer': {
            'phone': customer.phone or '',
            'region': customer.region or '',
            'location_link': customer.location_link or '',
            'contract_date': customer.contract_date.isoformat() if customer.contract_date else '',
        }
    }


def _create_service_history(service, action, user=None):
    return ServiceHistory.objects.create(
        service=service,
        user=user if user and user.is_authenticated else None,
        action=action,
        snapshot=_build_service_snapshot(service),
    )


def _user_display(user_obj):
    if not user_obj:
        return '-'
    return user_obj.get_full_name() or user_obj.username


def _text_preview(value, max_len=80):
    text = (value or '').strip()
    if not text:
        return '-'
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}..."


def _capture_service_state(service):
    return {
        'customer': service.customer.name if service.customer_id else '-',
        'status': service.status.name if service.status_id else '-',
        'priority': service.priority.name if service.priority_id else '-',
        'warranty_status': service.get_warranty_status_display(),
        'solution_partner': service.solution_partner.name if service.solution_partner_id else '-',
        'service_personnel': service.service_personnel.name if service.service_personnel_id else '-',
        'assigned_to': _user_display(service.assigned_to),
        'notes': _text_preview(service.notes),
        'products': tuple(sorted(service.products.values_list('name', flat=True))),
        'service_types': tuple(sorted(service.service_types.values_list('name', flat=True))),
    }


def _diff_service_state(before_state, after_state):
    labels = {
        'customer': 'Müşteri',
        'status': 'Durum',
        'priority': 'Öncelik',
        'warranty_status': 'Garanti Durumu',
        'solution_partner': 'Çözüm Ortağı',
        'service_personnel': 'Servis Personeli',
        'assigned_to': 'Atanan Kullanıcı',
        'notes': 'Servis Notu',
        'products': 'Ürünler',
        'service_types': 'Servis Tipleri',
    }
    changes = []
    for key, label in labels.items():
        before_val = before_state.get(key)
        after_val = after_state.get(key)
        if before_val == after_val:
            continue
        if key in {'products', 'service_types'}:
            before_text = ', '.join(before_val) if before_val else '-'
            after_text = ', '.join(after_val) if after_val else '-'
        else:
            before_text = before_val or '-'
            after_text = after_val or '-'
        changes.append(f"{label}: {before_text} -> {after_text}")
    return changes

class ServiceListView(ListView):
    model = ServiceRecord
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('status', 'priority', 'customer', 'solution_partner', 'service_personnel', 'service_personnel__team').prefetch_related('products', 'service_types')
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        product = self.request.GET.get('product')
        warranty = self.request.GET.get('warranty')
        team = self.request.GET.get('team')
        personnel = self.request.GET.get('personnel')

        if q:
            queryset = queryset.filter(
                Q(customer__name__icontains=q) |
                Q(customer__phone__icontains=q) |
                Q(customer__region__icontains=q) |
                Q(notes__icontains=q) |
                Q(products__name__icontains=q) |
                Q(service_types__name__icontains=q)
            )
        if status:
            queryset = queryset.filter(status_id=status)
        if priority:
            queryset = queryset.filter(priority_id=priority)
        if product:
            queryset = queryset.filter(products__id=product)
        if team and team.isdigit():
            queryset = queryset.filter(service_personnel__team_id=int(team))
        if personnel and personnel.isdigit():
            queryset = queryset.filter(service_personnel_id=int(personnel))
        
        if warranty == 'expired':
            queryset = queryset.filter(
                Q(warranty_status='expired') | Q(status__name__icontains='ücretli')
            )
        elif warranty == 'active':
            queryset = queryset.filter(warranty_status='active').exclude(status__name__icontains='ücretli')
            
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core_settings.models import ProductOption, StatusOption, PriorityOption, ServiceTypeOption
        context['products'] = ProductOption.objects.all()
        context['statuses'] = StatusOption.objects.all()
        context['priorities'] = PriorityOption.objects.all()
        context['service_types'] = ServiceTypeOption.objects.order_by('name')
        context['teams'] = ServiceTeam.objects.filter(is_active=True).order_by('name')
        context['personnel_list'] = ServicePersonnel.objects.filter(is_active=True).select_related('team').order_by('name')
        return context

class ServiceCreateView(CreateView):
    model = ServiceRecord
    form_class = ServiceRecordForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_service_form_context())
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Proactive Logic: Sync service products back to customer profile
        # So the next service for this customer will have these products pre-selected.
        customer = self.object.customer
        for product in self.object.products.all():
            customer.products.add(product)
            
        _create_service_history(self.object, "Servis kaydı oluşturuldu.", self.request.user)
        images = self.request.FILES.getlist('images')
        for img in images:
            ServiceImage.objects.create(service=self.object, image=img)
        return response

class ServiceUpdateView(UpdateView):
    model = ServiceRecord
    form_class = ServiceRecordForm
    template_name = 'services/service_form.html'
    success_url = reverse_lazy('services')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_service_form_context(self.object))
        return context

    def form_valid(self, form):
        before_state = _capture_service_state(self.object)
        response = super().form_valid(form)
        self.object.refresh_from_db()
        after_state = _capture_service_state(self.object)
        changes = _diff_service_state(before_state, after_state)

        if changes:
            _create_service_history(self.object, " | ".join(changes), self.request.user)
        
        # Sync service products back to customer profile
        customer = self.object.customer
        for product in self.object.products.all():
            customer.products.add(product)
            
        images = self.request.FILES.getlist('images')
        for img in images:
            ServiceImage.objects.create(service=self.object, image=img)
        return response

class ServiceDeleteView(DeleteView):
    model = ServiceRecord
    success_url = reverse_lazy('services')

class ServicePrintView(DetailView):
    model = ServiceRecord
    template_name = 'services/service_print.html'
    context_object_name = 's'

class ServiceBulkPrintView(ServiceListView):
    template_name = 'services/service_bulk_print.html'
    context_object_name = 'services'
    pagination_class = None # Show all on print page

    SORT_OPTIONS = [
        ('created_desc', 'Tarih (Yeni -> Eski)'),
        ('created_asc', 'Tarih (Eski -> Yeni)'),
        ('customer', 'Müşteri Adına Göre'),
        ('product', 'Ürüne Göre'),
        ('team', 'Ekibe Göre'),
        ('personnel', 'Personele Göre'),
        ('status', 'Duruma Göre'),
        ('priority', 'Önceliğe Göre'),
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_key = self.request.GET.get('sort', 'created_desc')

        if sort_key == 'created_asc':
            return queryset.order_by('created_at')
        if sort_key == 'customer':
            return queryset.order_by('customer__name', '-created_at')
        if sort_key == 'product':
            return queryset.annotate(first_product_name=Min('products__name')).order_by('first_product_name', '-created_at')
        if sort_key == 'team':
            return queryset.order_by('service_personnel__team__name', 'service_personnel__name', '-created_at')
        if sort_key == 'personnel':
            return queryset.order_by('service_personnel__name', '-created_at')
        if sort_key == 'status':
            return queryset.order_by('status__name', '-created_at')
        if sort_key == 'priority':
            return queryset.order_by('priority__name', '-created_at')
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_options'] = self.SORT_OPTIONS
        context['current_sort'] = self.request.GET.get('sort', 'created_desc')
        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get('download') == 'csv':
            return self._download_csv()
        return super().get(request, *args, **kwargs)

    def _download_csv(self):
        queryset = self.get_queryset()
        ts = timezone.localtime().strftime('%Y%m%d-%H%M')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="servis-raporu-{ts}.csv"'
        response.write('\ufeff')

        writer = csv.writer(response, delimiter=';')

        header = [
            'ID',
            'Musteri',
            'Telefon',
            'Bolge',
            'Urunler',
            'Urun Renkleri',
            'Ariza Tipleri',
            'Ariza Tipi Renkleri',
            'Durum',
            'Durum Renk',
            'Oncelik',
            'Oncelik Renk',
            'Garanti Durumu',
            'Atanan Personel',
            'Notlar',
            'Olusturma Tarihi',
        ]
        writer.writerow(header)

        def safe_phone(phone_value):
            value = (phone_value or '-').replace('"', '""')
            if value == '-':
                return value
            return f'="{value}"'

        def service_type_color_for_row(service_obj, service_type_obj):
            first_product = None
            for product in service_obj.products.all():
                if first_product is None:
                    first_product = product
                if any(st.id == service_type_obj.id for st in product.service_types.all()):
                    return product.color_hex
            if first_product is not None:
                return first_product.color_hex
            linked = service_type_obj.products.order_by('name').first()
            return linked.color_hex if linked else service_type_obj.color_hex

        for s in queryset:
            products = list(s.products.all())
            service_types = list(s.service_types.all())
            assigned = '-'
            if s.assigned_to:
                assigned = s.assigned_to.get_full_name() or s.assigned_to.username
            writer.writerow([
                s.id,
                s.customer.name,
                safe_phone(s.customer.phone),
                s.customer.region or '-',
                ', '.join(p.name for p in products) or '-',
                ', '.join(f'{p.name}:{p.color_hex}' for p in products) or '-',
                ', '.join(st.name for st in service_types) or '-',
                ', '.join(f'{st.name}:{service_type_color_for_row(s, st)}' for st in service_types) or '-',
                s.status.name,
                s.status.color_hex,
                s.priority.name,
                s.priority.color_hex,
                s.get_warranty_status_display(),
                assigned,
                s.notes or '-',
                timezone.localtime(s.created_at).strftime('%d.%m.%Y %H:%M'),
            ])
        return response

def bulk_delete_services(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids')
        ServiceRecord.objects.filter(id__in=ids).delete()
    return redirect('services')


@require_POST
def bulk_manage_services(request):
    ids = [int(x) for x in request.POST.getlist('ids') if str(x).isdigit()]
    action = (request.POST.get('bulk_action') or '').strip()
    queryset = ServiceRecord.objects.filter(id__in=ids)

    if not ids:
        messages.error(request, "Toplu işlem için en az bir servis seçin.")
        return redirect('services')
    if not action:
        messages.error(request, "Toplu işlem türü seçin.")
        return redirect('services')

    if action == 'delete':
        count = queryset.count()
        queryset.delete()
        messages.success(request, f"{count} servis kaydı silindi.")
        return redirect('services')

    if action == 'set_status':
        status_id = request.POST.get('bulk_status_id')
        if not status_id or not str(status_id).isdigit():
            messages.error(request, "Geçerli bir durum seçin.")
            return redirect('services')
        status = get_object_or_404(StatusOption, pk=int(status_id))
        updated = 0
        for service in queryset:
            before_state = _capture_service_state(service)
            service.status = status
            service.save(update_fields=['status', 'updated_at'])
            service.refresh_from_db()
            after_state = _capture_service_state(service)
            changes = _diff_service_state(before_state, after_state)
            _create_service_history(
                service,
                ' | '.join(changes) if changes else f"Durum aynı kaldı: {status.name}",
                request.user,
            )
            updated += 1
        messages.success(request, f"{updated} servis kaydının durumu güncellendi.")
        return redirect('services')

    if action == 'set_priority':
        priority_id = request.POST.get('bulk_priority_id')
        if not priority_id or not str(priority_id).isdigit():
            messages.error(request, "Geçerli bir öncelik seçin.")
            return redirect('services')
        priority = get_object_or_404(PriorityOption, pk=int(priority_id))
        updated = 0
        for service in queryset:
            before_state = _capture_service_state(service)
            service.priority = priority
            service.save(update_fields=['priority', 'updated_at'])
            service.refresh_from_db()
            after_state = _capture_service_state(service)
            changes = _diff_service_state(before_state, after_state)
            _create_service_history(
                service,
                ' | '.join(changes) if changes else f"Öncelik aynı kaldı: {priority.name}",
                request.user,
            )
            updated += 1
        messages.success(request, f"{updated} servis kaydının önceliği güncellendi.")
        return redirect('services')

    if action == 'set_personnel':
        personnel_value = (request.POST.get('bulk_personnel_id') or '').strip()
        personnel = None
        label = "Boş"
        if personnel_value and personnel_value != 'clear':
            if not personnel_value.isdigit():
                messages.error(request, "Geçerli bir personel seçin.")
                return redirect('services')
            personnel = get_object_or_404(ServicePersonnel, pk=int(personnel_value))
            label = personnel.name
        updated = 0
        for service in queryset:
            before_state = _capture_service_state(service)
            service.service_personnel = personnel
            service.save(update_fields=['service_personnel', 'updated_at'])
            service.refresh_from_db()
            after_state = _capture_service_state(service)
            changes = _diff_service_state(before_state, after_state)
            _create_service_history(
                service,
                ' | '.join(changes) if changes else f"Servis personeli aynı kaldı: {label}",
                request.user,
            )
            updated += 1
        messages.success(request, f"{updated} servis kaydının personel ataması güncellendi.")
        return redirect('services')

    messages.error(request, "Geçersiz toplu işlem.")
    return redirect('services')


@require_POST
def quick_update_service_field(request):
    service_id = request.POST.get('service_id')
    field = request.POST.get('field')
    value = request.POST.get('value')

    if not service_id or not str(service_id).isdigit():
        return JsonResponse({'error': 'Geçersiz servis kaydı.'}, status=400)
    if field not in {'status', 'priority'}:
        return JsonResponse({'error': 'Geçersiz alan.'}, status=400)
    if not value or not str(value).isdigit():
        return JsonResponse({'error': 'Geçersiz değer.'}, status=400)

    service = get_object_or_404(ServiceRecord, pk=int(service_id))
    option_model = StatusOption if field == 'status' else PriorityOption
    option = get_object_or_404(option_model, pk=int(value))
    before_state = _capture_service_state(service)

    if field == 'status':
        service.status = option
    else:
        service.priority = option
    service.save(update_fields=[field, 'updated_at'])
    service.refresh_from_db()
    after_state = _capture_service_state(service)
    changes = _diff_service_state(before_state, after_state)

    _create_service_history(
        service,
        ' | '.join(changes) if changes else f"{field} aynı kaldı: {option.name}",
        request.user,
    )

    return JsonResponse({
        'ok': True,
        'field': field,
        'value': option.id,
        'label': option.name,
        'color': option.color_hex,
    })


@require_http_methods(["GET", "POST"])
def service_quick_edit_api(request, pk):
    service = get_object_or_404(
        ServiceRecord.objects.select_related('customer', 'status', 'priority').prefetch_related('products', 'service_types'),
        pk=pk,
    )

    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'service': {
                'id': service.id,
                'status_id': service.status_id,
                'priority_id': service.priority_id,
                'product_ids': list(service.products.values_list('id', flat=True)),
                'service_type_ids': list(service.service_types.values_list('id', flat=True)),
                'notes': service.notes or '',
            },
            'customer': {
                'id': service.customer_id,
                'name': service.customer.name,
                'phone': service.customer.phone or '',
                'region': service.customer.region or '',
                'location_link': service.customer.location_link or '',
                'contract_date': service.customer.contract_date.isoformat() if service.customer.contract_date else '',
            },
        })

    before_state = _capture_service_state(service)

    status_id = request.POST.get('status_id')
    priority_id = request.POST.get('priority_id')
    notes = request.POST.get('notes', '').strip()
    product_ids = [int(x) for x in request.POST.getlist('product_ids') if str(x).isdigit()]
    service_type_ids = [int(x) for x in request.POST.getlist('service_type_ids') if str(x).isdigit()]

    customer_phone = request.POST.get('customer_phone', '').strip()
    customer_region = request.POST.get('customer_region', '').strip()
    customer_location_link = request.POST.get('customer_location_link', '').strip()
    customer_contract_date = request.POST.get('customer_contract_date', '').strip()

    if not status_id or not str(status_id).isdigit():
        return JsonResponse({'ok': False, 'error': 'Durum seçimi zorunlu.'}, status=400)
    if not priority_id or not str(priority_id).isdigit():
        return JsonResponse({'ok': False, 'error': 'Öncelik seçimi zorunlu.'}, status=400)

    status = get_object_or_404(StatusOption, pk=int(status_id))
    priority = get_object_or_404(PriorityOption, pk=int(priority_id))

    service.status = status
    service.priority = priority
    service.notes = notes
    service.save(update_fields=['status', 'priority', 'notes', 'updated_at'])
    service.products.set(product_ids)
    service.service_types.set(service_type_ids)

    customer = service.customer
    customer.phone = customer_phone or None
    customer.region = customer_region or None
    customer.location_link = customer_location_link or None
    customer.contract_date = customer_contract_date or None
    customer.save(update_fields=['phone', 'region', 'location_link', 'contract_date', 'updated_at'])

    service.refresh_from_db()
    after_state = _capture_service_state(service)
    changes = _diff_service_state(before_state, after_state)

    _create_service_history(
        service,
        ' | '.join(changes) if changes else 'Hızlı düzenleme uygulandı (değişiklik yok).',
        request.user,
    )

    return JsonResponse({'ok': True})


def _restore_service_from_snapshot(service, snapshot):
    service_data = snapshot.get('service', {})
    customer_data = snapshot.get('customer', {})

    status_id = service_data.get('status_id')
    priority_id = service_data.get('priority_id')
    if status_id:
        service.status_id = status_id
    if priority_id:
        service.priority_id = priority_id

    service.solution_partner_id = service_data.get('solution_partner_id')
    service.assigned_to_id = service_data.get('assigned_to_id')
    service.service_personnel_id = service_data.get('service_personnel_id')
    service.warranty_status = service_data.get('warranty_status') or service.warranty_status
    service.notes = service_data.get('notes') or ''
    service.save()

    service.products.set(service_data.get('product_ids') or [])
    service.service_types.set(service_data.get('service_type_ids') or [])

    customer = service.customer
    customer.phone = customer_data.get('phone') or None
    customer.region = customer_data.get('region') or None
    customer.location_link = customer_data.get('location_link') or None
    customer.contract_date = customer_data.get('contract_date') or None
    customer.save(update_fields=['phone', 'region', 'location_link', 'contract_date', 'updated_at'])

@require_POST
def restore_service_history_entry(request, pk, history_id):
    service = get_object_or_404(ServiceRecord, pk=pk)
    history_entry = get_object_or_404(ServiceHistory, pk=history_id, service=service)
    snapshot = history_entry.snapshot or {}
    if not snapshot:
        messages.error(request, "Bu geçmiş kaydında geri yükleme snapshot verisi yok.")
        return redirect('service_update', pk=service.id)

    before_state = _capture_service_state(service)
    _restore_service_from_snapshot(service, snapshot)
    service.refresh_from_db()
    after_state = _capture_service_state(service)
    changes = _diff_service_state(before_state, after_state)

    restore_action = f"İşlem geçmişinden geri yüklendi ({history_entry.created_at.strftime('%d.%m.%Y %H:%M')})"
    if changes:
        restore_action = f"{restore_action} | {' | '.join(changes)}"

    _create_service_history(
        service,
        restore_action,
        request.user,
    )
    messages.success(request, "Servis kaydı işlem geçmişinden geri yüklendi.")
    return redirect('service_update', pk=service.id)


def send_services_whatsapp(request):
    team_id = request.GET.get('team')
    personnel_id = request.GET.get('personnel')
    qs = ServiceRecord.objects.select_related(
        'customer', 'status', 'priority', 'service_personnel', 'service_personnel__team'
    ).prefetch_related('products', 'service_types')

    if team_id and team_id.isdigit():
        qs = qs.filter(service_personnel__team_id=int(team_id))
    if personnel_id and personnel_id.isdigit():
        qs = qs.filter(service_personnel_id=int(personnel_id))

    target_phone = ''
    target_label = ''
    if personnel_id and personnel_id.isdigit():
        person = ServicePersonnel.objects.filter(pk=int(personnel_id), is_active=True).select_related('team').prefetch_related('product_groups').first()
        if person:
            target_phone = (person.company_phone or '').strip()
            target_label = person.name
            skill_product_ids = list(person.product_groups.values_list('id', flat=True))
            if not skill_product_ids:
                messages.error(request, "Bu personel için yetenekli ürün grubu tanımlı değil.")
                return redirect('services')
            qs = qs.filter(products__id__in=skill_product_ids)
    elif team_id and team_id.isdigit():
        team = ServiceTeam.objects.filter(pk=int(team_id), is_active=True).first()
        if team:
            target_phone = (team.company_phone or '').strip()
            target_label = team.name

    if not target_phone:
        messages.error(request, "WhatsApp için ekip/personel şirket numarası tanımlı değil.")
        return redirect('services')

    services = list(qs.distinct().order_by('-created_at')[:40])
    if not services:
        messages.error(request, "Seçilen ekip/personel ve yetenek ürün grupları için gönderilecek servis bulunamadı.")
        return redirect('services')

    message = _build_service_summary_message(target_label, services)
    clean_phone = _normalize_phone_for_wa(target_phone)

    return redirect(f"https://wa.me/{clean_phone}?text={quote(message)}")


def send_services_whatsapp_auto(request):
    base_qs = ServiceRecord.objects.select_related(
        'customer', 'status', 'priority', 'service_personnel', 'service_personnel__team'
    ).prefetch_related('products', 'service_types')
    services = list(_apply_service_filters(base_qs, request).order_by('-created_at')[:120])
    if not services:
        messages.error(request, "Dağıtılacak servis kaydı bulunamadı.")
        return redirect('services')

    personnel_candidates = list(
        ServicePersonnel.objects.filter(is_active=True)
        .select_related('team')
        .prefetch_related('product_groups', 'team__product_groups')
        .order_by('name')
    )
    team_candidates = list(
        ServiceTeam.objects.filter(is_active=True)
        .prefetch_related('product_groups')
        .order_by('name')
    )

    assignments = {}

    def add_assignment(kind, pk, label, phone, team_label, service):
        key = (kind, pk)
        if key not in assignments:
            assignments[key] = {
                'kind': kind,
                'label': label,
                'phone': phone,
                'team_label': team_label or 'Ekipsiz',
                'services': [],
            }
        assignments[key]['services'].append(service)

    for service in services:
        service_product_ids = set(service.products.values_list('id', flat=True))
        assigned = False

        if service.service_personnel and service.service_personnel.is_active and service.service_personnel.company_phone:
            person = service.service_personnel
            add_assignment(
                'personnel',
                person.id,
                person.name,
                person.company_phone,
                person.team.name if person.team else 'Ekipsiz',
                service,
            )
            assigned = True
        if assigned:
            continue

        for person in personnel_candidates:
            skill_ids = set(person.product_groups.values_list('id', flat=True))
            if not skill_ids and person.team_id:
                skill_ids = set(person.team.product_groups.values_list('id', flat=True)) if person.team else set()
            if not skill_ids or not person.company_phone:
                continue
            if service_product_ids & skill_ids:
                add_assignment(
                    'personnel',
                    person.id,
                    person.name,
                    person.company_phone,
                    person.team.name if person.team else 'Ekipsiz',
                    service,
                )
                assigned = True
                break
        if assigned:
            continue

        for team in team_candidates:
            team_skill_ids = set(team.product_groups.values_list('id', flat=True))
            if not team_skill_ids or not team.company_phone:
                continue
            if service_product_ids & team_skill_ids:
                add_assignment('team', team.id, team.name, team.company_phone, team.name, service)
                assigned = True
                break

    assignment_cards = []
    for _, payload in assignments.items():
        if not payload['services']:
            continue
        phone = _normalize_phone_for_wa(payload['phone'])
        if not phone:
            continue
        ordered_services = sorted(payload['services'], key=lambda s: s.created_at, reverse=True)
        message = _build_service_summary_message(payload['label'], ordered_services)
        assignment_cards.append({
            'recipient_type': payload['kind'],
            'recipient_label': payload['label'],
            'team_label': payload['team_label'],
            'count': len(ordered_services),
            'phone': phone,
            'message': message,
            'services': [
                {
                    'id': s.id,
                    'customer_name': s.customer.name,
                    'region': s.customer.region or '-',
                }
                for s in ordered_services
            ],
        })

    if not assignment_cards:
        messages.error(request, "Uygun ekip/personel ve ürün eşleşmesi bulunamadı.")
        return redirect('services')

    grouped = {}
    for card in assignment_cards:
        key = card['team_label']
        if key not in grouped:
            grouped[key] = {'team_label': key, 'total_count': 0, 'items': []}
        grouped[key]['total_count'] += card['count']
        grouped[key]['items'].append(card)

    team_groups = sorted(grouped.values(), key=lambda g: g['team_label'].lower())
    for group in team_groups:
        group['items'].sort(
            key=lambda item: (0 if item['recipient_type'] == 'team' else 1, item['recipient_label'].lower())
        )

    return render(
        request,
        'services/whatsapp_dispatch.html',
        {
            'team_groups': team_groups,
            'total_service_count': sum(group['total_count'] for group in team_groups),
            'total_receiver_count': sum(len(group['items']) for group in team_groups),
        },
    )
