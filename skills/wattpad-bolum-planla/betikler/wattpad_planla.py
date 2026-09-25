#!/usr/bin/env python3
"""Wattpad için bölüm bölme, mobil okunabilirlik denetimi ve yayın takvimi.

Kullanım::

    wattpad_planla.py denetle --proje KITAP [--alt 1500 --ust 3000] [--json]
    wattpad_planla.py bol --dosya metin/bolum-004_x.md [--hedef 2000] [--cikti klasor] [--json]
    wattpad_planla.py takvim --proje KITAP --baslangic 2026-10-02 --gunler cuma[,salı] [--saat 20:00] [--tampon 3]

``denetle`` her bölümün uzunluğunu Wattpad aralığına, paragraflarını telefonda okunurluğa
(uzun paragraf uyarısı) ve bölüm sonunu kancaya göre değerlendirir. ``bol`` uzun bir metni
sahne ayraçlarından (``* * *``), yoksa paragraf sınırlarından, hedefe en yakın noktalardan
böler; ``--cikti`` verilmezse yalnızca öneri yazar, metni değiştirmez. ``takvim`` yazılmış
ve planlanmış bölümlerden yayın tarihleri üretir ve tampon (önceden yazılmış bölüm) uyarısı
verir.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metin_olcum  # noqa: E402

try:  # argparse iletilerini ve hata iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
    from turkce_argparse import hata_iletisi
except ImportError:  # pragma: no cover
    hata_iletisi = str

GUNLER = {"pazartesi": 0, "salı": 1, "sali": 1, "çarşamba": 2, "carsamba": 2, "perşembe": 3, "persembe": 3,
          "cuma": 4, "cumartesi": 5, "pazar": 6}
GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AY_ADLARI = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
AYRAC = re.compile(r"^\s*(\*\s*\*\s*\*|⁂|\*{3,})\s*$")
UZUN_PARAGRAF = 120


def paragraflar(metin: str) -> list[str]:
    govde = metin_olcum.gorunur_govde(metin)
    return [p.strip() for p in re.split(r"\n\s*\n", govde) if p.strip()]


def kanca_puani(son_paragraf: str) -> tuple[int, str]:
    """Kaba bir sezgi: kısa son paragraf, soru, yarım kalan konuşma, beklenmedik bilgi işaretleri."""
    puan, neden = 0, []
    kelime = len(son_paragraf.split())
    if kelime <= 25:
        puan += 1
        neden.append("kısa son paragraf")
    if son_paragraf.rstrip().endswith(("?", "…", "!")):
        puan += 1
        neden.append("soru/askı noktalaması")
    if son_paragraf.lstrip().startswith("—"):
        puan += 1
        neden.append("konuşmayla bitiş")
    if re.search(r"\b(ama|oysa|meğer|birden|kapı|telefon|mesaj|ses)\b", son_paragraf.lower()):
        puan += 1
        neden.append("değişim sözcüğü")
    return puan, ", ".join(neden) or "belirgin kanca işareti yok"


def bolum_dosyalari(proje: Path) -> list[Path]:
    return sorted((proje / "metin").glob("bolum-*.md"))


def denetle(proje: Path, alt: int, ust: int) -> list[dict[str, Any]]:
    sonuc = []
    for yol in bolum_dosyalari(proje):
        metin = yol.read_text(encoding="utf-8")
        kelime = metin_olcum.kelime_say(metin)
        pler = paragraflar(metin)
        uzun = [i + 1 for i, p in enumerate(pler) if len(p.split()) > UZUN_PARAGRAF]
        puan, neden = kanca_puani(pler[-1]) if pler else (0, "boş")
        uyarilar = []
        if kelime < alt:
            uyarilar.append(f"kısa ({kelime} < {alt}); bir sonraki bölümle birleştirmeyi düşünün")
        if kelime > ust:
            uyarilar.append(f"uzun ({kelime} > {ust}); 'bol' komutuyla bölmeyi düşünün")
        if uzun:
            uyarilar.append(f"telefonda uzun görünen paragraflar: {', '.join(map(str, uzun[:8]))}")
        if pler and len(pler[0].split()) > 80:
            uyarilar.append("ilk paragraf uzun; ilk ekranda merak uyandıracak kısa bir açılış önerilir")
        if puan == 0:
            uyarilar.append("bölüm sonu kancası zayıf görünüyor (sezgisel)")
        sonuc.append({"dosya": yol.name, "kelime": kelime, "paragraf": len(pler), "kanca_puani": puan,
                      "kanca_nedeni": neden, "uyarilar": uyarilar})
    return sonuc


def bolme_noktalari(metin: str, hedef: int) -> list[dict[str, Any]]:
    satirlar = metin_olcum.satir_sonlarini_duzelt(metin).split("\n")
    adaylar: list[tuple[int, int, bool]] = []  # (satır indeksi, o noktaya kadarki kelime, sahne ayracı mı)
    sayac = 0
    for i, s in enumerate(satirlar):
        if AYRAC.match(s):
            adaylar.append((i, sayac, True))
            continue
        if not s.lstrip().startswith("#"):
            sayac += len(metin_olcum.KELIME_DESENI.findall(s))
        if not s.strip() and i + 1 < len(satirlar):
            adaylar.append((i, sayac, False))
    toplam = sayac
    parca_sayisi = max(1, round(toplam / hedef))
    noktalar = []
    for k in range(1, parca_sayisi):
        istenen = toplam * k / parca_sayisi
        uygun = [a for a in adaylar if abs(a[1] - istenen) <= hedef * 0.25] or adaylar
        if not uygun:
            break
        # sahne ayracı tercih edilir; sonra hedefe yakınlık
        secilen = min(uygun, key=lambda a: (not a[2], abs(a[1] - istenen)))
        if noktalar and secilen[0] <= noktalar[-1]["satir"]:
            continue
        noktalar.append({"satir": secilen[0] + 1, "kelime": secilen[1], "sahne_ayraci": secilen[2]})
    return noktalar


def bol(dosya: Path, hedef: int, cikti: Path | None) -> dict[str, Any]:
    metin = dosya.read_text(encoding="utf-8")
    noktalar = bolme_noktalari(metin, hedef)
    sonuc: dict[str, Any] = {"dosya": str(dosya), "toplam_kelime": metin_olcum.kelime_say(metin), "hedef": hedef,
                             "bolme_noktalari": noktalar}
    if cikti is not None:
        satirlar = metin_olcum.satir_sonlarini_duzelt(metin).split("\n")
        sinirlar = [0] + [n["satir"] for n in noktalar] + [len(satirlar)]
        cikti.mkdir(parents=True, exist_ok=True)
        yazilan = []
        for i in range(len(sinirlar) - 1):
            dilim = satirlar[sinirlar[i]:sinirlar[i + 1]]
            while dilim and (not dilim[0].strip() or AYRAC.match(dilim[0])):
                dilim.pop(0)
            while dilim and (not dilim[-1].strip() or AYRAC.match(dilim[-1])):
                dilim.pop()
            parca = "\n".join(dilim) + "\n"
            yol = cikti / f"{dosya.stem}_parca-{i + 1}.md"
            if yol.exists():
                raise FileExistsError(f"{yol} zaten var; üzerine yazılmaz")
            yol.write_text(parca, encoding="utf-8", newline="\n")
            yazilan.append({"dosya": str(yol), "kelime": metin_olcum.kelime_say(parca)})
        sonuc["yazilan"] = yazilan
    return sonuc


def tarih_metni(g: date) -> str:
    return f"{g.day} {AY_ADLARI[g.month - 1]} {g.year} {GUN_ADLARI[g.weekday()]}"


def takvim(proje: Path, baslangic: date, gunler: list[int], saat: str, tampon: int) -> dict[str, Any]:
    yazilan = [p.name for p in bolum_dosyalari(proje)]
    planlanan = sorted(p.name for p in (proje / "plan").glob("bolum-plani_*.md"))
    toplam = max(len(yazilan), len(planlanan))
    tarihler = []
    g = baslangic
    while len(tarihler) < toplam:
        if g.weekday() in gunler:
            tarihler.append(g)
        g += timedelta(days=1)
    satirlar = []
    for i, t in enumerate(tarihler, start=1):
        durum = "yazıldı" if i <= len(yazilan) else "planlandı"
        satirlar.append({"bolum": i, "tarih": t.isoformat(), "tarih_metni": f"{tarih_metni(t)} {saat}", "durum": durum})
    uyari = None
    if len(yazilan) < tampon:
        uyari = (f"Tamponda yalnızca {len(yazilan)} yazılmış bölüm var; yayına başlamadan en az {tampon} bölüm "
                 "önceden yazılmış olmalı (düzenli yayın okur kaybını önler).")
    return {"yazilan": len(yazilan), "planlanan": len(planlanan), "takvim": satirlar, "uyari": uyari}


def takvim_md(t: dict[str, Any]) -> str:
    s = ["# Wattpad Yayın Takvimi", "", f"Yazılmış: {t['yazilan']} · Planlanmış: {t['planlanan']}", ""]
    if t["uyari"]:
        s += [f"> ⚠️ {t['uyari']}", ""]
    s += ["| Bölüm | Yayın | Durum |", "|---|---|---|"] + [f"| {r['bolum']} | {r['tarih_metni']} | {r['durum']} |" for r in t["takvim"]]
    return "\n".join(s) + "\n"


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    d = alt.add_parser("denetle")
    d.add_argument("--proje", required=True, type=Path)
    d.add_argument("--alt", type=int, default=1500)
    d.add_argument("--ust", type=int, default=3000)
    d.add_argument("--json", action="store_true")
    b = alt.add_parser("bol")
    b.add_argument("--dosya", required=True, type=Path)
    b.add_argument("--hedef", type=int, default=2000)
    b.add_argument("--cikti", type=Path)
    b.add_argument("--json", action="store_true")
    t = alt.add_parser("takvim")
    t.add_argument("--proje", required=True, type=Path)
    t.add_argument("--baslangic", required=True)
    t.add_argument("--gunler", required=True, help="virgülle: cuma,salı")
    t.add_argument("--saat", default="20:00")
    t.add_argument("--tampon", type=int, default=3)
    t.add_argument("--json", action="store_true")
    t.add_argument("--cikti", type=Path, help="Markdown takvim dosyası (ör. plan/wattpad-takvimi.md)")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "denetle":
            sonuc: Any = denetle(arg.proje, arg.alt, arg.ust)
            if not arg.json:
                for r in sonuc:
                    print(f"{r['dosya']}: {r['kelime']} kelime · kanca {r['kanca_puani']}/4 ({r['kanca_nedeni']})")
                    for u in r["uyarilar"]:
                        print(f"   ⚠️ {u}")
                return 0
        elif arg.komut == "bol":
            if arg.hedef < 100:
                raise ValueError("hedef en az 100 kelime olmalı")
            sonuc = bol(arg.dosya, arg.hedef, arg.cikti)
        else:
            gunler = [GUNLER[g.strip().lower()] for g in arg.gunler.split(",") if g.strip()]
            if not gunler:
                raise ValueError("en az bir gün verin")
            sonuc = takvim(arg.proje, datetime.strptime(arg.baslangic, "%Y-%m-%d").date(), sorted(set(gunler)), arg.saat, arg.tampon)
            if arg.cikti:
                arg.cikti.write_text(takvim_md(sonuc), encoding="utf-8", newline="\n")
            if not arg.json:
                print(takvim_md(sonuc), end="")
                return 0
    except KeyError as hata:
        print(f"Tanınmayan gün: {hata}. Seçenekler: {', '.join(GUN_ADLARI).lower()}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as hata:
        print(f"Hata: {hata_iletisi(hata)}", file=sys.stderr)
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
