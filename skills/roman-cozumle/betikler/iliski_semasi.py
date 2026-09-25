#!/usr/bin/env python3
"""karakterler/iliskiler.md tablosundan Mermaid ilişki şeması üretir.

Kullanım::

    iliski_semasi.py --kok cozumleme-kutuphanesi/kitap        # iliski-semasi.md yazar
    iliski_semasi.py --dosya kurgu/iliskiler.md --cikti -      # kendi kitabınız için, stdout

Beklenen tablo (başlık adları büyük/küçük harf duyarsız)::

    | Kimden | Kime | İlişki | Bölüm | Not |
    |---|---|---|---|---|
    | Defne | Kerem | güvensizlik → iş birliği | 2 | kapaktaki tarih |

Aynı çiftin birden çok satırı varsa şemada son durum gösterilir, gelişim ayrıca listelenir.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

BASLIKLAR = {"kimden": ("kimden", "karakter a", "a"), "kime": ("kime", "karakter b", "b"),
             "iliski": ("ilişki", "iliski", "tür"), "bolum": ("bölüm", "bolum"), "not": ("not", "açıklama")}


class SemaHatasi(ValueError):
    pass


def hucreler(satir: str) -> list[str]:
    return [h.strip() for h in satir.strip().strip("|").split("|")]


def iliskileri_oku(metin: str) -> list[dict[str, str]]:
    satirlar = [s for s in metin.splitlines() if s.strip().startswith("|")]
    if len(satirlar) < 2:
        raise SemaHatasi("ilişki tablosu bulunamadı ('| Kimden | Kime | İlişki | Bölüm | Not |')")
    baslik = [h.replace("I", "ı").replace("İ", "i").lower() for h in hucreler(satirlar[0])]
    sira = {}
    for anahtar, adlar in BASLIKLAR.items():
        for i, h in enumerate(baslik):
            if h in adlar:
                sira[anahtar] = i
                break
    if not {"kimden", "kime", "iliski"} <= sira.keys():
        raise SemaHatasi("tabloda Kimden, Kime ve İlişki sütunları olmalı")
    sonuc = []
    for s in satirlar[2:]:
        h = hucreler(s)
        kayit = {k: (h[i] if i < len(h) else "") for k, i in sira.items()}
        if kayit["kimden"] and kayit["kime"]:
            sonuc.append(kayit)
    return sonuc


def kimlik(ad: str, tablo: dict[str, str]) -> str:
    if ad not in tablo:
        tablo[ad] = f"K{len(tablo) + 1}"
    return tablo[ad]


def etiket(metin: str) -> str:
    return re.sub(r'["\[\]{}|<>]', "", metin).strip() or "…"


def sema_metni(baslik: str, iliskiler: list[dict[str, str]]) -> str:
    son: dict[tuple[str, str], dict[str, str]] = {}
    gelisim: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in iliskiler:
        cift = (r["kimden"], r["kime"])
        son[cift] = r
        gelisim.setdefault(cift, []).append(r)
    kimlikler: dict[str, str] = {}
    satir = [f"# İlişki Şeması: {baslik}", "", "```mermaid", "graph LR"]
    for (a, b), r in son.items():
        ka, kb = kimlik(a, kimlikler), kimlik(b, kimlikler)
        satir.append(f'  {ka}["{etiket(a)}"] -->|"{etiket(r["iliski"])}"| {kb}["{etiket(b)}"]')
    satir += ["```", "", "## Gelişim", ""]
    for (a, b), liste in gelisim.items():
        adimlar = " → ".join(f"{etiket(r['iliski'])}" + (f" ({r.get('bolum')}. bölüm)" if r.get("bolum") else "") for r in liste)
        satir.append(f"- **{a} → {b}:** {adimlar}")
    return "\n".join(satir) + "\n"


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grup = ayr.add_mutually_exclusive_group(required=True)
    grup.add_argument("--kok", type=Path)
    grup.add_argument("--dosya", type=Path)
    ayr.add_argument("--cikti", help="çıktı dosyası; '-' stdout")
    arg = ayr.parse_args(argv)
    kaynak = arg.dosya or arg.kok / "karakterler" / "iliskiler.md"
    try:
        iliskiler = iliskileri_oku(kaynak.read_text(encoding="utf-8"))
    except OSError:
        print(f"Dosya okunamadı: {kaynak}", file=sys.stderr)
        return 2
    except SemaHatasi as hata:
        print(f"Hata: {hata}", file=sys.stderr)
        return 1
    baslik = (arg.kok.name if arg.kok else kaynak.parent.parent.name) or "kitap"
    metin = sema_metni(baslik, iliskiler)
    cikti = arg.cikti or (str(arg.kok / "iliski-semasi.md") if arg.kok else "-")
    if cikti == "-":
        sys.stdout.write(metin)
    else:
        Path(cikti).write_text(metin, encoding="utf-8", newline="\n")
        print(f"Yazıldı: {cikti} ({len(iliskiler)} ilişki)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
