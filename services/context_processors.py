"""Yardım masası şablon bağlamı."""


def services_weather_banner(request):
    path = (getattr(request, 'path', '') or '')
    if not path.startswith('/services-dashboard'):
        return {}
    try:
        from core_settings.models import SiteSettings
        from common.module_runtime import is_module_installed

        if not is_module_installed('integration_weather'):
            return {}
        settings = SiteSettings.objects.first()
        if not settings:
            return {}
        from common.weather_service import saturday_forecast_for_site

        sat = saturday_forecast_for_site(settings)
        if not sat:
            return {}
        return {'services_saturday_weather': sat}
    except Exception:
        return {}
