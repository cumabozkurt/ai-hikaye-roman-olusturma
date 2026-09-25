#!/usr/bin/env python3
"""Süreklilik (tutarlılık) denetleyicisi — takip durumu ile yazılan metni karşılaştırır.

Kullanım::

    sureklilik_denetle.py --proje KITAP [--bolum N] [--json]

``--bolum`` verilmezse son kaydedilen bölümden sonraki taslak (yoksa son bölüm)
denetlenir. Denetimler:

  * olu-karakter        öldüğü kayıtlı karakter sahnede eylem yapıyor
  * suresi-gecen-ipucu  planlanan çözüm bölümü geçmiş ama hâlâ açık ipucu
  * gizli-olay-sizintisi açığa çıkmamış olayın anahtar kelimesi metinde (plan bu bölümde açmıyorsa)
  * isim-benzerligi     birbirine çok benzeyen karakter adları (okuru karıştırır)
  * isim-kaymasi        metinde bilinen bir adın bir harf farklı yazımı (Elif → Elıf)
  * nitelik-celiskisi   göz/saç rengi ya da yaşın karakter dosyasıyla çelişmesi

"hata" düzeyi çıkış kodunu 1 yapar; "uyari" yapmaz.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import metin_olcum  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

RENKLER = ("mavi", "yeşil", "kahverengi", "ela", "siyah", "gri", "lacivert", "bal rengi", "kara", "sarı",
           "kızıl", "kumral", "beyaz", "kestane", "sarışın", "esmer", "turuncu", "mor")
ANI_SOZCUKLERI = ("hatırla", "anı", "mezar", "rahmetli", "ölmüş", "özle", "yas", "cenaze", "fotoğraf", "rüya",
                  "hayal", "geçmiş", "eskiden", "yıllar önce", "kabrin", "ruhu", "ölen", "ölümün", "öldüğ")
UZUN_ACIK_IPUCU = 30


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    onceki = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        simdiki = [i]
        for j, cb in enumerate(b, 1):
            simdiki.append(min(onceki[j] + 1, simdiki[j - 1] + 1, onceki[j - 1] + (ca != cb)))
        onceki = simdiki
    return onceki[-1]


def karakter_nitelikleri(proje: Path) -> dict[str, dict[str, str]]:
    sonuc: dict[str, dict[str, str]] = {}
    klasor = proje / "kurgu" / "karakterler"
    if not klasor.is_dir():
        return sonuc
    for yol in sorted(klasor.glob("*.md")):
        metin = dosya_oku.metin_oku(yol)
        baslik = re.search(r"^#\s+(.+)$", metin, re.M)
        ad = (baslik.group(1) if baslik else yol.stem).split("—")[0].strip()
        nitelik: dict[str, str] = {}
        for anahtar, desen in (("goz", r"göz(?:\s+rengi)?"), ("sac", r"saç(?:\s+rengi)?"), ("yas", r"yaş")):
            m = re.search(rf"^\s*[-*]\s*\**{desen}\**\s*:\s*(.+)$", metin, re.M | re.I)
            if m:
                nitelik[anahtar] = tk.tr_kucuk(m.group(1).strip())
        sonuc[ad] = nitelik
    return sonuc


def cumleler(metin: str) -> list[tuple[int, str]]:
    sonuc = []
    for no, satir in enumerate(metin.splitlines(), 1):
        for c in re.split(r"(?<=[.!?…])\s+", satir):
            if c.strip():
                sonuc.append((no, c))
    return sonuc


def ad_bicimleri(ad: str, tum_adlar: list[str]) -> list[str]:
    """Tam ad ve (başka karakterle çakışmıyorsa) ilk ad: "Defne Aras" metinde çoğunlukla "Defne" diye geçer."""
    bicimler = [ad]
    ilk = ad.split()[0] if " " in ad else ""
    if len(ilk) >= 3 and sum(1 for a in tum_adlar if a.split()[0] == ilk) == 1:
        bicimler.append(ilk)
    return bicimler


def ad_gecer(ad: str, cumle: str, tum_adlar: list[str] | None = None) -> bool:
    if tum_adlar is not None:
        return any(ad_gecer(b, cumle) for b in ad_bicimleri(ad, tum_adlar))
    return re.search(rf"(?<![{tk.HARF}]){re.escape(ad)}(?:['’][{tk.HARF}]+|[{tk.HARF}]{{0,4}})?(?![{tk.HARF}])", cumle) is not None


def denetle(proje: Path, bolum: int | None = None) -> dict[str, Any]:
    bulgular: list[dict[str, Any]] = []

    def ekle(duzey: str, kural: str, mesaj: str, satir: int = 0, kanit: str = "") -> None:
        bulgular.append({"duzey": duzey, "kural": kural, "satir": satir, "mesaj": mesaj, "kanit": kanit[:120]})

    durum_yolu = proje / "takip" / "_takip-durumu.json"
    durum = dosya_oku.json_nesne_oku(durum_yolu, bos={})
    son = int(durum.get("son_kaydedilen_bolum", 0))
    if bolum is None:
        bolum = son + 1
        try:
            metin_olcum.bolum_dosyasi_bul(proje / "metin", bolum, plan=False)
        except metin_olcum.OlcumHatasi:
            bolum = max(son, 1)
    try:
        metin_yolu = metin_olcum.bolum_dosyasi_bul(proje / "metin", bolum, plan=False)
        metin = metin_olcum.gorunur_govde(dosya_oku.metin_oku(metin_yolu))
    except metin_olcum.OlcumHatasi:
        metin_yolu, metin = None, ""
    try:
        plan_metni = dosya_oku.metin_oku(metin_olcum.bolum_dosyasi_bul(proje / "plan", bolum, plan=True))
    except metin_olcum.OlcumHatasi:
        plan_metni = ""
    karakterler: dict[str, Any] = durum.get("karakterler", {})
    nitelikler = karakter_nitelikleri(proje)
    adlar = sorted(set(karakterler) | set(nitelikler))
    cumle_listesi = cumleler(metin)

    # 1. Ölü karakter sahnede
    for ad, k in karakterler.items():
        if k.get("yasam_durumu") != "öldü" or not metin:
            continue
        for no, c in cumle_listesi:
            kucuk = tk.tr_kucuk(c)
            if ad_gecer(ad, c, list(karakterler)) and not any(s in kucuk for s in ANI_SOZCUKLERI) and not tk.diyalog_satiri_mi(c):
                if bolum > son:
                    ekle("hata", "olu-karakter", f"{ad} öldü olarak kayıtlı ama sahnede görünüyor (anı/rüya ise bunu metinde belirginleştirin).", no, c)
                else:
                    ekle("uyari", "olu-karakter", f"{ad} öldü olarak kayıtlı ve sahnede görünüyor; ölüm bu bölümden sonraysa sorun yoktur.", no, c)
                break
    # 2. Süresi geçen ipuçları
    for kimlik, ip in sorted(durum.get("ipuclari", {}).items()):
        if ip.get("durum") != "ekili":
            continue
        plan = ip.get("planlanan_cozum_bolumu")
        if plan is not None and plan < bolum:
            duzey = "hata" if ip.get("onem") == "yüksek" else "uyari"
            ekle(duzey, "suresi-gecen-ipucu", f"{kimlik} ({ip.get('ozet')}) {plan}. bölümde çözülecekti; hâlâ açık. Çözün, ertelemeyi kaydedin ya da 'süresi geçti' yapın.")
        elif plan is None and bolum - int(ip.get("ekildigi_bolum", bolum)) > UZUN_ACIK_IPUCU:
            ekle("uyari", "suresi-gecen-ipucu", f"{kimlik} {UZUN_ACIK_IPUCU} bölümden uzun süredir açık ve çözüm planı yok.")
    # 3. Gizli olay sızıntısı
    for kimlik, olay in sorted(durum.get("zaman_cizelgesi", {}).items()):
        if olay.get("aciga_cikma") != "gizli" or not metin:
            continue
        planli = kimlik in plan_metni
        for kelime in olay.get("anahtar_kelimeler", []):
            k = tk.tr_kucuk(kelime)
            for no, c in cumle_listesi:
                if k and k in tk.tr_kucuk(c):
                    if planli:
                        ekle("uyari", "gizli-olay-sizintisi", f"{kimlik} bu bölümde planlı olarak açılıyor; kayıtta aciga_cikma ve acilma_bolumu güncellenmeli.", no, c)
                    else:
                        ekle("hata", "gizli-olay-sizintisi", f"{kimlik} henüz gizli; '{kelime}' metinde geçiyor. Plan bu bölümde açmıyorsa sızıntıdır.", no, c)
                    break
    # 4. Benzer adlar
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            ka, kb = tk.tr_kucuk(a), tk.tr_kucuk(b)
            if min(len(ka), len(kb)) >= 3 and (levenshtein(ka, kb) <= 1 or (ka[:3] == kb[:3] and levenshtein(ka, kb) <= 2)):
                ekle("uyari", "isim-benzerligi", f"'{a}' ile '{b}' çok benziyor; okur karıştırabilir.")
    # 5. İsim kayması
    if metin and adlar:
        bilinen = {tk.tr_kucuk(a.split()[0]) for a in adlar}
        adaylar: dict[str, int] = {}
        for m in re.finditer(rf"(?<![{tk.HARF}])([A-ZÇĞİÖŞÜ][{tk.HARF}]{{2,}})", metin):
            kelime = m.group(1)
            adaylar[kelime] = adaylar.get(kelime, 0) + 1
        for kelime, adet in adaylar.items():
            k = tk.tr_kucuk(kelime)
            if k in bilinen or adet > 2:
                continue
            for dogru in bilinen:
                if len(dogru) >= 4 and levenshtein(k, dogru) == 1 and len(k) == len(dogru):
                    ekle("uyari", "isim-kaymasi", f"'{kelime}' bilinen '{dogru.capitalize()}' adının yanlış yazımı olabilir.")
    # 6. Nitelik çelişkisi
    for ad, nit in nitelikler.items():
        ilk_ad = ad.split()[0]
        for no, c in cumle_listesi:
            if not ad_gecer(ilk_ad, c):
                continue
            kucuk = tk.tr_kucuk(c)
            for anahtar, kok in (("goz", "göz"), ("sac", "saç")):
                if anahtar in nit and kok in kucuk:
                    renkler = [r for r in RENKLER if re.search(rf"(?<![{tk.HARF}]){r}", kucuk)]
                    if renkler and not any(r in nit[anahtar] for r in renkler):
                        ekle("hata", "nitelik-celiskisi", f"{ad}: {kok} rengi karakter dosyasında '{nit[anahtar]}', metinde '{renkler[0]}'.", no, c)
            if "yas" in nit:
                m = re.search(r"(\d{1,3})\s+yaşında", kucuk)
                kanon = re.search(r"\d+", nit["yas"])
                if m and kanon and m.group(1) != kanon.group(0):
                    ekle("uyari", "nitelik-celiskisi", f"{ad}: yaş karakter dosyasında {kanon.group(0)}, metinde {m.group(1)} (hikâye zamanı ilerlediyse dosyayı güncelleyin).", no, c)
    return {"tamam": not any(b["duzey"] == "hata" for b in bulgular), "bolum": bolum,
            "metin": str(metin_yolu) if metin_yolu else None, "bulgular": bulgular}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--proje", required=True, type=Path)
    ayr.add_argument("--bolum", type=int)
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    if not arg.proje.is_dir():
        print(f"proje klasörü yok: {arg.proje}", file=sys.stderr)
        return 2
    sonuc = denetle(arg.proje, arg.bolum)
    if arg.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        for b in sonuc["bulgular"]:
            yer = f"{b['satir']}. satır " if b["satir"] else ""
            print(f"[{b['duzey']}] {b['kural']}: {yer}{b['mesaj']}")
        print(f"{sonuc['bolum']}. bölüm süreklilik denetimi: " + ("geçti." if sonuc["tamam"] else "sorun var."))
    return 0 if sonuc["tamam"] else 1


if __name__ == "__main__":
    sys.exit(main())
