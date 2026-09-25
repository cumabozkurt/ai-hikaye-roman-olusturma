#!/usr/bin/env python3
"""Kapak istemi oluşturur; isteğe bağlı olarak görsel API'siyle üretir ve platform boyutuna kırpar.

Kullanım::

    kapak_olustur.py istem --baslik "Saatçinin Kızı" --yazar "Deniz Ak" --tur polisiye --platform wattpad [--not "..."]
    kapak_olustur.py uret  --baslik … --yazar … --tur … --platform … --cikti kapaklar/saatcinin-kizi [--kuru]
    kapak_olustur.py kirp  --girdi kapak.png --platform wattpad --cikti kapak-wattpad.png

``uret`` yalnızca ajan ortamında yerleşik görsel üretim aracı YOKSA ve yazar açıkça
isterse kullanılır (ücretli olabilir). Anahtar yalnızca ortam değişkeninden okunur
(``GPT_IMAGE_API_KEY``) ve hiçbir çıktıya yazılmaz. İsteğe bağlı değişkenler:
``GPT_IMAGE_BASE_URL`` (varsayılan https://api.openai.com/v1), ``GPT_IMAGE_MODEL``
(varsayılan gpt-image-2), ``GPT_IMAGE_SIZE`` (varsayılan platforma göre).
``kirp`` için Pillow gerekir (``pip install pillow``).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

PLATFORMLAR: dict[str, dict[str, Any]] = {
    "wattpad": {"ad": "Wattpad", "boyut": (512, 800), "oran": "16:25 (dikey)", "uretim": "1024x1536"},
    "e-kitap": {"ad": "E-kitap (Amazon KDP, Google Play Kitaplar)", "boyut": (1600, 2560), "oran": "1:1,6 (dikey)", "uretim": "1024x1536"},
    "basili": {"ad": "Basılı ön kapak 13,5×21 cm, 300 dpi", "boyut": (1594, 2480), "oran": "9:14 (dikey)", "uretim": "1024x1536"},
    "sesli-kitap": {"ad": "Sesli kitap (Storytel, Audible)", "boyut": (3000, 3000), "oran": "1:1 (kare)", "uretim": "1024x1024"},
}
TURLER: dict[str, str] = {
    "romantik": "sıcak gün batımı tonları, iki silüet arasında bırakılmış mesafe, yumuşak ışık, zarif el yazısı tipografi",
    "genc-kurgu": "canlı pastel ya da neon renkler, modern sans-serif tipografi, telefon ekranı ışığı, kent ya da okul silüeti",
    "fantastik": "destansı manzara, Anadolu ve Orta Asya motiflerinden esinli semboller, altın ve lacivert, süslü serif tipografi",
    "polisiye": "karanlık ve düşük doygunlukta renkler, tek bir kırmızı vurgu, İstanbul sokak dokusu, keskin serif tipografi",
    "tarihi": "dönem dokusu, eski kâğıt ve minyatür esintisi, sepya ve bordo, klasik serif tipografi",
    "psikolojik-gerilim": "yakın plan ve bölünmüş kompozisyon, soğuk tonlar, boşluk kullanımı, dar ve gergin tipografi",
    "bilimkurgu": "soğuk mavi ve camgöbeği, geometrik ışıklar, kent silüeti, teknik sans-serif tipografi",
    "korku": "sis, tek ışık kaynağı, köy evi ya da eski apartman, siyah ve kirli yeşil, aşınmış tipografi",
    "aile-dram": "konak ya da yalı, sıcak ama kasvetli ışık, kuşaklar arası nesneler, dizi afişi dengesinde kompozisyon",
    "mizah": "parlak renkler, çizgi roman esintili figür, eğlenceli el yapımı tipografi",
    "edebi": "minimal kompozisyon, tek güçlü imge, bol boşluk, sade serif tipografi",
    "oyku": "tek sahneden alınmış imge, sade düzen, küçük ama okunaklı tipografi",
}


class KapakHatasi(RuntimeError):
    pass


def istem_olustur(baslik: str, yazar: str, tur: str, platform: str, not_: str = "") -> str:
    if not baslik.strip() or not yazar.strip():
        raise KapakHatasi("kitap adı ve yazar adı (ya da mahlas) zorunludur; uydurulmaz")
    if tur not in TURLER:
        raise KapakHatasi(f"tanınmayan tür: {tur} (seçenekler: {', '.join(TURLER)})")
    p = PLATFORMLAR[platform]
    return (
        f"Profesyonel bir kitap kapağı tasarla. Oran: {p['oran']}.\n"
        f"Kitap adı tam olarak şu Türkçe metin olmalı, harfleri değiştirme: \"{baslik}\"\n"
        f"Yazar adı tam olarak: \"{yazar}\"\n"
        "Türkçe karakterler (ç, ğ, ı, İ, ö, ş, ü) doğru ve okunaklı çizilmeli; noktalı/noktasız i ayrımına dikkat et.\n"
        f"Tür ve görsel dil: {TURLER[tur]}.\n"
        "Kompozisyon: kitap adı üst üçte birde büyük ve okunaklı, yazar adı altta; kenarlardan en az %6 güvenli boşluk; "
        "küçük boyutta (telefon listesinde) bile okunur olsun.\n"
        "Kaçın: başka kitapların, filmlerin ya da gerçek kişilerin tanınabilir görselleri; filigran; ek metin, slogan ya da logo.\n"
        + (f"Yazarın notu: {not_}\n" if not_.strip() else "")
    )


def uret(istem: str, platform: str, cikti: Path, kuru: bool) -> dict[str, Any]:
    temel = os.environ.get("GPT_IMAGE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    boyut = os.environ.get("GPT_IMAGE_SIZE", PLATFORMLAR[platform]["uretim"])
    govde = {"model": model, "prompt": istem, "size": boyut, "n": 1}
    if kuru:
        return {"tamam": True, "kuru": True, "adres": f"{temel}/images/generations", "govde": govde}
    anahtar = os.environ.get("GPT_IMAGE_API_KEY")
    if not anahtar:
        raise KapakHatasi("GPT_IMAGE_API_KEY ortam değişkeni tanımlı değil (anahtarı sohbete yazmayın; terminalde export edin)")
    if not temel.startswith("https://"):
        raise KapakHatasi("GPT_IMAGE_BASE_URL https ile başlamalı")
    istek = urllib.request.Request(f"{temel}/images/generations", data=json.dumps(govde).encode("utf-8"), method="POST",
                                   headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(istek, timeout=180) as y:  # noqa: S310 - https zorunlu
            yanit = json.loads(y.read().decode("utf-8"))
    except urllib.error.HTTPError as hata:
        ayrinti = hata.read().decode("utf-8", "replace")[:300].replace(anahtar, "***")
        raise KapakHatasi(f"API hatası {hata.code}: {ayrinti}") from None
    except (urllib.error.URLError, TimeoutError, ValueError) as hata:
        raise KapakHatasi(f"API'ye ulaşılamadı: {hata}") from None
    veri = (yanit.get("data") or [{}])[0]
    if not veri.get("b64_json"):
        raise KapakHatasi("API yanıtında görsel yok (b64_json bekleniyordu)")
    cikti.mkdir(parents=True, exist_ok=True)
    mevcut = sorted(cikti.glob("kapak-*.png"))
    yol = cikti / f"kapak-{len(mevcut) + 1:02d}.png"
    yol.write_bytes(base64.b64decode(veri["b64_json"]))
    (cikti / f"{yol.stem}-istem.txt").write_text(istem, encoding="utf-8")
    return {"tamam": True, "dosya": str(yol), "model": model, "boyut": boyut}


def kirp(girdi: Path, platform: str, cikti: Path) -> dict[str, Any]:
    try:
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError as hata:
        raise KapakHatasi("kırpma için Pillow gerekli: pip install pillow") from hata
    hedef_g, hedef_y = PLATFORMLAR[platform]["boyut"]
    with Image.open(girdi) as resim:
        g, y = resim.size
        oran = hedef_g / hedef_y
        if g / y > oran:
            yeni_g = round(y * oran)
            kutu = ((g - yeni_g) // 2, 0, (g - yeni_g) // 2 + yeni_g, y)
        else:
            yeni_y = round(g / oran)
            kutu = (0, (y - yeni_y) // 2, g, (y - yeni_y) // 2 + yeni_y)
        resim.crop(kutu).resize((hedef_g, hedef_y), Image.Resampling.LANCZOS).save(cikti)
    return {"tamam": True, "dosya": str(cikti), "boyut": f"{hedef_g}x{hedef_y}",
            "uyari": "Kırpma kenarları keser; kitap adı ve yazar adının görünür kaldığını kontrol edin."}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    for ad in ("istem", "uret"):
        p = alt.add_parser(ad)
        p.add_argument("--baslik", required=True)
        p.add_argument("--yazar", required=True)
        p.add_argument("--tur", required=True, choices=list(TURLER))
        p.add_argument("--platform", default="wattpad", choices=list(PLATFORMLAR))
        p.add_argument("--not", dest="not_", default="")
        if ad == "uret":
            p.add_argument("--cikti", required=True, type=Path)
            p.add_argument("--kuru", action="store_true")
    k = alt.add_parser("kirp")
    k.add_argument("--girdi", required=True, type=Path)
    k.add_argument("--platform", required=True, choices=list(PLATFORMLAR))
    k.add_argument("--cikti", required=True, type=Path)
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "istem":
            print(istem_olustur(arg.baslik, arg.yazar, arg.tur, arg.platform, arg.not_))
            return 0
        if arg.komut == "uret":
            sonuc = uret(istem_olustur(arg.baslik, arg.yazar, arg.tur, arg.platform, arg.not_), arg.platform, arg.cikti, arg.kuru)
        else:
            sonuc = kirp(arg.girdi, arg.platform, arg.cikti)
    except (KapakHatasi, OSError) as hata:
        print(json.dumps({"tamam": False, "hata": str(hata)}, ensure_ascii=False))
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
