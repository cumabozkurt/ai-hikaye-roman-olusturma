#!/usr/bin/env python3
"""Kaynak romanın mekanik bölüm dizini (bölüm sınırlarının tek doğru kaynağı).

Kullanım::

    bolum_dizini.py --kaynak KUTUPHANE/kitap/kaynak/metin.txt --cikti KUTUPHANE/kitap/bolum-dizini.csv

Tanınan başlıklar: "BÖLÜM 1", "Bölüm Yedi: Kapı", "1. Bölüm", "# 12", "Chapter 3",
"1." (tek başına satır) ve özel bölümler (Önsöz, Giriş, Prolog, Epilog, Son Söz, Sonsöz,
Ek Bölüm). Baştaki içindekiler listesi (başlıkların arka arkaya dizildiği blok) atılır.
Dizin anlam yorumlamaz; yalnızca satır aralıklarını, kelime sayılarını ve SHA-256
özetlerini yazar. Kaynak değişmediyse dosya bayt bayt aynı kalır.

Bu modül ayrıca ``bolum-cikarici`` ajanının grup çıktısı için ``GRUP_SEMASI``
tanımını ve ``grup_dogrula`` işlevini içerir.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

AYRISTIRICI_SURUMU = "1"
SUTUNLAR = ("bolum", "kaynak_bolum", "baslik", "baslangic_satiri", "bitis_satiri", "kelime", "tur",
            "bolum_sha256", "kaynak_sha256", "ayristirici_surumu")
SAYI_SOZCUKLERI = {
    "bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6, "yedi": 7, "sekiz": 8, "dokuz": 9,
    "on": 10, "yirmi": 20, "otuz": 30, "kırk": 40, "elli": 50, "altmış": 60, "yetmiş": 70,
    "seksen": 80, "doksan": 90, "yüz": 100,
}
SIRA_SOZCUKLERI = {"birinci": 1, "ikinci": 2, "üçüncü": 3, "dördüncü": 4, "beşinci": 5, "altıncı": 6,
                   "yedinci": 7, "sekizinci": 8, "dokuzuncu": 9, "onuncu": 10}
SAYI = r"(?P<sayi>\d{1,4}|[A-Za-zÇĞİÖŞÜçğıöşü ]{2,40}?)"
DESENLER = [
    re.compile(rf"^\s*#{{0,3}}\s*(?:BÖLÜM|Bölüm|bölüm|KISIM|Kısım)\s+{SAYI}\s*(?:[:.\-–—]\s*(?P<baslik>.*))?$"),
    re.compile(r"^\s*#{0,3}\s*(?P<sayi>\d{1,4})\s*\.\s*(?:BÖLÜM|Bölüm)\s*(?:[:.\-–—]\s*(?P<baslik>.*))?$"),
    re.compile(r"^\s*#{0,3}\s*(?P<sayi>[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?:BÖLÜM|Bölüm)\s*(?:[:.\-–—]\s*(?P<baslik>.*))?$"),
    re.compile(r"^\s*#{0,3}\s*Chapter\s+(?P<sayi>\d{1,4})\b\s*[:.\-–—]?\s*(?P<baslik>.*)$", re.I),
    re.compile(r"^\s*#{1,3}\s+(?P<sayi>\d{1,4})\s*[:.\-–—]?\s*(?P<baslik>.*)$"),
    re.compile(r"^\s*(?P<sayi>\d{1,4})\s*\.?\s*$"),
]
OZEL = re.compile(r"^\s*#{0,3}\s*(?P<etiket>Önsöz|ÖNSÖZ|Giriş|GİRİŞ|Prolog|PROLOG|Epilog|EPİLOG|Son Söz|SON SÖZ|Sonsöz|SONSÖZ|Ek Bölüm|EK BÖLÜM)\s*(?:[:.\-–—]\s*(?P<baslik>.*))?$")


class DizinHatasi(ValueError):
    pass


def sha256(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


def kaynak_coz(ham: bytes) -> str:
    for kodlama in ("utf-8-sig", "cp1254", "iso-8859-9"):
        try:
            return ham.decode(kodlama).replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            continue
    raise DizinHatasi("kaynak metnin kodlaması çözülemedi (UTF-8 ya da Windows-1254 bekleniyor)")


def sayi_coz(ham: str) -> int | None:
    ham = ham.strip().lower().replace("i̇", "i")
    if ham.isdigit():
        return int(ham)
    if ham in SIRA_SOZCUKLERI:
        return SIRA_SOZCUKLERI[ham]
    toplam = 0
    for parca in ham.split():
        if parca not in SAYI_SOZCUKLERI:
            return None
        deger = SAYI_SOZCUKLERI[parca]
        toplam = toplam * 100 if deger == 100 and toplam else toplam + deger
    return toplam or None


def adaylar(satirlar: list[str]) -> list[dict[str, Any]]:
    sonuc = []
    for i, satir in enumerate(satirlar, start=1):
        if len(satir) > 120 or not satir.strip():
            continue
        m = OZEL.match(satir)
        if m:
            sonuc.append({"satir": i, "sayi": None, "tur": "ozel", "baslik": (m.group("baslik") or m.group("etiket")).strip()})
            continue
        for desen in DESENLER:
            m = desen.match(satir)
            if m:
                sayi = sayi_coz(m.group("sayi"))
                if sayi is not None:
                    baslik = (m.groupdict().get("baslik") or "").strip()
                    sonuc.append({"satir": i, "sayi": sayi, "tur": "bolum", "baslik": baslik})
                break
    return sonuc


def icindekileri_at(aday: list[dict[str, Any]], satirlar: list[str]) -> list[dict[str, Any]]:
    """Numaralama ikinci kez 1'den başlıyorsa, ondan önceki gövdesiz bölüm başlıkları içindekiler listesidir."""
    birler = [i for i, a in enumerate(aday) if a["sayi"] == 1]
    if len(birler) < 2:
        return aday
    ikinci = birler[1]

    def govdesiz(i: int) -> bool:
        bitis = aday[i + 1]["satir"] - 1 if i + 1 < len(aday) else len(satirlar)
        return not any(s.strip() for s in satirlar[aday[i]["satir"]:bitis])

    if all(govdesiz(i) for i in range(birler[0], ikinci) if aday[i]["tur"] == "bolum"):
        return [a for i, a in enumerate(aday) if i >= ikinci or a["tur"] != "bolum"]
    return aday


def dizin_olustur(metin: str) -> list[dict[str, Any]]:
    satirlar = metin.split("\n")
    kaynak_ozeti = sha256(metin.encode("utf-8"))
    aday = icindekileri_at(adaylar(satirlar), satirlar)
    if not any(a["tur"] == "bolum" for a in aday):
        raise DizinHatasi("hiç bölüm başlığı bulunamadı; başlıkları 'Bölüm 1' ya da '# 1' biçiminde işaretleyin")
    sayilar = [a["sayi"] for a in aday if a["tur"] == "bolum"]
    for onceki, sonraki in zip(sayilar, sayilar[1:]):
        if sonraki not in (onceki + 1, 1):
            raise DizinHatasi(f"bölüm numaraları sıralı değil: {onceki} → {sonraki}; kaynağı düzeltin")
    satirlar_listesi = []
    sira = 0
    for i, a in enumerate(aday):
        bitis = (aday[i + 1]["satir"] - 1) if i + 1 < len(aday) else len(satirlar)
        govde = "\n".join(satirlar[a["satir"]:bitis]).strip()
        if a["tur"] == "bolum":
            sira += 1
        satirlar_listesi.append({
            "bolum": sira if a["tur"] == "bolum" else 0,
            "kaynak_bolum": a["sayi"] if a["sayi"] is not None else "",
            "baslik": a["baslik"],
            "baslangic_satiri": a["satir"],
            "bitis_satiri": bitis,
            "kelime": len(re.findall(r"[\wÇĞİÖŞÜçğıöşüÂâÎîÛû]+(?:['’][\wçğıöşü]+)*", govde)),
            "tur": a["tur"],
            "bolum_sha256": sha256(govde.encode("utf-8")),
            "kaynak_sha256": kaynak_ozeti,
            "ayristirici_surumu": AYRISTIRICI_SURUMU,
        })
    return satirlar_listesi


def csv_metni(satirlar: list[dict[str, Any]]) -> bytes:
    tampon = io.StringIO()
    yazici = csv.DictWriter(tampon, fieldnames=SUTUNLAR, lineterminator="\n")
    yazici.writeheader()
    yazici.writerows(satirlar)
    return tampon.getvalue().encode("utf-8")


def atomik_yaz(yol: Path, veri: bytes) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(dir=yol.parent, prefix=".gecici-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(veri)
        os.replace(gecici, yol)
    finally:
        if os.path.exists(gecici):
            os.unlink(gecici)


def dizin_oku(yol: Path) -> list[dict[str, str]]:
    with yol.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- bölüm çıkarıcı grup şeması

GRUP_SEMASI: dict[str, Any] = {
    "grup": {"ilk": "int", "son": "int"},
    "bolumler": [{
        "bolum": "int",
        "ozet": "str (en çok 3 cümle)",
        "sahneler": [{"yer": "str", "zaman": "str", "karakterler": ["str"]}],
        "karakter_degisimleri": [{"karakter": "str", "degisim": "str"}],
        "ipuclari": [{"ipucu": "str", "islem": "ekildi|ilerledi|cozuldu"}],
        "olaylar": [{"yazar_gercegi": "str", "okur_bilgisi": "gizli|kismen|acik"}],
        "duygu": {"gerilim": "int 1-10", "baskin_duygu": "str"},
        "kanca": {"acilis": "str", "kapanis": "str"},
        "olay_noktalari": ["str (10-30 madde)"],
        "uslup_ornegi": ["str (en çok 2 kısa cümle, her biri en çok 25 kelime)"],
    }],
}
IPUCU_ISLEMLERI = {"ekildi", "ilerledi", "cozuldu"}
OKUR_BILGISI = {"gizli", "kismen", "acik"}
EN_AZ_NOKTA, EN_COK_NOKTA = 10, 30
EN_COK_GRUP = 3


def grup_dogrula(veri: Any, ilk: int | None = None, son: int | None = None) -> list[str]:
    """Grup JSON'unu GRUP_SEMASI'na göre denetler; sorun listesi döndürür (boşsa geçerli)."""
    s: list[str] = []
    if not isinstance(veri, dict):
        return ["kök bir JSON nesnesi olmalı"]
    grup = veri.get("grup")
    if not isinstance(grup, dict) or not all(isinstance(grup.get(k), int) for k in ("ilk", "son")):
        return ["'grup' alanı {ilk, son} tamsayılarını içermeli"]
    if ilk is not None and (grup["ilk"], grup["son"]) != (ilk, son):
        s.append(f"grup aralığı beklenen {ilk}-{son} değil: {grup['ilk']}-{grup['son']}")
    if grup["son"] - grup["ilk"] + 1 > EN_COK_GRUP:
        s.append(f"bir grup en çok {EN_COK_GRUP} bölüm olabilir")
    bolumler = veri.get("bolumler")
    if not isinstance(bolumler, list):
        return s + ["'bolumler' bir liste olmalı"]
    numaralar = [b.get("bolum") for b in bolumler if isinstance(b, dict)]
    if numaralar != list(range(grup["ilk"], grup["son"] + 1)):
        s.append(f"bölüm numaraları grup aralığıyla aynı olmalı: {numaralar}")
    for b in bolumler:
        if not isinstance(b, dict):
            s.append("her bölüm kaydı bir nesne olmalı")
            continue
        n = b.get("bolum")
        if not isinstance(b.get("ozet"), str) or not b["ozet"].strip():
            s.append(f"bölüm {n}: özet boş")
        noktalar = b.get("olay_noktalari")
        if not isinstance(noktalar, list) or not EN_AZ_NOKTA <= len(noktalar) <= EN_COK_NOKTA:
            s.append(f"bölüm {n}: olay_noktalari {EN_AZ_NOKTA}-{EN_COK_NOKTA} madde olmalı")
        duygu = b.get("duygu") or {}
        if not (isinstance(duygu, dict) and isinstance(duygu.get("gerilim"), int) and 1 <= duygu["gerilim"] <= 10):
            s.append(f"bölüm {n}: duygu.gerilim 1-10 arası tamsayı olmalı")
        for ip in b.get("ipuclari") or []:
            if not isinstance(ip, dict) or ip.get("islem") not in IPUCU_ISLEMLERI:
                s.append(f"bölüm {n}: ipucu işlemi {sorted(IPUCU_ISLEMLERI)} değerlerinden biri olmalı")
        for ol in b.get("olaylar") or []:
            if not isinstance(ol, dict) or ol.get("okur_bilgisi") not in OKUR_BILGISI:
                s.append(f"bölüm {n}: okur_bilgisi {sorted(OKUR_BILGISI)} değerlerinden biri olmalı")
        ornek = b.get("uslup_ornegi") or []
        if not isinstance(ornek, list) or len(ornek) > 2 or any(len(str(x).split()) > 25 for x in ornek):
            s.append(f"bölüm {n}: üslup örneği en çok 2 kısa cümle (telif nedeniyle uzun alıntı yok)")
    return s


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--kaynak", required=True, type=Path)
    ayr.add_argument("--cikti", required=True, type=Path)
    arg = ayr.parse_args(argv)
    try:
        metin = kaynak_coz(arg.kaynak.read_bytes())
        satirlar = dizin_olustur(metin)
    except OSError as hata:
        print(json.dumps({"tamam": False, "hata": f"kaynak okunamadı: {hata}"}, ensure_ascii=False))
        return 2
    except DizinHatasi as hata:
        print(json.dumps({"tamam": False, "hata": str(hata)}, ensure_ascii=False))
        return 1
    veri = csv_metni(satirlar)
    degisti = not (arg.cikti.is_file() and arg.cikti.read_bytes() == veri)
    if degisti:
        atomik_yaz(arg.cikti, veri)
    bolum_sayisi = sum(1 for s in satirlar if s["tur"] == "bolum")
    print(json.dumps({"tamam": True, "bolum": bolum_sayisi, "ozel": len(satirlar) - bolum_sayisi,
                      "toplam_kelime": sum(s["kelime"] for s in satirlar), "degisti": degisti,
                      "cikti": str(arg.cikti)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
