#!/usr/bin/env python3
"""Wattpad herkese açık arama API'siyle tür ve etiket taraması (Türkçe öyküler).

Kullanım::

    liste_tara.py --sorgu polisiye --sorgu gizem [--adet 60] [--json] [--cikti rapor.md]
    liste_tara.py --girdi kayitli.json        # çevrim dışı: daha önce kaydedilmiş API yanıtı

Yalnızca https://www.wattpad.com/api/v3/stories uç noktasını, düşük hızla (istekler
arasında 1 sn) ve yalnızca herkese açık alanlar için çağırır; oturum, çerez ya da kişisel
veri kullanmaz. Wattpad'in dil alanı Türkçe öykülerde güvenilir olmadığı için Türkçe
süzgeci başlık ve etiketlerdeki Türkçe harf/sözcüklerle yapılır (``--tum-diller`` kapatır).
Kitapyurdu, D&R, idefix gibi mağazalar otomatik erişimi engellediği için bu betik onları
taramaz; onlar için tarayici-cdp becerisiyle yazarın kendi tarayıcısı kullanılır.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

API = "https://www.wattpad.com/api/v3/stories"
ALANLAR = "stories(id,title,readCount,voteCount,commentCount,numParts,tags,user(name),completed,url,mature),total"
KULLANICI_AJANI = "ai-hikaye-roman-olusturma/1.0 (+https://github.com/cumabozkurt/ai-hikaye-roman-olusturma)"
TR_HARF = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
AZ_HARF = re.compile(r"[əƏ]")  # Azerbaycan Türkçesi öyküleri ayrılır
TR_SOZCUK = {"ve", "bir", "aşk", "ask", "gizem", "romantik", "genckurgu", "gençkurgu", "wattpadturkey", "türk",
             "turk", "mafya", "okul", "aile", "dram", "polisiye", "korku", "fantastik", "tarihi", "türkçe", "turkce"}
SAYFA = 50


class TaramaHatasi(RuntimeError):
    pass


def turkce_mi(oyku: dict[str, Any]) -> bool:
    metin = " ".join([str(oyku.get("title", ""))] + [str(t) for t in oyku.get("tags") or []])
    if AZ_HARF.search(metin):
        return False
    if TR_HARF.search(metin):
        return True
    return len(TR_SOZCUK & {str(t).lower() for t in oyku.get("tags") or []}) >= 2


def api_getir(sorgu: str, adet: int, bekle: float = 1.0) -> list[dict[str, Any]]:
    oykuler: list[dict[str, Any]] = []
    ofset = 0
    while len(oykuler) < adet:
        parametre = urllib.parse.urlencode({"query": sorgu, "limit": min(SAYFA, adet - len(oykuler)),
                                            "offset": ofset, "fields": ALANLAR})
        istek = urllib.request.Request(f"{API}?{parametre}", headers={"User-Agent": KULLANICI_AJANI, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(istek, timeout=20) as yanit:  # noqa: S310 - sabit https uç noktası
                veri = json.loads(yanit.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as hata:
            raise TaramaHatasi(f"Wattpad API'sine ulaşılamadı ({hata}). Wattpad Türkiye'de Temmuz 2024'ten beri erişime kapalıdır; "
                               "Türkiye'deki bir ağdaysanız bu beklenen bir durumdur. Kayıtlı bir yanıt için --girdi kullanın "
                               "ya da mağaza listelerine tarayici-cdp ile bakın.") from hata
        sayfa = veri.get("stories") or []
        oykuler.extend(sayfa)
        if len(sayfa) < SAYFA:
            break
        ofset += len(sayfa)
        time.sleep(bekle)
    return oykuler


def ozetle(oykuler: list[dict[str, Any]], sorgular: list[str], tum_diller: bool) -> dict[str, Any]:
    tekil: dict[str, dict[str, Any]] = {}
    for o in oykuler:
        anahtar = str(o.get("id") or o.get("url") or o.get("title"))
        tekil.setdefault(anahtar, o)
    liste = [o for o in tekil.values() if tum_diller or turkce_mi(o)]
    liste.sort(key=lambda o: int(o.get("readCount") or 0), reverse=True)
    if not liste:
        return {"sorgular": sorgular, "oyku_sayisi": 0, "uyari": "sonuç yok"}
    ust = liste[: max(10, len(liste) // 3)]
    etiketler = Counter(str(t).lower() for o in ust for t in (o.get("tags") or []))
    for s in sorgular:
        etiketler.pop(s.lower().lstrip("#"), None)

    def orta(anahtar: str, kume: list[dict[str, Any]]) -> float:
        degerler = [int(o.get(anahtar) or 0) for o in kume]
        return statistics.median(degerler) if degerler else 0

    return {
        "sorgular": sorgular,
        "oyku_sayisi": len(liste),
        "tamamlanan_orani": round(sum(1 for o in liste if o.get("completed")) / len(liste), 2),
        "yetiskin_orani": round(sum(1 for o in liste if o.get("mature")) / len(liste), 2),
        "ortanca_bolum": orta("numParts", liste),
        "ust_dilim_ortanca_bolum": orta("numParts", ust),
        "ust_dilim_ortanca_okunma": orta("readCount", ust),
        "oy_okunma_orani": round(sum(int(o.get("voteCount") or 0) for o in ust) / max(1, sum(int(o.get("readCount") or 0) for o in ust)), 4),
        "sik_etiketler": etiketler.most_common(15),
        "en_cok_okunanlar": [{"baslik": str(o.get("title", "")).strip(), "yazar": (o.get("user") or {}).get("name", ""),
                              "okunma": int(o.get("readCount") or 0), "oy": int(o.get("voteCount") or 0),
                              "bolum": int(o.get("numParts") or 0), "tamamlandi": bool(o.get("completed")),
                              "adres": o.get("url", "")} for o in liste[:10]],
    }


def sayi(n: float) -> str:
    return f"{int(n):,}".replace(",", ".")


def rapor_metni(o: dict[str, Any]) -> str:
    if not o.get("oyku_sayisi"):
        return f"# Wattpad Taraması: {', '.join(o['sorgular'])}\n\nSonuç bulunamadı.\n"
    s = [f"# Wattpad Taraması: {', '.join(o['sorgular'])}", "",
         f"- İncelenen Türkçe öykü: {o['oyku_sayisi']}",
         f"- Tamamlanmış öykü oranı: %{round(o['tamamlanan_orani'] * 100)}",
         f"- Yetişkin içerik işaretli: %{round(o['yetiskin_orani'] * 100)}",
         f"- Ortanca bölüm sayısı: {sayi(o['ortanca_bolum'])} (en çok okunan dilimde {sayi(o['ust_dilim_ortanca_bolum'])})",
         f"- En çok okunan dilimde ortanca okunma: {sayi(o['ust_dilim_ortanca_okunma'])}",
         f"- Oy / okunma oranı: %{str(round(o['oy_okunma_orani'] * 100, 2)).replace('.', ',')}", "",
         "## Sık etiketler (en çok okunan dilim)", "",
         ", ".join(f"{e} ({n})" for e, n in o["sik_etiketler"]), "",
         "## En çok okunanlar", "", "| # | Başlık | Yazar | Okunma | Oy | Bölüm | Durum |", "|---|---|---|---|---|---|---|"]
    for i, k in enumerate(o["en_cok_okunanlar"], start=1):
        baslik = k["baslik"].replace("|", "/")
        s.append(f"| {i} | [{baslik}]({k['adres']}) | {k['yazar']} | {sayi(k['okunma'])} | {sayi(k['oy'])} | {k['bolum']} | {'tamamlandı' if k['tamamlandi'] else 'devam ediyor'} |")
    s += ["", "_Kaynak: Wattpad herkese açık arama API'si. Sayılar tarama anındaki değerlerdir; okunma sayısı kalite ölçüsü değildir._", ""]
    return "\n".join(s)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--sorgu", action="append", default=[], help="arama sözcüğü ya da etiket (birden çok verilebilir)")
    ayr.add_argument("--adet", type=int, default=60, help="sorgu başına en çok öykü (1–200)")
    ayr.add_argument("--girdi", type=Path, help="kayıtlı API yanıtı (JSON: {stories: [...]}) ya da öykü listesi")
    ayr.add_argument("--tum-diller", action="store_true")
    ayr.add_argument("--json", action="store_true")
    ayr.add_argument("--cikti", type=Path)
    arg = ayr.parse_args(argv)
    if not arg.sorgu and not arg.girdi:
        ayr.error("--sorgu ya da --girdi gerekli")
    adet = max(1, min(200, arg.adet))
    try:
        if arg.girdi:
            ham = json.loads(arg.girdi.read_text(encoding="utf-8"))
            oykuler = ham.get("stories", []) if isinstance(ham, dict) else ham
        else:
            oykuler = []
            for s in arg.sorgu:
                oykuler.extend(api_getir(s, adet))
    except (OSError, ValueError, TaramaHatasi) as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 2
    ozet = ozetle(oykuler, arg.sorgu or [arg.girdi.stem], arg.tum_diller)
    metin = json.dumps(ozet, ensure_ascii=False, indent=2) + "\n" if arg.json else rapor_metni(ozet)
    if arg.cikti:
        arg.cikti.parent.mkdir(parents=True, exist_ok=True)
        arg.cikti.write_text(metin, encoding="utf-8")
        print(f"Yazıldı: {arg.cikti}")
    else:
        sys.stdout.write(metin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
