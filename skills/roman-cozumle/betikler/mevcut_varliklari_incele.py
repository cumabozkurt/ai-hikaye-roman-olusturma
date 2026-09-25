#!/usr/bin/env python3
"""Var olan bir çözümleme klasörünü salt okunur inceler ve ne yapılacağını söyler.

Kullanım::

    mevcut_varliklari_incele.py --kok cozumleme-kutuphanesi/kitap [--kisa]

Karar değerleri:
  * ``dogrudan_kullan``  bütün teslim dosyaları var; metni yeniden okumaya gerek yok
  * ``devam_et``         dizin ya da bazı özetler/aşamalar eksik
  * ``yeni_baslat``      klasör boş ya da yalnızca kaynak metin var
Klasör yoksa çıkış kodu 2 döner.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bolum_dizini as bd  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

TESLIM = ["cozumleme-raporu.md", "ozet.md", "hizli-bakis.md", "bolumler/ilk-uc-bolum.md",
          "olay-orgusu/hikaye-hatti.md", "olay-orgusu/tempo.md", "olay-orgusu/duygu-mekanizmalari.md",
          "karakterler/iliskiler.md", "iliski-semasi.md", "uslup.md", "bolum-dizini.csv"]


def incele(kok: Path) -> dict[str, Any]:
    eksik = [d for d in TESLIM if not (kok / d).is_file()]
    ozet_eksik: list[int] = []
    bolum_sayisi = 0
    if (kok / "bolum-dizini.csv").is_file():
        satirlar = [s for s in bd.dizin_oku(kok / "bolum-dizini.csv") if s["tur"] == "bolum"]
        bolum_sayisi = len(satirlar)
        ozet_eksik = [int(s["bolum"]) for s in satirlar
                      if int(s["bolum"]) > 3 and not (kok / "bolumler" / f"bolum-{int(s['bolum']):03d}_ozet.md").is_file()]
    kaynak_var = (kok / "kaynak" / "metin.txt").is_file()
    dolu = [p for p in kok.rglob("*") if p.is_file() and "kaynak" not in p.relative_to(kok).parts]
    if not eksik and not ozet_eksik:
        karar = "dogrudan_kullan"
    elif not dolu:
        karar = "yeni_baslat"
    else:
        karar = "devam_et"
    return {"karar": karar, "kaynak_metin": kaynak_var, "bolum_sayisi": bolum_sayisi,
            "eksik_dosyalar": eksik, "eksik_ozetler": ozet_eksik}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--kok", required=True, type=Path)
    ayr.add_argument("--kisa", action="store_true", help="eksik özetleri aralık olarak göster")
    arg = ayr.parse_args(argv)
    if not arg.kok.is_dir():
        print(json.dumps({"hata": f"klasör yok: {arg.kok}"}, ensure_ascii=False))
        return 2
    sonuc = incele(arg.kok)
    if arg.kisa and sonuc["eksik_ozetler"]:
        e = sonuc["eksik_ozetler"]
        araliklar, bas = [], e[0]
        for onceki, simdiki in zip(e, e[1:] + [None]):
            if simdiki != (onceki + 1 if onceki is not None else None):
                araliklar.append(f"{bas}-{onceki}" if bas != onceki else str(bas))
                bas = simdiki
        sonuc["eksik_ozetler"] = araliklar
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
