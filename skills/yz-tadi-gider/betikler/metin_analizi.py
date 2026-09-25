#!/usr/bin/env python3
"""Türkçe düzyazı için nesnel anlatım ölçümleri (editörün ilk okuması).

Bir kalite puanı değildir; editörün göz atacağı yerleri sayılarla gösterir:

  okunabilirlik   Ateşman (1997) formülü: 198,825 − 40,175 × (hece/kelime)
                  − 2,610 × (kelime/cümle). Türkçede hece sayısı ünlü sayısına eşittir.
  cumle           ortalama ve standart sapma; sapma düşükse ritim tekdüzedir.
  diyalog         konuşma çizgisi ya da tırnakla başlayan satırlardaki kelime oranı.
  yankilar        birbirine yakın (varsayılan 40 kelime) tekrarlanan içerik kelimeleri.
  cumle_basi      art arda aynı kelimeyle başlayan 3 ya da daha fazla cümle.
  duyular         görme, işitme, koku, dokunma ve tat kelimelerinin kaba dağılımı.
  isaretler       bitmemiş metin işaretleri: [TK], [DOLDUR], ⟦…⟧, TODO, XXX.

Çıkış kodu: 0 temiz, 1 bitmemiş metin işareti var, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

UNLULER = set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")
ON_BILGI = re.compile(r"\A---\n.*?\n---\n", re.S)
HTML_YORUM = re.compile(r"<!--.*?-->", re.S)
CUMLE_SONU = re.compile(r"(?<=[.!?…])[\"”’»)]*\s+")
ISARET = re.compile(r"\[(?:TK|DOLDUR|YAZILACAK|KONTROL ET|KAYNAK)\b[^\]\n]*\]|⟦[^⟧\n]*⟧|\bTODO\b|\bXXX\b")
TEKDUZE_SAPMA_ORANI = 0.35   # standart sapma / ortalama bunun altındaysa ritim tekdüze
VARSAYILAN_PENCERE = 40
EN_COK_YANKI = 15

# Yankı sayımından çıkarılan işlev ve çok sık kullanılan kelimelerin kökleri (ilk 5 harf).
DURAK = {
    "bir", "bu", "şu", "ve", "ile", "ama", "için", "gibi", "daha", "çok", "kadar", "sonra",
    "önce", "şey", "şeyi", "diye", "değil", "değild", "olan", "oldu", "olarak", "olmuş", "olmak",
    "etti", "etmek", "dedi", "diyor", "demek", "her", "hiç", "ben", "beni", "bana", "benim", "sen",
    "seni", "sana", "senin", "biz", "bizi", "bize", "bizim", "onu", "ona", "onun", "onlar", "kendi",
    "bütün", "neden", "nasıl", "nerede", "şimdi", "sonra", "yine", "bile", "artık", "hemen", "bunu",
    "buna", "bunun", "şunu", "orada", "burada", "yoktu", "vardı", "degil", "hala", "hâlâ", "tekra",
    "başka", "birka", "birço", "hiçbi", "hepsi", "belki", "sadec", "yalnı", "ancak", "fakat", "çünkü",
    "sanki", "adeta", "olduğ", "ettiğ", "dediğ", "istiy", "gerek", "zaman", "evet", "hayır", "tamam",
}

DUYULAR = {
    "görme": ("gör", "bak", "izle", "parla", "ışı", "karanl", "gölge", "renk", "kırmız", "mavi", "sarı",
              "yeşil", "beyaz", "siyah", "gri", "soluk", "seçil", "belir"),
    "işitme": ("ses", "duy", "dinle", "fısıl", "gıcır", "tıkır", "çınla", "uğul", "bağır", "sessiz",
               "yankı", "gürül", "tık tak", "vurdu", "öksür", "fokur", "hışır"),
    "koku": ("koku", "kokl", "burn", "mis gibi", "lavanta", "yanık", "küf", "is kok"),
    "dokunma": ("dokun", "soğuk", "sıcak", "ıslak", "pürüz", "yumuşa", "kaygan", "titre", "üşü",
                "avuc", "avuç", "parmak", "ağır", "serin", "yapış"),
    "tat": ("tadı", "tadın", "tatlı", "tuzlu", "ekşi", "buruk", "yut", "damağ", "damak", "acımsı"),
}


class AnalizHatasi(ValueError):
    """Beklenen kullanım hatası."""


def govde(metin: str) -> str:
    metin = metin.replace("\r\n", "\n").replace("\r", "\n")
    metin = ON_BILGI.sub("", metin, count=1)
    metin = HTML_YORUM.sub("", metin)
    return "\n".join("" if s.lstrip().startswith(("#", "|", "```")) else s for s in metin.split("\n"))


def hece_say(kelime: str) -> int:
    return max(1, sum(1 for h in kelime if h in UNLULER)) if any(h.isalpha() for h in kelime) else 0


def cumleler(metin: str) -> list[str]:
    parcalar: list[str] = []
    for paragraf in metin.split("\n"):
        paragraf = paragraf.strip().lstrip("—–-").strip()
        if paragraf:
            parcalar.extend(c.strip() for c in CUMLE_SONU.split(paragraf) if tk.KELIME.search(c))
    return parcalar


def atesman_duzeyi(puan: float) -> str:
    if puan >= 90:
        return "çok kolay"
    if puan >= 70:
        return "kolay"
    if puan >= 50:
        return "orta güçlükte"
    if puan >= 30:
        return "zor"
    return "çok zor"


def _kok(kelime: str) -> str:
    kucuk = tk.tr_kucuk(kelime.split("'")[0].split("’")[0])
    return kucuk[:5]


def yankilari_bul(metin: str, pencere: int = VARSAYILAN_PENCERE) -> list[dict[str, Any]]:
    """Aynı köke sahip içerik kelimeleri ``pencere`` kelime içinde yeniden geçiyorsa raporlar."""
    if pencere < 2:
        raise AnalizHatasi("pencere en az 2 kelime olmalı")
    son_gorulen: dict[str, int] = {}
    olaylar: dict[str, dict[str, Any]] = {}
    sira = 0
    for satir_no, satir in enumerate(metin.split("\n"), 1):
        for m in tk.KELIME.finditer(satir):
            kelime = m.group(0)
            sira += 1
            if len(kelime) < 4 or kelime[0].isupper() or kelime[0].isdigit():
                continue
            kok = _kok(kelime)
            if kok in DURAK or len(kok) < 4:
                continue
            onceki = son_gorulen.get(kok)
            if onceki is not None and sira - onceki <= pencere:
                kayit = olaylar.setdefault(kok, {"kok": kok, "sayi": 1, "satirlar": [], "ornekler": []})
                kayit["sayi"] += 1
                if satir_no not in kayit["satirlar"]:
                    kayit["satirlar"].append(satir_no)
                if tk.tr_kucuk(kelime) not in kayit["ornekler"] and len(kayit["ornekler"]) < 4:
                    kayit["ornekler"].append(tk.tr_kucuk(kelime))
            son_gorulen[kok] = sira
    return sorted(olaylar.values(), key=lambda k: (-k["sayi"], k["satirlar"][0]))[:EN_COK_YANKI]


def cumle_basi_tekrarlari(metin: str) -> list[dict[str, Any]]:
    sonuc: list[dict[str, Any]] = []
    onceki = ""
    dizi: list[str] = []
    for cumle in cumleler(metin) + [""]:
        ilk = tk.KELIME.search(cumle)
        bas = tk.tr_kucuk(ilk.group(0)) if ilk else ""
        if bas and bas == onceki:
            dizi.append(cumle)
            continue
        if len(dizi) >= 3:
            sonuc.append({"kelime": onceki, "sayi": len(dizi), "ilk_cumle": dizi[0][:60]})
        dizi = [cumle]
        onceki = bas
    return sonuc


def duyu_dagilimi(metin: str) -> dict[str, int]:
    kucuk = tk.tr_kucuk(metin)
    kelimeler = [tk.tr_kucuk(k) for k in tk.KELIME.findall(metin)]
    sayim: dict[str, int] = {}
    for duyu, onekler in DUYULAR.items():
        tek = [o for o in onekler if " " not in o]
        cok = [o for o in onekler if " " in o]
        sayim[duyu] = sum(1 for k in kelimeler if k.startswith(tuple(tek))) + sum(kucuk.count(o) for o in cok)
    return sayim


def isaretleri_bul(metin: str) -> list[dict[str, Any]]:
    bulunan = []
    for no, satir in enumerate(metin.replace("\r\n", "\n").split("\n"), 1):
        for m in ISARET.finditer(satir):
            bulunan.append({"satir": no, "sutun": m.start() + 1, "isaret": m.group(0)})
    return bulunan


def analiz_et(ham: str, pencere: int = VARSAYILAN_PENCERE) -> dict[str, Any]:
    metin = govde(ham)
    kelimeler = tk.KELIME.findall(metin)
    kelime_sayisi = len(kelimeler)
    cumle_listesi = cumleler(metin)
    uzunluklar = [len(tk.KELIME.findall(c)) for c in cumle_listesi]
    cumle_sayisi = max(1, len(uzunluklar))
    hece = sum(hece_say(k) for k in kelimeler)
    sonuc: dict[str, Any] = {"kelime": kelime_sayisi, "cumle": len(uzunluklar), "uyarilar": []}
    if kelime_sayisi == 0:
        sonuc["uyarilar"].append("Metin boş ya da ölçülecek kelime yok.")
        sonuc["isaretler"] = isaretleri_bul(ham)
        return sonuc
    ortalama = kelime_sayisi / cumle_sayisi
    sapma = math.sqrt(sum((u - ortalama) ** 2 for u in uzunluklar) / cumle_sayisi) if uzunluklar else 0.0
    puan = 198.825 - 40.175 * (hece / kelime_sayisi) - 2.610 * ortalama
    diyalog_kelime = sum(len(tk.KELIME.findall(s)) for s in metin.split("\n") if s.strip() and tk.diyalog_satiri_mi(s))
    paragraflar = [s for s in metin.split("\n") if s.strip()]
    sonuc.update({
        "okunabilirlik": {"atesman": round(puan, 1), "duzey": atesman_duzeyi(puan),
                          "hece_kelime": round(hece / kelime_sayisi, 2)},
        "cumle_uzunlugu": {"ortalama": round(ortalama, 1), "sapma": round(sapma, 1),
                           "en_uzun": max(uzunluklar, default=0), "en_kisa": min(uzunluklar, default=0)},
        "paragraf": {"sayi": len(paragraflar), "ortalama_kelime": round(kelime_sayisi / max(1, len(paragraflar)), 1)},
        "diyalog_orani": round(diyalog_kelime / kelime_sayisi, 2),
        "yankilar": yankilari_bul(metin, pencere),
        "cumle_basi": cumle_basi_tekrarlari(metin),
        "duyular": duyu_dagilimi(metin),
        "isaretler": isaretleri_bul(ham),
    })
    uyarilar = sonuc["uyarilar"]
    if len(uzunluklar) >= 8 and ortalama and sapma / ortalama < TEKDUZE_SAPMA_ORANI:
        uyarilar.append(f"Cümle ritmi tekdüze (ortalama {tk.tr_ondalik(ortalama)}, sapma {tk.tr_ondalik(sapma)}); kısa ve uzun cümleleri karıştırın.")
    if ortalama > 22:
        uyarilar.append(f"Ortalama cümle {tk.tr_ondalik(ortalama)} kelime; telefonda okunan metin için uzun.")
    for yanki in sonuc["yankilar"]:
        if yanki["sayi"] >= 3:
            uyarilar.append(f"'{yanki['ornekler'][0]}' kökü yakın aralıkla {yanki['sayi']} kez geçiyor (satır {', '.join(map(str, yanki['satirlar'][:5]))}).")
    for tekrar in sonuc["cumle_basi"]:
        uyarilar.append(f"{tekrar['sayi']} cümle art arda '{tekrar['kelime']}' ile başlıyor: “{tekrar['ilk_cumle']}…”")
    duyu = sonuc["duyular"]
    toplam_duyu = sum(duyu.values())
    if toplam_duyu >= 10 and duyu["görme"] / toplam_duyu > 0.7:
        uyarilar.append("Duyusal ayrıntıların çoğu görsel; bir ses, koku ya da dokunma ekleyin.")
    elif kelime_sayisi >= 500 and sum(1 for v in duyu.values() if v == 0) >= 3:
        eksik = ", ".join(k for k, v in duyu.items() if v == 0)
        uyarilar.append(f"Bu duyulara hiç değinilmemiş: {eksik}.")
    if sonuc["isaretler"]:
        uyarilar.append(f"{len(sonuc['isaretler'])} bitmemiş metin işareti var; teslimden önce doldurun.")
    return sonuc


def rapor_yaz(dosya: str, s: dict[str, Any]) -> str:
    satirlar = [f"== {dosya}", f"Kelime: {s['kelime']} · Cümle: {s['cumle']}"]
    if "okunabilirlik" in s:
        o, c, p = s["okunabilirlik"], s["cumle_uzunlugu"], s["paragraf"]
        satirlar += [
            f"Okunabilirlik (Ateşman): {tk.tr_ondalik(o['atesman'])} · {o['duzey']} · kelime başına {tk.tr_ondalik(o['hece_kelime'], 2)} hece",
            f"Cümle uzunluğu: ortalama {tk.tr_ondalik(c['ortalama'])} · sapma {tk.tr_ondalik(c['sapma'])} · en kısa {c['en_kisa']} · en uzun {c['en_uzun']}",
            f"Paragraf: {p['sayi']} · ortalama {tk.tr_ondalik(p['ortalama_kelime'])} kelime · Diyalog oranı: %{round(s['diyalog_orani'] * 100)}",
            "Duyular: " + " · ".join(f"{k} {v}" for k, v in s["duyular"].items()),
        ]
        if s["yankilar"]:
            satirlar.append("Yakın tekrarlar: " + ", ".join(f"{y['ornekler'][0]} ×{y['sayi']}" for y in s["yankilar"][:8]))
    for i in s.get("isaretler", []):
        satirlar.append(f"{dosya}:{i['satir']}:{i['sutun']}\tbitmemiş işaret {i['isaret']}")
    for u in s["uyarilar"]:
        satirlar.append(f"  ! {u}")
    if not s["uyarilar"]:
        satirlar.append("  ✓ Dikkat çeken bir ölçüm yok.")
    return "\n".join(satirlar)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("dosyalar", nargs="+", type=Path, help="incelenecek Markdown ya da metin dosyaları")
    ayr.add_argument("--json", action="store_true", help="sonucu JSON olarak yaz")
    ayr.add_argument("--pencere", type=int, default=VARSAYILAN_PENCERE,
                     help=f"yakın tekrar penceresi, kelime (varsayılan {VARSAYILAN_PENCERE})")
    arg = ayr.parse_args(argv)
    sonuclar: dict[str, Any] = {}
    try:
        for yol in arg.dosyalar:
            sonuclar[str(yol)] = analiz_et(dosya_oku.metin_oku(yol), arg.pencere)
    except (AnalizHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    if arg.json:
        print(json.dumps(sonuclar, ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(rapor_yaz(d, s) for d, s in sonuclar.items()))
    return 1 if any(s.get("isaretler") for s in sonuclar.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
