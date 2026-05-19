"""Hex renk normalleştirme ve Tailwind adından geçiş."""

TAILWIND_TO_HEX = {
    'slate': '#64748b',
    'gray': '#6b7280',
    'zinc': '#71717a',
    'red': '#ef4444',
    'rose': '#f43f5e',
    'orange': '#f97316',
    'amber': '#f59e0b',
    'yellow': '#eab308',
    'lime': '#84cc16',
    'green': '#22c55e',
    'emerald': '#10b981',
    'teal': '#14b8a6',
    'cyan': '#06b6d4',
    'sky': '#0ea5e9',
    'blue': '#3b82f6',
    'indigo': '#6366f1',
    'violet': '#8b5cf6',
    'purple': '#a855f7',
    'fuchsia': '#d946ef',
    'pink': '#ec4899',
    'brand': '#0284c7',
}

DEFAULT_HEX = {
    'status': '#3b82f6',
    'priority': '#6b7280',
    'product': '#0284c7',
    'service_type': '#8b5cf6',
}


def normalize_hex(value, fallback='#3b82f6'):
    if not value:
        return fallback
    value = str(value).strip().lower()
    if value in TAILWIND_TO_HEX:
        return TAILWIND_TO_HEX[value]
    if value.startswith('#'):
        hex_body = value[1:]
        if len(hex_body) == 3:
            hex_body = ''.join(c * 2 for c in hex_body)
        if len(hex_body) == 6 and all(c in '0123456789abcdef' for c in hex_body):
            return f'#{hex_body}'
    return fallback


def hex_to_rgb(hex_color):
    hex_color = normalize_hex(hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def hex_to_rgba(hex_color, alpha=1.0):
    r, g, b = hex_to_rgb(hex_color)
    return f'rgba({r}, {g}, {b}, {alpha})'


def badge_styles(hex_color):
    color = normalize_hex(hex_color)
    return {
        'background': hex_to_rgba(color, 0.12),
        'color': color,
        'border': hex_to_rgba(color, 0.25),
    }


def dot_style(hex_color):
    color = normalize_hex(hex_color)
    return f'background-color: {color};'
