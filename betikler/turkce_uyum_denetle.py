#!/usr/bin/env python3
"""Türkçe uyum denetimi: Çince/Japonca/Korece (CJK) karakter ve Türkçe karakter hataları.

Kullanım::

    python betikler/turkce_uyum_denetle.py [--json] [YOL ...]

Denetimler:
  1. ``cjk``: Deponun bütün metin dosyalarında Han/CJK, Hiragana/Katakana, Hangul ve tam
     genişlikli noktalama karakterleri. Tek bir karakter bile hatadır.
  2. ``ascii-turkce``: Markdown belgelerinin düzyazısında (kod blokları, satır içi kod,
     bağlantı adresleri ve tire/alt çizgili tanımlayıcılar hariç) Türkçe harfleri yitirmiş
     yaygın sözcükler (ör. "Turkce", "icin", "degil", "Tesekkur").
  3. ``yazim``: Belgelerde sık yazım yanlışları (ör. "herkez", "birşey", "yanlız", "şuan").
  4. ``kodlama``: UTF-8 olmayan dosya ya da bozuk karakter (U+FFFD).
  5. ``ingilizce``: Belge düzyazısında İngilizce işlev sözcükleri (the, and, with, you …).
Çıkış: 0 temiz, 1 bulgu var.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paylasilan" / "betikler"))
try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KOK = Path(__file__).resolve().parent.parent
METIN_UZANTILARI = {".md", ".py", ".json", ".ts", ".toml", ".yml", ".yaml", ".txt", ".html", ".sh", ".ps1", ".sablon", ".ini", ".cfg", ".csv"}
ATLANAN = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".ruff_cache"}
CJK = re.compile("[\u2E80-\u2FDF\u3000-\u303F\u3040-\u30FF\u3100-\u31FF\u3400-\u4DBF\u4E00-\u9FFF\uA960-\uA97F\uAC00-\uD7AF\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFFEF\U00020000-\U0002FA1F]")
ASCII_YANLIS = {
    "turkce": "Türkçe", "turkiye": "Türkiye", "icin": "için", "degil": "değil", "tesekkur": "teşekkür",
    "tesekkurler": "teşekkürler", "cok": "çok", "gore": "göre", "boyle": "böyle", "simdi": "şimdi",
    "ornek": "örnek", "ornegin": "örneğin", "bolum": "bölüm", "bolumu": "bölümü", "bolumler": "bölümler",
    "ozet": "özet", "ozellik": "özellik", "ozellikler": "özellikler", "guncel": "güncel",
    "guncelleme": "güncelleme", "kullanici": "kullanıcı", "kullanim": "kullanım", "olustur": "oluştur",
    "olusturma": "oluşturma", "dosyasi": "dosyası", "yazim": "yazım", "gorev": "görev", "gecis": "geçiş",
    "baslik": "başlık", "icerik": "içerik", "asama": "aşama", "baglanti": "bağlantı", "ayrinti": "ayrıntı",
    "kisa": "kısa", "oyku": "öykü", "sureklilik": "süreklilik", "yapay zeka": "yapay zekâ",
    "hikayeler": "hikâyeler", "katki": "katkı", "lisans": None,
}
YAZIM_YANLIS = {
    "herkez": "herkes", "birşey": "bir şey", "herşey": "her şey", "yanlız": "yalnız", "şuan": "şu an",
    "pekçok": "pek çok", "hiçbirşey": "hiçbir şey", "yalnış": "yanlış", "orjinal": "orijinal",
    "süpriz": "sürpriz", "kirpik": None, "eşortman": "eşofman", "entellektüel": "entelektüel",
    "kaynak ve tesekkur": "Kaynak ve Teşekkür",
}
INGILIZCE = {"the", "and", "with", "you", "your", "should", "must", "this", "that", "from", "into", "which", "when"}
# Bilerek yanlış yazımları listeleyen dosyalar (denetim kuralları, kural belgeleri) yazım denetiminden muaftır.
YAZIM_MUAF = {"tdk-yazim-rehberi.md", "INCELEME-RAPORU.md"}
# Satır sonuna HTML yorumu olarak eklenirse o satırın yazım denetimi atlanır (bilinçli yanlış örnekler için).
YOKSAY = "turkce-uyum: yoksay"
YOKSAY_ISARET = "\x00"
TANIMLAYICI = re.compile(r"[\w.]*[-_/][\w./-]*")


def tr_kucuk(metin: str) -> str:
    return metin.replace("I", "ı").replace("İ", "i").lower()


def _goreli(p: Path) -> Path:
    return p.relative_to(KOK) if p.is_relative_to(KOK) else p


def metin_dosyalari(yollar: list[Path]) -> list[Path]:
    sonuc = []
    for yol in yollar:
        adaylar = [yol] if yol.is_file() else yol.rglob("*")
        for p in adaylar:
            if p.is_file() and not p.is_symlink() and p.suffix in METIN_UZANTILARI and not (set(_goreli(p).parts) & ATLANAN):
                sonuc.append(p)
    return sorted(set(sonuc))


def duzyazi(metin: str) -> list[tuple[int, str]]:
    """Markdown'dan kod blokları, satır içi kod, bağlantı adresleri, HTML yorumları ve ön bilgi atılmış satırlar."""
    satirlar = []
    blokta = False
    on_bilgi = metin.startswith("---\n")
    for no, satir in enumerate(metin.split("\n"), start=1):
        if on_bilgi:
            if no > 1 and satir.strip() == "---":
                on_bilgi = False
            # ön bilgide yalnızca description alanı düzyazıdır
            if satir.startswith("description:"):
                satirlar.append((no, _temizle(satir[len("description:"):])))
            continue
        if satir.lstrip().startswith(("```", "~~~")):
            blokta = not blokta
            continue
        if blokta:
            continue
        satirlar.append((no, _temizle(satir) + (YOKSAY_ISARET if YOKSAY in satir else "")))
    return satirlar


def _temizle(satir: str) -> str:
    s = re.sub(r"`[^`]*`", " ", satir)
    s = re.sub(r"\]\([^)]*\)", "]", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    return TANIMLAYICI.sub(" ", s)


def denetle(yollar: list[Path]) -> list[dict[str, object]]:
    bulgular: list[dict[str, object]] = []
    for p in metin_dosyalari(yollar):
        goreli = _goreli(p).as_posix()
        try:
            metin = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bulgular.append({"dosya": goreli, "satir": 0, "kural": "kodlama", "bulunan": "", "oneri": "UTF-8 olmalı"})
            continue
        for no, satir in enumerate(metin.split("\n"), start=1):
            for m in CJK.finditer(satir):
                bulgular.append({"dosya": goreli, "satir": no, "kural": "cjk", "bulunan": m.group(0),
                                 "oneri": "CJK karakteri kaldırın; bütün içerik Türkçe olmalı"})
            if "\ufffd" in satir:
                bulgular.append({"dosya": goreli, "satir": no, "kural": "kodlama", "bulunan": "\ufffd",
                                 "oneri": "bozuk karakter (U+FFFD); dosyayı UTF-8 olarak yeniden kaydedin"})
        if p.suffix != ".md":
            continue
        for no, satir in duzyazi(metin):
            kucuk = tr_kucuk(satir)
            for yanlis, dogru in ASCII_YANLIS.items():
                if dogru and re.search(rf"(?<![\wçğıöşüâîû]){re.escape(yanlis)}(?![\wçğıöşüâîû])", kucuk):
                    bulgular.append({"dosya": goreli, "satir": no, "kural": "ascii-turkce", "bulunan": yanlis, "oneri": dogru})
            if p.name not in YAZIM_MUAF and YOKSAY_ISARET not in satir:
                for yanlis, dogru in YAZIM_YANLIS.items():
                    if dogru and re.search(rf"(?<![\wçğıöşüâîû]){re.escape(yanlis)}(?![\wçğıöşüâîû])", kucuk):
                        bulgular.append({"dosya": goreli, "satir": no, "kural": "yazim", "bulunan": yanlis, "oneri": dogru})
            for kelime in re.findall(r"[a-z]+", kucuk):
                if kelime in INGILIZCE:
                    bulgular.append({"dosya": goreli, "satir": no, "kural": "ingilizce", "bulunan": kelime,
                                     "oneri": "Türkçe karşılığını kullanın ya da özel adı kod içine alın"})
    return bulgular


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("yollar", nargs="*", type=Path, help="denetlenecek dosya ya da klasörler (varsayılan: depo kökü)")
    ayr.add_argument("--json", action="store_true", help="bulguları JSON olarak yaz")
    arg = ayr.parse_args(argv)
    eksik = [str(p) for p in arg.yollar if not p.exists()]
    if eksik:
        ayr.error("bulunamayan yol: " + ", ".join(eksik))
    yollar = [p.resolve() for p in arg.yollar] or [KOK]
    bulgular = denetle(yollar)
    if arg.json:
        print(json.dumps({"tamam": not bulgular, "bulgular": bulgular}, ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b['dosya']}:{b['satir']}: [{b['kural']}] “{b['bulunan']}” → {b['oneri']}")
        cjk = sum(1 for b in bulgular if b["kural"] == "cjk")
        print(f"Türkçe uyum: {len(bulgular)} bulgu (CJK: {cjk}).")
    return 0 if not bulgular else 1


if __name__ == "__main__":
    sys.exit(main())
