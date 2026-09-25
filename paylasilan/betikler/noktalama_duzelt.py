#!/usr/bin/env python3
"""Türkçe noktalama ve dizgi (tipografi) düzeltmeleri — TDK Yazım Kılavuzu esaslı.

Yalnızca anlamı değiştirmeyen, mekanik düzeltmeleri yapar:
  * satır başındaki "-" / "–" konuşma işaretini konuşma çizgisine (—) çevirir,
  * noktalama işaretinden önceki boşluğu siler, virgül ve noktadan sonra boşluk ekler,
  * iki ya da dörtten fazla noktayı üç noktaya (...) indirir,
  * harf arasındaki ’ işaretini kesme işaretine (') çevirir,
  * birden fazla boşluğu teke, üçten fazla boş satırı ikiye indirir,
  * isteğe bağlı olarak düz çift tırnağı Türkçe dizgi tırnağına (“ ”) çevirir.

Kullanım: ``noktalama_duzelt.py dosya.md`` (değişiklikleri raporlar),
``--yaz`` ile dosyayı yerinde düzeltir.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

HARF = "A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû"

KURALLAR: list[tuple[str, re.Pattern[str], str]] = [
    ("konusma-cizgisi", re.compile(r"^(\s*)(?:-|–)\s*(?=\S)", re.M), r"\1— "),
    ("cizgiden-sonra-bosluk", re.compile(r"^(\s*)—(?=\S)", re.M), r"\1— "),
    ("isaret-oncesi-bosluk", re.compile(rf"(?<=[^\s—–-])[ \t]+([,;:!?…]|\.(?!\.))(?=\s|$|[{HARF}])"), r"\1"),
    ("virgulden-sonra-bosluk", re.compile(rf"(?<=[{HARF}]),(?=[{HARF}])"), ", "),
    ("noktadan-sonra-bosluk", re.compile(rf"(?<=[a-zçğıöşü]{{2}})\.(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])"), ". "),
    ("uc-nokta", re.compile(r"(?<!\.)\.{2}(?!\.)|\.{4,}"), "..."),
    ("kesme-isareti", re.compile(rf"(?<=[{HARF}])’(?=[{HARF}])"), "'"),
    ("coklu-bosluk", re.compile(r"(?<=\S)[ \t]{2,}(?=\S)"), " "),
    ("fazla-bos-satir", re.compile(r"\n{3,}"), "\n\n"),
    ("tirnak-ici-bosluk", re.compile(r"“\s+|\s+”"), lambda m: m.group(0).strip()),  # type: ignore[list-item]
]


def tipografik_tirnak(metin: str) -> str:
    """Düz çift tırnakları açılış/kapanış dizgi tırnağına çevirir (satır satır, eşli ise)."""
    sonuc = []
    for satir in metin.split("\n"):
        if satir.count('"') % 2 == 0:
            acik = True
            parcalar = []
            for karakter in satir:
                if karakter == '"':
                    parcalar.append("“" if acik else "”")
                    acik = not acik
                else:
                    parcalar.append(karakter)
            satir = "".join(parcalar)
        sonuc.append(satir)
    return "\n".join(sonuc)


def duzelt(metin: str, *, tirnak: bool = False, diyalog_tiresi: bool = True) -> tuple[str, list[dict[str, object]]]:
    degisiklikler: list[dict[str, object]] = []
    on_bilgi = ""
    if metin.startswith("---\n"):
        son = metin.find("\n---\n", 4)
        if son > 0:
            on_bilgi, metin = metin[: son + 5], metin[son + 5:]
    kod_bloklari: list[str] = []

    def kodu_sakla(m: re.Match[str]) -> str:
        kod_bloklari.append(m.group(0))
        return f"\x00KOD{len(kod_bloklari) - 1}\x00"

    metin = re.sub(r"```.*?```", kodu_sakla, metin, flags=re.S)
    for ad, desen, yerine in KURALLAR:
        if ad.startswith(("konusma", "cizgiden")) and not diyalog_tiresi:
            continue
        # Başlık ve tablo satırlarına dokunma.
        satirlar = metin.split("\n")
        yeni_satirlar = []
        for no, satir in enumerate(satirlar, 1):
            if ad == "fazla-bos-satir" or satir.lstrip().startswith(("#", "|", ">", "* ", "- [")) and ad != "coklu-bosluk":
                yeni_satirlar.append(satir)
                continue
            yeni, adet = desen.subn(yerine, satir)  # type: ignore[arg-type]
            if adet:
                degisiklikler.append({"kural": ad, "satir": no, "adet": adet})
            yeni_satirlar.append(yeni)
        metin = "\n".join(yeni_satirlar)
        if ad == "fazla-bos-satir":
            metin, adet = desen.subn(yerine, metin)  # type: ignore[arg-type]
            if adet:
                degisiklikler.append({"kural": ad, "satir": 0, "adet": adet})
    if tirnak:
        yeni = tipografik_tirnak(metin)
        if yeni != metin:
            degisiklikler.append({"kural": "tipografik-tirnak", "satir": 0, "adet": yeni.count("“") - metin.count("“")})
            metin = yeni
    metin = re.sub(r"\x00KOD(\d+)\x00", lambda m: kod_bloklari[int(m.group(1))], metin)
    return on_bilgi + metin, degisiklikler


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("dosyalar", nargs="+", type=Path)
    ayr.add_argument("--yaz", action="store_true", help="dosyayı yerinde düzelt")
    ayr.add_argument("--tipografik-tirnak", action="store_true", help='düz "..." tırnaklarını “...” yap')
    ayr.add_argument("--diyalog-tiresi-yok", action="store_true", help="satır başı konuşma çizgisine dokunma")
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    toplam = 0
    rapor = {}
    for yol in arg.dosyalar:
        eski = yol.read_text(encoding="utf-8")
        yeni, degisiklikler = duzelt(eski, tirnak=arg.tipografik_tirnak, diyalog_tiresi=not arg.diyalog_tiresi_yok)
        toplam += sum(int(d["adet"]) for d in degisiklikler)
        rapor[str(yol)] = degisiklikler
        if arg.yaz and yeni != eski:
            yol.write_text(yeni, encoding="utf-8")
    if arg.json:
        print(json.dumps({"toplam": toplam, "dosyalar": rapor}, ensure_ascii=False, indent=2))
    else:
        for dosya, degisiklikler in rapor.items():
            for d in degisiklikler:
                print(f"{dosya}:{d['satir']}\t{d['kural']} ×{d['adet']}")
        eylem = "düzeltildi" if arg.yaz else "düzeltilebilir (--yaz ile uygulayın)"
        print(f"Toplam {toplam} noktalama sorunu {eylem}.")
    return 0 if (arg.yaz or toplam == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
