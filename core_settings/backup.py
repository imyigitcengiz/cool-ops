import gzip
import os
import shutil
from datetime import datetime
from io import StringIO
from tempfile import NamedTemporaryFile

from django.core import management
from django.db import transaction
from django.http import HttpResponse


def export_backup_response() -> HttpResponse:
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
    file_name = f'gy-dashboard-backup-{ts}.json.gz'
    response = HttpResponse(gzip.compress(raw_json), content_type='application/gzip')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


def import_backup_file(uploaded) -> tuple[bool, str]:
    if not uploaded:
        return False, 'Lütfen bir dosya seçin.'

    filename = (uploaded.name or '').lower()
    if not (filename.endswith('.json') or filename.endswith('.json.gz')):
        return False, 'Sadece .json veya .json.gz dosyaları içe aktarılabilir.'

    tmp_input = None
    tmp_json = None
    try:
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
        return True, 'Yedek dosyası başarıyla içe aktarıldı.'
    except Exception as exc:
        return False, f'İçe aktarma sırasında hata oluştu: {exc}'
    finally:
        if tmp_input and os.path.exists(tmp_input.name):
            os.unlink(tmp_input.name)
        if tmp_json and os.path.exists(tmp_json.name):
            os.unlink(tmp_json.name)
