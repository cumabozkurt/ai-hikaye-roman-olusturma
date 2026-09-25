#!/usr/bin/env python3
"""Kitap projesinde tam metin arama (BM25): "kırmızı defter en son nerede geçti?"

Gömme (embedding) modeli ya da veritabanı gerektirmez. Metin, plan, kurgu,
araştırma ve takip dosyaları paragraf paragraf dizinlenir; sözcükler Türkçe
küçük harfe çevrilip ilk beş harfine indirilir (Türkçe bilgi erişiminde etkili
olduğu bilinen sabit önek kökleme: "defterini", "deftere" → "defte"). Sonuçlar
BM25 puanına göre sıralanır ve dosya:satır konumuyla verilir.

Kullanım::

    bilgi_ara.py --proje KITAP --sorgu "kırmızı defter" [--kapsam metin] [--adet 8] [--json]
    bilgi_ara.py --proje KITAP --sorgu "\\"cep saati\\"" --tam     # tam ifade

Kapsamlar: hepsi (varsayılan), metin, plan, kurgu, arastirma, takip.
Çıkış kodu: 0 sonuç bulundu, 1 sonuç yok, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KAPSAMLAR = ("metin", "plan", "kurgu", "arastirma", "takip")
KELIME = re.compile(r"[0-9a-zçğıöşüâîû]+")
DURAK = {"ve", "ile", "bir", "bu", "şu", "o", "da", "de", "ki", "mi", "mı", "mu", "mü", "ne", "için", "gibi",
         "ama", "fakat", "çok", "daha", "en", "her", "hiç", "ya", "veya", "ise", "diye", "kadar"}
K1, B = 1.5, 0.75
ONEK = 5


@dataclass
class Parca:
    dosya: str
    satir: int
    metin: str
    terimler: Counter[str]


def kok(kelime: str) -> str:
    return kelime[:ONEK]


def terimlere_ayir(metin: str) -> list[str]:
    kucuk = tk.tr_kucuk(metin).replace("’", "'")
    kucuk = re.sub(r"'[a-zçğıöşü]+", "", kucuk)  # özel ad ekleri: Defne'nin → defne
    return [kok(k) for k in KELIME.findall(kucuk) if k not in DURAK]


def parcalara_bol(yol: Path, goreli: str) -> list[Parca]:
    metin = kitap_proje.satir_koruyan_govde(dosya_oku.metin_oku(yol, uyar=False).replace("\r\n", "\n")) \
        if yol.suffix == ".md" else dosya_oku.metin_oku(yol, uyar=False)
    parcalar, tampon, bas = [], [], 1
    for no, satir in enumerate(metin.split("\n") + [""], start=1):
        if satir.strip():
            if not tampon:
                bas = no
            tampon.append(satir.strip())
            continue
        if tampon:
            govde = " ".join(tampon)
            parcalar.append(Parca(goreli, bas, govde, Counter(terimlere_ayir(govde))))
            tampon = []
    return [p for p in parcalar if p.terimler]


def dizin_olustur(proje: Path, kapsam: str = "hepsi") -> list[Parca]:
    kitap_proje.proje_klasoru(proje)
    klasorler = KAPSAMLAR if kapsam == "hepsi" else (kapsam,)
    parcalar: list[Parca] = []
    for klasor in klasorler:
        taban = proje / klasor
        if not taban.is_dir():
            continue
        for yol in sorted(taban.rglob("*")):
            if yol.is_file() and yol.suffix.lower() in (".md", ".txt") and not yol.name.startswith("."):
                try:
                    parcalar += parcalara_bol(yol, yol.relative_to(proje).as_posix())
                except dosya_oku.DosyaHatasi as hata:
                    print(f"uyarı: atlandı: {hata}", file=sys.stderr)
    return parcalar


def ara(proje: Path, sorgu: str, kapsam: str = "hepsi", adet: int = 8, tam: bool = False) -> list[dict[str, Any]]:
    sorgu = sorgu.strip()
    ifadeler = re.findall(r'"([^"]+)"', sorgu)
    if tam and not ifadeler:
        ifadeler = [sorgu]
    terimler = terimlere_ayir(sorgu.replace('"', " "))
    if not terimler:
        raise ValueError("sorgu anlamlı bir sözcük içermiyor (yalnızca bağlaç ya da noktalama)")
    parcalar = dizin_olustur(proje, kapsam)
    if not parcalar:
        return []
    n = len(parcalar)
    ort = sum(sum(p.terimler.values()) for p in parcalar) / n
    df = Counter(t for p in parcalar for t in set(p.terimler))
    sonuc = []
    kucuk_ifadeler = [tk.tr_kucuk(i) for i in ifadeler]
    for p in parcalar:
        if kucuk_ifadeler and not all(i in tk.tr_kucuk(p.metin) for i in kucuk_ifadeler):
            continue
        uzunluk = sum(p.terimler.values())
        puan = 0.0
        for t in set(terimler):
            f = p.terimler.get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            puan += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * uzunluk / ort))
        if puan > 0:
            sonuc.append({"dosya": p.dosya, "satir": p.satir, "puan": round(puan, 3), "metin": p.metin})
    sonuc.sort(key=lambda s: (-s["puan"], s["dosya"], s["satir"]))
    return sonuc[:adet]


def kesit(metin: str, sorgu: str, genislik: int = 220) -> str:
    kokler = set(terimlere_ayir(sorgu))
    kucuk = tk.tr_kucuk(metin)
    konum = next((m.start() for m in KELIME.finditer(kucuk) if kok(m.group()) in kokler), 0)
    bas = max(0, konum - genislik // 3)
    parca = metin[bas:bas + genislik]
    return ("…" if bas else "") + parca + ("…" if bas + genislik < len(metin) else "")


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Kitap projesinde BM25 tam metin arama (Türkçe köklemeli).")
    ayr.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    ayr.add_argument("--sorgu", required=True, nargs="+", help="aranacak sözcükler; tam ifade için --tam kullanın")
    ayr.add_argument("--kapsam", choices=("hepsi",) + KAPSAMLAR, default="hepsi", help="aranacak klasör")
    ayr.add_argument("--adet", type=int, default=8, help="en fazla sonuç sayısı (varsayılan 8)")
    ayr.add_argument("--tam", action="store_true", help="bütün sorguyu tam ifade olarak ara")
    ayr.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    arg = ayr.parse_args(argv)
    arg.sorgu = " ".join(arg.sorgu)
    if not 1 <= arg.adet <= 200:
        print("hata: --adet 1 ile 200 arasında olmalı", file=sys.stderr)
        return 2
    try:
        sonuclar = ara(arg.proje, arg.sorgu, arg.kapsam, arg.adet, arg.tam)
    except (kitap_proje.ProjeHatasi, ValueError) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    if arg.json:
        print(json.dumps(sonuclar, ensure_ascii=False, indent=2))
    elif not sonuclar:
        print("Sonuç bulunamadı.")
    else:
        for s in sonuclar:
            print(f"{s['dosya']}:{s['satir']}  (puan {tk.tr_ondalik(s['puan'], 2)})\n  {kesit(s['metin'], arg.sorgu)}\n")
    return 0 if sonuclar else 1


if __name__ == "__main__":
    sys.exit(main())
