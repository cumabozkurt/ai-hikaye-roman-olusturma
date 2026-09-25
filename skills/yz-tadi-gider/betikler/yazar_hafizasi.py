#!/usr/bin/env python3
"""Yazar hafızası: kanıta dayalı yazar tercihleri ve bunlardan üretilen Markdown görünümleri.

İki düzeyli depo vardır:
  * proje deposu  ``{calisma_alani}/.hikaye/yazar-hafizasi/``   genel / tür / iş akışı maddeleri (AP kimlikleri)
  * kitap deposu  ``{kitap}/.hikaye/yazar-hafizasi/``           yalnızca o kitaba özgü maddeler (KP kimlikleri)
Kitap klasörü çalışma alanının kendisiyse kitap deposu ``.../yazar-hafizasi/kitap/`` altına taşınır.

Yalnızca yazarın açıkça söylediği ya da onayladığı tercihler kaydedilir; model
kendi çıkarımını hafızaya yazamaz. Bu hafıza, kitabın hikâye sürekliliği
takibinden (takip/) ayrıdır.

Komutlar::

    baslat   --calisma-alani . [--kitap KITAP]
    kaydet   --calisma-alani . [--kitap KITAP] --girdi islem.json
    sorgula  --calisma-alani . [--kitap KITAP] [--tur anlatim_uslubu ...] [--tur-adi polisiye] [--is-akisi yz-tadi-gider]
    denetle  --calisma-alani . [--kitap KITAP]

İşlem girdisi::

    {"sema_surumu": 1, "islem_kimligi": "2026-09-25-01", "islemler": [
      {"eylem": "hatirla", "iddia": "Diyaloglarda argo kullanma", "tur": "anlatim_uslubu",
       "kapsam": {"duzey": "genel"}, "kaynak": "yazar_acikca", "kanit": "Argo istemiyorum, dedi.",
       "onem": "yuksek"},
      {"eylem": "degistir", "id": "AP002", "iddia": "...", "kanit": "..."},
      {"eylem": "karar", "id": "AP004", "karar": "onayla"},
      {"eylem": "unut", "id": "KP001", "neden": "yazar vazgeçti"}]}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

SEMA_SURUMU = 1
SORGU_AZAMI_BAYT = 2048
IDDIA_AZAMI_BAYT = 120
KANIT_AZAMI_BAYT = 240
GUNLUK_AZAMI_BAYT = 24576
TURLER = {
    "anlatim_uslubu": "Anlatım ve Üslup",
    "hikaye_tasarimi": "Hikâye Tasarımı",
    "is_akisi": "Yazım Süreci",
    "teslim_bicimi": "Teslim Biçimi",
    "is_birligi": "Birlikte Çalışma",
}
DUZEYLER = ("genel", "tur", "kitap", "is_akisi")
DURUMLAR = ("etkin", "bekliyor", "celiskili", "reddedildi", "yerine_gecti")
DERECELER = ("dusuk", "orta", "yuksek")
KAYNAKLAR = ("yazar_acikca", "onaylanan_oneri", "elle")
SIRA = {"dusuk": 0, "orta": 1, "yuksek": 2}
GOREV_BIRLESIMLERI = {
    "bolum-taslagi": ("anlatim_uslubu", "hikaye_tasarimi"),
    "yz-tadi-gider": ("anlatim_uslubu",),
    "kurgu-plan": ("hikaye_tasarimi", "is_akisi", "is_birligi"),
    "inceleme": ("teslim_bicimi", "is_birligi", "anlatim_uslubu"),
}


class HafizaHatasi(ValueError):
    pass


def gerekli(kosul: bool, mesaj: str) -> None:
    if not kosul:
        raise HafizaHatasi(mesaj)


def temiz(deger: object, etiket: str, azami: int) -> str:
    gerekli(isinstance(deger, str), f"{etiket} metin olmalı")
    metin = " ".join(str(deger).replace("|", "¦").split())
    gerekli(bool(metin), f"{etiket} boş olamaz")
    gerekli(len(metin.encode("utf-8")) <= azami, f"{etiket} {azami} baytı aşıyor; tek cümleye indirin")
    return metin


def depo_yolu(calisma: Path, kitap: Path | None, duzey: str) -> Path:
    if duzey == "proje":
        return calisma / ".hikaye" / "yazar-hafizasi"
    gerekli(kitap is not None, "kitap düzeyi madde için --kitap verilmeli")
    assert kitap is not None
    if kitap.resolve() == calisma.resolve():
        return calisma / ".hikaye" / "yazar-hafizasi" / "kitap"
    return kitap / ".hikaye" / "yazar-hafizasi"


def bos_durum(depo: str, kitap_adi: str | None) -> dict[str, Any]:
    return {"sema_surumu": SEMA_SURUMU, "depo": depo, "kitap_adi": kitap_adi, "revizyon": 0,
            "sonraki_no": 1, "uygulanan_islemler": {}, "maddeler": {}}


def oku(klasor: Path) -> dict[str, Any] | None:
    yol = klasor / "durum.json"
    if not yol.exists():
        return None
    belge = json.loads(yol.read_text(encoding="utf-8"))
    gerekli(isinstance(belge, dict) and belge.get("sema_surumu") == SEMA_SURUMU, f"{yol} şeması desteklenmiyor")
    return belge


def atomik_yaz(yol: Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    fd, gecici = tempfile.mkstemp(dir=yol.parent, prefix=".gecici-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(icerik)
        os.replace(gecici, yol)
    except BaseException:
        Path(gecici).unlink(missing_ok=True)
        raise


def profil_gorunumu(durum: dict[str, Any]) -> str:
    baslik = "Yazar Profili" + (f" — {durum['kitap_adi']}" if durum.get("kitap_adi") else "")
    satirlar = [f"# {baslik}", "", "> Bu dosya yazar_hafizasi.py tarafından üretilir; elle düzenlemeyin.", ""]
    for tur, tur_basligi in TURLER.items():
        maddeler = [m for m in durum["maddeler"].values() if m["tur"] == tur and m["durum"] == "etkin"]
        if not maddeler:
            continue
        satirlar += [f"## {tur_basligi}", ""]
        for m in sorted(maddeler, key=lambda m: (-SIRA[m["onem"]], m["id"])):
            kapsam = m["kapsam"]["duzey"] + (f": {m['kapsam']['deger']}" if m["kapsam"].get("deger") else "")
            satirlar.append(f"- **{m['id']}** ({kapsam}, önem {m['onem']}) {m['iddia']}")
        satirlar.append("")
    bekleyen = [m for m in durum["maddeler"].values() if m["durum"] in {"bekliyor", "celiskili"}]
    if bekleyen:
        satirlar += ["## Karar Bekleyenler", ""]
        satirlar += [f"- **{m['id']}** [{m['durum']}] {m['iddia']}" for m in sorted(bekleyen, key=lambda m: m["id"])]
        satirlar.append("")
    return "\n".join(satirlar).rstrip() + "\n"


def yaz(klasor: Path, durum: dict[str, Any], gunluk_satirlari: list[str]) -> None:
    atomik_yaz(klasor / "profil.md", profil_gorunumu(durum))
    gunluk = klasor / "gunluk.md"
    eski = gunluk.read_text(encoding="utf-8") if gunluk.exists() else "# Yazar Hafızası Günlüğü\n\n"
    yeni = eski + "".join(f"- {s}\n" for s in gunluk_satirlari)
    if len(yeni.encode("utf-8")) > GUNLUK_AZAMI_BAYT:
        satirlar = yeni.splitlines(keepends=True)
        while len("".join(satirlar).encode("utf-8")) > GUNLUK_AZAMI_BAYT and len(satirlar) > 3:
            satirlar.pop(2)
        yeni = "".join(satirlar)
    atomik_yaz(gunluk, yeni)
    atomik_yaz(klasor / "durum.json", json.dumps(durum, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def baslat(calisma: Path, kitap: Path | None) -> dict[str, Any]:
    olusan = []
    for depo in ("proje", "kitap") if kitap else ("proje",):
        klasor = depo_yolu(calisma, kitap, depo)
        if oku(klasor) is None:
            yaz(klasor, bos_durum(depo, kitap.name if (kitap and depo == "kitap") else None), [])
            olusan.append(str(klasor))
    return {"tamam": True, "olusturulan": olusan}


def _kapsam(ham: object) -> dict[str, str]:
    gerekli(isinstance(ham, dict), "kapsam nesne olmalı")
    assert isinstance(ham, dict)
    duzey = ham.get("duzey")
    gerekli(duzey in DUZEYLER, f"kapsam.duzey şunlardan biri olmalı: {', '.join(DUZEYLER)}")
    sonuc = {"duzey": str(duzey)}
    if duzey in {"tur", "is_akisi"}:
        sonuc["deger"] = temiz(ham.get("deger"), "kapsam.deger", 60)
    return sonuc


def kaydet(calisma: Path, kitap: Path | None, belge: object) -> dict[str, Any]:
    gerekli(isinstance(belge, dict), "girdi nesne olmalı")
    assert isinstance(belge, dict)
    gerekli(belge.get("sema_surumu") == SEMA_SURUMU, "sema_surumu 1 olmalı")
    islem_kimligi = temiz(belge.get("islem_kimligi"), "islem_kimligi", 80)
    islemler = belge.get("islemler")
    gerekli(isinstance(islemler, list) and islemler, "islemler boş olmayan liste olmalı")
    ozet = hashlib.sha256(json.dumps(belge, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    depolar: dict[str, tuple[Path, dict[str, Any]]] = {}

    def depo_al(ad: str) -> dict[str, Any]:
        if ad not in depolar:
            klasor = depo_yolu(calisma, kitap, ad)
            durum = oku(klasor) or bos_durum(ad, kitap.name if (kitap and ad == "kitap") else None)
            onceki = durum["uygulanan_islemler"].get(islem_kimligi)
            if onceki is not None:
                gerekli(onceki == ozet, f"islem_kimligi {islem_kimligi} farklı içerikle daha önce kullanılmış")
            depolar[ad] = (klasor, durum)
        return depolar[ad][1]

    tarih = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    makbuz: list[str] = []
    gunluk: dict[str, list[str]] = {}
    for i, ham in enumerate(islemler):
        gerekli(isinstance(ham, dict), f"islemler[{i}] nesne olmalı")
        eylem = ham.get("eylem")
        if eylem in {"hatirla", "degistir"}:
            eski_id = ham.get("id") if eylem == "degistir" else None
            if eski_id:
                eski_depo = "kitap" if str(eski_id).startswith("KP") else "proje"
                eski = depo_al(eski_depo)["maddeler"].get(eski_id)
                gerekli(eski is not None, f"{eski_id} bulunamadı")
                assert eski is not None
                varsayilan = {"tur": eski["tur"], "kapsam": eski["kapsam"], "onem": eski["onem"]}
            else:
                varsayilan = {}
            kapsam = _kapsam(ham.get("kapsam", varsayilan.get("kapsam")))
            depo = "kitap" if kapsam["duzey"] == "kitap" else "proje"
            durum = depo_al(depo)
            if depolar[depo][1].get("uygulanan_islemler", {}).get(islem_kimligi) == ozet:
                continue
            tur = ham.get("tur", varsayilan.get("tur"))
            gerekli(tur in TURLER, f"islemler[{i}].tur şunlardan biri olmalı: {', '.join(TURLER)}")
            kaynak = ham.get("kaynak", "yazar_acikca")
            gerekli(kaynak in KAYNAKLAR, f"islemler[{i}].kaynak yalnızca {', '.join(KAYNAKLAR)} olabilir (model çıkarımı kaydedilmez)")
            onem = ham.get("onem", varsayilan.get("onem", "orta"))
            guven = ham.get("guven", "yuksek" if kaynak == "yazar_acikca" else "orta")
            gerekli(onem in DERECELER and guven in DERECELER, f"islemler[{i}] onem/guven geçersiz")
            iddia = temiz(ham.get("iddia"), f"islemler[{i}].iddia", IDDIA_AZAMI_BAYT)
            kanit = {"tarih": tarih, "alinti": temiz(ham.get("kanit"), f"islemler[{i}].kanit", KANIT_AZAMI_BAYT)}
            ayni = next((m for m in durum["maddeler"].values() if m["durum"] == "etkin" and m["tur"] == tur
                         and m["kapsam"] == kapsam and m["iddia"].casefold() == iddia.casefold()), None)
            if ayni and not eski_id:
                ayni["kanitlar"] = (ayni["kanitlar"] + [kanit])[-5:]
                ayni["guven"] = max(ayni["guven"], guven, key=SIRA.get)  # type: ignore[arg-type]
                ayni["guncellenme"] = durum["revizyon"] + 1
                makbuz.append(f"güçlendirildi {ayni['id']}: {iddia}")
                gunluk.setdefault(depo, []).append(f"{tarih} güçlendirildi {ayni['id']}")
                continue
            onek = "KP" if depo == "kitap" else "AP"
            yeni_id = f"{onek}{durum['sonraki_no']:03d}"
            durum["sonraki_no"] += 1
            celisir = [str(c) for c in ham.get("celisir", [])]
            yeni = {"id": yeni_id, "iddia": iddia, "tur": tur, "kapsam": kapsam, "onem": onem, "guven": guven,
                    "kaynak": kaynak, "durum": "celiskili" if celisir else "etkin", "kanitlar": [kanit],
                    "neden": " ".join(str(ham.get("neden", "")).split())[:240], "olusturma": durum["revizyon"] + 1,
                    "guncellenme": durum["revizyon"] + 1, "celisir": celisir}
            durum["maddeler"][yeni_id] = yeni
            for c in celisir:
                hedef = depo_al("kitap" if c.startswith("KP") else "proje")["maddeler"].get(c)
                gerekli(hedef is not None, f"celisir: {c} bulunamadı")
                assert hedef is not None
                hedef["durum"] = "celiskili"
            if eski_id:
                eski_durum = depo_al("kitap" if str(eski_id).startswith("KP") else "proje")
                eski_durum["maddeler"][eski_id]["durum"] = "yerine_gecti"
                eski_durum["maddeler"][eski_id]["yerine_gecen"] = yeni_id
                makbuz.append(f"değiştirildi {eski_id} → {yeni_id}: {iddia}")
            else:
                makbuz.append(f"eklendi {yeni_id}{' (çelişkili, karar bekliyor)' if celisir else ''}: {iddia}")
            gunluk.setdefault(depo, []).append(f"{tarih} {makbuz[-1]}")
        elif eylem in {"karar", "unut"}:
            kimlik = str(ham.get("id", ""))
            depo = "kitap" if kimlik.startswith("KP") else "proje"
            durum = depo_al(depo)
            madde = durum["maddeler"].get(kimlik)
            gerekli(madde is not None, f"{kimlik} bulunamadı")
            assert madde is not None
            if eylem == "karar":
                karar = ham.get("karar")
                gerekli(karar in {"onayla", "reddet"}, "karar 'onayla' ya da 'reddet' olmalı")
                madde["durum"] = "etkin" if karar == "onayla" else "reddedildi"
                if karar == "onayla":
                    for c in madde.get("celisir", []):
                        diger = depo_al("kitap" if c.startswith("KP") else "proje")["maddeler"].get(c)
                        if diger and diger["durum"] == "celiskili":
                            diger["durum"] = "yerine_gecti"
                            diger["yerine_gecen"] = kimlik
                makbuz.append(f"karar {kimlik}: {karar}")
            else:
                madde["durum"] = "reddedildi"
                madde["neden"] = " ".join(str(ham.get("neden", "yazar unutulmasını istedi")).split())[:240]
                makbuz.append(f"unutuldu {kimlik}")
            madde["guncellenme"] = durum["revizyon"] + 1
            gunluk.setdefault(depo, []).append(f"{tarih} {makbuz[-1]}")
        else:
            raise HafizaHatasi(f"islemler[{i}].eylem geçersiz: hatirla, degistir, karar, unut")
    for ad, (klasor, durum) in depolar.items():
        if durum["uygulanan_islemler"].get(islem_kimligi) == ozet:
            continue
        durum["revizyon"] += 1
        durum["uygulanan_islemler"][islem_kimligi] = ozet
        yaz(klasor, durum, gunluk.get(ad, []))
    if not makbuz:
        return {"tamam": True, "zaten_uygulandi": True, "makbuz": "Yazar Hafızası Makbuzu: bu işlem daha önce uygulanmış."}
    return {"tamam": True, "makbuz": "Yazar Hafızası Makbuzu: " + "; ".join(makbuz)}


def sorgula(calisma: Path, kitap: Path | None, turler: list[str] | None, tur_adi: str | None, is_akisi: str | None) -> dict[str, Any]:
    secili = set(turler or TURLER)
    if is_akisi in GOREV_BIRLESIMLERI and not turler:
        secili = set(GOREV_BIRLESIMLERI[is_akisi])
    adaylar = []
    for depo in ("proje", "kitap") if kitap else ("proje",):
        durum = oku(depo_yolu(calisma, kitap, depo))
        if not durum:
            continue
        for m in durum["maddeler"].values():
            if m["durum"] != "etkin" or m["tur"] not in secili:
                continue
            k = m["kapsam"]
            if k["duzey"] == "tur" and (not tur_adi or k["deger"].casefold() != tur_adi.casefold()):
                continue
            if k["duzey"] == "is_akisi" and (not is_akisi or k["deger"].casefold() != is_akisi.casefold()):
                continue
            adaylar.append(m)
    adaylar.sort(key=lambda m: (-SIRA[m["onem"]], m["kapsam"]["duzey"] != "kitap", -m["guncellenme"], m["id"]))
    yuklenen, atlanan, boyut = [], [], 0
    for m in adaylar:
        satir = f"{m['id']} [{TURLER[m['tur']]}] {m['iddia']}"
        ek = len(satir.encode("utf-8")) + 2
        if boyut + ek > SORGU_AZAMI_BAYT:
            atlanan.append(m["id"])
            continue
        yuklenen.append(satir)
        boyut += ek
    makbuz = f"Yazar Hafızası Makbuzu: {len(yuklenen)} tercih yüklendi"
    if atlanan:
        makbuz += f", {len(atlanan)} tercih bütçe nedeniyle atlandı ({', '.join(atlanan[:20])}); hafızayı düzenleyin"
    return {"tamam": True, "makbuz": makbuz, "tercihler": yuklenen, "atlanan": atlanan}


def denetle(calisma: Path, kitap: Path | None) -> dict[str, Any]:
    sorunlar = []
    for depo in ("proje", "kitap") if kitap else ("proje",):
        klasor = depo_yolu(calisma, kitap, depo)
        durum = oku(klasor)
        if durum is None:
            sorunlar.append(f"{depo} deposu başlatılmamış: {klasor}")
            continue
        for m in durum["maddeler"].values():
            if m["tur"] not in TURLER or m["durum"] not in DURUMLAR:
                sorunlar.append(f"{m['id']} geçersiz tür ya da durum")
        profil = klasor / "profil.md"
        if not profil.exists() or profil.read_text(encoding="utf-8") != profil_gorunumu(durum):
            sorunlar.append(f"{profil} elle değiştirilmiş ya da eski; yeniden üretmek için boş bir işlem yerine 'baslat' sonrası kaydedin")
    return {"tamam": not sorunlar, "sorunlar": sorunlar}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    for ad in ("baslat", "kaydet", "sorgula", "denetle"):
        p = alt.add_parser(ad)
        p.add_argument("--calisma-alani", required=True, type=Path)
        p.add_argument("--kitap", type=Path)
        if ad == "kaydet":
            p.add_argument("--girdi", required=True, type=Path)
        if ad == "sorgula":
            p.add_argument("--tur", action="append", choices=list(TURLER))
            p.add_argument("--tur-adi")
            p.add_argument("--is-akisi")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "baslat":
            sonuc = baslat(arg.calisma_alani, arg.kitap)
        elif arg.komut == "kaydet":
            sonuc = kaydet(arg.calisma_alani, arg.kitap, json.loads(arg.girdi.read_text(encoding="utf-8")))
        elif arg.komut == "sorgula":
            sonuc = sorgula(arg.calisma_alani, arg.kitap, arg.tur, arg.tur_adi, arg.is_akisi)
        else:
            sonuc = denetle(arg.calisma_alani, arg.kitap)
    except (HafizaHatasi, OSError, ValueError) as hata:
        print(json.dumps({"tamam": False, "hata": str(hata)}, ensure_ascii=False))
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0 if sonuc.get("tamam") else 1


if __name__ == "__main__":
    sys.exit(main())
