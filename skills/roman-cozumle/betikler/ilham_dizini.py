#!/usr/bin/env python3
"""Kitaplar arası ilham kütüphanesi: çözümlenmiş kitapların mekanizma kartlarını dizinler.

Kullanım::

    ilham_dizini.py olustur --kutuphane cozumleme-kutuphanesi
    ilham_dizini.py sorgula --kutuphane cozumleme-kutuphanesi --etiket intikam --etiket aile [--sinir 6]
    ilham_dizini.py kapsam  --kutuphane cozumleme-kutuphanesi

Kart kaynağı: her kitabın ``olay-orgusu/duygu-mekanizmalari.md`` dosyasındaki
``## DM-001: Başlık`` bölümleri; bölüm içindeki ``Etiketler: a, b`` satırı etiketleri,
``Mekanizma:`` satırı özeti verir. Dizin ``_ilham-dizini.json`` dosyasına yazılır.
Kartlar soyut mekanizmadır: özgün eserin adlarını, olay zincirini ya da cümlelerini
yeni metne taşımayın.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KART = re.compile(r"^##\s+(?P<kimlik>DM-\d{3})\s*[:.\-–—]\s*(?P<baslik>.+)$", re.M)


def kucuk(metin: str) -> str:
    return metin.replace("I", "ı").replace("İ", "i").lower().strip()


def kartlari_oku(kitap: Path) -> list[dict[str, Any]]:
    yol = kitap / "olay-orgusu" / "duygu-mekanizmalari.md"
    if not yol.is_file():
        return []
    metin = yol.read_text(encoding="utf-8")
    eslesmeler = list(KART.finditer(metin))
    kartlar = []
    for i, m in enumerate(eslesmeler):
        govde = metin[m.end(): eslesmeler[i + 1].start() if i + 1 < len(eslesmeler) else len(metin)]
        etiket = re.search(r"^\s*[-*]?\s*Etiketler\s*:\s*(.+)$", govde, re.M)
        mekanizma = re.search(r"^\s*[-*]?\s*Mekanizma\s*:\s*(.+)$", govde, re.M)
        kartlar.append({
            "kitap": kitap.name, "kimlik": m.group("kimlik"), "baslik": m.group("baslik").strip(),
            "etiketler": sorted({kucuk(e) for e in etiket.group(1).split(",") if e.strip()}) if etiket else [],
            "mekanizma": mekanizma.group(1).strip() if mekanizma else "",
            "kaynak": f"{kitap.name}/olay-orgusu/duygu-mekanizmalari.md#{m.group('kimlik')}",
        })
    return kartlar


def olustur(kutuphane: Path) -> dict[str, Any]:
    kartlar = [k for kitap in sorted(p for p in kutuphane.iterdir() if p.is_dir() and not p.name.startswith("_"))
               for k in kartlari_oku(kitap)]
    veri = {"sema_surumu": 1, "kart_sayisi": len(kartlar), "kartlar": kartlar}
    (kutuphane / "_ilham-dizini.json").write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"tamam": True, "kart_sayisi": len(kartlar)}


def dizin_oku(kutuphane: Path) -> dict[str, Any]:
    yol = kutuphane / "_ilham-dizini.json"
    if not yol.is_file():
        olustur(kutuphane)
    return json.loads(yol.read_text(encoding="utf-8"))


def sorgula(kutuphane: Path, etiketler: list[str], sinir: int) -> list[dict[str, Any]]:
    istenen = {kucuk(e) for e in etiketler}
    puanli = []
    for k in dizin_oku(kutuphane)["kartlar"]:
        ortak = len(istenen & set(k["etiketler"]))
        if ortak or not istenen:
            puanli.append((ortak, k["kitap"], k["kimlik"], k))
    puanli.sort(key=lambda x: (-x[0], x[1], x[2]))
    # aynı kitaptan en çok iki kart: çeşitlilik
    sonuc, sayac = [], {}
    for _, kitap, _, k in puanli:
        if sayac.get(kitap, 0) >= 2:
            continue
        sayac[kitap] = sayac.get(kitap, 0) + 1
        sonuc.append(k)
        if len(sonuc) >= sinir:
            break
    return sonuc


def kapsam(kutuphane: Path) -> dict[str, Any]:
    veri = dizin_oku(kutuphane)
    etiket: dict[str, int] = {}
    for k in veri["kartlar"]:
        for e in k["etiketler"]:
            etiket[e] = etiket.get(e, 0) + 1
    return {"kart_sayisi": veri["kart_sayisi"], "kitap_sayisi": len({k["kitap"] for k in veri["kartlar"]}),
            "etiketler": dict(sorted(etiket.items(), key=lambda x: (-x[1], x[0])))}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    for ad in ("olustur", "sorgula", "kapsam"):
        p = alt.add_parser(ad)
        p.add_argument("--kutuphane", required=True, type=Path)
        if ad == "sorgula":
            p.add_argument("--etiket", action="append", default=[])
            p.add_argument("--sinir", type=int, default=6)
    arg = ayr.parse_args(argv)
    if not arg.kutuphane.is_dir():
        print(json.dumps({"hata": f"kütüphane klasörü yok: {arg.kutuphane}"}, ensure_ascii=False))
        return 2
    if arg.komut == "olustur":
        sonuc: Any = olustur(arg.kutuphane)
    elif arg.komut == "sorgula":
        sonuc = sorgula(arg.kutuphane, arg.etiket, arg.sinir)
    else:
        sonuc = kapsam(arg.kutuphane)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
