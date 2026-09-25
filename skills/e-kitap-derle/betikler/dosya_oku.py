"""Kullanıcı dosyalarını güvenle okur: Türkçe hata iletileri ve kodlama toleransı.

* ``metin_oku``: UTF-8 (BOM'lu ya da BOM'suz) okur. Dosya UTF-8 değilse ve ikili değilse
  Windows-1254 (Türkçe Windows'un eski varsayılanı, ör. Not Defteri "ANSI") olarak dener ve
  stderr'e bir uyarı yazar. Klasör, eksik dosya ve ikili dosya için ``DosyaHatasi`` verir.
* ``json_nesne_oku``: JSON dosyasını okur ve kökün nesne (sözlük) olduğunu doğrular.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def json_iletisi(hata: json.JSONDecodeError) -> str:
    try:
        from turkce_argparse import json_iletisi as cevir
    except ImportError:  # pragma: no cover
        return f"geçersiz JSON (satır {hata.lineno}, sütun {hata.colno})"
    return cevir(hata)


class DosyaHatasi(ValueError):
    """Kullanıcıya gösterilecek, Türkçe iletili dosya hatası."""


def _var_mi(yol: Path) -> None:
    if not yol.exists():
        raise DosyaHatasi(f"dosya bulunamadı: {yol}")
    if yol.is_dir():
        raise DosyaHatasi(f"dosya bekleniyordu, klasör verildi: {yol}")


def metin_oku(yol: Path | str, uyar: bool = True) -> str:
    yol = Path(yol)
    _var_mi(yol)
    ham = yol.read_bytes()
    if b"\x00" in ham[:8192]:
        raise DosyaHatasi(f"ikili (metin olmayan) dosya: {yol}. Word belgesini önce .txt ya da .md olarak kaydedin.")
    try:
        return ham.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    metin = ham.decode("cp1254", errors="strict") if _cp1254_mu(ham) else None
    if metin is None:
        raise DosyaHatasi(f"dosya UTF-8 değil ve Türkçe Windows kodlamasıyla da okunamadı: {yol}. Dosyayı UTF-8 olarak kaydedin.")
    if uyar:
        print(f"uyarı: {yol} UTF-8 değil; Windows-1254 (Türkçe) olarak okundu. Dosyayı UTF-8 olarak kaydetmeniz önerilir.",
              file=sys.stderr)
    return metin


def _cp1254_mu(ham: bytes) -> bool:
    try:
        metin = ham.decode("cp1254")
    except UnicodeDecodeError:
        return False
    # Denetim karakteri yoğunluğu yüksekse metin değildir.
    kontrol = sum(1 for c in metin if ord(c) < 32 and c not in "\r\n\t\f")
    return kontrol <= max(2, len(metin) // 200)


def json_nesne_oku(yol: Path | str, bos: dict[str, Any] | None = None) -> dict[str, Any]:
    """JSON nesnesi okur. ``bos`` verilmişse ve dosya yoksa onu döndürür."""
    yol = Path(yol)
    if bos is not None and not yol.exists():
        return dict(bos)
    metin = metin_oku(yol, uyar=False)
    try:
        veri = json.loads(metin)
    except json.JSONDecodeError as hata:
        raise DosyaHatasi(f"{yol}: {json_iletisi(hata)}") from hata
    if not isinstance(veri, dict):
        raise DosyaHatasi(f"{yol}: JSON kökü nesne ({{...}}) olmalı, {type(veri).__name__} bulundu")
    return veri
