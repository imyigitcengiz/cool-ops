from django.views.generic import TemplateView
from django.db.models import Count, Q
from services.models import ServiceRecord
from customers.models import Customer
from core_settings.models import SiteSettings, StatusOption, PriorityOption
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_services = ServiceRecord.objects.all()
        total_services = all_services.count()
        total_customers = Customer.objects.count()

        today = timezone.localdate()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        day_labels = [d.strftime('%a') for d in days]
        trend_counts = []
        for d in days:
            next_day = d + timedelta(days=1)
            trend_counts.append(
                all_services.filter(created_at__date__gte=d, created_at__date__lt=next_day).count()
            )

        top_statuses = (
            all_services.values('status__name')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )

        context['service_counts'] = {
            'open': all_services.filter(status__name__icontains='servis').count(),
            'pending': all_services.filter(status__name__icontains='beklemede').count(),
            'completed': all_services.filter(status__name__icontains='tamam').count(),
        }
        context['total_services'] = total_services
        context['total_customers'] = total_customers
        context['completion_rate'] = round(
            (context['service_counts']['completed'] / total_services * 100), 1
        ) if total_services else 0
        context['warranty_active_count'] = all_services.filter(warranty_status='active').count()
        context['recent_services'] = all_services.order_by('-created_at')[:5]
        product_stats = ServiceRecord.objects.values('products__name').annotate(total=Count('products')).exclude(products__name=None)
        context['product_distribution'] = {p['products__name']: p['total'] for p in product_stats}
        context['service_trend_labels'] = day_labels
        context['service_trend_data'] = trend_counts
        context['top_statuses'] = [s['status__name'] or 'Durum Yok' for s in top_statuses]
        context['top_status_counts'] = [s['total'] for s in top_statuses]
        context['statuses'] = StatusOption.objects.order_by('name')
        context['priorities'] = PriorityOption.objects.order_by('name')
        return context

class AIPanelView(TemplateView):
    template_name = 'analytics/ai_panel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = SiteSettings.objects.first()
        context['site_settings'] = settings
        context['stats'] = {
            'total_customers': Customer.objects.count(),
            'total_services': ServiceRecord.objects.count(),
            'product_count': ServiceRecord.objects.values('products').distinct().count(),
        }
        return context

@csrf_exempt
def ai_chat_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        settings = SiteSettings.objects.first()
        if not settings or not settings.ai_chat_enabled:
            return JsonResponse({'error': 'AI Chat is disabled'}, status=403)
            
        # Prepare context for AI
        total_customers = Customer.objects.count()
        total_services = ServiceRecord.objects.count()
        recent_services = ServiceRecord.objects.order_by('-created_at')[:5]
        service_summary = "\n".join([f"- {s.customer.name}: {s.status.name} ({s.priority.name})" for s in recent_services])
        
        system_context = f"""
        {settings.ai_system_prompt}
        
        Sistem Bilgileri:
        - Toplam Müşteri: {total_customers}
        - Toplam Servis Kaydı: {total_services}
        
        Son Servis Kayıtları:
        {service_summary}
        
        Kullanıcıya yardımcı ol, verileri analiz et ve istendiğinde tavsiyelerde bulun.
        """
        
        response_text = ""
        
        # Try Google AI (Gemini) first if key exists
        if settings.google_api_key:
            try:
                from google import genai

                client = genai.Client(api_key=settings.google_api_key)
                chat_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"{system_context}\n\nKullanıcı: {user_message}",
                )
                response_text = chat_response.text
            except Exception as e:
                print(f"Gemini Error: {e}")
                
        # If Gemini failed or no key, try OpenAI
        if not response_text and settings.openai_api_key:
            try:
                client = openai.OpenAI(api_key=settings.openai_api_key)
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_context},
                        {"role": "user", "content": user_message}
                    ]
                )
                response_text = completion.choices[0].message.content
            except Exception as e:
                print(f"OpenAI Error: {e}")
                
        if not response_text:
            return JsonResponse({'error': 'AI providers failed or keys missing'}, status=500)
            
        return JsonResponse({'message': response_text})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
