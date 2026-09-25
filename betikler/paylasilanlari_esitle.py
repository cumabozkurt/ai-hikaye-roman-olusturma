#!/usr/bin/env python3
"""Paylaşılan betik ve kaynakları becerilere kopyalar (tek doğru kaynak: paylasilan/).

Beceriler bağımsız kurulabilsin diye (npx skills, ClawHub, elle kopyalama) her beceri
ihtiyaç duyduğu dosyaların kendi kopyasını taşır. Bu betik o kopyaları üretir;
``--denetle`` ile yalnızca eşitliği doğrular (CI bunu çalıştırır).

Kullanım:
    python betikler/paylasilanlari_esitle.py            # kopyala
    python betikler/paylasilanlari_esitle.py --denetle  # fark varsa çıkış kodu 1
"""
from __future__ import annotations

import argparse
import ast
import filecmp
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paylasilan" / "betikler"))
try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KOK = Path(__file__).resolve().parent.parent
PAYLASILAN = KOK / "paylasilan"
YAPILANDIRMA = KOK / "betikler" / "paylasilan_dosyalar.json"


def yerel_bagimliliklar(dosya: Path) -> set[str]:
    """Bir betiğin ``import x`` ile çağırdığı paylaşılan modülleri bulur."""
    agac = ast.parse(dosya.read_text(encoding="utf-8"))
    adlar: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Import):
            adlar.update(a.name.split(".")[0] for a in dugum.names)
        elif isinstance(dugum, ast.ImportFrom) and dugum.module and dugum.level == 0:
            adlar.add(dugum.module.split(".")[0])
    metin = dosya.read_text(encoding="utf-8")
    if '"metin_olcum.py"' in metin or "'metin_olcum.py'" in metin:
        adlar.add("metin_olcum")
    return {f"{a}.py" for a in adlar if (PAYLASILAN / "betikler" / f"{a}.py").is_file()}


def kapanis(dosyalar: list[str]) -> list[str]:
    sonuc: set[str] = set()
    bekleyen = list(dosyalar)
    while bekleyen:
        ad = bekleyen.pop()
        if ad in sonuc:
            continue
        yol = PAYLASILAN / "betikler" / ad
        if not yol.is_file():
            raise SystemExit(f"Paylaşılan betik bulunamadı: {yol}")
        sonuc.add(ad)
        bekleyen.extend(yerel_bagimliliklar(yol) - sonuc)
    return sorted(sonuc)


def plan() -> list[tuple[Path, Path]]:
    yap = json.loads(YAPILANDIRMA.read_text(encoding="utf-8"))
    ciftler: list[tuple[Path, Path]] = []
    for beceri, dosyalar in yap["betikler"].items():
        hedef_kok = KOK / "skills" / beceri
        if not hedef_kok.is_dir():
            raise SystemExit(f"Beceri dizini yok: {hedef_kok}")
        # Becerinin kendi betiklerinin (paylaşılan olmayanlar) içe aktardığı paylaşılan modüller de eklenir.
        yerel = [p for p in sorted((hedef_kok / "betikler").glob("*.py")) if not (PAYLASILAN / "betikler" / p.name).is_file()]
        ek = set().union(*(yerel_bagimliliklar(p) for p in yerel)) if yerel else set()
        for ad in kapanis(sorted(set(dosyalar) | ek)):
            ciftler.append((PAYLASILAN / "betikler" / ad, hedef_kok / "betikler" / ad))
    for kaynak, beceriler in yap["kaynaklar"].items():
        yol = PAYLASILAN / "kaynaklar" / kaynak
        for beceri in beceriler:
            hedef = KOK / "skills" / beceri / "kaynaklar" / kaynak
            if yol.is_dir():
                for alt in sorted(yol.rglob("*")):
                    if alt.is_file():
                        ciftler.append((alt, hedef / alt.relative_to(yol)))
            elif yol.is_file():
                ciftler.append((yol, hedef))
            else:
                raise SystemExit(f"Paylaşılan kaynak bulunamadı: {yol}")
    return ciftler


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--denetle", action="store_true", help="kopyalamadan eşitliği denetle")
    ns = ap.parse_args(argv)
    farklar = []
    for kaynak, hedef in plan():
        if hedef.is_file() and filecmp.cmp(kaynak, hedef, shallow=False):
            continue
        farklar.append(hedef)
        if not ns.denetle:
            hedef.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(kaynak, hedef)
    goreli = [str(f.relative_to(KOK)) for f in farklar]
    if ns.denetle:
        if goreli:
            print("Eşit olmayan kopyalar (python betikler/paylasilanlari_esitle.py çalıştırın):")
            print("\n".join(f"  - {g}" for g in goreli))
            return 1
        print("Tüm paylaşılan kopyalar eşit.")
        return 0
    print(f"{len(goreli)} dosya güncellendi." if goreli else "Güncellenecek dosya yok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
