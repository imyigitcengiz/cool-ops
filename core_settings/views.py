from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import (
    SiteSettings, ServiceTypeOption, ProductOption, StatusOption, PriorityOption,
    WhatsAppTemplate, SolutionPartner, SolutionPartnerType, ServiceTeam, ServicePersonnel
)
from .forms import (
    SiteSettingsForm, ServiceTypeOptionForm, ProductOptionForm, StatusOptionForm,
    PriorityOptionForm, WhatsAppTemplateForm, SolutionPartnerForm, SolutionPartnerTypeForm,
    ServiceTeamForm, ServicePersonnelForm, ProfileSettingsForm
)
from django.core import management
from django.http import HttpResponse, JsonResponse
from tempfile import NamedTemporaryFile
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
import os
import json
import gzip
import shutil
from io import StringIO
from datetime import datetime


def _update_color_option(request, model, label):
    obj = get_object_or_404(model, pk=request.POST.get('id'))
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, f"{label}: isim boş olamaz.")
        return
    obj.name = name
    obj.color = request.POST.get('color', obj.color)
    obj.save()
    messages.success(request, f"{label} güncellendi.")


class SiteSettingsView(TemplateView):
    template_name = 'settings/site_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = SiteSettings.objects.first()
        context['settings_form'] = SiteSettingsForm(instance=settings)
        context['service_type_form'] = ServiceTypeOptionForm()
        context['product_form'] = ProductOptionForm()
        context['status_form'] = StatusOptionForm()
        context['priority_form'] = PriorityOptionForm()
        context['whatsapp_form'] = WhatsAppTemplateForm()
        context['solution_partner_type_form'] = SolutionPartnerTypeForm()
        
        context['service_types'] = ServiceTypeOption.objects.prefetch_related('products').all().order_by('name')
        context['products'] = ProductOption.objects.prefetch_related('service_types').all().order_by('name')
        context['all_service_types'] = context['service_types']
        context['all_products'] = context['products']
        context['statuses'] = StatusOption.objects.all()
        context['priorities'] = PriorityOption.objects.all()
        context['whatsapp_templates'] = WhatsAppTemplate.objects.all()
        context['solution_partner_types'] = SolutionPartnerType.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        if 'update_site' in request.POST:
            settings = SiteSettings.objects.first()
            form = SiteSettingsForm(request.POST, request.FILES, instance=settings)
            try:
                if form.is_valid():
                    form.save()
                    messages.success(request, "Site ayarları güncellendi.")
                else:
                    # Show detailed form errors to help debugging
                    messages.error(request, f"Ayarlar güncellenirken hata oluştu: {form.errors.as_text()}")
            except Exception as e:
                messages.error(request, f"Ayarlar kaydedilirken beklenmeyen hata oluştu: {str(e)}")
                
        elif 'add_service_type' in request.POST:
            form = ServiceTypeOptionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Servis tipi eklendi.")
            else:
                messages.error(request, "Geçersiz servis tipi verisi.")
                
        elif 'add_product' in request.POST:
            form = ProductOptionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Ürün eklendi.")
            else:
                messages.error(request, "Geçersiz ürün verisi.")
                
        elif 'add_status' in request.POST:
            form = StatusOptionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Durum seçeneği eklendi.")
            else:
                messages.error(request, "Geçersiz durum verisi. İsim ve renk gerekli.")
                
        elif 'add_priority' in request.POST:
            form = PriorityOptionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Öncelik seçeneği eklendi.")
            else:
                messages.error(request, "Geçersiz öncelik verisi. İsim ve renk gerekli.")
                
        elif 'add_whatsapp' in request.POST:
            form = WhatsAppTemplateForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "WhatsApp şablonu eklendi.")
            else:
                messages.error(request, "Geçersiz şablon verisi.")
        elif 'add_solution_partner_type' in request.POST:
            form = SolutionPartnerTypeForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Çözüm ortağı türü eklendi.")
            else:
                messages.error(request, "Geçersiz tür verisi.")
        elif 'update_service_type' in request.POST:
            obj = get_object_or_404(ServiceTypeOption, pk=request.POST.get('id'))
            obj.products.set(request.POST.getlist('product_ids'))
            messages.success(request, "Servis tipi ürün ilişkileri güncellendi.")
        elif 'update_product' in request.POST:
            obj = get_object_or_404(ProductOption, pk=request.POST.get('id'))
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, "Ürün: isim boş olamaz.")
            else:
                obj.name = name
                obj.color = request.POST.get('color', obj.color)
                obj.save()
                obj.service_types.set(request.POST.getlist('service_type_ids'))
                messages.success(request, "Ürün güncellendi.")
        elif 'update_status' in request.POST:
            _update_color_option(request, StatusOption, 'Durum')
        elif 'update_priority' in request.POST:
            _update_color_option(request, PriorityOption, 'Öncelik')
        elif 'update_whatsapp' in request.POST:
            obj = get_object_or_404(WhatsAppTemplate, pk=request.POST.get('id'))
            title = request.POST.get('title', '').strip()
            message = request.POST.get('message', '').strip()
            if not title or not message:
                messages.error(request, "Şablon başlığı ve mesajı gerekli.")
            else:
                obj.title = title
                obj.message = message
                obj.save()
                messages.success(request, "WhatsApp şablonu güncellendi.")
        elif 'update_solution_partner_type' in request.POST:
            obj = get_object_or_404(SolutionPartnerType, pk=request.POST.get('id'))
            form = SolutionPartnerTypeForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, "Çözüm ortağı türü güncellendi.")
            else:
                messages.error(request, "Tür güncellenemedi.")
        elif 'delete_service_type' in request.POST:
            ServiceTypeOption.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Servis tipi silindi.")
        elif 'delete_product' in request.POST:
            ProductOption.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Ürün silindi.")
        elif 'delete_status' in request.POST:
            StatusOption.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Durum silindi.")
        elif 'delete_priority' in request.POST:
            PriorityOption.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Öncelik silindi.")
        elif 'delete_whatsapp' in request.POST:
            WhatsAppTemplate.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Şablon silindi.")
        elif 'delete_solution_partner_type' in request.POST:
            try:
                SolutionPartnerType.objects.filter(id=request.POST.get('id')).delete()
                messages.info(request, "Çözüm ortağı türü silindi.")
            except Exception:
                messages.error(request, "Bu tür kullanımda olduğu için silinemedi.")
        elif 'export_backup' in request.POST:
            try:
                sio = StringIO()
                management.call_command(
                    'dumpdata',
                    stdout=sio,
                    indent=2,
                    natural_foreign=True,
                    natural_primary=True,
                )
                sio.seek(0)
                raw_json = sio.read().encode('utf-8')

                ts = datetime.now().strftime('%Y%m%d-%H%M%S')
                file_name = f"gy-dashboard-backup-{ts}.json.gz"

                gz_buffer = gzip.compress(raw_json)
                response = HttpResponse(gz_buffer, content_type='application/gzip')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
            except Exception as e:
                messages.error(request, f"Yedekleme sırasında hata oluştu: {str(e)}")

        elif 'import_backup' in request.POST:
            uploaded = request.FILES.get('backup_file')
            if not uploaded:
                messages.error(request, "Lütfen bir dosya seçin.")
            else:
                tmp_input = None
                tmp_json = None
                try:
                    filename = (uploaded.name or '').lower()
                    if not (filename.endswith('.json') or filename.endswith('.json.gz')):
                        messages.error(request, "Sadece .json veya .json.gz dosyaları içe aktarılabilir.")
                        return redirect('site_settings')

                    tmp_suffix = '.json.gz' if filename.endswith('.json.gz') else '.json'
                    tmp_input = NamedTemporaryFile(delete=False, suffix=tmp_suffix)
                    for chunk in uploaded.chunks():
                        tmp_input.write(chunk)
                    tmp_input.flush()
                    tmp_input.close()

                    if tmp_suffix == '.json.gz':
                        tmp_json = NamedTemporaryFile(delete=False, suffix='.json')
                        with gzip.open(tmp_input.name, 'rb') as gz_file, open(tmp_json.name, 'wb') as out_file:
                            shutil.copyfileobj(gz_file, out_file)
                        fixture_path = tmp_json.name
                    else:
                        fixture_path = tmp_input.name

                    with transaction.atomic():
                        management.call_command('loaddata', fixture_path)
                    messages.success(request, "Yedek dosyası başarıyla içe aktarıldı.")
                except Exception as e:
                    messages.error(request, f"İçe aktarma sırasında hata oluştu: {str(e)}")
                finally:
                    if tmp_input and os.path.exists(tmp_input.name):
                        os.unlink(tmp_input.name)
                    if tmp_json and os.path.exists(tmp_json.name):
                        os.unlink(tmp_json.name)
            
        return redirect('site_settings')


class ProfileSettingsView(TemplateView):
    template_name = 'settings/profile_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = SiteSettings.objects.first()
        context['profile_form'] = ProfileSettingsForm(instance=settings)
        return context

    def post(self, request, *args, **kwargs):
        settings = SiteSettings.objects.first()
        form = ProfileSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil ayarları güncellendi.")
        else:
            messages.error(request, "Profil ayarları güncellenemedi.")
        return redirect('profile_settings')


class SolutionNetworkView(TemplateView):
    template_name = 'settings/solution_network.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        t = self.request.GET.get('type', '').strip()
        active = self.request.GET.get('active', '').strip()

        partners = SolutionPartner.objects.all().order_by('name')
        if q:
            partners = partners.filter(
                Q(name__icontains=q) | Q(phone__icontains=q) | Q(notes__icontains=q)
            )
        if t and t.isdigit():
            partners = partners.filter(partner_type_id=int(t))
        if active == '1':
            partners = partners.filter(is_active=True)
        elif active == '0':
            partners = partners.filter(is_active=False)

        context['solution_partner_form'] = SolutionPartnerForm()
        context['solution_partners'] = partners
        context['partner_types'] = SolutionPartnerType.objects.order_by('name')
        context['active_count'] = SolutionPartner.objects.filter(is_active=True).count()
        context['total_count'] = SolutionPartner.objects.count()
        return context

    def post(self, request, *args, **kwargs):
        if 'add_solution_partner' in request.POST:
            form = SolutionPartnerForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Çözüm ortağı eklendi.")
            else:
                messages.error(request, "Geçersiz çözüm ortağı verisi.")
        elif 'update_solution_partner' in request.POST:
            obj = get_object_or_404(SolutionPartner, pk=request.POST.get('id'))
            form = SolutionPartnerForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, "Çözüm ortağı güncellendi.")
            else:
                messages.error(request, "Çözüm ortağı güncellenemedi.")
        elif 'delete_solution_partner' in request.POST:
            SolutionPartner.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Çözüm ortağı silindi.")
        return redirect('solution_network')


class PersonnelNetworkView(TemplateView):
    template_name = 'settings/personnel_network.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        team = self.request.GET.get('team', '').strip()

        personnel = ServicePersonnel.objects.select_related('team').prefetch_related('product_groups').all().order_by('name')
        if q:
            personnel = personnel.filter(Q(name__icontains=q) | Q(company_phone__icontains=q) | Q(notes__icontains=q))
        if team and team.isdigit():
            personnel = personnel.filter(team_id=int(team))

        context['team_form'] = ServiceTeamForm()
        context['personnel_form'] = ServicePersonnelForm()
        context['teams'] = ServiceTeam.objects.prefetch_related('product_groups').all().order_by('name')
        context['personnel_list'] = personnel
        return context

    def post(self, request, *args, **kwargs):
        if 'add_team' in request.POST:
            form = ServiceTeamForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Ekip eklendi.")
            else:
                messages.error(request, "Ekip kaydı eklenemedi.")
        elif 'update_team' in request.POST:
            obj = get_object_or_404(ServiceTeam, pk=request.POST.get('id'))
            form = ServiceTeamForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, "Ekip güncellendi.")
            else:
                messages.error(request, "Ekip güncellenemedi.")
        elif 'delete_team' in request.POST:
            try:
                ServiceTeam.objects.filter(id=request.POST.get('id')).delete()
                messages.info(request, "Ekip silindi.")
            except Exception:
                messages.error(request, "Ekip silinemedi.")
        elif 'add_personnel' in request.POST:
            form = ServicePersonnelForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Personel eklendi.")
            else:
                messages.error(request, "Personel kaydı eklenemedi.")
        elif 'update_personnel' in request.POST:
            obj = get_object_or_404(ServicePersonnel, pk=request.POST.get('id'))
            form = ServicePersonnelForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, "Personel güncellendi.")
            else:
                messages.error(request, "Personel güncellenemedi.")
        elif 'delete_personnel' in request.POST:
            ServicePersonnel.objects.filter(id=request.POST.get('id')).delete()
            messages.info(request, "Personel silindi.")
        return redirect('personnel_network')


@csrf_exempt
def settings_api(request):
    """Simple JSON API for reading/updating SiteSettings.

    GET: returns current settings (public read)
    POST: updates settings (staff only) with JSON body
    """
    try:
        settings = SiteSettings.objects.first()
        if request.method == 'GET':
            return JsonResponse({
                'site_name': settings.site_name if settings else '',
                'company_phone': settings.company_phone if settings else '',
                'company_address': settings.company_address if settings else '',
                'ai_chat_enabled': settings.ai_chat_enabled if settings else False,
                'ai_system_prompt': settings.ai_system_prompt if settings else '',
            })

        if request.method == 'POST':
            # Only allow staff users to change settings
            if not request.user.is_authenticated or not request.user.is_staff:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            data = json.loads(request.body.decode('utf-8')) if request.body else {}
            form = SiteSettingsForm(data, files=None, instance=settings)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'validation_error', 'details': form.errors}, status=400)

        return JsonResponse({'error': 'Method not allowed'}, status=405)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _serialize_option(obj):
    return {'id': obj.id, 'name': obj.name, 'color': obj.color_hex}


def options_catalog_api(request):
    """Servis formu için tüm seçenekler ve ürün–servis tipi eşlemesi."""
    products = ProductOption.objects.prefetch_related('service_types').order_by('name')
    service_types = ServiceTypeOption.objects.prefetch_related('products').order_by('name')

    def service_type_color(st):
        first_product = next(iter(st.products.all()), None)
        return first_product.color_hex if first_product else st.color_hex

    return JsonResponse({
        'products': [
            {
                **_serialize_option(p),
                'service_type_ids': list(p.service_types.values_list('id', flat=True)),
            }
            for p in products
        ],
        'service_types': [
            {'id': s.id, 'name': s.name, 'color': service_type_color(s)}
            for s in service_types
        ],
        'statuses': [_serialize_option(s) for s in StatusOption.objects.order_by('name')],
        'priorities': [_serialize_option(p) for p in PriorityOption.objects.order_by('name')],
    })


def service_types_for_products_api(request):
    """Seçili ürünlere göre servis tiplerini döndürür."""
    raw = request.GET.get('product_ids', '')
    product_ids = [int(x) for x in raw.split(',') if x.strip().isdigit()]
    all_types = list(ServiceTypeOption.objects.order_by('name'))

    if not product_ids:
        return JsonResponse({
            'service_types': [_serialize_option(s) for s in all_types],
            'filter_mode': 'none',
            'message': 'Ürün seçilmedi; tüm servis tipleri listeleniyor.',
        })

    products = ProductOption.objects.filter(id__in=product_ids).prefetch_related('service_types')
    allowed_ids = set()
    any_mapping = False
    for product in products:
        ids = list(product.service_types.values_list('id', flat=True))
        if ids:
            any_mapping = True
            allowed_ids.update(ids)

    if not any_mapping:
        filtered = all_types
        message = 'Seçili ürünlerde tanımlı arıza tipi yok; tüm tipler gösteriliyor.'
        mode = 'all_fallback'
    else:
        filtered = [s for s in all_types if s.id in allowed_ids]
        message = f'{len(filtered)} servis tipi bu ürün(ler) için tanımlı.'
        mode = 'filtered'

    return JsonResponse({
        'service_types': [_serialize_option(s) for s in filtered],
        'filter_mode': mode,
        'message': message,
    })


def quick_option_create_api(request):
    """Servis formundan hızlı seçenek ekleme."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Geçersiz JSON'}, status=400)

    kind = data.get('type')
    name = (data.get('name') or '').strip()
    color = data.get('color') or '#3b82f6'

    if not name:
        return JsonResponse({'error': 'İsim gerekli'}, status=400)

    model_map = {
        'status': StatusOption,
        'priority': PriorityOption,
        'product': ProductOption,
        'service_type': ServiceTypeOption,
    }
    model = model_map.get(kind)
    if not model:
        return JsonResponse({'error': 'Geçersiz tip'}, status=400)

    obj = model.objects.create(name=name, color=color)
    payload = _serialize_option(obj)
    if kind == 'product':
        st_ids = data.get('service_type_ids') or []
        if st_ids:
            obj.service_types.set(st_ids)
        payload['service_type_ids'] = list(obj.service_types.values_list('id', flat=True))

    return JsonResponse({'ok': True, 'item': payload, 'type': kind})


def quick_option_update_api(request):
    """Servis formundan hızlı seçenek güncelleme."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Geçersiz JSON'}, status=400)

    kind = data.get('type')
    pk = data.get('id')
    name = (data.get('name') or '').strip()
    if not pk or not name:
        return JsonResponse({'error': 'id ve name gerekli'}, status=400)

    model_map = {
        'status': StatusOption,
        'priority': PriorityOption,
        'product': ProductOption,
        'service_type': ServiceTypeOption,
    }
    model = model_map.get(kind)
    if not model:
        return JsonResponse({'error': 'Geçersiz tip'}, status=400)

    obj = get_object_or_404(model, pk=pk)
    obj.name = name
    if 'color' in data:
        obj.color = data['color']
    obj.save()

    if kind == 'product' and 'service_type_ids' in data:
        obj.service_types.set(data['service_type_ids'] or [])

    payload = _serialize_option(obj)
    if kind == 'product':
        payload['service_type_ids'] = list(obj.service_types.values_list('id', flat=True))

    return JsonResponse({'ok': True, 'item': payload})
