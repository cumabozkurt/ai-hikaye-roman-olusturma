#!/usr/bin/env python3
"""Bölüm planı (sahne planı) sözleşme denetleyicisi ve plan-kopya dedektörü.

Kullanım::

    plan_denetle.py sozlesme plan/bolum-plani_007.md [...]
    plan_denetle.py sozlesme --proje KITAP --bolum 7
    plan_denetle.py kopya --plan plan/bolum-plani_007.md --metin metin/bolum-007_x.md

Sözleşme denetimi yalnızca yapıyı denetler: yazılı şablondaki alanlar, alt
başlıklar ve olay akışı tablosu yerinde mi? Değerin iyi olup olmadığına karar
vermez; bilinmeyen değerler ``[doldurulacak]`` yazılabilir. Yalnızca iki niyet
alanı (duygu hedefi, kahramanın amacı) gerçek içerik ister; çünkü metin
kalitesini doğrudan etkilerler.

Kopya denetimi, yazılan metnin plandaki cümleleri aynen aktarıp aktarmadığını
7 kelimelik parçalar (shingle) ile arar. Plan satırını metne yapıştırmak
"planı anlatmak" demektir; sahneye dönüştürülmelidir.

Çıkış: 0 geçti, 1 engelleyici sorun, 2 hatalı kullanım.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import metin_olcum  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

ALANLAR = (
    "Ana olay", "Hedef uzunluk", "Uzunluk ölçütü", "Evre", "Birim", "Duygu hedefi",
    "Kahramanın amacı / kritik seçimi", "Bölümün işlevi", "Bölüm formülü", "Açılış kancası",
    "Doyum anı", "Bölüm sonu kancası", "Kapanma durumu", "Bu bölümde açığa çıkmayacaklar",
    "Yazara serbest alan", "Sözleşme riskleri",
)
NIYET_ALANLARI = ("Duygu hedefi", "Kahramanın amacı / kritik seçimi")
ALT_BASLIKLAR = ("Özet", "Olay Akışı", "Karakterler ve Sahneye Giriş Sırası", "Ayrıntılı Sahne Planı")
BES_EVRE = ("Başlangıç", "Gelişme", "Dönüm", "Doruk", "Kapanış")
YER_TUTUCU = re.compile(r"^\s*(?:\[doldurulacak\]|\[yer tutucu\]|yok|-|—|tbd|todo)?\s*$", re.I)
KOPYA_PENCERE = 7
KOPYA_ESIGI = 3


def alan_deseni(ad: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*[-*+]\s*\*{{0,2}}{re.escape(ad)}\*{{0,2}}[ \t]*:[ \t]*(.*)$", re.M | re.I)


def kontrol(kimlik: str, tamam: bool, dosya: str, kanit: str, onarim: str, onem: str = "engelleyici") -> dict[str, object]:
    return {"id": kimlik, "tamam": tamam, "onem": onem, "dosya": dosya, "kanit": kanit, "onarim": onarim}


def sozlesme_denetle(yol: Path) -> list[dict[str, object]]:
    dosya = str(yol)
    if not yol.is_file():
        return [kontrol("plan-var", False, dosya, "dosya yok", "Bölüm planını plan/bolum-plani_NNN.md olarak yazın.")]
    metin = dosya_oku.metin_oku(yol).lstrip("\ufeff")
    sonuc = []
    for ad in ALANLAR:
        m = alan_deseni(ad).search(metin)
        sonuc.append(kontrol(f"alan:{ad}", m is not None, dosya, "var" if m else "eksik",
                             f"'- {ad}: ...' satırını ekleyin (bilinmiyorsa [doldurulacak])."))
        if m and ad in NIYET_ALANLARI and YER_TUTUCU.match(m.group(1)):
            sonuc.append(kontrol(f"niyet:{ad}", False, dosya, "boş ya da yer tutucu",
                                 f"'{ad}' alanına somut içerik yazın; bu alan metin kalitesini doğrudan belirler."))
    try:
        metin_olcum.plandan_hedef(metin)
        sonuc.append(kontrol("hedef-uzunluk-gecerli", True, dosya, "geçerli", ""))
    except metin_olcum.OlcumHatasi as hata:
        sonuc.append(kontrol("hedef-uzunluk-gecerli", False, dosya, str(hata), "'Hedef uzunluk: 2200 kelime' biçiminde yazın (100–50000)."))
    if re.search(r"Uzunluk ölçütü\**[ \t]*:[ \t]*(?!.*gorunur_kelime_v1)", metin, re.I):
        sonuc.append(kontrol("olcut", False, dosya, "ölçüt gorunur_kelime_v1 değil", "'Uzunluk ölçütü: gorunur_kelime_v1' yazın.", "uyari"))
    basliklar = {tk.tr_kucuk(b.strip()) for b in re.findall(r"^#{2,4}\s+(.+)$", metin, re.M)}
    for baslik in ALT_BASLIKLAR:
        var = any(tk.tr_kucuk(baslik) in b for b in basliklar)
        sonuc.append(kontrol(f"baslik:{baslik}", var, dosya, "var" if var else "eksik", f"'## {baslik}' alt başlığını ekleyin."))
    akis = re.search(r"^#{2,4}\s+Olay Akışı.*?$(.*?)(?=^#{2,4}\s|\Z)", metin, re.M | re.S)
    tablo_var = bool(akis and re.search(r"^\|\s*(?:#|Sıra)\s*\|", akis.group(1), re.M))
    sonuc.append(kontrol("olay-akisi-tablosu", tablo_var, dosya, "var" if tablo_var else "eksik",
                         "Olay Akışı altına '| # | Sahne | Olay | Amaç |' başlıklı bir tablo koyun."))
    ayrinti = re.search(r"^#{2,4}\s+Ayrıntılı Sahne Planı.*?$(.*?)(?=^##\s|\Z)", metin, re.M | re.S)
    for evre in BES_EVRE:
        var = bool(ayrinti and re.search(rf"^\s*(?:#{{3,5}}\s*|[-*]\s*\**){re.escape(evre)}", ayrinti.group(1), re.M))
        sonuc.append(kontrol(f"evre:{evre}", var, dosya, "var" if var else "eksik",
                             f"Ayrıntılı Sahne Planı içinde '{evre}' evresini yazın."))
    return sonuc


def _parcalar(metin: str) -> set[tuple[str, ...]]:
    kelimeler = [tk.tr_kucuk(k) for k in tk.KELIME.findall(metin)]
    return {tuple(kelimeler[i:i + KOPYA_PENCERE]) for i in range(len(kelimeler) - KOPYA_PENCERE + 1)}


def kopya_denetle(plan: Path, metin_yolu: Path) -> dict[str, object]:
    plan_metni = dosya_oku.metin_oku(plan)
    plan_metni = "\n".join(re.sub(r"^\s*[-*+|]\s*\**[^:|]{0,40}\**\s*[:|]", "", s) for s in plan_metni.splitlines()
                           if not s.lstrip().startswith("#"))
    govde = metin_olcum.gorunur_govde(dosya_oku.metin_oku(metin_yolu))
    ortak = _parcalar(plan_metni) & _parcalar(govde)
    ornekler = sorted(" ".join(p) for p in ortak)[:5]
    tamam = len(ortak) < KOPYA_ESIGI
    return {"tamam": tamam, "ortak_parca": len(ortak), "ornekler": ornekler,
            "onarim": "" if tamam else "Plan cümlelerini metne aktarmayın; olayı sahne, eylem ve diyalogla gösterin."}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    s = alt.add_parser("sozlesme")
    s.add_argument("planlar", nargs="*", type=Path)
    s.add_argument("--proje", type=Path)
    s.add_argument("--bolum", type=int)
    k = alt.add_parser("kopya")
    k.add_argument("--plan", type=Path, required=True)
    k.add_argument("--metin", type=Path, required=True)
    for p in (s, k):
        p.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    if arg.komut == "kopya":
        if not arg.plan.is_file() or not arg.metin.is_file():
            print("plan ya da metin dosyası yok", file=sys.stderr)
            return 2
        sonuc = kopya_denetle(arg.plan, arg.metin)
        if arg.json:
            print(json.dumps(sonuc, ensure_ascii=False, indent=2))
        else:
            print(("GEÇTİ" if sonuc["tamam"] else "KALDI") + f": planla ortak {sonuc['ortak_parca']} parça")
            for o in sonuc["ornekler"]:  # type: ignore[union-attr]
                print(f"  · {o}")
        return 0 if sonuc["tamam"] else 1
    planlar = list(arg.planlar)
    if arg.proje is not None:
        if arg.bolum is None:
            print("--proje ile --bolum de verilmeli", file=sys.stderr)
            return 2
        try:
            planlar.append(metin_olcum.bolum_dosyasi_bul(arg.proje / "plan", arg.bolum, plan=True))
        except metin_olcum.OlcumHatasi as hata:
            planlar.append(arg.proje / "plan" / f"bolum-plani_{arg.bolum:03d}.md")
            print(f"uyarı: {hata}", file=sys.stderr)
    if not planlar:
        print("denetlenecek plan yok", file=sys.stderr)
        return 2
    kontroller = [c for p in planlar for c in sozlesme_denetle(p)]
    basarisiz = [c for c in kontroller if not c["tamam"] and c["onem"] == "engelleyici"]
    if arg.json:
        print(json.dumps({"tamam": not basarisiz, "kontroller": kontroller}, ensure_ascii=False, indent=2))
    else:
        for c in kontroller:
            if not c["tamam"]:
                print(f"[{c['onem']}] {c['dosya']} · {c['id']}: {c['kanit']} → {c['onarim']}")
        print("Sözleşme " + ("geçti." if not basarisiz else f"kaldı ({len(basarisiz)} engelleyici sorun)."))
    return 0 if not basarisiz else 1


if __name__ == "__main__":
    sys.exit(main())
