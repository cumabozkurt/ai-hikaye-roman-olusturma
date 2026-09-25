#!/usr/bin/env python3
"""Üretim bozulmalarını (dejenerasyon) bulur: yarım kalan metin, döngüye giren
tekrarlar, yapay zekânın kendini ele veren cümleleri ve metne sızan çalışma
notları. Bunlar zayıf ya da sıkıştırılmış bir modelin kendisinin fark
edemediği "sert sinyaller"dir; hepsi engelleyicidir (markdown artığı hariç).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

NGRAM = 8
NGRAM_TEKRAR = 3
SATIR_TEKRAR = 3
EN_AZ_KELIME = 50
BITIS_ISARETLERI = (".", "!", "?", "…", "”", "\"", "»", "'", "’", ")")


@dataclass
class Bulgu:
    dosya: str
    satir: int
    onem: str
    kural: str
    alinti: str
    oneri: str


def denetle_metin(metin: str, dosya: str = "<metin>") -> list[Bulgu]:
    metin = metin.replace("\r\n", "\n")
    satirlar = metin.split("\n")
    bulgular: list[Bulgu] = []

    def ekle(no: int, onem: str, kural: str, alinti: str, oneri: str) -> None:
        bulgular.append(Bulgu(dosya, no, onem, kural, alinti.strip()[:80], oneri))

    govde_satirlari = [(i, s) for i, s in enumerate(satirlar, 1) if s.strip() and not s.lstrip().startswith("#")]
    kelimeler = tk.KELIME.findall(" ".join(s for _, s in govde_satirlari))
    if len(kelimeler) < EN_AZ_KELIME:
        ekle(1, "engelleyici", "bos-ya-da-cok-kisa", f"{len(kelimeler)} kelime", "Metin boş ya da yazma işlemi yarım kalmış; dosyayı yeniden yazın.")
        return bulgular

    # Yarım kalan bitiş
    son_no, son = govde_satirlari[-1]
    if not son.rstrip().endswith(BITIS_ISARETLERI):
        ekle(son_no, "engelleyici", "yarim-bitis", son[-60:], "Metin cümlenin ortasında bitiyor; kesilen yeri tamamlayın.")

    # Art arda ya da sık tekrarlanan tam satırlar
    onceki = None
    sayac: Counter[str] = Counter()
    for no, s in govde_satirlari:
        anahtar = " ".join(s.split())
        if len(anahtar) >= 12 and anahtar == onceki:
            ekle(no, "engelleyici", "ardisik-tekrar", anahtar, "Aynı satır art arda tekrarlanmış; birini silin.")
        if len(anahtar) >= 25:
            sayac[anahtar] += 1
            if sayac[anahtar] == SATIR_TEKRAR:
                ekle(no, "engelleyici", "satir-tekrari", anahtar, f"Bu satır metinde {SATIR_TEKRAR} kez geçiyor; döngüye girilmiş.")
        onceki = anahtar

    # Uzun kelime dizisi döngüsü
    kucuk = [tk.tr_kucuk(k) for k in kelimeler]
    ngramlar: Counter[tuple[str, ...]] = Counter(tuple(kucuk[i:i + NGRAM]) for i in range(len(kucuk) - NGRAM + 1))
    for ngram, adet in ngramlar.most_common(3):
        if adet >= NGRAM_TEKRAR:
            ifade = " ".join(ngram)
            no = next((n for n, s in govde_satirlari if ifade.split()[0] in tk.tr_kucuk(s)), 1)
            ekle(no, "engelleyici", "tekrar-dongusu", ifade, f"{NGRAM} kelimelik dizi {adet} kez tekrarlanıyor; model döngüye girmiş.")
            break

    for no, s in govde_satirlari:
        k = tk.tr_kucuk(s)
        for ifade in tk.YZ_OZ_GONDERME:
            if ifade in k:
                ekle(no, "engelleyici", "yz-oz-gonderme", s, "Yapay zekâ kendinden söz ediyor ya da sohbet dili sızmış; satırı silin.")
                break
        for ifade in tk.MUHENDISLIK_SIZINTILARI:
            if (re.search(rf"\b{re.escape(ifade)}\b", k) if ifade.isalpha() else ifade in k):
                ekle(no, "engelleyici", "muhendislik-sizintisi", s, f"Çalışma notu ('{ifade}') metne sızmış; okurun göreceği metinden çıkarın.")
                break
        if re.match(r"^\s*(?:\d+\.\s|\*\s|\*\*[^*]+\*\*\s*:)", s):
            ekle(no, "uyari", "markdown-artigi", s, "Liste/kalın başlık biçimi düzyazıya uymuyor; paragrafa çevirin.")
    return bulgular


def denetle_dosya(yol: Path) -> list[Bulgu]:
    return denetle_metin(dosya_oku.metin_oku(yol), str(yol))


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__)
    ayr.add_argument("dosyalar", nargs="+", type=Path)
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    bulgular = [b for yol in arg.dosyalar for b in denetle_dosya(yol)]
    if arg.json:
        print(json.dumps([asdict(b) for b in bulgular], ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b.dosya}:{b.satir}\t[{b.onem}] {b.kural}\t({b.alinti})\n\t→ {b.oneri}")
        print(f"Toplam {len(bulgular)} bozulma bulgusu.")
    return 1 if any(b.onem == "engelleyici" for b in bulgular) else 0


if __name__ == "__main__":
    sys.exit(main())
