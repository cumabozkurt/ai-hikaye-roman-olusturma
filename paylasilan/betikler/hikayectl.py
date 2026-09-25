#!/usr/bin/env python3
"""Uzun roman yazımının tek komut noktası: ölç, denetle, kaydet.

Komutlar::

    hikayectl.py uzunluk olc     --dosya METIN
    hikayectl.py uzunluk kontrol --dosya METIN --hedef 2200
    hikayectl.py bolum denetle   --proje KITAP --bolum 7 [--yazar-onayladi]
    hikayectl.py bolum kaydet    --proje KITAP --bolum 7 --girdi islem.json [--yazar-onayladi]

``bolum denetle`` sert kapıları çalıştırır: plan sözleşmesi, metin dosyası,
bozulma, yapay zekâ kalıpları (engelleyiciler), uzunluk bandı ve önceki
bölümün takibe kaydedilmiş olması. ``bolum kaydet`` önce denetler, sonra
uzunluk kaydını işleme ekleyip ``takip_kaydet.uygula`` ile tek seferde işler
ve bölümün çalışma klasörünü siler.

Çıkış: 0 geçti/kaydedildi, 1 kapı kaldı, 2 hatalı girdi.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_kalip_denetle  # noqa: E402
import bozulma_denetle  # noqa: E402
import metin_olcum  # noqa: E402
import plan_denetle  # noqa: E402
import takip_kaydet  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass


def cikti(belge: dict[str, Any], kod: int) -> int:
    print(json.dumps(belge, ensure_ascii=False, indent=2))
    return kod


def bolum_denetle(proje: Path, bolum: int, *, yazar_onayladi: bool = False) -> dict[str, Any]:
    kapilar: list[dict[str, Any]] = []

    def kapi(ad: str, tamam: bool, ayrinti: Any, onem: str = "engelleyici") -> None:
        kapilar.append({"kapi": ad, "tamam": tamam, "onem": onem, "ayrinti": ayrinti})

    try:
        plan = metin_olcum.bolum_dosyasi_bul(proje / "plan", bolum, plan=True)
        sozlesme = [c for c in plan_denetle.sozlesme_denetle(plan) if not c["tamam"] and c["onem"] == "engelleyici"]
        kapi("plan-sozlesmesi", not sozlesme, [f"{c['id']}: {c['onarim']}" for c in sozlesme])
    except metin_olcum.OlcumHatasi as hata:
        plan = None
        kapi("plan-sozlesmesi", False, str(hata))
    try:
        metin_yolu = metin_olcum.bolum_dosyasi_bul(proje / "metin", bolum, plan=False)
    except metin_olcum.OlcumHatasi as hata:
        kapi("metin-dosyasi", False, str(hata))
        return {"tamam": False, "bolum": bolum, "kapilar": kapilar}
    kapi("metin-dosyasi", True, str(metin_yolu))
    metin = metin_yolu.read_text(encoding="utf-8")
    bozulma = [b for b in bozulma_denetle.denetle_metin(metin, str(metin_yolu)) if b.onem == "engelleyici"]
    kapi("bozulma", not bozulma, [f"{b.satir}. satır {b.kural}: {b.oneri}" for b in bozulma])
    kaliplar = [b for b in ai_kalip_denetle.denetle_metin(metin, str(metin_yolu), beyaz=ai_kalip_denetle.beyaz_liste_yukle(metin_yolu))
                if b.onem == "engelleyici"]
    kapi("yz-kaliplari", not kaliplar, [f"{b.satir}. satır {b.kural}: {b.oneri}" for b in kaliplar])
    if plan is not None:
        try:
            deger = metin_olcum.uzunluk_degerlendir(metin_olcum.kelime_say(metin), metin_olcum.plandan_hedef(plan.read_text(encoding="utf-8")))
            durum = deger["durum"]
            if durum == "ic_gecti":
                kapi("uzunluk", True, deger)
            elif durum in {"kisa", "uzun"}:
                kapi("uzunluk", yazar_onayladi, {**deger, "not": "iç bandın dışında; genişletin/kısaltın ya da yazar onayıyla --yazar-onayladi"})
            else:
                kapi("uzunluk", False, {**deger, "not": "sert sınırın dışında; bölümü yeniden yazın"})
        except metin_olcum.OlcumHatasi as hata:
            kapi("uzunluk", False, str(hata))
        kopya = plan_denetle.kopya_denetle(plan, metin_yolu)
        kapi("plan-kopyasi", bool(kopya["tamam"]), kopya)
    durum_yolu = takip_kaydet.durum_yolu(proje)
    if bolum > 1:
        if durum_yolu.exists():
            son = takip_kaydet.durumu_yukle(proje)["son_kaydedilen_bolum"]
            kapi("onceki-bolum-kaydi", son >= bolum - 1, f"son kaydedilen bölüm: {son}")
        else:
            kapi("onceki-bolum-kaydi", False, "takip durumu yok; takip_kaydet.py baslat")
    return {"tamam": all(k["tamam"] for k in kapilar if k["onem"] == "engelleyici"), "bolum": bolum, "kapilar": kapilar}


def bolum_kaydet(proje: Path, bolum: int, girdi: Path, *, yazar_onayladi: bool = False) -> tuple[dict[str, Any], int]:
    rapor = bolum_denetle(proje, bolum, yazar_onayladi=yazar_onayladi)
    if not rapor["tamam"]:
        return {"tamam": False, "takip_kaydedildi": False, "denetim": rapor}, 1
    belge = json.loads(girdi.read_text(encoding="utf-8"))
    if not isinstance(belge, dict):
        raise takip_kaydet.TakipHatasi("işlem JSON nesnesi olmalı")
    if belge.get("bolum") != bolum:
        raise takip_kaydet.TakipHatasi(f"işlemdeki bölüm ({belge.get('bolum')}) komuttaki bölümle ({bolum}) aynı değil")
    try:
        belge["uzunluk"] = metin_olcum.proje_uzunluk_kaydi(proje, bolum, cozum="yazar_onayladi" if yazar_onayladi else "hedef_bandinda")
    except metin_olcum.OlcumHatasi as hata:
        raise takip_kaydet.TakipHatasi(str(hata)) from hata
    sonuc = takip_kaydet.uygula(proje, belge)
    calisma = proje / ".hikaye" / "calisma" / f"bolum-{bolum:03d}"
    if calisma.is_dir():
        shutil.rmtree(calisma)
        sonuc["calisma_klasoru_silindi"] = str(calisma)
    return sonuc, 0


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    komutlar = ayr.add_subparsers(dest="grup", required=True)
    uzunluk = komutlar.add_parser("uzunluk").add_subparsers(dest="komut", required=True)
    olc = uzunluk.add_parser("olc")
    olc.add_argument("--dosya", required=True, type=Path)
    kontrol = uzunluk.add_parser("kontrol")
    kontrol.add_argument("--dosya", required=True, type=Path)
    kontrol.add_argument("--hedef", required=True)
    bolum = komutlar.add_parser("bolum").add_subparsers(dest="komut", required=True)
    for ad in ("denetle", "kaydet"):
        p = bolum.add_parser(ad)
        p.add_argument("--proje", required=True, type=Path)
        p.add_argument("--bolum", required=True, type=int)
        p.add_argument("--yazar-onayladi", action="store_true", help="iç band dışındaki uzunluğu yazar onayladı")
        if ad == "kaydet":
            p.add_argument("--girdi", required=True, type=Path)
    arg = ayr.parse_args(argv)
    try:
        if arg.grup == "uzunluk":
            metin = arg.dosya.read_text(encoding="utf-8")
            sayi = metin_olcum.kelime_say(metin)
            if arg.komut == "olc":
                return cikti({"dosya": str(arg.dosya), "olcu": metin_olcum.OLCU, "kelime": sayi}, 0)
            deger = metin_olcum.uzunluk_degerlendir(sayi, arg.hedef)
            return cikti(deger, 0 if deger["durum"] == "ic_gecti" else 1)
        if arg.komut == "denetle":
            rapor = bolum_denetle(arg.proje, arg.bolum, yazar_onayladi=arg.yazar_onayladi)
            return cikti(rapor, 0 if rapor["tamam"] else 1)
        sonuc, kod = bolum_kaydet(arg.proje, arg.bolum, arg.girdi, yazar_onayladi=arg.yazar_onayladi)
        return cikti(sonuc, kod)
    except (OSError, ValueError) as hata:
        return cikti({"tamam": False, "hata": str(hata)}, 2)


if __name__ == "__main__":
    sys.exit(main())
