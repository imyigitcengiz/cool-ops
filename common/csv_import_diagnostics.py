"""CSV içe aktarma — eşleştirme planı, kullanılmayan sütunlar ve satır günlüğü."""

from __future__ import annotations

from common.csv_import_registry import import_type_config, import_type_fields
from common.csv_mapping import (
    ImportField,
    auto_map_headers,
    encode_mapping_headers,
    mapping_headers,
    merge_row_columns,
    parse_mapping_payload,
)


def resolve_import_mapping(
    headers: list[str],
    fields: list[ImportField],
    import_type: str,
    user_mapping: dict | str | None = None,
    *,
    use_auto_mapping: bool = True,
) -> tuple[dict[str, str | None], dict[str, str], dict[str, str]]:
    """
    final_mapping: canonical_key → csv header (None = atla)
    mapping_sources: canonical_key → auto | manual | skip | empty | boosted
    auto_mapping: yalnızca başlık tahmini (boost öncesi)
    """
    auto = auto_map_headers(headers, fields)
    parsed = parse_mapping_payload(user_mapping) if user_mapping else {}
    final: dict[str, str | None] = {}
    sources: dict[str, str] = {}

    for field in fields:
        user_submitted = user_mapping is not None and field.key in parsed
        user_choice = parsed.get(field.key) if user_submitted else None

        if user_submitted:
            chosen_list = mapping_headers(user_choice)
            if not chosen_list and use_auto_mapping:
                chosen_list = mapping_headers(auto.get(field.key))
            chosen = encode_mapping_headers(chosen_list)
            final[field.key] = chosen
            if not chosen_list:
                sources[field.key] = 'skip'
            elif chosen_list == mapping_headers(auto.get(field.key)):
                sources[field.key] = 'auto'
            else:
                sources[field.key] = 'manual'
        elif use_auto_mapping:
            chosen_list = mapping_headers(auto.get(field.key))
            chosen = encode_mapping_headers(chosen_list)
            final[field.key] = chosen
            sources[field.key] = 'auto' if chosen else 'empty'
        else:
            final[field.key] = None
            sources[field.key] = 'empty'

    if user_mapping is None and use_auto_mapping:
        from common.csv_mapping import boost_import_mapping

        boosted = boost_import_mapping(import_type, headers, dict(final))
        for key, header in boosted.items():
            if header and not final.get(key):
                final[key] = header
                sources[key] = 'boosted'

    return final, sources, auto


def unmapped_csv_columns(headers: list[str], mapping: dict[str, str | None], *, extra_used: list[str] | None = None) -> list[str]:
    used: set[str] = set()
    for spec in mapping.values():
        used.update(mapping_headers(spec))
    if extra_used:
        used.update(extra_used)
    return [h for h in headers if h not in used]


def mapping_plan_rows(
    fields: list[ImportField],
    *,
    final_mapping: dict[str, str | None],
    mapping_sources: dict[str, str],
    auto_mapping: dict[str, str],
    sample_row: dict[str, str],
) -> list[dict]:
    rows = []
    for field in fields:
        selected_list = mapping_headers(final_mapping.get(field.key))
        selected = encode_mapping_headers(selected_list) or ''
        source = mapping_sources.get(field.key, 'empty')
        source_label = {
            'auto': 'Otomatik',
            'manual': 'Manuel',
            'skip': 'Atlandı',
            'empty': 'Eşleşmedi',
            'boosted': 'Otomatik (tahmin)',
        }.get(source, source)
        sample = (
            merge_row_columns(sample_row, selected_list, field_key=field.key)[:80]
            if selected_list
            else '—'
        )
        rows.append({
            'key': field.key,
            'label': field.label,
            'required': field.required,
            'selected_header': selected,
            'selected_headers': selected_list,
            'auto_header': auto_mapping.get(field.key, ''),
            'mapping_source': source,
            'mapping_source_label': source_label,
            'sample': sample,
        })
    return rows


def row_preview(row: dict, limit: int = 4) -> str:
    parts = []
    for key, val in row.items():
        if not (val or '').strip():
            continue
        text = str(val).strip().replace('\n', ' ')
        if len(text) > 40:
            text = text[:37] + '…'
        parts.append(f'{key}={text}')
        if len(parts) >= limit:
            break
    return '; '.join(parts) or '(boş satır)'


def empty_result_shell(import_type: str) -> dict:
    return {
        'import_type': import_type,
        'log': [],
        'skipped_rows': [],
        'warnings': [],
        'unmapped_columns': [],
        'mapping': {},
        'mapping_sources': {},
    }


def merge_import_result(base: dict, **extra) -> dict:
    out = {**base}
    for key in ('log', 'skipped_rows', 'warnings'):
        if key in extra:
            out[key] = list(out.get(key, [])) + list(extra[key])
    for key, val in extra.items():
        if key not in ('log', 'skipped_rows', 'warnings'):
            out[key] = val
    return out


def build_mapping_summary(
    import_type: str,
    headers: list[str],
    final_mapping: dict[str, str | None],
    mapping_sources: dict[str, str],
    *,
    extra_used_headers: list[str] | None = None,
    user=None,
) -> dict:
    field_labels = {f.key: f.label for f in import_type_fields(import_type, user)}
    mapped_fields = []
    skipped_fields = []
    for key, header in final_mapping.items():
        label = field_labels.get(key, key)
        cols = mapping_headers(header)
        if cols:
            col_text = ' + '.join(cols) if len(cols) > 1 else cols[0]
            mapped_fields.append(f'{label} → {col_text} ({mapping_sources.get(key, "?")})')
        else:
            skipped_fields.append(label)
    return {
        'mapped_fields': mapped_fields,
        'skipped_fields': skipped_fields,
        'unmapped_columns': unmapped_csv_columns(headers, final_mapping, extra_used=extra_used_headers),
    }


def store_import_report(request, report: dict) -> None:
    request.session['csv_import_last_report'] = report
    request.session.modified = True


def pop_import_report(request) -> dict | None:
    report = request.session.pop('csv_import_last_report', None)
    if report:
        request.session.modified = True
    return report


def peek_import_report(request) -> dict | None:
    return request.session.get('csv_import_last_report')
