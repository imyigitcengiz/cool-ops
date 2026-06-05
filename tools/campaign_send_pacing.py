"""WhatsApp köprüsü ile toplu gönderim — insan benzeri bekleme aralıkları."""

from __future__ import annotations

import random


def compute_bridge_wait_seconds(
    *,
    base_seconds: float,
    sent_index: int,
    message_length: int = 0,
) -> float:
    """
    Sabit aralık yerine değişken tempo — otomasyon / spam algısını azaltır.

    sent_index: bu batch içinde başarıyla gönderilmiş mesaj sayısı (0 tabanlı).
    """
    base = max(float(base_seconds or 12), 10.0)
    typing = min(message_length / 45.0, 7.0) + random.uniform(1.0, 3.5)
    delay = random.uniform(base * 0.72, base * 1.38) + typing

    n = sent_index + 1
    if n >= 10 and n % 10 == 0:
        delay += random.uniform(40, 100)
    if n >= 32 and n % 32 == 0:
        delay += random.uniform(120, 240)
    if random.random() < 0.05:
        delay += random.uniform(15, 50)

    return round(max(8.0, min(delay, 600.0)), 1)
