import json
import re
import time
import urllib.parse

import requests

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
}
PLACE_ID_RE = re.compile(r'^ChIJ[\w-]+$')
PAGE_SIZE = 20


class GoogleMapsSearchError(Exception):
    pass


def _safe_get(obj, *path):
    cur = obj
    for part in path:
        if not isinstance(cur, list) or part >= len(cur):
            return None
        cur = cur[part]
    return cur


def _whatsapp_url(phone):
    from tools.phone_utils import whatsapp_url
    return whatsapp_url(phone)


def _resolve_search_urls(search_text):
    maps_url = 'https://www.google.com/maps/search/' + urllib.parse.quote(search_text)
    page = requests.get(maps_url, headers=HEADERS, timeout=30)
    page.raise_for_status()

    match = re.search(r'href="(/search\?tbm=map[^"]+)"', page.text)
    if not match:
        raise GoogleMapsSearchError('Google Maps arama bağlantısı alınamadı. Lütfen tekrar deneyin.')

    search_path = match.group(1).replace('&amp;', '&')
    search_url = 'https://www.google.com' + search_path
    pb_match = re.search(r'pb=([^&]+)', search_url)
    if not pb_match:
        raise GoogleMapsSearchError('Google Maps arama parametreleri alınamadı.')

    base_pb = urllib.parse.unquote(pb_match.group(1))
    return search_url, base_pb


def _fetch_payload_with_pb(search_text, base_pb, page_offset=0):
    pb = base_pb if page_offset == 0 else f'{base_pb}!8i{page_offset}'
    url = (
        'https://www.google.com/search?tbm=map&authuser=0&hl=tr&gl=tr&q='
        + urllib.parse.quote(search_text)
        + '&pb='
        + urllib.parse.quote(pb, safe='!')
    )
    response = requests.get(url, headers=HEADERS, timeout=45)
    response.raise_for_status()

    raw = response.text
    if raw.startswith(")]}'"):
        raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GoogleMapsSearchError('Google Maps yanıtı işlenemedi.') from exc


def _extract_reviews(block):
    for obj in _walk_lists(block):
        if len(obj) >= 4 and obj[0] is None and obj[1] is None and obj[2] is None and isinstance(obj[3], list):
            inner = obj[3]
            if (
                len(inner) >= 3
                and inner[0] is None
                and isinstance(inner[1], str)
                and re.match(r'^\d(\.\d)?$', inner[1])
                and str(inner[2]).isdigit()
            ):
                return str(inner[2])
    return '-'


def _walk_lists(obj):
    if isinstance(obj, list):
        yield obj
        for item in obj:
            yield from _walk_lists(item)


def _parse_listing_block(block):
    place_id = _safe_get(block, 78)
    name = _safe_get(block, 11)
    if not isinstance(place_id, str) or not PLACE_ID_RE.match(place_id):
        return None
    if not isinstance(name, str) or not name.strip():
        return None

    website = _safe_get(block, 7, 0)
    if not isinstance(website, str) or not website.startswith('http'):
        website = '-'

    phone = _safe_get(block, 178, 0, 0)
    if not isinstance(phone, str) or not phone.strip():
        phone = '-'
    else:
        phone = phone.strip()

    address = _safe_get(block, 18)
    if not isinstance(address, str) or not address.strip():
        address = '-'

    rating = _safe_get(block, 4, 7)
    if rating is None:
        rating = '-'

    lat = _safe_get(block, 9, 2)
    lng = _safe_get(block, 9, 3)

    return {
        'name': name.strip(),
        'address': address.strip(),
        'phone': phone,
        'whatsapp_url': _whatsapp_url(phone),
        'website': website.strip(),
        'rating': rating,
        'reviews': _extract_reviews(block),
        'maps_url': f'https://www.google.com/maps/place/?q=place_id:{place_id}',
        'lat': lat if lat is not None else '',
        'lng': lng if lng is not None else '',
        'place_id': place_id,
    }


def _collect_listing_blocks(payload):
    blocks = []

    def walk(obj):
        if isinstance(obj, list):
            if len(obj) == 260:
                serialized = json.dumps(obj, ensure_ascii=False)
                if 'ChIJ' in serialized and 7500 < len(serialized) < 10000:
                    blocks.append(obj)
            for item in obj:
                walk(item)

    walk(payload)
    return blocks


def _parse_payload(payload, seen):
    results = []
    for block in _collect_listing_blocks(payload):
        item = _parse_listing_block(block)
        if not item or item['place_id'] in seen:
            continue
        seen.add(item['place_id'])
        results.append(item)
    return results


def search_businesses(query, location='', max_results=20):
    search_text = f'{query} {location}'.strip() if location else query
    if not search_text:
        raise GoogleMapsSearchError('Arama ifadesi girin.')

    try:
        max_results = max(int(max_results or 20), 1)
    except (TypeError, ValueError):
        max_results = 20

    _, base_pb = _resolve_search_urls(search_text)
    seen = set()
    results = []

    page_offset = 0
    empty_pages = 0
    while len(results) < max_results:
        payload = _fetch_payload_with_pb(search_text, base_pb, page_offset)
        batch = _parse_payload(payload, seen)
        if not batch:
            empty_pages += 1
            if empty_pages >= 2 or page_offset > 0:
                break
        else:
            empty_pages = 0
            results.extend(batch)

        if len(results) >= max_results:
            break
        page_offset += PAGE_SIZE
        if page_offset > max_results + PAGE_SIZE * 5:
            break
        time.sleep(0.6)

    return results[:max_results]
