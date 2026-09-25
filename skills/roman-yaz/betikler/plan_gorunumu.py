#!/usr/bin/env python3
"""Cilt planı parça seçici — cilt planını baştan sona okumadan gereken parçayı verir.

Her ``##``/``###``/``####`` başlığının altındaki ilk dolu satır kapsamı bildirir::

    > Kapsam: cilt geneli
    > Kapsam: birim C1-03
    > Kapsam: taslak C1-03 | Durum: kullanımda
    > Kapsam: taslak C1-02 | Durum: emekli

``⊘`` ile başlayan liste/tablo satırları emekliye ayrılmıştır ve varsayılan
olarak gösterilmez. Kapsamı bildirilmemiş eski bölümler temkinli olarak dahil
edilir ve uyarı verilir.

Kullanım::

    plan_gorunumu.py --icindekiler cilt-plani_1.md
    plan_gorunumu.py --birim C1-03 cilt-plani_1.md
    plan_gorunumu.py --sozlesme cilt-plani_1.md   # yalnızca cilt geneli kurallar
    plan_gorunumu.py --denetle cilt-plani_1.md
    (her komuta --gecmis eklenirse emekli satırlar da gösterilir)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

BASLIK = re.compile(r"^(#{2,4})\s+(.*\S)\s*$")
KAPSAM = re.compile(r"^>\s*Kapsam\s*:\s*(.+?)\s*$", re.I)
EMEKLI_SATIR = re.compile(r"^\s*(?:[-*]\s*)?⊘|^\s*\|\s*⊘")
SIZINTI = re.compile(r"tüm cilt boyunca|cilt boyunca geçerli|bundan sonra hep|kitap sonuna kadar", re.I)
_H = "A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû"
KALICI_BUYRUK = re.compile(rf"(?<![{_H}])(?:asla|hiçbir zaman|bundan sonra|sonuna kadar)(?![{_H}])", re.I)


def ayristir(metin: str) -> list[dict[str, object]]:
    satirlar = metin.replace("\r\n", "\n").split("\n")
    parcalar: list[dict[str, object]] = []
    for i, satir in enumerate(satirlar):
        m = BASLIK.match(satir)
        if not m:
            if parcalar:
                parcalar[-1]["govde"].append(satir)  # type: ignore[union-attr]
            continue
        kapsam = None
        for sonraki in satirlar[i + 1:]:
            if sonraki.strip():
                k = KAPSAM.match(sonraki.strip())
                kapsam = k.group(1) if k else None
                break
        tur, birim, durum = "belirsiz", None, "kullanımda"
        if kapsam:
            parcalar_k = [p.strip() for p in kapsam.split("|")]
            ana = parcalar_k[0].lower()
            if ana.startswith("cilt geneli"):
                tur = "cilt"
            elif ana.startswith("birim"):
                tur, birim = "birim", parcalar_k[0].split()[-1]
            elif ana.startswith("taslak"):
                tur, birim = "taslak", parcalar_k[0].split()[-1]
            for p in parcalar_k[1:]:
                if p.lower().startswith("durum"):
                    durum = p.split(":", 1)[-1].strip().lower()
        parcalar.append({"duzey": len(m.group(1)), "baslik": m.group(2), "tur": tur, "birim": birim,
                         "durum": durum, "govde": [satir], "kapsam_var": kapsam is not None})
    return parcalar


def metni_ver(parca: dict[str, object], gecmis: bool) -> str:
    govde = parca["govde"]  # type: ignore[assignment]
    return "\n".join(s for s in govde if gecmis or not EMEKLI_SATIR.match(s))  # type: ignore[union-attr]


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("yol", type=Path)
    grup = ayr.add_mutually_exclusive_group(required=True)
    grup.add_argument("--icindekiler", action="store_true")
    grup.add_argument("--birim")
    grup.add_argument("--sozlesme", action="store_true")
    grup.add_argument("--denetle", action="store_true")
    ayr.add_argument("--gecmis", action="store_true")
    arg = ayr.parse_args(argv)
    if not arg.yol.is_file():
        print(f"dosya yok: {arg.yol}", file=sys.stderr)
        return 2
    parcalar = ayristir(arg.yol.read_text(encoding="utf-8"))
    if arg.icindekiler:
        for p in parcalar:
            etiket = p["tur"] + (f" {p['birim']}" if p["birim"] else "") + ("" if p["durum"] == "kullanımda" else f" ({p['durum']})")
            print(f"{'  ' * (int(p['duzey']) - 2)}- {p['baslik']}  [{etiket}]")  # type: ignore[operator]
        return 0
    if arg.denetle:
        sorun = 0
        for p in parcalar:
            govde = "\n".join(s for s in p["govde"] if not EMEKLI_SATIR.match(s))  # type: ignore[union-attr]
            if not p["kapsam_var"]:
                print(f"uyarı: '{p['baslik']}' kapsam bildirmiyor ('> Kapsam: ...' satırı ekleyin)")
            if p["tur"] == "birim" and SIZINTI.search(govde):
                sorun += 1
                print(f"HATA: '{p['baslik']}' birim bölümü cilt geneli kural içeriyor; kuralı cilt geneli bölüme taşıyın")
            if p["tur"] == "taslak" and p["durum"] == "kullanımda" and KALICI_BUYRUK.search(govde):
                sorun += 1
                print(f"HATA: '{p['baslik']}' taslakta kalıcı buyruk var; yazım sırasında taslak verilmez, kuralı birime ya da cilt geneline taşıyın")
        print("Cilt planı denetimi " + ("geçti." if not sorun else f"{sorun} sorun buldu."))
        return 0 if not sorun else 1
    secilen = []
    for p in parcalar:
        if p["durum"] == "emekli" and not arg.gecmis:
            continue
        if arg.sozlesme and p["tur"] in {"cilt", "belirsiz"}:
            secilen.append(p)
        elif arg.birim and (p["tur"] in {"cilt", "belirsiz"} or p["birim"] == arg.birim):
            secilen.append(p)
    uyarilar = [p["baslik"] for p in secilen if p["tur"] == "belirsiz"]
    print("\n\n".join(metni_ver(p, arg.gecmis) for p in secilen).strip())
    if uyarilar:
        print(f"\n<!-- uyarı: kapsamı bildirilmemiş {len(uyarilar)} bölüm temkinli olarak dahil edildi -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
