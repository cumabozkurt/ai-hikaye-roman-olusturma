#!/usr/bin/env python3
"""Sesli kitap hazırlığı: seslendirme metni, süre tahmini, telaffuz sözlüğü adayları.

Kullanım::

    sesli_kitap_hazirla.py --proje KITAP [--hiz 150] [--cikti KITAP/sesli-kitap] [--json]
    sesli_kitap_hazirla.py --dosya oyku/son-vapur/metin.md [...]

Üretilenler:
  * ``seslendirme/bolum-NNN.txt`` Markdown işaretleri temizlenmiş, konuşma çizgileri korunmuş,
    sahne ayraçları ``[DURAKSAMA]`` olarak işaretlenmiş düz metin (TTS ve seslendirmen için)
  * ``sure.md``  bölüm başına tahmini süre (Türkçe anlatımda dakikada ≈140–160 kelime)
  * ``telaffuz.md``  özel adlar, yabancı sözcükler, kısaltmalar ve sayılar için aday liste
Var olan dosyaların üzerine yazılmaz; ``--yeniden`` ile yalnızca bu betiğin ürettikleri yenilenir.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metin_olcum  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

AYRAC = re.compile(r"^\s*(\*\s*\*\s*\*|⁂|\*{3,}|-{3,})\s*$")
OZEL_AD = re.compile(r"(?<![.!?…—]\s)(?<!^)\b([A-ZÇĞİÖŞÜ][a-zçğıöşüâîû]+(?:['’][a-zçğıöşü]+)?)")
KISALTMA = re.compile(r"\b([A-ZÇĞİÖŞÜ]{2,6})\b")
SAYI = re.compile(r"\b\d+(?:[.,:]\d+)*\b")
YABANCI = re.compile(r"\b\w*(?:w|x|q)\w*\b", re.I)


def seslendirme_metni(metin: str) -> str:
    satirlar = []
    for s in metin_olcum.satir_sonlarini_duzelt(metin).split("\n"):
        if AYRAC.match(s):
            satirlar.append("[DURAKSAMA]")
            continue
        if s.lstrip().startswith("#"):
            satirlar.append(s.lstrip("# ").strip() + ".")
            continue
        s = re.sub(r"(\*\*|__|\*|_)(.+?)\1", r"\2", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"<!--.*?-->", "", s)
        satirlar.append(s.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(satirlar)).strip() + "\n"


def ondalik(x: float) -> str:
    return str(x).replace(".", ",")


def sure_dk(kelime: int, hiz: int) -> float:
    return round(kelime / hiz, 1)


def telaffuz_adaylari(metinler: list[str]) -> dict[str, list[tuple[str, int]]]:
    ozel: Counter[str] = Counter()
    kisaltma: Counter[str] = Counter()
    sayi: Counter[str] = Counter()
    yabanci: Counter[str] = Counter()
    for metin in metinler:
        govde = metin_olcum.gorunur_govde(metin)
        for satir in govde.split("\n"):
            for m in OZEL_AD.finditer(satir):
                ozel[re.split(r"['’]", m.group(1))[0]] += 1
        kisaltma.update(KISALTMA.findall(govde))
        sayi.update(SAYI.findall(govde))
        yabanci.update(w.lower() for w in YABANCI.findall(govde))
    return {"ozel_adlar": ozel.most_common(40), "kisaltmalar": kisaltma.most_common(20),
            "sayilar": sayi.most_common(20), "yabanci_gorunumlu": yabanci.most_common(20)}


def hazirla(dosyalar: list[Path], cikti: Path, hiz: int, yeniden: bool) -> dict[str, Any]:
    cikti.mkdir(parents=True, exist_ok=True)
    (cikti / "seslendirme").mkdir(exist_ok=True)
    kayitlar, metinler = [], []
    for i, d in enumerate(dosyalar, start=1):
        metin = d.read_text(encoding="utf-8")
        metinler.append(metin)
        hedef = cikti / "seslendirme" / (f"{d.stem}.txt" if d.stem != "metin" else f"{d.parent.name}.txt")
        if hedef.exists() and not yeniden:
            raise FileExistsError(f"{hedef} zaten var (yenilemek için --yeniden)")
        hedef.write_text(seslendirme_metni(metin), encoding="utf-8")
        kelime = metin_olcum.kelime_say(metin)
        kayitlar.append({"sira": i, "dosya": d.name, "kelime": kelime, "dakika": sure_dk(kelime, hiz), "cikti": str(hedef)})
    toplam = sum(k["kelime"] for k in kayitlar)
    toplam_dk = sure_dk(toplam, hiz)
    s = ["# Tahmini Süre", "", f"Anlatım hızı: dakikada {hiz} kelime. Toplam: {toplam} kelime ≈ {int(toplam_dk // 60)} sa {round(toplam_dk % 60)} dk", "",
         "| # | Dosya | Kelime | Süre (dk) |", "|---|---|---|---|"] + [f"| {k['sira']} | {k['dosya']} | {k['kelime']} | {ondalik(k['dakika'])} |" for k in kayitlar]
    for ad, icerik in (("sure.md", "\n".join(s) + "\n"),):
        yol = cikti / ad
        if yol.exists() and not yeniden:
            raise FileExistsError(f"{yol} zaten var (yenilemek için --yeniden)")
        yol.write_text(icerik, encoding="utf-8")
    aday = telaffuz_adaylari(metinler)
    t = ["# Telaffuz Sözlüğü (aday)", "", "Seslendirmen ya da TTS için doğru okunuşu yazın. Örnek: `Kuzguncuk — kuz-gun-cuk (vurgu sonda)`.", ""]
    for baslik, anahtar in (("Özel adlar", "ozel_adlar"), ("Kısaltmalar", "kisaltmalar"), ("Sayılar ve saatler", "sayilar"), ("Yabancı görünümlü sözcükler", "yabanci_gorunumlu")):
        t += [f"## {baslik}", ""] + [f"- {w} ({n}) — [okunuş]" for w, n in aday[anahtar]] + [""]
    yol = cikti / "telaffuz.md"
    if yol.exists() and not yeniden:
        raise FileExistsError(f"{yol} zaten var (yenilemek için --yeniden)")
    yol.write_text("\n".join(t), encoding="utf-8")
    return {"tamam": True, "toplam_kelime": toplam, "toplam_dakika": toplam_dk, "bolumler": kayitlar, "klasor": str(cikti)}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grup = ayr.add_mutually_exclusive_group(required=True)
    grup.add_argument("--proje", type=Path)
    grup.add_argument("--dosya", type=Path, nargs="+")
    ayr.add_argument("--hiz", type=int, default=150)
    ayr.add_argument("--cikti", type=Path)
    ayr.add_argument("--yeniden", action="store_true")
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    if not 80 <= arg.hiz <= 250:
        print("Hata: --hiz 80–250 arasında olmalı", file=sys.stderr)
        return 2
    dosyalar = sorted((arg.proje / "metin").glob("bolum-*.md")) if arg.proje else arg.dosya
    if not dosyalar:
        print("Hata: seslendirilecek metin bulunamadı", file=sys.stderr)
        return 2
    cikti = arg.cikti or ((arg.proje / "sesli-kitap") if arg.proje else dosyalar[0].parent / "sesli-kitap")
    try:
        sonuc = hazirla(dosyalar, cikti, arg.hiz, arg.yeniden)
    except (OSError, UnicodeDecodeError) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 2
    if arg.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        print(f"Hazır: {sonuc['klasor']} · {sonuc['toplam_kelime']} kelime ≈ {ondalik(sonuc['toplam_dakika'])} dk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
