#!/usr/bin/env python3
"""Türkçe metin ölçüm çekirdeği: kelime sayımı, hedef uzunluk ve uzunluk kaydı.

Türkçe yayıncılık ve Wattpad kelime üzerinden konuşur; bu yüzden tek ölçü
``gorunur_kelime_v1``: ön bilgi (frontmatter), Markdown başlıkları ve HTML
yorumları çıkarıldıktan sonra kalan metindeki kelimeler. Kesme işaretiyle
bağlanan ekler (``Ali'nin``) ve tireli birleşikler (``yarı-resmî``) tek kelime
sayılır.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

OLCU = "gorunur_kelime_v1"
KELIME_DESENI = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+(?:['’\-][0-9A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+)*")
ON_BILGI = re.compile(r"\A---\n.*?\n---\n", re.S)
HTML_YORUM = re.compile(r"<!--.*?-->", re.S)
HEDEF_DESENI = re.compile(
    r"^\s*[-*]?\s*\**\s*Hedef uzunluk[ \t]*\**[ \t]*:[ \t]*\**[ \t]*([0-9][0-9.]*)\s*(?:kelime)?",
    re.I | re.M,
)
# Bant oranları: hedefin yüzde kaçı hangi sonuca düşer.
IC_BANT = (0.85, 1.15)
SERT_BANT = (0.60, 1.50)


class OlcumHatasi(ValueError):
    """Beklenen doğrulama hatası."""


def gerekli(kosul: bool, mesaj: str) -> None:
    if not kosul:
        raise OlcumHatasi(mesaj)


def satir_sonlarini_duzelt(metin: str) -> str:
    return metin.replace("\r\n", "\n").replace("\r", "\n")


def gorunur_govde(metin: str) -> str:
    """Sayıma girecek metni döndürür (ön bilgi, başlık ve yorumlar hariç)."""
    metin = satir_sonlarini_duzelt(metin)
    metin = ON_BILGI.sub("", metin, count=1)
    metin = HTML_YORUM.sub("", metin)
    satirlar = [s for s in metin.split("\n") if not s.lstrip().startswith("#")]
    return "\n".join(satirlar).strip()


def kelime_say(metin: str) -> int:
    return len(KELIME_DESENI.findall(gorunur_govde(metin)))


def hedef_coz(deger: Any) -> int:
    """'2.200', 2200 veya '2200 kelime' biçimlerini tamsayıya çevirir."""
    if isinstance(deger, bool):
        raise OlcumHatasi("hedef uzunluk sayı olmalı")
    if isinstance(deger, int):
        hedef = deger
    else:
        m = re.search(r"(-?)(\d{1,3}(?:[.\u00a0 ]\d{3})+(?!\d)|\d+)", str(deger or ""))
        gerekli(m is not None, f"hedef uzunluk bulunamadı: {deger!r} (ör. 2200 ya da '2.200 kelime')")
        hedef = int(re.sub(r"\D", "", m.group(2))) * (-1 if m.group(1) else 1)
    gerekli(100 <= hedef <= 50000, f"hedef uzunluk makul aralıkta değil: {hedef}")
    return hedef


def bantlari_hesapla(hedef: Any) -> dict[str, dict[str, int]]:
    h = hedef_coz(hedef)
    return {
        "ic": {"alt": round(h * IC_BANT[0]), "ust": round(h * IC_BANT[1])},
        "sert": {"alt": round(h * SERT_BANT[0]), "ust": round(h * SERT_BANT[1])},
    }


def uzunluk_degerlendir(gercek: int, hedef: Any) -> dict[str, Any]:
    """Gerçek kelime sayısını hedefe göre sınıflandırır."""
    h = hedef_coz(hedef)
    bant = bantlari_hesapla(h)
    if bant["ic"]["alt"] <= gercek <= bant["ic"]["ust"]:
        durum = "ic_gecti"
    elif gercek < bant["sert"]["alt"]:
        durum = "cok_kisa"
    elif gercek > bant["sert"]["ust"]:
        durum = "cok_uzun"
    elif gercek < bant["ic"]["alt"]:
        durum = "kisa"
    else:
        durum = "uzun"
    return {"olcu": OLCU, "gercek": gercek, "hedef": h, "durum": durum, "bantlar": bant}


def plandan_hedef(plan_metni: str) -> int:
    """Bölüm planındaki ``Hedef uzunluk:`` satırını okur; yoksa hata verir (varsayılana düşmez)."""
    eslesme = HEDEF_DESENI.search(satir_sonlarini_duzelt(plan_metni))
    gerekli(eslesme is not None, "bölüm planında 'Hedef uzunluk:' satırı yok")
    return hedef_coz(eslesme.group(1))


_NUMARA = re.compile(r"(\d{1,4})")


def dosya_bolum_no(ad: str, onek: str) -> int | None:
    if not ad.startswith(onek) or not ad.endswith(".md"):
        return None
    eslesme = _NUMARA.search(ad[len(onek):])
    return int(eslesme.group(1)) if eslesme else None


def bolum_dosyasi_bul(klasor: Path, bolum: int, *, plan: bool) -> Path:
    """``metin/bolum-007_*.md`` veya ``plan/bolum-plani_007.md`` dosyasını bulur."""
    onek = "bolum-plani_" if plan else "bolum-"
    adaylar = []
    if klasor.is_dir():
        for yol in sorted(klasor.iterdir()):
            if yol.is_file() and dosya_bolum_no(yol.name, onek) == bolum:
                if not plan and yol.name.startswith("bolum-plani_"):
                    continue
                adaylar.append(yol)
    gerekli(len(adaylar) == 1, f"{klasor} içinde {bolum}. bölüm için tek dosya bekleniyordu, {len(adaylar)} bulundu")
    return adaylar[0]


def govde_ozeti(metin: str) -> str:
    return hashlib.sha256(gorunur_govde(metin).encode("utf-8")).hexdigest()


def proje_uzunluk_kaydi(proje: Path, bolum: int, *, cozum: str = "hedef_bandinda") -> dict[str, Any]:
    """Bir bölüm için takip durumuna yazılacak uzunluk kaydını üretir."""
    plan = bolum_dosyasi_bul(proje / "plan", bolum, plan=True)
    metin_yolu = bolum_dosyasi_bul(proje / "metin", bolum, plan=False)
    metin = dosya_oku.metin_oku(metin_yolu)
    degerlendirme = uzunluk_degerlendir(kelime_say(metin), plandan_hedef(dosya_oku.metin_oku(plan)))
    gerekli(cozum in {"hedef_bandinda", "yazar_onayladi"}, "çözüm türü bilinmiyor")
    if degerlendirme["durum"] != "ic_gecti":
        gerekli(cozum == "yazar_onayladi", f"uzunluk bandın dışında ({degerlendirme['durum']}); yazar onayı gerekli")
    return {
        "olcu": OLCU,
        "gercek": degerlendirme["gercek"],
        "hedef": degerlendirme["hedef"],
        "durum": degerlendirme["durum"],
        "cozum": cozum,
        "govde_sha256": govde_ozeti(metin),
    }


def uzunluk_kaydi_dogrula(proje: Path, bolum: int, kayit: object) -> dict[str, Any]:
    """Önceden hazırlanmış kaydın hâlâ diskteki metne uyduğunu doğrular."""
    gerekli(isinstance(kayit, dict), "uzunluk kaydı nesne olmalı")
    assert isinstance(kayit, dict)
    taze = proje_uzunluk_kaydi(proje, bolum, cozum=str(kayit.get("cozum", "hedef_bandinda")))
    gerekli(kayit.get("govde_sha256") == taze["govde_sha256"], "metin, uzunluk ölçüldükten sonra değişmiş; yeniden ölçün")
    return taze


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Türkçe kelime sayacı ve uzunluk bandı denetimi")
    ayr.add_argument("dosyalar", nargs="+", type=Path)
    ayr.add_argument("--hedef", help="hedef kelime sayısı (ör. 2200)")
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    sonuc = []
    try:
        for yol in arg.dosyalar:
            sayi = kelime_say(dosya_oku.metin_oku(yol))
            kayit: dict[str, Any] = {"dosya": str(yol), "kelime": sayi}
            if arg.hedef:
                kayit.update(uzunluk_degerlendir(sayi, arg.hedef))
            sonuc.append(kayit)
    except (OlcumHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    if arg.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        for kayit in sonuc:
            ek = f" · hedef {kayit['hedef']} · {kayit['durum']}" if "hedef" in kayit else ""
            print(f"{kayit['dosya']}: {kayit['kelime']} kelime{ek}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
