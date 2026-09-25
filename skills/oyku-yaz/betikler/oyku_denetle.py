#!/usr/bin/env python3
"""Kısa öykü kapıları: tasarım sözleşmesi ve teslim denetimi.

Kullanım::

    oyku_denetle.py tasarim oyku/son-vapur [--json]
    oyku_denetle.py teslim  oyku/son-vapur [--json]

``tasarim``: kurgu.md zorunlu başlıkları, hedef uzunluk, sahne-plani.md içinde
3–8 sahne ve her sahnede Amaç/Duygu/Olay/Kanca satırları.
``teslim``: tasarım + metin.md var, sahne sayısı plana eşit (``* * *`` ayraçları),
uzunluk sert bandın içinde, engelleyici bozulma ve yapay zekâ kalıbı yok, plandan
metne kopya yok.

Çıkış: 0 geçti, 1 kapı kaldı, 2 hatalı girdi.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_kalip_denetle  # noqa: E402
import bozulma_denetle  # noqa: E402
import metin_olcum  # noqa: E402
import plan_denetle  # noqa: E402

try:  # argparse iletilerini ve hata iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
    from turkce_argparse import hata_iletisi
except ImportError:  # pragma: no cover
    hata_iletisi = str

KURGU_BASLIKLARI = ("Hedef duygu", "Öncül", "Karakterler", "Dönüm noktası", "Anlatıcı ve zaman", "Hedef uzunluk")
SAHNE_ALANLARI = ("Amaç", "Duygu", "Olay", "Kanca")
SAHNE_BASLIGI = re.compile(r"^##\s+Sahne\s+(\d+)\s*[:.–-]?\s*(.*)$", re.M)
AYRAC = re.compile(r"^\s*(\*\s*\*\s*\*|⁂|-{3,}|\*{3,})\s*$", re.M)
EN_AZ_SAHNE, EN_COK_SAHNE = 3, 8


def kontrol(ad: str, tamam: bool, ayrinti: str, onarim: str = "") -> dict[str, Any]:
    return {"ad": ad, "tamam": tamam, "ayrinti": ayrinti, "onarim": "" if tamam else onarim}


def bolum_govdesi(metin: str, baslik: str) -> str | None:
    m = re.search(rf"^##\s+{re.escape(baslik)}\s*$(.*?)(?=^##\s|\Z)", metin, re.M | re.S | re.I)
    return m.group(1).strip() if m else None


def sahneler(plan_metni: str) -> list[tuple[int, str, str]]:
    eslesmeler = list(SAHNE_BASLIGI.finditer(plan_metni))
    sonuc = []
    for i, m in enumerate(eslesmeler):
        son = eslesmeler[i + 1].start() if i + 1 < len(eslesmeler) else len(plan_metni)
        sonuc.append((int(m.group(1)), m.group(2).strip(), plan_metni[m.end():son]))
    return sonuc


def hedef_uzunluk(kurgu: str) -> int | None:
    govde = bolum_govdesi(kurgu, "Hedef uzunluk")
    if not govde:
        return None
    m = re.search(r"\d{1,3}(?:\.\d{3})+|\d+", govde)
    if not m:
        return None
    try:
        return metin_olcum.hedef_coz(m.group(0))
    except metin_olcum.OlcumHatasi:
        return None


def tasarim_denetle(klasor: Path) -> list[dict[str, Any]]:
    sonuc: list[dict[str, Any]] = []
    kurgu_yolu, plan_yolu = klasor / "kurgu.md", klasor / "sahne-plani.md"
    if not kurgu_yolu.is_file():
        return [kontrol("kurgu-var", False, str(kurgu_yolu), "kurgu.md dosyasını oyku-tasarimi.md şablonuyla oluşturun.")]
    kurgu = kurgu_yolu.read_text(encoding="utf-8")
    for baslik in KURGU_BASLIKLARI:
        govde = bolum_govdesi(kurgu, baslik)
        sonuc.append(kontrol(f"kurgu:{baslik}", bool(govde), "var" if govde else "eksik ya da boş",
                             f"kurgu.md içine '## {baslik}' başlığını ve içeriğini ekleyin."))
    hedef = hedef_uzunluk(kurgu)
    sonuc.append(kontrol("hedef-uzunluk", hedef is not None, str(hedef) if hedef else "okunamadı",
                         "'## Hedef uzunluk' altına '3.000 kelime' gibi bir sayı yazın."))
    if not plan_yolu.is_file():
        sonuc.append(kontrol("sahne-plani-var", False, str(plan_yolu), "sahne-plani.md dosyasını oluşturun."))
        return sonuc
    liste = sahneler(plan_yolu.read_text(encoding="utf-8"))
    sonuc.append(kontrol("sahne-sayisi", EN_AZ_SAHNE <= len(liste) <= EN_COK_SAHNE, f"{len(liste)} sahne",
                         f"Kısa öykü {EN_AZ_SAHNE}–{EN_COK_SAHNE} sahne olmalı; '## Sahne N: başlık' biçimini kullanın."))
    numaralar = [n for n, _, _ in liste]
    sonuc.append(kontrol("sahne-sirasi", numaralar == list(range(1, len(liste) + 1)), ", ".join(map(str, numaralar)),
                         "Sahneleri 1'den başlayıp boşluksuz numaralayın."))
    for n, _, govde in liste:
        for alan in SAHNE_ALANLARI:
            m = re.search(rf"^\s*[-*]\s*\**{alan}\**\s*:\s*(\S.*)$", govde, re.M)
            if not m:
                sonuc.append(kontrol(f"sahne-{n}:{alan}", False, "eksik", f"Sahne {n} için '- {alan}: ...' satırını ekleyin."))
    return sonuc


def teslim_denetle(klasor: Path) -> list[dict[str, Any]]:
    sonuc = tasarim_denetle(klasor)
    metin_yolu = klasor / "metin.md"
    if not metin_yolu.is_file():
        sonuc.append(kontrol("metin-var", False, str(metin_yolu), "Öykü metnini metin.md olarak yazın."))
        return sonuc
    metin = metin_yolu.read_text(encoding="utf-8")
    plan_yolu, kurgu_yolu = klasor / "sahne-plani.md", klasor / "kurgu.md"
    if plan_yolu.is_file():
        beklenen = len(sahneler(plan_yolu.read_text(encoding="utf-8")))
        govde = metin_olcum.gorunur_govde(metin)
        gercek = len(AYRAC.findall(metin)) + 1 if govde.strip() else 0
        sonuc.append(kontrol("metin-sahne-sayisi", gercek == beklenen, f"metin {gercek}, plan {beklenen}",
                             "Sahneleri '* * *' satırıyla ayırın; sahne sayısı planla aynı olmalı (birleştirme/atlama yok)."))
        kopya = plan_denetle.kopya_denetle(plan_yolu, metin_yolu)
        sonuc.append(kontrol("plan-kopyasi", bool(kopya["tamam"]), f"{kopya['ortak_parca']} ortak 7'li parça",
                             str(kopya["onarim"])))
    hedef = hedef_uzunluk(kurgu_yolu.read_text(encoding="utf-8")) if kurgu_yolu.is_file() else None
    if hedef:
        d = metin_olcum.uzunluk_degerlendir(metin_olcum.kelime_say(metin), hedef)
        sonuc.append(kontrol("uzunluk", d["durum"] not in {"cok_kisa", "cok_uzun"},
                             f"{d['gercek']} kelime (hedef {hedef}, durum {d['durum']})",
                             "Uzunluk hedefin %60–150 aralığında olmalı; eksikse plandaki olayı derinleştirin, fazlaysa tekrarları çıkarın."))
    bozulma = [b for b in bozulma_denetle.denetle_metin(metin, str(metin_yolu)) if b.onem == "engelleyici"]
    sonuc.append(kontrol("bozulma", not bozulma, f"{len(bozulma)} engelleyici",
                         "; ".join(f"{b.satir}. satır {b.kural}" for b in bozulma[:5])))
    beyaz = ai_kalip_denetle.beyaz_liste_yukle(metin_yolu)
    kalip = [b for b in ai_kalip_denetle.denetle_metin(metin, str(metin_yolu), beyaz) if b.onem == "engelleyici"]
    sonuc.append(kontrol("yz-kaliplari", not kalip, f"{len(kalip)} engelleyici",
                         "; ".join(f"{b.satir}. satır “{b.alinti}” → {b.oneri}" for b in kalip[:5])))
    return sonuc


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("komut", choices=("tasarim", "teslim"))
    ayr.add_argument("klasor", type=Path)
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    if not arg.klasor.is_dir():
        print(f"Öykü klasörü bulunamadı: {arg.klasor}", file=sys.stderr)
        return 2
    try:
        sonuc = tasarim_denetle(arg.klasor) if arg.komut == "tasarim" else teslim_denetle(arg.klasor)
    except (OSError, UnicodeDecodeError) as hata:
        print(f"Dosya okunamadı: {hata_iletisi(hata)}", file=sys.stderr)
        return 2
    kalan = [k for k in sonuc if not k["tamam"]]
    if arg.json:
        print(json.dumps({"tamam": not kalan, "kontroller": sonuc}, ensure_ascii=False, indent=2))
    else:
        for k in sonuc:
            print(f"{'✓' if k['tamam'] else '✗'} {k['ad']}: {k['ayrinti']}" + (f"\n    → {k['onarim']}" if k["onarim"] else ""))
        print("Sonuç: GEÇTİ" if not kalan else f"Sonuç: {len(kalan)} kapı kaldı")
    return 0 if not kalan else 1


if __name__ == "__main__":
    sys.exit(main())
