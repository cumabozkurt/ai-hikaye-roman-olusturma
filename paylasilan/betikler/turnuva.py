#!/usr/bin/env python3
"""Bölüm turnuvası: aynı bölümün birden fazla taslağını ikili karşılaştırmalarla sıralar (Elo).

Model ya da yazar her maçta iki taslağı okuyup birini seçer; araç eşleşmeleri
kurar, sonuçları kaydeder ve Elo puanıyla sıralar. Konum yanlılığını azaltmak için
varsayılan olarak her çift iki kez, taraflar yer değiştirerek eşleşir.

Kullanım::

    turnuva.py baslat   --proje KITAP --ad bolum-007 --aday A=taslak-a.md --aday B=taslak-b.md --aday C=taslak-c.md
    turnuva.py sirada   --proje KITAP --ad bolum-007           # sıradaki maç ve hakem yönergesi
    turnuva.py sonuc    --proje KITAP --ad bolum-007 --mac 1 --kazanan A [--gerekce "gerilim daha iyi"]
    turnuva.py siralama --proje KITAP --ad bolum-007 [--json]
    turnuva.py listele  --proje KITAP

Kayıtlar ``KITAP/.hikaye/turnuvalar/<ad>.json`` dosyasında tutulur. Aday dosyası
turnuva başladıktan sonra değişirse sonuç kaydı reddedilir (karşılaştırılan metin
ile sıralanan metin aynı olmalı).

Çıkış kodu: 0 başarılı, 1 oynanacak maç kalmadı (sirada), 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import itertools
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

BASLANGIC = 1500.0
K = 32.0
AD = re.compile(r"^[a-z0-9][a-z0-9_-]{0,59}$")
ETIKET = re.compile(r"^[A-Za-z0-9]{1,12}$")
OLCUTLER = ("okuru sayfada tutma gücü (gerilim, merak)", "bölüm planına sadakat", "karakterlerin tutarlılığı ve sesi",
            "somutluk ve duyusal ayrıntı", "diyalogun doğallığı", "Türkçenin akışı ve doğruluğu")


class TurnuvaHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def _yol(proje: Path, ad: str) -> Path:
    if not AD.match(ad):
        raise TurnuvaHatasi("--ad küçük harf, rakam, tire ve alt çizgiden oluşmalı (ör. bolum-007)")
    return proje / ".hikaye" / "turnuvalar" / f"{ad}.json"


def _ozet(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def oku(proje: Path, ad: str) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    yol = _yol(proje, ad)
    if not yol.is_file():
        raise TurnuvaHatasi(f"turnuva bulunamadı: {ad} (önce 'baslat')")
    veri = dosya_oku.json_nesne_oku(yol)
    if not isinstance(veri.get("adaylar"), dict) or not isinstance(veri.get("maclar"), list):
        raise TurnuvaHatasi(f"turnuva dosyası bozuk: {yol}")
    return veri


def yaz(proje: Path, ad: str, veri: dict[str, Any]) -> None:
    yol = _yol(proje, ad)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(".gecici")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(gecici, yol)


def baslat(proje: Path, ad: str, adaylar: list[str], cift_yonlu: bool = True) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    yol = _yol(proje, ad)
    if yol.exists():
        raise TurnuvaHatasi(f"'{ad}' adlı turnuva zaten var; başka bir ad seçin")
    sozluk: dict[str, dict[str, str]] = {}
    for aday in adaylar:
        if "=" not in aday:
            raise TurnuvaHatasi(f"aday 'ETİKET=dosya' biçiminde olmalı: {aday!r}")
        etiket, dosya = aday.split("=", 1)
        etiket = etiket.strip()
        if not ETIKET.match(etiket):
            raise TurnuvaHatasi(f"geçersiz etiket: {etiket!r} (harf ve rakam, en fazla 12)")
        if etiket in sozluk:
            raise TurnuvaHatasi(f"etiket iki kez kullanılmış: {etiket}")
        dosya_yolu = Path(dosya.strip())
        if not dosya_yolu.is_absolute() and not dosya_yolu.exists() and (proje / dosya_yolu).exists():
            dosya_yolu = proje / dosya_yolu  # proje klasörüne göre verilmiş göreli yol
        dosya_oku.metin_oku(dosya_yolu, uyar=False)  # var mı, metin mi
        mutlak = dosya_yolu.resolve()
        try:  # proje içindeki dosyalar göreli saklanır; proje taşınsa da turnuva çalışır
            saklanan = mutlak.relative_to(proje.resolve()).as_posix()
        except ValueError:
            saklanan = str(mutlak)
        sozluk[etiket] = {"dosya": saklanan, "ozet": _ozet(dosya_yolu)}
    if len(sozluk) < 2:
        raise TurnuvaHatasi("en az iki aday gerekli")
    if len(sozluk) > 12:
        raise TurnuvaHatasi("en fazla 12 aday (maç sayısı hızla büyür)")
    maclar = []
    for a, b in itertools.combinations(sozluk, 2):
        maclar.append({"no": len(maclar) + 1, "sol": a, "sag": b, "kazanan": None})
    if cift_yonlu:
        for a, b in itertools.combinations(sozluk, 2):
            maclar.append({"no": len(maclar) + 1, "sol": b, "sag": a, "kazanan": None})
    veri = {"sema_surumu": 1, "ad": ad, "olusturma": dt.datetime.now().replace(microsecond=0).isoformat(),
            "adaylar": sozluk, "maclar": maclar}
    yaz(proje, ad, veri)
    return veri


def aday_yolu(proje: Path, dosya: str) -> Path:
    yol = Path(dosya)
    return yol if yol.is_absolute() else proje / yol


def sirada(veri: dict[str, Any]) -> dict[str, Any] | None:
    return next((m for m in veri["maclar"] if m.get("kazanan") is None), None)


def hakem_yonergesi(veri: dict[str, Any], mac: dict[str, Any]) -> str:
    sol, sag = veri["adaylar"][mac["sol"]], veri["adaylar"][mac["sag"]]
    olcut = "\n".join(f"{i}. {o}" for i, o in enumerate(OLCUTLER, 1))
    return (f"Maç {mac['no']}/{len(veri['maclar'])}: {mac['sol']} ile {mac['sag']}\n\n"
            f"SOL ({mac['sol']}): {sol['dosya']}\nSAĞ ({mac['sag']}): {sag['dosya']}\n\n"
            "İki taslağı baştan sona okuyun. Uzunluk ya da sıra sizi etkilemesin; hangisi okuru daha iyi taşıyor?\n"
            f"Ölçütler (önem sırasıyla):\n{olcut}\n\n"
            "Önce her ölçüt için bir cümlelik karşılaştırma yazın, sonra tek bir karar verin: "
            f"{mac['sol']}, {mac['sag']} ya da berabere.\n"
            f"Kaydetmek için: turnuva.py sonuc --proje ... --ad {veri['ad']} --mac {mac['no']} --kazanan <ETİKET|berabere> "
            "--gerekce \"...\"")


def sonuc_kaydet(proje: Path, ad: str, mac_no: int, kazanan: str, gerekce: str = "") -> dict[str, Any]:
    veri = oku(proje, ad)
    mac = next((m for m in veri["maclar"] if m.get("no") == mac_no), None)
    if mac is None:
        raise TurnuvaHatasi(f"{mac_no} numaralı maç yok (1–{len(veri['maclar'])})")
    kazanan = kazanan.strip()
    if kazanan.lower() == "berabere":
        kazanan = "berabere"
    elif kazanan not in (mac["sol"], mac["sag"]):
        raise TurnuvaHatasi(f"kazanan {mac['sol']}, {mac['sag']} ya da berabere olmalı")
    for etiket in (mac["sol"], mac["sag"]):
        aday = veri["adaylar"][etiket]
        yol = aday_yolu(proje, aday["dosya"])
        if not yol.is_file() or _ozet(yol) != aday["ozet"]:
            raise TurnuvaHatasi(f"{etiket} adayının dosyası turnuva başladıktan sonra değişti ya da silindi: {yol}. "
                                "Yeni sürüm için yeni turnuva başlatın.")
    mac["kazanan"] = kazanan
    mac["gerekce"] = gerekce.strip()[:2000]
    mac["zaman"] = dt.datetime.now().replace(microsecond=0).isoformat()
    yaz(proje, ad, veri)
    return mac


def siralama(veri: dict[str, Any]) -> list[dict[str, Any]]:
    puan = {e: BASLANGIC for e in veri["adaylar"]}
    kayit = {e: {"galibiyet": 0, "maglubiyet": 0, "beraberlik": 0} for e in veri["adaylar"]}
    for m in veri["maclar"]:
        if m.get("kazanan") is None:
            continue
        a, b = m["sol"], m["sag"]
        if a not in puan or b not in puan:
            continue
        beklenen_a = 1 / (1 + 10 ** ((puan[b] - puan[a]) / 400))
        skor_a = 0.5 if m["kazanan"] == "berabere" else (1.0 if m["kazanan"] == a else 0.0)
        puan[a] += K * (skor_a - beklenen_a)
        puan[b] += K * ((1 - skor_a) - (1 - beklenen_a))
        if skor_a == 0.5:
            kayit[a]["beraberlik"] += 1
            kayit[b]["beraberlik"] += 1
        else:
            kazanan, kaybeden = (a, b) if skor_a == 1.0 else (b, a)
            kayit[kazanan]["galibiyet"] += 1
            kayit[kaybeden]["maglubiyet"] += 1
    sonuc = [{"etiket": e, "elo": round(puan[e]), "dosya": veri["adaylar"][e]["dosya"], **kayit[e]} for e in puan]
    sonuc.sort(key=lambda x: (-x["elo"], -x["galibiyet"], x["etiket"]))
    return sonuc


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Bölüm turnuvası: taslakları ikili karşılaştırıp Elo ile sırala.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_b = alt.add_parser("baslat", help="yeni turnuva kur")
    p_b.add_argument("--aday", action="append", required=True, help="ETİKET=dosya (en az iki kez)")
    p_b.add_argument("--tek-yonlu", action="store_true", help="her çifti yalnızca bir kez eşleştir")
    p_s = alt.add_parser("sirada", help="sıradaki maçı ve hakem yönergesini göster")
    p_r = alt.add_parser("sonuc", help="bir maçın sonucunu kaydet")
    p_r.add_argument("--mac", type=int, required=True, help="maç numarası")
    p_r.add_argument("--kazanan", required=True, help="kazanan adayın etiketi ya da 'berabere'")
    p_r.add_argument("--gerekce", default="", help="kararın kısa gerekçesi")
    p_g = alt.add_parser("siralama", help="Elo sıralamasını göster")
    p_g.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_l = alt.add_parser("listele", help="projedeki turnuvaları listele")
    for p in (p_b, p_s, p_r, p_g, p_l):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    for p in (p_b, p_s, p_r, p_g):
        p.add_argument("--ad", required=True, help="turnuva adı (ör. bolum-007)")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "baslat":
            veri = baslat(arg.proje, arg.ad, arg.aday, not arg.tek_yonlu)
            print(f"Turnuva kuruldu: {arg.ad} ({len(veri['adaylar'])} aday, {len(veri['maclar'])} maç)\n")
            print(hakem_yonergesi(veri, veri["maclar"][0]))
        elif arg.komut == "sirada":
            veri = oku(arg.proje, arg.ad)
            mac = sirada(veri)
            if mac is None:
                print("Bütün maçlar oynandı; 'siralama' komutuyla sonucu görün.")
                return 1
            print(hakem_yonergesi(veri, mac))
        elif arg.komut == "sonuc":
            mac = sonuc_kaydet(arg.proje, arg.ad, arg.mac, arg.kazanan, arg.gerekce)
            kalan = sum(1 for m in oku(arg.proje, arg.ad)["maclar"] if m.get("kazanan") is None)
            print(f"Maç {mac['no']} kaydedildi: {mac['kazanan']}. Kalan maç: {kalan}")
        elif arg.komut == "siralama":
            veri = oku(arg.proje, arg.ad)
            liste = siralama(veri)
            oynanan = sum(1 for m in veri["maclar"] if m.get("kazanan") is not None)
            if arg.json:
                print(json.dumps({"oynanan": oynanan, "toplam": len(veri["maclar"]), "siralama": liste},
                                 ensure_ascii=False, indent=2))
            else:
                print(f"{arg.ad}: {oynanan}/{len(veri['maclar'])} maç oynandı")
                for i, x in enumerate(liste, 1):
                    print(f"{i}. {x['etiket']:<6} Elo {x['elo']:>5}  {x['galibiyet']}G {x['beraberlik']}B "
                          f"{x['maglubiyet']}M  {x['dosya']}")
                if oynanan < len(veri["maclar"]):
                    print("Not: bütün maçlar oynanmadan sıralama kesin değildir.")
        else:
            klasor = kitap_proje.proje_klasoru(arg.proje) / ".hikaye" / "turnuvalar"
            adlar = sorted(y.stem for y in klasor.glob("*.json")) if klasor.is_dir() else []
            print("\n".join(adlar) if adlar else "Henüz turnuva yok.")
    except (TurnuvaHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
