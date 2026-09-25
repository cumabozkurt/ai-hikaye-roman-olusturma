#!/usr/bin/env python3
"""Tek yapılandırılmış hikâye durumu ve ondan türetilen Markdown görünümleri.

Dil modeli yalnızca küçük, anlamsal bir JSON (işlem) verir. Bu araç işlemi
doğrular, bellekte birleştirir, bütün türetilmiş görünümleri yeniden üretir ve
en son ``takip/_takip-durumu.json`` dosyasını atomik olarak yazar; tek kayıt
noktası odur. Proje başına kilit, aynı anda çalışan yazarları sıraya sokar.

Komutlar::

    baslat   --proje KITAP --girdi baslangic.json   # ilk durum (içe aktarma / yeni kitap)
    uygula   --proje KITAP --girdi islem.json       # bir bölümün değişimini işle
    denetle  --proje KITAP                          # görünümler elle bozulmuş mu?
    goster   --proje KITAP                          # kısa özet
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

_OLCUM_YOLU = Path(__file__).with_name("metin_olcum.py")
_spec = importlib.util.spec_from_file_location("hikaye_metin_olcum", _OLCUM_YOLU)
if _spec is None or _spec.loader is None:  # pragma: no cover - bozuk kurulum
    raise RuntimeError("ARAC_YOK: metin_olcum.py")
metin_olcum = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(metin_olcum)

GIRDI_SEMA_SURUMU = 1
DURUM_SEMA_SURUMU = 1
BAGLAM_AZAMI_BAYT = 12288
ANLIK_AZAMI_BAYT = 8192
KAYIT_AZAMI_BAYT = 4096

BAGLAM_BASLIKLARI = (
    "## Şu Anki Konum",
    "## Kalıcı Kısıtlar",
    "## Ana Karakterlerin Durumu",
    "## Açık İpuçları",
    "## Son Üç Bölüm",
    "## Sonraki Bölüm Sözleri",
    "## Süreklilik Riskleri",
)
IPUCU_DURUMLARI = ("ekili", "çözüldü", "süresi geçti", "vazgeçildi")
IPUCU_ONEMI = ("yüksek", "orta", "düşük")
ACIGA_CIKMA = ("gizli", "kısmen", "açık")
YASAM_DURUMLARI = ("hayatta", "öldü", "kayıp", "bilinmiyor")
GECERSIZ_DOSYA_KARAKTERI = re.compile(r"[<>:\"/\\|?*\x00-\x1f]")
IPUCU_KIMLIGI = re.compile(r"^F\d{3,}$")
OLAY_KIMLIGI = re.compile(r"^E\d{3,}$")
WINDOWS_AYRILMIS = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
ANLIK_ALANLARI = {
    "kimlik", "durum", "hedef", "konum", "yasam_durumu",
    "bildikleri", "yetenek_ve_kaynaklar", "iliskiler", "acik_meseleler",
}


class TakipHatasi(ValueError):
    """Beklenen doğrulama veya takip durumu hatası."""


# ---------------------------------------------------------------- yardımcılar

def gerekli(kosul: bool, mesaj: str) -> None:
    if not kosul:
        raise TakipHatasi(mesaj)


def sozluk(deger: object, etiket: str) -> dict[str, Any]:
    gerekli(isinstance(deger, dict), f"{etiket} bir nesne olmalı")
    return deger  # type: ignore[return-value]


def liste(deger: object, etiket: str) -> list[Any]:
    gerekli(isinstance(deger, list), f"{etiket} bir liste olmalı")
    return deger  # type: ignore[return-value]


def tamsayi(deger: object, etiket: str, *, en_az: int = 0) -> int:
    gerekli(isinstance(deger, int) and not isinstance(deger, bool), f"{etiket} tamsayı olmalı")
    gerekli(deger >= en_az, f"{etiket} en az {en_az} olmalı")  # type: ignore[operator]
    return deger  # type: ignore[return-value]


def bilinen_anahtarlar(nesne: dict[str, Any], izinli: set[str], etiket: str) -> None:
    fazla = sorted(set(nesne) - izinli)
    gerekli(not fazla, f"{etiket} bilinmeyen alan içeriyor: {', '.join(fazla)}")


def temiz_metin(deger: object, etiket: str, *, bos_olabilir: bool = False, azami_bayt: int = 768) -> str:
    gerekli(isinstance(deger, str), f"{etiket} metin olmalı")
    metin = " ".join(str(deger).split())
    gerekli(bos_olabilir or bool(metin), f"{etiket} boş olamaz")
    gerekli(len(metin.encode("utf-8")) <= azami_bayt, f"{etiket} {azami_bayt} baytı aşıyor")
    return metin


def temiz_liste(deger: object, etiket: str, *, azami: int = 12, azami_bayt: int = 360) -> list[str]:
    ogeler = [temiz_metin(o, f"{etiket}[{i}]", azami_bayt=azami_bayt) for i, o in enumerate(liste(deger, etiket))]
    gerekli(len(ogeler) <= azami, f"{etiket} en fazla {azami} öğe içerebilir")
    gerekli(len(set(ogeler)) == len(ogeler), f"{etiket} yinelenen öğe içeriyor")
    return ogeler


def guvenli_dosya_adi(deger: object, etiket: str) -> str:
    ad = temiz_metin(deger, etiket, azami_bayt=120)
    gerekli(not GECERSIZ_DOSYA_KARAKTERI.search(ad), f"{etiket} dosya adında kullanılamayan karakter içeriyor")
    gerekli(ad not in {".", ".."} and not ad.endswith((".", " ")), f"{etiket} geçerli bir dosya adı değil")
    gerekli(ad.upper().split(".")[0] not in WINDOWS_AYRILMIS, f"{etiket} Windows'ta ayrılmış bir ad")
    return ad


def tasinabilir_anahtar(ad: str) -> str:
    """Büyük/küçük harf ve Unicode biçimi farkını yok sayan karşılaştırma anahtarı."""
    return unicodedata.normalize("NFC", ad).casefold()


def bayt(metin: str) -> int:
    return len(metin.encode("utf-8"))


def json_oku(yol: Path) -> object:
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError as hata:
        raise TakipHatasi(f"{yol} geçerli JSON değil: {hata}") from hata


def json_metni(belge: object) -> str:
    return json.dumps(belge, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomik_yaz(yol: Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(prefix=f".{yol.name}.", suffix=".tmp", dir=str(yol.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as akis:
            akis.write(icerik)
            akis.flush()
            os.fsync(akis.fileno())
        os.replace(gecici, yol)
    except BaseException:
        Path(gecici).unlink(missing_ok=True)
        raise


def degistiyse_yaz(yol: Path, icerik: str) -> None:
    if yol.exists() and yol.read_text(encoding="utf-8") == icerik:
        return
    atomik_yaz(yol, icerik)


def takip_koku(proje: Path) -> Path:
    return proje / "takip"


def durum_yolu(proje: Path) -> Path:
    return takip_koku(proje) / "_takip-durumu.json"


@contextmanager
def proje_kilidi(proje: Path, *, zaman_asimi: float = 10.0) -> Iterator[None]:
    kilit = takip_koku(proje) / ".kilit"
    kilit.parent.mkdir(parents=True, exist_ok=True)
    bitis = time.monotonic() + zaman_asimi
    while True:
        try:
            fd = os.open(str(kilit), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            # 10 dakikadan eski kilit, çökmüş bir süreçten kalmıştır.
            try:
                if time.time() - kilit.stat().st_mtime > 600:
                    kilit.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            gerekli(time.monotonic() < bitis, "takip kilidi alınamadı; başka bir yazma işlemi sürüyor")
            time.sleep(0.05)
    try:
        yield
    finally:
        kilit.unlink(missing_ok=True)


# ------------------------------------------------------------ normalleştirme

def konum_dogrula(deger: object, etiket: str = "baglam.konum") -> dict[str, Any]:
    konum = sozluk(deger, etiket)
    bilinen_anahtarlar(konum, {"cilt", "cilt_baslangic_bolumu", "hikaye_zamani", "sahne"}, etiket)
    return {
        "cilt": temiz_metin(konum.get("cilt"), f"{etiket}.cilt", azami_bayt=160),
        "cilt_baslangic_bolumu": tamsayi(konum.get("cilt_baslangic_bolumu", 1), f"{etiket}.cilt_baslangic_bolumu", en_az=1),
        "hikaye_zamani": temiz_metin(konum.get("hikaye_zamani"), f"{etiket}.hikaye_zamani", azami_bayt=200),
        "sahne": temiz_metin(konum.get("sahne"), f"{etiket}.sahne", azami_bayt=240),
    }


def anlik_normallestir(deger: object, etiket: str) -> dict[str, Any]:
    anlik = sozluk(deger, etiket)
    bilinen_anahtarlar(anlik, ANLIK_ALANLARI, etiket)
    yasam = str(anlik.get("yasam_durumu", "hayatta"))
    gerekli(yasam in YASAM_DURUMLARI, f"{etiket}.yasam_durumu şunlardan biri olmalı: {', '.join(YASAM_DURUMLARI)}")
    sonuc = {
        "kimlik": temiz_metin(anlik.get("kimlik"), f"{etiket}.kimlik", azami_bayt=240),
        "durum": temiz_metin(anlik.get("durum"), f"{etiket}.durum", azami_bayt=360),
        "hedef": temiz_metin(anlik.get("hedef"), f"{etiket}.hedef", azami_bayt=360),
        "konum": temiz_metin(anlik.get("konum", "belirsiz"), f"{etiket}.konum", azami_bayt=200),
        "yasam_durumu": yasam,
        "bildikleri": temiz_liste(anlik.get("bildikleri", []), f"{etiket}.bildikleri", azami=8),
        "yetenek_ve_kaynaklar": temiz_liste(anlik.get("yetenek_ve_kaynaklar", []), f"{etiket}.yetenek_ve_kaynaklar", azami=8),
        "iliskiler": temiz_liste(anlik.get("iliskiler", []), f"{etiket}.iliskiler", azami=8),
        "acik_meseleler": temiz_liste(anlik.get("acik_meseleler", []), f"{etiket}.acik_meseleler", azami=6),
    }
    return sonuc


def anliklari_normallestir(deger: object, etiket: str = "karakter_anliklari") -> dict[str, dict[str, Any]]:
    ham = sozluk(deger, etiket)
    sonuc: dict[str, dict[str, Any]] = {}
    anahtarlar: set[str] = set()
    for ad, anlik in ham.items():
        guvenli = guvenli_dosya_adi(ad, f"{etiket} anahtarı")
        anahtar = tasinabilir_anahtar(guvenli)
        gerekli(anahtar not in anahtarlar, f"{etiket} içinde '{guvenli}' iki kez geçiyor (büyük/küçük harf farkı)")
        anahtarlar.add(anahtar)
        sonuc[guvenli] = anlik_normallestir(anlik, f"{etiket}.{guvenli}")
    return sonuc


def ipucu_degisimi(deger: object, etiket: str, *, silinebilir: bool, son_bolum: int) -> dict[str, Any]:
    ham = sozluk(deger, etiket)
    islem = str(ham.get("islem", "guncelle"))
    gerekli(islem in ({"ekle", "guncelle", "sil"} if silinebilir else {"ekle", "guncelle"}), f"{etiket}.islem geçersiz")
    kimlik = str(ham.get("id", ""))
    gerekli(bool(IPUCU_KIMLIGI.match(kimlik)), f"{etiket}.id F001 biçiminde olmalı")
    if islem == "sil":
        bilinen_anahtarlar(ham, {"islem", "id"}, etiket)
        return {"islem": "sil", "id": kimlik}
    bilinen_anahtarlar(ham, {"islem", "id", "ozet", "onem", "durum", "ekildigi_bolum", "planlanan_cozum_bolumu"}, etiket)
    onem = str(ham.get("onem", "orta"))
    durum = str(ham.get("durum", "ekili"))
    gerekli(onem in IPUCU_ONEMI, f"{etiket}.onem şunlardan biri olmalı: {', '.join(IPUCU_ONEMI)}")
    gerekli(durum in IPUCU_DURUMLARI, f"{etiket}.durum şunlardan biri olmalı: {', '.join(IPUCU_DURUMLARI)}")
    ekildigi = tamsayi(ham.get("ekildigi_bolum"), f"{etiket}.ekildigi_bolum", en_az=1)
    gerekli(son_bolum == 0 or ekildigi <= son_bolum, f"{etiket}.ekildigi_bolum henüz yazılmamış bir bölüm")
    plan = ham.get("planlanan_cozum_bolumu")
    if plan is not None:
        plan = tamsayi(plan, f"{etiket}.planlanan_cozum_bolumu", en_az=1)
    return {
        "islem": islem,
        "id": kimlik,
        "ozet": temiz_metin(ham.get("ozet"), f"{etiket}.ozet", azami_bayt=360),
        "onem": onem,
        "durum": durum,
        "ekildigi_bolum": ekildigi,
        "planlanan_cozum_bolumu": plan,
    }


def olay_degisimi(deger: object, etiket: str, *, silinebilir: bool, son_bolum: int) -> dict[str, Any]:
    ham = sozluk(deger, etiket)
    islem = str(ham.get("islem", "guncelle"))
    gerekli(islem in ({"ekle", "guncelle", "sil"} if silinebilir else {"ekle", "guncelle"}), f"{etiket}.islem geçersiz")
    kimlik = str(ham.get("id", ""))
    gerekli(bool(OLAY_KIMLIGI.match(kimlik)), f"{etiket}.id E001 biçiminde olmalı")
    if islem == "sil":
        bilinen_anahtarlar(ham, {"islem", "id"}, etiket)
        return {"islem": "sil", "id": kimlik}
    bilinen_anahtarlar(
        ham,
        {"islem", "id", "nesnel_olgu", "okur_bilgisi", "hikaye_zamani", "karakterler", "aciga_cikma", "acilma_bolumu", "anahtar_kelimeler"},
        etiket,
    )
    aciga = str(ham.get("aciga_cikma", "gizli"))
    gerekli(aciga in ACIGA_CIKMA, f"{etiket}.aciga_cikma şunlardan biri olmalı: {', '.join(ACIGA_CIKMA)}")
    acilma = ham.get("acilma_bolumu")
    if aciga == "gizli":
        gerekli(acilma is None, f"{etiket}: gizli olayın açılma bölümü olamaz")
    else:
        acilma = tamsayi(acilma, f"{etiket}.acilma_bolumu", en_az=1)
        gerekli(son_bolum == 0 or acilma <= son_bolum, f"{etiket}.acilma_bolumu henüz yazılmamış bir bölüm")
    return {
        "islem": islem,
        "id": kimlik,
        "nesnel_olgu": temiz_metin(ham.get("nesnel_olgu"), f"{etiket}.nesnel_olgu", azami_bayt=480),
        "okur_bilgisi": temiz_metin(ham.get("okur_bilgisi", ""), f"{etiket}.okur_bilgisi", bos_olabilir=True, azami_bayt=360),
        "hikaye_zamani": temiz_metin(ham.get("hikaye_zamani", "belirsiz"), f"{etiket}.hikaye_zamani", azami_bayt=160),
        "karakterler": temiz_liste(ham.get("karakterler", []), f"{etiket}.karakterler", azami=8, azami_bayt=120),
        "aciga_cikma": aciga,
        "acilma_bolumu": acilma,
        "anahtar_kelimeler": temiz_liste(ham.get("anahtar_kelimeler", []), f"{etiket}.anahtar_kelimeler", azami=6, azami_bayt=80),
    }


def baglam_girdisi(deger: object, *, ilk: bool) -> dict[str, Any]:
    baglam = sozluk(deger, "baglam")
    izinli = {"konum", "kalici_kisitlar", "aktif_karakterler", "sureklilik_riskleri"}
    if ilk:
        izinli |= {"son_bolumler", "sonraki_bolum_sozleri"}
    bilinen_anahtarlar(baglam, izinli, "baglam")
    sonuc: dict[str, Any] = {
        "konum": konum_dogrula(baglam.get("konum")),
        "kalici_kisitlar": temiz_liste(baglam.get("kalici_kisitlar", []), "baglam.kalici_kisitlar", azami=6),
        "aktif_karakterler": [
            guvenli_dosya_adi(ad, f"baglam.aktif_karakterler[{i}]")
            for i, ad in enumerate(liste(baglam.get("aktif_karakterler", []), "baglam.aktif_karakterler"))
        ],
        "sureklilik_riskleri": temiz_liste(baglam.get("sureklilik_riskleri", []), "baglam.sureklilik_riskleri", azami=5),
    }
    gerekli(len(sonuc["aktif_karakterler"]) <= 6, "baglam.aktif_karakterler en fazla 6 ad içerebilir")
    gerekli(
        len({tasinabilir_anahtar(a) for a in sonuc["aktif_karakterler"]}) == len(sonuc["aktif_karakterler"]),
        "baglam.aktif_karakterler yinelenen ad içeriyor",
    )
    if ilk:
        son = []
        for i, ham in enumerate(liste(baglam.get("son_bolumler", []), "baglam.son_bolumler")):
            oge = sozluk(ham, f"baglam.son_bolumler[{i}]")
            bilinen_anahtarlar(oge, {"bolum", "ozet"}, f"baglam.son_bolumler[{i}]")
            son.append({
                "bolum": tamsayi(oge.get("bolum"), f"baglam.son_bolumler[{i}].bolum", en_az=1),
                "ozet": temiz_metin(oge.get("ozet"), f"baglam.son_bolumler[{i}].ozet", azami_bayt=360),
            })
        gerekli(len(son) <= 3, "baglam.son_bolumler en fazla 3 öğe içerebilir")
        sonuc["son_bolumler"] = son
        sonuc["sonraki_bolum_sozleri"] = temiz_liste(baglam.get("sonraki_bolum_sozleri", []), "baglam.sonraki_bolum_sozleri", azami=5)
    return sonuc


def durumu_normallestir(belge: object) -> dict[str, Any]:
    kok = sozluk(belge, "takip durumu")
    bilinen_anahtarlar(
        kok,
        {"sema_surumu", "kitap_adi", "son_kaydedilen_bolum", "ice_aktarilan_son_bolum", "durum_revizyonu",
         "baglam", "karakterler", "ipuclari", "zaman_cizelgesi", "uzunluk_kayitlari"},
        "takip durumu",
    )
    gerekli(kok.get("sema_surumu") == DURUM_SEMA_SURUMU, "takip durumu şema sürümü desteklenmiyor")
    son = tamsayi(kok.get("son_kaydedilen_bolum"), "son_kaydedilen_bolum")
    baglam = baglam_girdisi(kok.get("baglam"), ilk=True)
    karakterler = anliklari_normallestir(kok.get("karakterler", {}), "karakterler")
    for ad in baglam["aktif_karakterler"]:
        gerekli(ad in karakterler, f"aktif karakter '{ad}' için anlık durum yok")
    ipuclari: dict[str, dict[str, Any]] = {}
    for kimlik, ham in sozluk(kok.get("ipuclari", {}), "ipuclari").items():
        satir = dict(sozluk(ham, f"ipuclari.{kimlik}"))
        guncellendigi = satir.pop("guncellendigi_bolum", son or 1)
        norm = ipucu_degisimi({**satir, "islem": "guncelle"}, f"ipuclari.{kimlik}", silinebilir=False, son_bolum=son)
        norm.pop("islem")
        gerekli(norm["id"] == kimlik, f"ipuclari.{kimlik} kimliği anahtarla uyuşmuyor")
        norm["guncellendigi_bolum"] = tamsayi(guncellendigi, f"ipuclari.{kimlik}.guncellendigi_bolum", en_az=1)
        ipuclari[kimlik] = norm
    zaman: dict[str, dict[str, Any]] = {}
    for kimlik, ham in sozluk(kok.get("zaman_cizelgesi", {}), "zaman_cizelgesi").items():
        olay = dict(sozluk(ham, f"zaman_cizelgesi.{kimlik}"))
        ilk_kayit = olay.pop("ilk_kayit_bolumu", son or 1)
        guncellendigi = olay.pop("guncellendigi_bolum", son or 1)
        norm = olay_degisimi({**olay, "islem": "guncelle"}, f"zaman_cizelgesi.{kimlik}", silinebilir=False, son_bolum=son)
        norm.pop("islem")
        gerekli(norm["id"] == kimlik, f"zaman_cizelgesi.{kimlik} kimliği anahtarla uyuşmuyor")
        norm["ilk_kayit_bolumu"] = tamsayi(ilk_kayit, f"zaman_cizelgesi.{kimlik}.ilk_kayit_bolumu", en_az=1)
        norm["guncellendigi_bolum"] = tamsayi(guncellendigi, f"zaman_cizelgesi.{kimlik}.guncellendigi_bolum", en_az=1)
        zaman[kimlik] = norm
    uzunluk = {str(k): dict(sozluk(v, f"uzunluk_kayitlari.{k}")) for k, v in sozluk(kok.get("uzunluk_kayitlari", {}), "uzunluk_kayitlari").items()}
    return {
        "sema_surumu": DURUM_SEMA_SURUMU,
        "kitap_adi": temiz_metin(kok.get("kitap_adi"), "kitap_adi", azami_bayt=240),
        "son_kaydedilen_bolum": son,
        "ice_aktarilan_son_bolum": tamsayi(kok.get("ice_aktarilan_son_bolum", 0), "ice_aktarilan_son_bolum"),
        "durum_revizyonu": tamsayi(kok.get("durum_revizyonu"), "durum_revizyonu"),
        "baglam": baglam,
        "karakterler": dict(sorted(karakterler.items())),
        "ipuclari": dict(sorted(ipuclari.items())),
        "zaman_cizelgesi": dict(sorted(zaman.items())),
        "uzunluk_kayitlari": dict(sorted(uzunluk.items(), key=lambda kv: int(kv[0]))),
    }


# ------------------------------------------------------------- görünümler

def _bolum(no: int | None, bos: str = "belirsiz") -> str:
    return f"{no}. bölüm" if no else bos


def acik_ipucu_satirlari(ipuclari: dict[str, dict[str, Any]]) -> list[str]:
    sira = {deger: i for i, deger in enumerate(IPUCU_ONEMI)}
    adaylar = [s for s in ipuclari.values() if s["durum"] == "ekili"]
    adaylar.sort(key=lambda s: (sira[s["onem"]], s["planlanan_cozum_bolumu"] or 10**9, s["id"]))
    return [
        f"{s['id']} | {s['ozet']} | ekildiği: {_bolum(s['ekildigi_bolum'])} | çözüm: "
        f"{_bolum(s['planlanan_cozum_bolumu'], 'henüz planlanmadı')} | önem: {s['onem']}"
        for s in adaylar[:8]
    ]


def baglam_gorunumu(durum: dict[str, Any]) -> str:
    baglam = durum["baglam"]
    konum = baglam["konum"]
    su_an = "henüz başlanmadı" if durum["son_kaydedilen_bolum"] == 0 else f"{durum['son_kaydedilen_bolum']}. bölüm"
    karakter_satirlari = []
    for ad in baglam["aktif_karakterler"]:
        k = durum["karakterler"][ad]
        yasam = "" if k["yasam_durumu"] == "hayatta" else f" | yaşam: {k['yasam_durumu']}"
        karakter_satirlari.append(f"{ad} | {k['kimlik']} | {k['durum']} | hedef: {k['hedef']}{yasam}")
    bolumler: list[tuple[str, list[str]]] = [
        ("## Şu Anki Konum", [
            f"Şu anki bölüm: {su_an}",
            f"Cilt: {konum['cilt']} ({konum['cilt_baslangic_bolumu']}. bölümde başladı)",
            f"Hikâye zamanı: {konum['hikaye_zamani']}",
            f"Sahne: {konum['sahne']}",
        ]),
        ("## Kalıcı Kısıtlar", baglam["kalici_kisitlar"]),
        ("## Ana Karakterlerin Durumu", karakter_satirlari),
        ("## Açık İpuçları", acik_ipucu_satirlari(durum["ipuclari"])),
        ("## Son Üç Bölüm", [f"{o['bolum']}. bölüm | {o['ozet']}" for o in baglam["son_bolumler"]]),
        ("## Sonraki Bölüm Sözleri", baglam["sonraki_bolum_sozleri"]),
        ("## Süreklilik Riskleri", baglam["sureklilik_riskleri"]),
    ]
    satirlar = [
        f"# Yazım Sürekliliği Bağlamı — {durum['kitap_adi']}",
        "",
        f"> Durum revizyonu: {durum['durum_revizyonu']}. Bu dosya _takip-durumu.json dosyasından üretilir; elle düzenlemeyin.",
        "> Yalnızca bir sonraki bölümün gerçekten ihtiyaç duyduğu süreklilik bilgisini taşır.",
        "",
    ]
    for baslik, degerler in bolumler:
        satirlar.append(baslik)
        satirlar.extend(f"- {d}" for d in (degerler or ["yok"]))
        satirlar.append("")
    icerik = "\n".join(satirlar).rstrip() + "\n"
    basliklar = tuple(s for s in icerik.splitlines() if s.startswith("## "))
    gerekli(basliklar == BAGLAM_BASLIKLARI, "üretilen bağlam başlıkları yedi bölümlük şemayla uyuşmuyor")
    gerekli(bayt(icerik) <= BAGLAM_AZAMI_BAYT, f"bağlam dosyası {BAGLAM_AZAMI_BAYT} baytı aşıyor; özetleri kısaltın")
    return icerik


def ipucu_gorunumu(ipuclari: dict[str, dict[str, Any]], revizyon: int) -> str:
    satirlar = [
        "# İpuçları ve Ön Hazırlıklar",
        "",
        f"> Durum revizyonu: {revizyon}. _takip-durumu.json dosyasından üretilir; elle düzenlemeyin.",
        "",
        "| Kimlik | Özet | Önem | Durum | Ekildiği bölüm | Planlanan çözüm | Son güncelleme |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in ipuclari.values():
        ozet = s["ozet"].replace("|", "/")
        satirlar.append(
            f"| {s['id']} | {ozet} | {s['onem']} | {s['durum']} | {s['ekildigi_bolum']} | "
            f"{s['planlanan_cozum_bolumu'] or '—'} | {s['guncellendigi_bolum']} |"
        )
    if not ipuclari:
        satirlar.append("| — | Henüz ipucu yok | — | — | — | — | — |")
    return "\n".join(satirlar) + "\n"


def zaman_gorunumleri(olaylar: dict[str, dict[str, Any]], revizyon: int) -> tuple[str, str]:
    ust = f"> Durum revizyonu: {revizyon}. _takip-durumu.json dosyasından üretilir; elle düzenlemeyin."
    yazar = ["# Zaman Çizelgesi — Yazarın Bildiği Gerçek", "", ust, "",
             "Okurun henüz görmediği olaylar da buradadır. Bu dosyadaki bilgi, açığa çıkana kadar metne sızmamalıdır.", ""]
    okur = ["# Zaman Çizelgesi — Okurun Bildiği", "", ust, "",
            "Yalnızca metinde gösterilmiş (açık ya da kısmen açık) olaylar. Karakterler ve anlatıcı bundan fazlasını ima etmemeli.", ""]
    for o in olaylar.values():
        kisiler = ", ".join(o["karakterler"]) or "—"
        yazar.append(f"- **{o['id']}** ({o['hikaye_zamani']}) {o['nesnel_olgu']} — karakterler: {kisiler}; "
                     f"açığa çıkma: {o['aciga_cikma']}{'' if o['acilma_bolumu'] is None else ', ' + str(o['acilma_bolumu']) + '. bölüm'}")
        if o["aciga_cikma"] != "gizli":
            bilgi = o["okur_bilgisi"] or o["nesnel_olgu"]
            okur.append(f"- **{o['id']}** ({o['hikaye_zamani']}, {o['acilma_bolumu']}. bölümde {o['aciga_cikma']}) {bilgi}")
    if len(yazar) == 6:
        yazar.append("- Henüz olay kaydı yok.")
    if len(okur) == 6:
        okur.append("- Okura henüz hiçbir olay gösterilmedi.")
    return "\n".join(yazar) + "\n", "\n".join(okur) + "\n"


def anlik_gorunumu(ad: str, k: dict[str, Any], son_bolum: int, revizyon: int) -> str:
    def madde(baslik: str, ogeler: list[str]) -> list[str]:
        return [f"## {baslik}", *(f"- {o}" for o in (ogeler or ["yok"])), ""]

    satirlar = [
        f"# Karakter Durumu — {ad}",
        "",
        f"> {son_bolum}. bölüm itibarıyla. Durum revizyonu: {revizyon}. Elle düzenlemeyin.",
        "",
        f"- Kimlik: {k['kimlik']}",
        f"- Yaşam durumu: {k['yasam_durumu']}",
        f"- Şu anki durum: {k['durum']}",
        f"- Hedef: {k['hedef']}",
        f"- Konum: {k['konum']}",
        "",
        *madde("Bildikleri", k["bildikleri"]),
        *madde("Yetenek ve Kaynaklar", k["yetenek_ve_kaynaklar"]),
        *madde("İlişkiler", k["iliskiler"]),
        *madde("Açık Meseleler", k["acik_meseleler"]),
    ]
    icerik = "\n".join(satirlar).rstrip() + "\n"
    gerekli(bayt(icerik) <= ANLIK_AZAMI_BAYT, f"{ad} karakter durumu {ANLIK_AZAMI_BAYT} baytı aşıyor")
    return icerik


def gorunumleri_uret(durum: dict[str, Any]) -> dict[str, str]:
    rev = durum["durum_revizyonu"]
    gorunumler = {
        "baglam.md": baglam_gorunumu(durum),
        "ipuclari.md": ipucu_gorunumu(durum["ipuclari"], rev),
    }
    yazar, okur = zaman_gorunumleri(durum["zaman_cizelgesi"], rev)
    gorunumler["zaman-cizelgesi/yazar-gercegi.md"] = yazar
    gorunumler["zaman-cizelgesi/okur-bilgisi.md"] = okur
    for ad, anlik in durum["karakterler"].items():
        gorunumler[f"karakter-durumu/{ad}.md"] = anlik_gorunumu(ad, anlik, durum["son_kaydedilen_bolum"], rev)
    return gorunumler


def gorunumleri_yaz(takip: Path, gorunumler: dict[str, str]) -> None:
    for goreli, icerik in gorunumler.items():
        degistiyse_yaz(takip / goreli, icerik)
    klasor = takip / "karakter-durumu"
    if klasor.is_dir():
        beklenen = {Path(g).name for g in gorunumler if g.startswith("karakter-durumu/")}
        for dosya in klasor.glob("*.md"):
            if dosya.name not in beklenen:
                dosya.unlink()


# ---------------------------------------------------------------- işlemler

def baslangic_belgesi(belge: object) -> dict[str, Any]:
    kok = sozluk(belge, "başlangıç girdisi")
    bilinen_anahtarlar(kok, {"sema_surumu", "kitap_adi", "son_bolum", "baglam", "karakter_anliklari", "ipuclari", "zaman_olaylari"}, "başlangıç girdisi")
    gerekli(kok.get("sema_surumu") == GIRDI_SEMA_SURUMU, "başlangıç girdisinin sema_surumu desteklenmiyor")
    son = tamsayi(kok.get("son_bolum", 0), "son_bolum")
    ipuclari = {}
    for i, ham in enumerate(liste(kok.get("ipuclari", []), "ipuclari")):
        s = ipucu_degisimi(ham, f"ipuclari[{i}]", silinebilir=False, son_bolum=son)
        gerekli(s["id"] not in ipuclari, f"yinelenen ipucu kimliği {s['id']}")
        s.pop("islem")
        s["guncellendigi_bolum"] = max(1, son)
        ipuclari[s["id"]] = s
    zaman = {}
    for i, ham in enumerate(liste(kok.get("zaman_olaylari", []), "zaman_olaylari")):
        o = olay_degisimi(ham, f"zaman_olaylari[{i}]", silinebilir=False, son_bolum=son)
        gerekli(o["id"] not in zaman, f"yinelenen olay kimliği {o['id']}")
        o.pop("islem")
        o["ilk_kayit_bolumu"] = max(1, son)
        o["guncellendigi_bolum"] = max(1, son)
        zaman[o["id"]] = o
    return durumu_normallestir({
        "sema_surumu": DURUM_SEMA_SURUMU,
        "kitap_adi": kok.get("kitap_adi"),
        "son_kaydedilen_bolum": son,
        "ice_aktarilan_son_bolum": son,
        "durum_revizyonu": 0,
        "baglam": kok.get("baglam"),
        "karakterler": kok.get("karakter_anliklari", {}),
        "ipuclari": ipuclari,
        "zaman_cizelgesi": zaman,
        "uzunluk_kayitlari": {},
    })


def islemi_normallestir(proje: Path, durum: dict[str, Any], belge: object) -> dict[str, Any]:
    kok = sozluk(belge, "işlem")
    bilinen_anahtarlar(kok, {"sema_surumu", "kip", "bolum", "bolum_basligi", "beklenen_revizyon", "degisim", "baglam", "karakter_anliklari", "uzunluk"}, "işlem")
    gerekli(kok.get("sema_surumu") == GIRDI_SEMA_SURUMU, "işlemin sema_surumu desteklenmiyor")
    kip = str(kok.get("kip"))
    gerekli(kip in {"ekle", "revizyon"}, "kip 'ekle' ya da 'revizyon' olmalı")
    bolum = tamsayi(kok.get("bolum"), "bolum", en_az=1)
    gerekli(tamsayi(kok.get("beklenen_revizyon"), "beklenen_revizyon") == durum["durum_revizyonu"],
            "takip durumu bu işlem hazırlandıktan sonra değişmiş; güncel durumu okuyup işlemi yeniden hazırlayın")
    son = durum["son_kaydedilen_bolum"]
    if kip == "ekle":
        gerekli(bolum == son + 1, f"'ekle' kipinde bölüm {son + 1} olmalı, {bolum} verildi")
    else:
        gerekli(bolum <= son, f"yazılmamış {bolum}. bölüm revize edilemez; son kayıtlı bölüm {son}")
    yeni_son = bolum if kip == "ekle" else son
    anliklar = anliklari_normallestir(kok.get("karakter_anliklari", {}))
    mevcut = {tasinabilir_anahtar(ad): ad for ad in durum["karakterler"]}
    for ad in anliklar:
        eski = mevcut.get(tasinabilir_anahtar(ad))
        gerekli(eski is None or eski == ad, f"'{ad}' mevcut '{eski}' karakteriyle çakışıyor")
    degisim = sozluk(kok.get("degisim"), "degisim")
    bilinen_anahtarlar(degisim, {"sonuc", "karakter_degisimleri", "ipucu_degisimleri", "zaman_olaylari",
                                 "sonraki_bolum_sozleri", "emekliye_ayrilan_baglam", "emekliye_ayrilan_karakterler"}, "degisim")
    emekli_karakterler = [guvenli_dosya_adi(a, f"degisim.emekliye_ayrilan_karakterler[{i}]")
                          for i, a in enumerate(liste(degisim.get("emekliye_ayrilan_karakterler", []), "degisim.emekliye_ayrilan_karakterler"))]
    karakter_degisimleri = []
    for i, ham in enumerate(liste(degisim.get("karakter_degisimleri", []), "degisim.karakter_degisimleri")):
        d = sozluk(ham, f"degisim.karakter_degisimleri[{i}]")
        bilinen_anahtarlar(d, {"ad", "degisim"}, f"degisim.karakter_degisimleri[{i}]")
        ad = guvenli_dosya_adi(d.get("ad"), f"degisim.karakter_degisimleri[{i}].ad")
        ana = ad in durum["karakterler"]
        gerekli(not ana or ad in anliklar or ad in emekli_karakterler,
                f"ana karakter '{ad}' değişti ama güncel anlık durumu (karakter_anliklari) verilmedi")
        karakter_degisimleri.append({"ad": ad, "degisim": temiz_metin(d.get("degisim"), f"degisim.karakter_degisimleri[{i}].degisim", azami_bayt=360)})
    ipucu = [ipucu_degisimi(h, f"degisim.ipucu_degisimleri[{i}]", silinebilir=True, son_bolum=yeni_son)
             for i, h in enumerate(liste(degisim.get("ipucu_degisimleri", []), "degisim.ipucu_degisimleri"))]
    olaylar = [olay_degisimi(h, f"degisim.zaman_olaylari[{i}]", silinebilir=True, son_bolum=yeni_son)
               for i, h in enumerate(liste(degisim.get("zaman_olaylari", []), "degisim.zaman_olaylari"))]
    gerekli(len({d["id"] for d in ipucu}) == len(ipucu), "degisim.ipucu_degisimleri aynı kimliği iki kez içeriyor")
    gerekli(len({d["id"] for d in olaylar}) == len(olaylar), "degisim.zaman_olaylari aynı kimliği iki kez içeriyor")
    for d in ipucu:
        if d["islem"] == "ekle":
            gerekli(d["id"] not in durum["ipuclari"], f"{d['id']} zaten var; 'guncelle' kullanın")
        elif d["islem"] in {"guncelle", "sil"}:
            gerekli(d["id"] in durum["ipuclari"] or d["islem"] == "guncelle", f"{d['id']} bulunamadı")
    uzunluk = None
    if kok.get("uzunluk") is not None:
        try:
            uzunluk = metin_olcum.uzunluk_kaydi_dogrula(proje, bolum, kok.get("uzunluk"))
        except metin_olcum.OlcumHatasi as hata:
            raise TakipHatasi(str(hata)) from hata
    return {
        "kip": kip,
        "bolum": bolum,
        "baslik": temiz_metin(kok.get("bolum_basligi"), "bolum_basligi", azami_bayt=240),
        "baglam": baglam_girdisi(kok.get("baglam"), ilk=False),
        "anliklar": anliklar,
        "uzunluk": uzunluk,
        "degisim": {
            "sonuc": temiz_metin(degisim.get("sonuc"), "degisim.sonuc", azami_bayt=360),
            "karakter_degisimleri": karakter_degisimleri,
            "ipucu_degisimleri": ipucu,
            "zaman_olaylari": olaylar,
            "sonraki_bolum_sozleri": temiz_liste(degisim.get("sonraki_bolum_sozleri", []), "degisim.sonraki_bolum_sozleri", azami=5),
            "emekliye_ayrilan_baglam": temiz_liste(degisim.get("emekliye_ayrilan_baglam", []), "degisim.emekliye_ayrilan_baglam", azami=12),
            "emekliye_ayrilan_karakterler": emekli_karakterler,
        },
    }


def _kayit(degisim: dict[str, Any], bolum: int, onceki: dict[str, Any] | None, *, ilk_bolumu_koru: bool = False) -> dict[str, Any]:
    guncel = {k: v for k, v in degisim.items() if k != "islem"}
    guncel["guncellendigi_bolum"] = max(onceki["guncellendigi_bolum"] if onceki else bolum, bolum)
    if ilk_bolumu_koru:
        guncel["ilk_kayit_bolumu"] = onceki["ilk_kayit_bolumu"] if onceki else bolum
    return guncel


def islemi_birlestir(durum: dict[str, Any], islem: dict[str, Any]) -> dict[str, Any]:
    yeni = copy.deepcopy(durum)
    bolum = islem["bolum"]
    revizyon_mu = islem["kip"] == "revizyon"
    if not revizyon_mu:
        yeni["son_kaydedilen_bolum"] = bolum
    yeni["durum_revizyonu"] += 1
    yeni["karakterler"].update(islem["anliklar"])
    if islem["uzunluk"] is not None:
        yeni["uzunluk_kayitlari"][str(bolum)] = islem["uzunluk"]
    baglam = islem["baglam"]
    degisim = islem["degisim"]
    gerekli(not (revizyon_mu and degisim["emekliye_ayrilan_karakterler"]),
            "karakter emekliye ayırma yalnızca 'ekle' kipinde yapılabilir (emeklilik o anki bölüme aittir)")
    for ad in degisim["emekliye_ayrilan_karakterler"]:
        gerekli(ad in yeni["karakterler"], f"emekliye ayrılan '{ad}' için anlık durum yok")
        gerekli(ad not in islem["anliklar"], f"'{ad}' aynı işlemde hem güncellenip hem emekliye ayrılamaz")
        gerekli(ad not in baglam["aktif_karakterler"], f"emekliye ayrılan '{ad}' hâlâ aktif karakterler listesinde")
        yeni["karakterler"].pop(ad)
    # Bağlam maddeleri bütün olarak yeniden gönderilir; sessizce düşen madde tarih kaybıdır.
    onceki = set(durum["baglam"]["kalici_kisitlar"]) | set(durum["baglam"]["sureklilik_riskleri"])
    dusen = onceki - (set(baglam["kalici_kisitlar"]) | set(baglam["sureklilik_riskleri"]))
    gerekli(not (revizyon_mu and dusen), "revizyon bütün bağlam maddelerini yeniden göndermeli; emekliye ayırma 'ekle' kipinde yapılır: " + "; ".join(sorted(dusen)))
    bildirilmemis = sorted(dusen - set(degisim["emekliye_ayrilan_baglam"]))
    gerekli(not bildirilmemis, "şu bağlam maddeleri degisim.emekliye_ayrilan_baglam içinde bildirilmeden düştü: " + "; ".join(bildirilmemis))
    degisim["emekliye_ayrilan_baglam"] = sorted(dusen)
    for d in degisim["ipucu_degisimleri"]:
        if d["islem"] == "sil":
            yeni["ipuclari"].pop(d["id"], None)
        else:
            yeni["ipuclari"][d["id"]] = _kayit(d, bolum, yeni["ipuclari"].get(d["id"]))
    for d in degisim["zaman_olaylari"]:
        if d["islem"] == "sil":
            yeni["zaman_cizelgesi"].pop(d["id"], None)
        else:
            yeni["zaman_cizelgesi"][d["id"]] = _kayit(d, bolum, yeni["zaman_cizelgesi"].get(d["id"]), ilk_bolumu_koru=True)
    son_bolumler = {o["bolum"]: o for o in durum["baglam"]["son_bolumler"]}
    if bolum in son_bolumler or not revizyon_mu:
        son_bolumler[bolum] = {"bolum": bolum, "ozet": degisim["sonuc"]}
    sozler = degisim["sonraki_bolum_sozleri"] if (not revizyon_mu or bolum == yeni["son_kaydedilen_bolum"]) else durum["baglam"]["sonraki_bolum_sozleri"]
    yeni["baglam"] = {**baglam, "son_bolumler": sorted(son_bolumler.values(), key=lambda o: o["bolum"])[-3:], "sonraki_bolum_sozleri": sozler}
    return durumu_normallestir(yeni)


def bolum_kaydi_gorunumu(islem: dict[str, Any]) -> str:
    d = islem["degisim"]
    satirlar = [f"# {islem['bolum']}. Bölüm Kaydı — {islem['baslik']}", "",
                f"- Kip: {islem['kip']}", f"- Sonuç: {d['sonuc']}", ""]
    def blok(baslik: str, ogeler: list[str]) -> None:
        satirlar.extend([f"## {baslik}", *(f"- {o}" for o in (ogeler or ["yok"])), ""])
    blok("Karakter Değişimleri", [f"{k['ad']}: {k['degisim']}" for k in d["karakter_degisimleri"]])
    blok("İpucu Değişimleri", [f"{k['id']} ({k['islem']})" + (f": {k['ozet']} [{k['durum']}]" if k["islem"] != "sil" else "") for k in d["ipucu_degisimleri"]])
    blok("Zaman Olayları", [f"{k['id']} ({k['islem']})" + (f": {k['nesnel_olgu']} [{k['aciga_cikma']}]" if k["islem"] != "sil" else "") for k in d["zaman_olaylari"]])
    blok("Sonraki Bölüm Sözleri", d["sonraki_bolum_sozleri"])
    blok("Bu Bölümde Emekliye Ayrılanlar", [*(f"bağlam: {m}" for m in d["emekliye_ayrilan_baglam"]), *(f"karakter: {m}" for m in d["emekliye_ayrilan_karakterler"])])
    icerik = "\n".join(satirlar).rstrip() + "\n"
    if bayt(icerik) > KAYIT_AZAMI_BAYT:
        print(f"Uyarı: bölüm kaydı {KAYIT_AZAMI_BAYT} baytı aşıyor; özetleri kısaltmayı düşünün.", file=sys.stderr)
    return icerik


def durumu_yukle(proje: Path) -> dict[str, Any]:
    yol = durum_yolu(proje)
    gerekli(yol.exists(), "takip durumu yok; önce 'baslat' çalıştırın")
    return durumu_normallestir(json_oku(yol))


def baslat(proje: Path, belge: object) -> dict[str, Any]:
    with proje_kilidi(proje):
        gerekli(not durum_yolu(proje).exists(), "takip durumu zaten var; değişiklik için 'uygula' kullanın")
        durum = baslangic_belgesi(belge)
        takip = takip_koku(proje)
        gorunumleri_yaz(takip, gorunumleri_uret(durum))
        atomik_yaz(durum_yolu(proje), json_metni(durum))
    return {"tamam": True, "durum_revizyonu": 0, "son_kaydedilen_bolum": durum["son_kaydedilen_bolum"]}


def uygula(proje: Path, belge: object) -> dict[str, Any]:
    with proje_kilidi(proje):
        durum = durumu_yukle(proje)
        islem = islemi_normallestir(proje, durum, belge)
        yeni = islemi_birlestir(durum, islem)
        gorunumler = gorunumleri_uret(yeni)
        takip = takip_koku(proje)
        kayit = bolum_kaydi_gorunumu(islem)
        gorunumleri_yaz(takip, gorunumler)
        atomik_yaz(takip / "bolum-kayitlari" / f"bolum-{islem['bolum']:03d}.md", kayit)
        atomik_yaz(durum_yolu(proje), json_metni(yeni))  # tek kayıt noktası: en son yazılır
    return {"tamam": True, "takip_kaydedildi": True, "durum_revizyonu": yeni["durum_revizyonu"],
            "son_kaydedilen_bolum": yeni["son_kaydedilen_bolum"], "bolum": islem["bolum"]}


def denetle(proje: Path) -> dict[str, Any]:
    durum = durumu_yukle(proje)
    takip = takip_koku(proje)
    sorunlar = []
    for goreli, beklenen in gorunumleri_uret(durum).items():
        yol = takip / goreli
        if not yol.exists():
            sorunlar.append(f"eksik görünüm: {goreli}")
        elif yol.read_text(encoding="utf-8") != beklenen:
            sorunlar.append(f"elle değiştirilmiş ya da eski görünüm: {goreli}")
    return {"tamam": not sorunlar, "durum_revizyonu": durum["durum_revizyonu"],
            "son_kaydedilen_bolum": durum["son_kaydedilen_bolum"], "sorunlar": sorunlar}


def onar(proje: Path) -> dict[str, Any]:
    """Görünümleri durumdan yeniden üretir (elle yapılan değişiklikler silinir)."""
    with proje_kilidi(proje):
        durum = durumu_yukle(proje)
        gorunumleri_yaz(takip_koku(proje), gorunumleri_uret(durum))
    return {"tamam": True, "durum_revizyonu": durum["durum_revizyonu"]}


def goster(proje: Path) -> dict[str, Any]:
    durum = durumu_yukle(proje)
    return {
        "kitap_adi": durum["kitap_adi"],
        "son_kaydedilen_bolum": durum["son_kaydedilen_bolum"],
        "durum_revizyonu": durum["durum_revizyonu"],
        "karakter_sayisi": len(durum["karakterler"]),
        "acik_ipucu": sum(1 for s in durum["ipuclari"].values() if s["durum"] == "ekili"),
        "gizli_olay": sum(1 for o in durum["zaman_cizelgesi"].values() if o["aciga_cikma"] == "gizli"),
    }


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    for komut in ("baslat", "uygula"):
        a = alt.add_parser(komut)
        a.add_argument("--proje", required=True, type=Path)
        a.add_argument("--girdi", required=True, type=Path)
    for komut in ("denetle", "goster", "onar"):
        alt.add_parser(komut).add_argument("--proje", required=True, type=Path)
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "baslat":
            sonuc = baslat(arg.proje, json_oku(arg.girdi))
        elif arg.komut == "uygula":
            sonuc = uygula(arg.proje, json_oku(arg.girdi))
        elif arg.komut == "denetle":
            sonuc = denetle(arg.proje)
        elif arg.komut == "onar":
            sonuc = onar(arg.proje)
        else:
            sonuc = goster(arg.proje)
    except TakipHatasi as hata:
        print(json.dumps({"tamam": False, "hata": str(hata)}, ensure_ascii=False))
        return 2
    print(json.dumps(sonuc, ensure_ascii=False))
    return 0 if sonuc.get("tamam", True) else 1


if __name__ == "__main__":
    sys.exit(main())
