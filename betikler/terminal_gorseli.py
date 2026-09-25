#!/usr/bin/env python3
"""README için gerçek komut çıktılarını terminal penceresi görünümünde SVG'ye çevirir.

Komutlar gerçekten çalıştırılır; çıktı yalnızca geçici klasör yolu kısaltılarak ve uzun
satırlar kaydırılarak çizilir. Görseller ``docs/gorseller/terminal-*.svg`` olarak yazılır.

Kullanım::

    python betikler/terminal_gorseli.py            # bütün görselleri üret
    python betikler/terminal_gorseli.py --liste    # üretilecek görselleri listele
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paylasilan" / "betikler"))
try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "docs" / "gorseller"
GENISLIK_KARAKTER = 104
SATIR_YUKSEKLIGI = 19
KARAKTER_GENISLIGI = 8.4
RENKLER = {"engelleyici": "#ff7b72", "uyari": "#e3b341", "✓": "#56d364", "!": "#e3b341", "→": "#8b949e", "$": "#79c0ff"}

# (dosya adı, pencere başlığı, gösterilen komut, gerçek argümanlar, örnek roman kopyasında mı çalışsın)
GORSELLER = [
    ("terminal-yz-tadi.svg", "Yapay zekâ tadı denetimi: önce",
     "python3 betikler/ai_kalip_denetle.py once.md",
     ["paylasilan/betikler/ai_kalip_denetle.py", "ornekler/yz-tadi-karsilastirma/once.md"], False),
    ("terminal-yz-tadi-sonra.svg", "Yapay zekâ tadı denetimi: sonra",
     "python3 betikler/ai_kalip_denetle.py sonra.md",
     ["paylasilan/betikler/ai_kalip_denetle.py", "ornekler/yz-tadi-karsilastirma/sonra.md"], False),
    ("terminal-metin-analizi.svg", "Editörün ilk okuması: metin_analizi",
     "python3 betikler/metin_analizi.py metin/bolum-001_durmus-saatler.md",
     ["paylasilan/betikler/metin_analizi.py", "ornekler/roman/saatcinin-kizi/metin/bolum-001_durmus-saatler.md"], False),
    ("terminal-e-kitap.svg", "EPUB ve okuma kopyası derleme",
     "python3 betikler/e_kitap_derle.py --proje saatcinin-kizi --yazar \"Örnek Yazar\"",
     ["skills/e-kitap-derle/betikler/e_kitap_derle.py", "--proje", "saatcinin-kizi", "--yazar", "Örnek Yazar"], True),
    ("terminal-ipucu-defteri.svg", "İpucu defteri: ekilen ipuçları ve çözüm planı",
     "python3 betikler/ipucu_defteri.py rapor --proje saatcinin-kizi",
     ["paylasilan/betikler/ipucu_defteri.py", "rapor", "--proje", "saatcinin-kizi"], True),
    ("terminal-kurgu-dagilim.svg", "Kurgu ansiklopedisi: kim hangi bölümde",
     "python3 betikler/kurgu_ansiklopedisi.py dagilim --proje saatcinin-kizi",
     ["paylasilan/betikler/kurgu_ansiklopedisi.py", "dagilim", "--proje", "saatcinin-kizi"], True),
]


def calistir(argumanlar: list[str], ornek_kopyada: bool) -> str:
    ortam = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "SOURCE_DATE_EPOCH": "1790000000"}
    with tempfile.TemporaryDirectory() as gecici:
        cwd = KOK
        betik = KOK / argumanlar[0]
        if ornek_kopyada:
            shutil.copytree(KOK / "ornekler" / "roman" / "saatcinin-kizi", Path(gecici) / "saatcinin-kizi")
            cwd = Path(gecici)
        sonuc = subprocess.run([sys.executable, str(betik), *argumanlar[1:]], cwd=cwd, env=ortam,
                               capture_output=True, text=True, encoding="utf-8", timeout=120)
        cikti = (sonuc.stdout + sonuc.stderr).replace(gecici + os.sep, "").replace(gecici, ".")
    return cikti.replace("ornekler/yz-tadi-karsilastirma/", "").replace("ornekler/roman/saatcinin-kizi/", "")


def satirlari_hazirla(komut: str, cikti: str) -> list[str]:
    satirlar = [f"$ {komut}"]
    for ham in cikti.rstrip("\n").split("\n"):
        ham = ham.replace("\t", "  ")
        girinti = len(ham) - len(ham.lstrip(" "))
        parcalar = textwrap.wrap(ham, GENISLIK_KARAKTER, subsequent_indent=" " * (girinti + 4),
                                 break_long_words=True, drop_whitespace=False) or [""]
        satirlar.extend(p.rstrip() for p in parcalar)
    return satirlar


def renk(satir: str) -> str:
    sade = satir.strip()
    if sade.startswith("$"):
        return RENKLER["$"]
    for anahtar in ("[engelleyici]", "[uyari]"):
        if anahtar in satir:
            return RENKLER[anahtar.strip("[]")]
    for anahtar in ("✓", "!", "→"):
        if sade.startswith(anahtar):
            return RENKLER[anahtar]
    return "#e6edf3"


def svg_uret(baslik: str, satirlar: list[str]) -> str:
    genislik = int(GENISLIK_KARAKTER * KARAKTER_GENISLIGI + 48)
    yukseklik = 56 + SATIR_YUKSEKLIGI * len(satirlar) + 20
    metinler = []
    for i, satir in enumerate(satirlar):
        y = 60 + i * SATIR_YUKSEKLIGI
        metinler.append(f'<text x="24" y="{y}" fill="{renk(satir)}" xml:space="preserve">{html.escape(satir)}</text>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{genislik}" height="{yukseklik}" viewBox="0 0 {genislik} {yukseklik}" role="img" aria-label="{html.escape(baslik)}">\n'
        f'<rect width="{genislik}" height="{yukseklik}" rx="10" fill="#0d1117"/>\n'
        f'<rect width="{genislik}" height="32" rx="10" fill="#161b22"/><rect y="22" width="{genislik}" height="10" fill="#161b22"/>\n'
        '<circle cx="20" cy="16" r="6" fill="#ff5f56"/><circle cx="40" cy="16" r="6" fill="#ffbd2e"/><circle cx="60" cy="16" r="6" fill="#27c93f"/>\n'
        f'<text x="{genislik // 2}" y="21" text-anchor="middle" fill="#8b949e" font-family="\'Segoe UI\', Arial, sans-serif" font-size="13">{html.escape(baslik)}</text>\n'
        '<g font-family="\'DejaVu Sans Mono\', \'Cascadia Mono\', Menlo, Consolas, monospace" font-size="14">\n'
        + "\n".join(metinler) + "\n</g>\n</svg>\n"
    )


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--liste", action="store_true", help="üretilecek görselleri listele, çalıştırma")
    ayr.add_argument("--cikti", type=Path, default=HEDEF, help="görsellerin yazılacağı klasör")
    arg = ayr.parse_args(argv)
    if arg.liste:
        for ad, baslik, komut, _, _ in GORSELLER:
            print(f"{ad}\t{baslik}\t$ {komut}")
        return 0
    arg.cikti.mkdir(parents=True, exist_ok=True)
    for ad, baslik, komut, argumanlar, kopyada in GORSELLER:
        (arg.cikti / ad).write_text(svg_uret(baslik, satirlari_hazirla(komut, calistir(argumanlar, kopyada))), encoding="utf-8")
        print(f"yazıldı: {arg.cikti / ad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
