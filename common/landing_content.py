"""Landing sayfası — KOBİ vitrin metinleri."""

from __future__ import annotations

LANDING_VERTICAL_COPY: dict[str, dict] = {
    'kobi': {
        'badge': 'KOBİ & saha servis',
        'headline': 'Müşteri, servis, satış ve saha ekibiniz tek panelde birleşsin.',
        'lead': (
            'Montaj ve teknik servis ekipleri ile B2B satış yapan işletmeler için '
            'yardım masası, müşteri rehberi, personel, bordro ve WhatsApp — aynı veri üzerinde.'
        ),
        'highlights': (
            ('headphones', 'Yardım Masası', 'Saha servis iş emirleri'),
            ('users-round', 'Saha Ekipleri', 'Montaj ve teknik kadro'),
            ('wallet', 'Maaş & Avans', 'Brüt − avans = net'),
            ('message-circle', 'WhatsApp', 'Ekip ve müşteri iletişimi'),
        ),
    },
}

DEFAULT_LANDING_VERTICAL = 'kobi'
