#!/usr/bin/env python3
"""Kitap projesinin anlık görüntüleri (sürümleri): al, listele, karşılaştır, geri yükle.

Git bilmeyen yazar için güvenli sürüm geçmişi. Her anlık görüntü, projedeki metin,
plan, kurgu ve takip dosyalarının o anki hâlidir. İçerik, özet değeriyle (SHA-256)
``.hikaye/anliklar/nesneler/`` altında bir kez saklanır; değişmeyen dosya ikinci kez
yer kaplamaz.

Kullanım::

    anlik_goruntu.py al        --proje KITAP [--not "3. bölüm revizyon öncesi"]
    anlik_goruntu.py listele   --proje KITAP [--json]
    anlik_goruntu.py fark      --proje KITAP [--a son~1] [--b calisma] [--dosya metin/bolum-003_x.md] [--kelime]
    anlik_goruntu.py geri-yukle --proje KITAP --kimlik 20260925-101500 --dosya metin/bolum-003_x.md
    anlik_goruntu.py geri-yukle --proje KITAP --kimlik son --hepsi --onayla
    anlik_goruntu.py temizle   --proje KITAP --tut 20
    anlik_goruntu.py dogrula   --proje KITAP

Kimlik yerine ``son`` (en yeni), ``son~1`` (bir önceki) ya da kimliğin başı
yazılabilir. ``fark`` komutunda ``calisma`` şu anki dosyalar demektir.
Geri yüklemeden önce şu anki hâlin anlık görüntüsü kendiliğinden alınır; hiçbir
şey geri dönüşsüz silinmez.

Çıkış kodu: 0 başarılı, 1 bütünlük sorunu, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KLASORLER = ("metin", "plan", "kurgu", "takip", "arastirma", "notlar")
KOK_DOSYALAR = (".yz-beyaz-liste", ".yasak-kaliplar", "README.md", "kitap.json")
UZANTILAR = {".md", ".txt", ".json", ".csv", ".tsv", ".yaml", ".yml"}
EN_BUYUK = 20 * 1024 * 1024
KIMLIK_DESENI = re.compile(r"^\d{8}-\d{6}(?:-\d+)?$")
KELIME = re.compile(r"\S+")


class AnlikHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def _kok(proje: Path) -> Path:
    return proje / ".hikaye" / "anliklar"


def _ozet(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


def _nesne_yolu(proje: Path, ozet: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", ozet):
        raise AnlikHatasi(f"geçersiz içerik özeti: {ozet[:20]}")
    return _kok(proje) / "nesneler" / ozet[:2] / ozet


def proje_dogrula(proje: Path) -> Path:
    if not proje.exists():
        raise AnlikHatasi(f"proje klasörü bulunamadı: {proje}")
    if not proje.is_dir():
        raise AnlikHatasi(f"proje klasörü bekleniyordu, dosya verildi: {proje}")
    return proje.resolve()


def izlenen_dosyalar(proje: Path) -> dict[str, Path]:
    """Göreli POSIX yol -> mutlak yol. Sıralı ve belirlenimci."""
    sonuc: dict[str, Path] = {}
    for ad in KOK_DOSYALAR:
        yol = proje / ad
        if yol.is_file():
            sonuc[ad] = yol
    for klasor in KLASORLER:
        taban = proje / klasor
        if not taban.is_dir():
            continue
        for yol in sorted(taban.rglob("*")):
            if not yol.is_file() or yol.is_symlink() or yol.suffix.lower() not in UZANTILAR:
                continue
            goreli = yol.relative_to(proje).as_posix()
            if any(p.startswith(".") for p in PurePosixPath(goreli).parts):
                continue
            if yol.stat().st_size > EN_BUYUK:
                print(f"uyarı: 20 MB'tan büyük dosya atlandı: {goreli}", file=sys.stderr)
                continue
            sonuc[goreli] = yol
    return dict(sorted(sonuc.items()))


def kelime_say(veri: bytes) -> int:
    try:
        return len(KELIME.findall(veri.decode("utf-8-sig")))
    except UnicodeDecodeError:
        return 0


def kayitlar(proje: Path) -> list[dict[str, Any]]:
    klasor = _kok(proje) / "kayitlar"
    if not klasor.is_dir():
        return []
    sonuc = []
    for yol in sorted(klasor.glob("*.json")):
        try:
            kayit = json.loads(yol.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            print(f"uyarı: bozuk anlık görüntü kaydı atlandı: {yol.name}", file=sys.stderr)
            continue
        if isinstance(kayit, dict) and KIMLIK_DESENI.match(str(kayit.get("kimlik", ""))) \
                and isinstance(kayit.get("dosyalar"), dict):
            sonuc.append(kayit)
    sonuc.sort(key=lambda k: (k.get("zaman", ""), k["kimlik"]))
    return sonuc


def kimlik_coz(proje: Path, istek: str) -> dict[str, Any]:
    liste = kayitlar(proje)
    if not liste:
        raise AnlikHatasi("bu projede henüz anlık görüntü yok; önce 'al' komutunu çalıştırın")
    istek = istek.strip()
    m = re.fullmatch(r"son(?:~(\d+))?", istek)
    if m:
        geri = int(m.group(1) or 0)
        if geri >= len(liste):
            raise AnlikHatasi(f"yalnızca {len(liste)} anlık görüntü var; '{istek}' bulunamadı")
        return liste[-1 - geri]
    eslesen = [k for k in liste if k["kimlik"].startswith(istek)] if istek else []
    if not eslesen:
        raise AnlikHatasi(f"anlık görüntü bulunamadı: {istek}")
    if len(eslesen) > 1 and not any(k["kimlik"] == istek for k in eslesen):
        raise AnlikHatasi(f"'{istek}' birden fazla anlık görüntüyle eşleşiyor; daha uzun yazın")
    return next((k for k in eslesen if k["kimlik"] == istek), eslesen[0])


def _yeni_kimlik(proje: Path, zaman: dt.datetime) -> str:
    taban = zaman.strftime("%Y%m%d-%H%M%S")
    klasor = _kok(proje) / "kayitlar"
    kimlik, sira = taban, 1
    while (klasor / f"{kimlik}.json").exists():
        sira += 1
        kimlik = f"{taban}-{sira}"
    return kimlik


def anlik_al(proje: Path, not_: str = "", degismediyse_atla: bool = True,
             zaman: dt.datetime | None = None) -> dict[str, Any] | None:
    """Anlık görüntü alır. Son görüntüden fark yoksa ve atla isteniyorsa None döner."""
    proje = proje_dogrula(proje)
    dosyalar: dict[str, str] = {}
    toplam_kelime = 0
    yeni_nesne = 0
    for goreli, yol in izlenen_dosyalar(proje).items():
        veri = yol.read_bytes()
        ozet = _ozet(veri)
        hedef = _nesne_yolu(proje, ozet)
        if not hedef.exists():
            hedef.parent.mkdir(parents=True, exist_ok=True)
            gecici = hedef.with_suffix(".gecici")
            gecici.write_bytes(veri)
            os.replace(gecici, hedef)
            yeni_nesne += 1
        dosyalar[goreli] = ozet
        if goreli.startswith("metin/"):
            toplam_kelime += kelime_say(veri)
    onceki = kayitlar(proje)
    if degismediyse_atla and onceki and onceki[-1]["dosyalar"] == dosyalar:
        return None
    zaman = zaman or dt.datetime.now().replace(microsecond=0)
    kayit = {
        "sema_surumu": 1,
        "kimlik": _yeni_kimlik(proje, zaman),
        "zaman": zaman.isoformat(),
        "not": not_.strip(),
        "metin_kelime": toplam_kelime,
        "dosya_sayisi": len(dosyalar),
        "dosyalar": dosyalar,
    }
    klasor = _kok(proje) / "kayitlar"
    klasor.mkdir(parents=True, exist_ok=True)
    gecici = klasor / f"{kayit['kimlik']}.json.gecici"
    gecici.write_text(json.dumps(kayit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(gecici, klasor / f"{kayit['kimlik']}.json")
    kayit["yeni_nesne"] = yeni_nesne
    return kayit


def _icerik(proje: Path, ozet: str | None) -> str:
    if ozet is None:
        return ""
    yol = _nesne_yolu(proje, ozet)
    if not yol.is_file():
        raise AnlikHatasi(f"anlık görüntü içeriği eksik (bozulmuş depo): {ozet[:12]}; 'dogrula' komutunu çalıştırın")
    return yol.read_bytes().decode("utf-8-sig", errors="replace")


def _calisma_durumu(proje: Path) -> dict[str, str]:
    return {g: _ozet(y.read_bytes()) for g, y in izlenen_dosyalar(proje).items()}


def _calisma_icerigi(proje: Path, goreli: str) -> str:
    yol = proje / goreli
    return dosya_oku.metin_oku(yol, uyar=False) if yol.is_file() else ""


def kelime_farki(eski: str, yeni: str) -> tuple[str, int, int]:
    """Kelime düzeyinde fark: [-silinen-] {+eklenen+}. (metin, eklenen, silinen)"""
    a, b = eski.split(), yeni.split()
    parcalar: list[str] = []
    eklenen = silinen = 0
    esleyici = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for islem, i1, i2, j1, j2 in esleyici.get_opcodes():
        if islem == "equal":
            ortak = a[i1:i2]
            parcalar.append(" ".join(ortak) if len(ortak) <= 12 else
                            " ".join(ortak[:5]) + " … " + " ".join(ortak[-5:]))
            continue
        if i2 > i1:
            parcalar.append("[-" + " ".join(a[i1:i2]) + "-]")
            silinen += i2 - i1
        if j2 > j1:
            parcalar.append("{+" + " ".join(b[j1:j2]) + "+}")
            eklenen += j2 - j1
    return " ".join(parcalar), eklenen, silinen


def fark_hesapla(proje: Path, a: str, b: str = "calisma", dosya: str | None = None,
                 kelime: bool = False) -> dict[str, Any]:
    proje = proje_dogrula(proje)
    kayit_a = kimlik_coz(proje, a)
    if b == "calisma":
        durum_b, ad_b = _calisma_durumu(proje), "calisma"
    else:
        kayit_b = kimlik_coz(proje, b)
        durum_b, ad_b = kayit_b["dosyalar"], kayit_b["kimlik"]
    durum_a = kayit_a["dosyalar"]
    if dosya:
        dosya = PurePosixPath(dosya.replace("\\", "/")).as_posix()
        if dosya not in durum_a and dosya not in durum_b:
            raise AnlikHatasi(f"dosya iki sürümde de yok: {dosya}")
        adlar = [dosya]
    else:
        adlar = sorted(set(durum_a) | set(durum_b))
    ozet = {"eklenen_dosya": [], "silinen_dosya": [], "degisen_dosya": [], "eklenen_kelime": 0, "silinen_kelime": 0}
    ayrinti: list[str] = []
    for ad in adlar:
        oa, ob = durum_a.get(ad), durum_b.get(ad)
        if oa == ob:
            continue
        eski = _icerik(proje, oa)
        yeni = _calisma_icerigi(proje, ad) if ad_b == "calisma" else _icerik(proje, ob)
        if oa is None:
            ozet["eklenen_dosya"].append(ad)
        elif ob is None:
            ozet["silinen_dosya"].append(ad)
        else:
            ozet["degisen_dosya"].append(ad)
        metin, ek, sil = kelime_farki(eski, yeni)
        ozet["eklenen_kelime"] += ek
        ozet["silinen_kelime"] += sil
        if kelime:
            ayrinti.append(f"### {ad}  (+{ek} / −{sil} kelime)\n{metin}\n")
        else:
            satirlar = difflib.unified_diff(eski.splitlines(), yeni.splitlines(),
                                            f"{kayit_a['kimlik']}/{ad}", f"{ad_b}/{ad}", lineterm="", n=2)
            ayrinti.append("\n".join(satirlar))
    return {"a": kayit_a["kimlik"], "b": ad_b, "ozet": ozet, "ayrinti": ayrinti}


def _guvenli_hedef(proje: Path, goreli: str) -> Path:
    yol = PurePosixPath(goreli.replace("\\", "/"))
    if yol.is_absolute() or ".." in yol.parts or not yol.parts or re.match(r"^[A-Za-z]:", goreli):
        raise AnlikHatasi(f"güvensiz dosya yolu reddedildi: {goreli}")
    hedef = (proje / Path(*yol.parts)).resolve()
    if proje != hedef and proje not in hedef.parents:
        raise AnlikHatasi(f"proje dışına yazma reddedildi: {goreli}")
    return hedef


def geri_yukle(proje: Path, kimlik: str, dosya: str | None = None, hepsi: bool = False) -> dict[str, Any]:
    proje = proje_dogrula(proje)
    kayit = kimlik_coz(proje, kimlik)
    if dosya:
        dosya = PurePosixPath(dosya.replace("\\", "/")).as_posix()
        if dosya not in kayit["dosyalar"]:
            raise AnlikHatasi(f"{kayit['kimlik']} anlık görüntüsünde bu dosya yok: {dosya}")
        secilen = {dosya: kayit["dosyalar"][dosya]}
    elif hepsi:
        secilen = dict(kayit["dosyalar"])
    else:
        raise AnlikHatasi("--dosya ya da --hepsi seçeneklerinden biri gerekli")
    for goreli, ozet in secilen.items():  # önce her şeyi doğrula, sonra yaz
        _guvenli_hedef(proje, goreli)
        if not _nesne_yolu(proje, ozet).is_file():
            raise AnlikHatasi(f"anlık görüntü içeriği eksik: {goreli}; geri yükleme yapılmadı")
    guvenlik = anlik_al(proje, f"geri yükleme öncesi ({kayit['kimlik']})", degismediyse_atla=True)
    yazilan = []
    for goreli, ozet in secilen.items():
        hedef = _guvenli_hedef(proje, goreli)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        veri = _nesne_yolu(proje, ozet).read_bytes()
        if hedef.is_file() and _ozet(hedef.read_bytes()) == ozet:
            continue
        gecici = hedef.with_name(hedef.name + ".gecici")
        gecici.write_bytes(veri)
        os.replace(gecici, hedef)
        yazilan.append(goreli)
    silinen = []
    if hepsi:  # görüntüde olmayan izlenen dosyalar yedeklendikten sonra kaldırılır
        for goreli, yol in izlenen_dosyalar(proje).items():
            if goreli not in secilen:
                yol.unlink()
                silinen.append(goreli)
    return {"kimlik": kayit["kimlik"], "yazilan": yazilan, "kaldirilan": silinen,
            "guvenlik_goruntusu": guvenlik["kimlik"] if guvenlik else None}


def temizle(proje: Path, tut: int) -> dict[str, int]:
    proje = proje_dogrula(proje)
    if tut < 1:
        raise AnlikHatasi("--tut en az 1 olmalı")
    liste = kayitlar(proje)
    silinecek = liste[:-tut] if len(liste) > tut else []
    for kayit in silinecek:
        (_kok(proje) / "kayitlar" / f"{kayit['kimlik']}.json").unlink()
    kullanilan = {o for k in liste[-tut:] for o in k["dosyalar"].values()}
    nesne_sil = 0
    nesneler = _kok(proje) / "nesneler"
    if nesneler.is_dir():
        for yol in nesneler.glob("*/*"):
            if yol.is_file() and yol.name not in kullanilan:
                yol.unlink()
                nesne_sil += 1
    return {"silinen_goruntu": len(silinecek), "silinen_nesne": nesne_sil, "kalan": min(len(liste), tut)}


def dogrula(proje: Path) -> list[str]:
    proje = proje_dogrula(proje)
    sorunlar = []
    for kayit in kayitlar(proje):
        for goreli, ozet in kayit["dosyalar"].items():
            try:
                yol = _nesne_yolu(proje, ozet)
            except AnlikHatasi as hata:
                sorunlar.append(f"{kayit['kimlik']}: {goreli}: {hata}")
                continue
            if not yol.is_file():
                sorunlar.append(f"{kayit['kimlik']}: {goreli}: içerik eksik")
            elif _ozet(yol.read_bytes()) != ozet:
                sorunlar.append(f"{kayit['kimlik']}: {goreli}: içerik bozulmuş (özet tutmuyor)")
    return sorunlar


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Kitap projesinin anlık görüntüleri: al, listele, fark, geri yükle.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_al = alt.add_parser("al", help="şu anki hâlin anlık görüntüsünü al")
    p_al.add_argument("--not", dest="not_", default="", help="bu sürüm için kısa açıklama")
    p_al.add_argument("--degismese-de", action="store_true", help="son görüntüden fark yoksa da yeni kayıt aç")
    p_ls = alt.add_parser("listele", help="anlık görüntüleri eskiden yeniye listele")
    p_fk = alt.add_parser("fark", help="iki sürümü (ya da bir sürümle şu anki hâli) karşılaştır")
    p_fk.add_argument("--a", default="son", help="eski sürüm (varsayılan: son)")
    p_fk.add_argument("--b", default="calisma", help="yeni sürüm (varsayılan: calisma, yani şu anki dosyalar)")
    p_fk.add_argument("--dosya", help="yalnızca bu dosyayı karşılaştır (proje içi göreli yol)")
    p_fk.add_argument("--kelime", action="store_true", help="satır yerine kelime düzeyinde fark göster")
    p_gy = alt.add_parser("geri-yukle", help="bir dosyayı ya da bütün projeyi eski sürüme döndür")
    p_gy.add_argument("--kimlik", required=True, help="anlık görüntü kimliği, 'son' ya da 'son~N'")
    p_gy.add_argument("--dosya", help="yalnızca bu dosyayı geri yükle (proje içi göreli yol)")
    p_gy.add_argument("--hepsi", action="store_true", help="bütün izlenen dosyaları geri yükle")
    p_gy.add_argument("--onayla", action="store_true", help="--hepsi ile zorunlu: yazarın açık onayı")
    p_tm = alt.add_parser("temizle", help="en yeni N görüntüyü tut, gerisini ve kullanılmayan içeriği sil")
    p_tm.add_argument("--tut", type=int, required=True, help="tutulacak en yeni anlık görüntü sayısı")
    p_dg = alt.add_parser("dogrula", help="saklanan içeriklerin bütünlüğünü denetle")
    for p in (p_al, p_ls, p_fk, p_gy, p_tm, p_dg):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
        p.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    arg = ayr.parse_args(argv)

    def yaz(veri: Any, metin: str) -> None:
        print(json.dumps(veri, ensure_ascii=False, indent=2) if arg.json else metin)

    try:
        if arg.komut == "al":
            kayit = anlik_al(arg.proje, arg.not_, degismediyse_atla=not arg.degismese_de)
            if kayit is None:
                yaz({"alindi": False}, "Değişiklik yok; yeni anlık görüntü alınmadı.")
            else:
                yaz({"alindi": True, **{k: v for k, v in kayit.items() if k != "dosyalar"}},
                    f"Anlık görüntü alındı: {kayit['kimlik']} ({kayit['dosya_sayisi']} dosya, "
                    f"metinde {kayit['metin_kelime']} kelime, {kayit['yeni_nesne']} yeni içerik)")
        elif arg.komut == "listele":
            liste = kayitlar(proje_dogrula(arg.proje))
            satirlar = [f"{k['kimlik']:<18}  {k.get('metin_kelime', 0):>7} kelime  {k.get('dosya_sayisi', 0):>4} dosya  "
                        f"{k.get('not', '')}" for k in liste] or ["Henüz anlık görüntü yok."]
            yaz([{x: y for x, y in k.items() if x != "dosyalar"} for k in liste], "\n".join(satirlar))
        elif arg.komut == "fark":
            sonuc = fark_hesapla(arg.proje, arg.a, arg.b, arg.dosya, arg.kelime)
            o = sonuc["ozet"]
            baslik = (f"{sonuc['a']} → {sonuc['b']}: {len(o['degisen_dosya'])} değişen, "
                      f"{len(o['eklenen_dosya'])} yeni, {len(o['silinen_dosya'])} silinen dosya; "
                      f"+{o['eklenen_kelime']} / −{o['silinen_kelime']} kelime")
            yaz(sonuc, "\n".join([baslik, ""] + sonuc["ayrinti"]) if sonuc["ayrinti"] else baslik + "\nFark yok.")
        elif arg.komut == "geri-yukle":
            if arg.hepsi and not arg.onayla:
                raise AnlikHatasi("bütün projeyi geri yüklemek için --onayla gerekli (önce 'fark' ile inceleyin)")
            sonuc = geri_yukle(arg.proje, arg.kimlik, arg.dosya, arg.hepsi)
            yaz(sonuc, f"{sonuc['kimlik']} sürümünden {len(sonuc['yazilan'])} dosya geri yüklendi"
                       + (f", {len(sonuc['kaldirilan'])} dosya kaldırıldı" if sonuc["kaldirilan"] else "")
                       + (f". Önceki hâl {sonuc['guvenlik_goruntusu']} olarak saklandı." if sonuc["guvenlik_goruntusu"]
                          else "."))
        elif arg.komut == "temizle":
            sonuc = temizle(arg.proje, arg.tut)
            yaz(sonuc, f"{sonuc['silinen_goruntu']} anlık görüntü ve {sonuc['silinen_nesne']} kullanılmayan içerik "
                       f"silindi; {sonuc['kalan']} görüntü kaldı.")
        else:
            sorunlar = dogrula(arg.proje)
            yaz({"sorunlar": sorunlar}, "\n".join(sorunlar) if sorunlar else "Bütün anlık görüntüler sağlam.")
            return 1 if sorunlar else 0
    except (AnlikHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
