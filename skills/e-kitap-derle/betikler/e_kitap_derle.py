#!/usr/bin/env python3
"""Markdown bölümlerinden EPUB 3, HTML, DOCX, ODT, baskıya hazır HTML/PDF, TXT ve tek Markdown derler.

Yalnızca Python standart kütüphanesiyle çalışır (pandoc gerekmez). Desteklenen
Markdown alt kümesi: ``#``/``##`` başlıklar, paragraflar, ``**kalın**``,
``*italik*``, ``>`` alıntı, konuşma çizgisiyle (—) başlayan diyalog satırları ve
``***`` / ``* * *`` / ``---`` sahne ayraçları. Ön bilgi (frontmatter) ve HTML
yorumları atlanır.

Kullanım::

    python3 e_kitap_derle.py --proje kitaplar/saatcinin-kizi --yazar "Ad Soyad"
    python3 e_kitap_derle.py --dosya oyku/son-vapur/metin.md --baslik "Son Vapur" --bicim html
    python3 e_kitap_derle.py --proje kitaplar/saatcinin-kizi --yazar "Ad Soyad" --bicim docx pdf

Biçimler (``--bicim``, birden çok verilebilir): ``epub``, ``html`` (okuma kopyası), ``docx``
ve ``odt`` (yayınevine gönderim biçimi: A4, Times New Roman 12 punto, 1,5 satır aralığı,
2,5 cm kenar boşluğu, üst bilgide "Soyad / Kitap adı", altta sayfa numarası), ``yazdir``
(A5 baskıya hazır HTML), ``pdf`` (``yazdir`` çıktısını yüklü Chrome/Chromium/Edge ile
PDF'ye çevirir; tarayıcı yoksa açıklayıcı hata verir), ``txt``, ``md`` ve ``hepsi``
(epub, html, docx, odt, yazdir; varsayılan).

Bitmemiş metin işareti ([TK], [DOLDUR], ⟦…⟧, TODO) bulunan bölümler varsa derleme
durur; taslak okuma kopyası için ``--taslak`` verin. Aynı girdi ve aynı
``SOURCE_DATE_EPOCH`` ile üretilen EPUB bayt bayt aynıdır.

Çıkış kodu: 0 başarılı, 1 bitmemiş işaret nedeniyle durdu, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import sys
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import belge_yazicilar as by  # noqa: E402
import dosya_oku  # noqa: E402
import metin_analizi  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    from turkce_argparse import hata_iletisi
except ImportError:  # pragma: no cover
    hata_iletisi = str  # type: ignore[assignment]

SABIT_ZAMAN = (2020, 1, 1, 0, 0, 0)
ON_BILGI = re.compile(r"\A---\n.*?\n---\n", re.S)
HTML_YORUM = re.compile(r"<!--.*?-->", re.S)
SAHNE_AYRACI = re.compile(r"^\s*(?:\*\s*\*\s*\*|-{3,}|⁂|#\s*#\s*#)\s*$")
BOLUM_DOSYASI = re.compile(r"^bolum-(\d{1,4})(?:[_-].*)?\.md$")
BICIMLER = ("epub", "html", "docx", "odt", "yazdir", "pdf", "txt", "md")
HEPSI = ("epub", "html", "docx", "odt", "yazdir")
KAPAK_TURLERI = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

CSS = """body { font-family: Georgia, "Times New Roman", serif; line-height: 1.55; margin: 0 5%; }
h1 { font-size: 1.5em; text-align: center; margin: 2em 0 1.5em; page-break-before: always; }
h2 { font-size: 1.2em; margin: 1.5em 0 .8em; }
p { margin: 0; text-indent: 1.4em; text-align: justify; hyphens: auto; }
p.ilk, h1 + p, h2 + p, hr + p { text-indent: 0; }
p.diyalog { text-indent: 1.4em; }
hr.sahne { border: 0; text-align: center; margin: 1.2em 0; }
hr.sahne::after { content: "* * *"; letter-spacing: .5em; }
blockquote { margin: 1em 2em; font-style: italic; }
.kunye { text-align: center; margin-top: 30%; }
.kunye p { text-indent: 0; text-align: center; }
"""

HTML_EK_CSS = """body { max-width: 38em; margin: 0 auto; padding: 1.5em; background: #fbf8f1; color: #222; font-size: 1.1em; }
nav.icindekiler { border-bottom: 1px solid #ccc; margin-bottom: 2em; padding-bottom: 1em; }
nav.icindekiler p { text-indent: 0; }
@media (prefers-color-scheme: dark) { body { background: #1d1c1a; color: #e8e2d4; } a { color: #d9b36c; } }
"""


class DerlemeHatasi(ValueError):
    """Beklenen kullanım hatası."""


@dataclass
class Bolum:
    baslik: str
    govde_html: str
    kaynak: str
    # Biçimden bağımsız blok listesi: (tür, satır içi Markdown). Türler: p, ilk, diyalog, h2, alinti, ayrac.
    bloklar: list[tuple[str, str]] = field(default_factory=list)


def satir_ici(metin: str) -> str:
    metin = html.escape(metin, quote=False)
    metin = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", metin)
    metin = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", metin)
    metin = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", metin)
    return metin


def markdown_bolum(ham: str, varsayilan_baslik: str, kaynak: str) -> Bolum:
    """Bir bölüm dosyasını başlık ve XHTML gövdesine çevirir."""
    metin = ham.replace("\r\n", "\n").replace("\r", "\n")
    metin = ON_BILGI.sub("", metin, count=1)
    metin = HTML_YORUM.sub("", metin)
    baslik = ""
    parcalar: list[str] = []
    paragraf: list[str] = []
    alinti: list[str] = []
    bloklar: list[tuple[str, str]] = []

    def paragraf_bitir() -> None:
        if paragraf:
            satir = " ".join(s.strip() for s in paragraf)
            diyalog = satir.startswith(("—", "–"))
            sinif = ' class="diyalog"' if diyalog else ""
            parcalar.append(f"<p{sinif}>{satir_ici(satir)}</p>")
            bloklar.append(("diyalog" if diyalog else "p", satir))
            paragraf.clear()
        if alinti:
            parcalar.append("<blockquote><p>" + satir_ici(" ".join(alinti)) + "</p></blockquote>")
            bloklar.append(("alinti", " ".join(alinti)))
            alinti.clear()

    for satir in metin.split("\n"):
        sade = satir.strip()
        if not sade:
            paragraf_bitir()
            continue
        if SAHNE_AYRACI.match(sade):
            paragraf_bitir()
            parcalar.append('<hr class="sahne"/>')
            bloklar.append(("ayrac", ""))
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", sade)
        if m:
            paragraf_bitir()
            if len(m.group(1)) == 1 and not baslik:
                baslik = m.group(2)
            else:
                parcalar.append(f"<h2>{satir_ici(m.group(2))}</h2>")
                bloklar.append(("h2", m.group(2)))
            continue
        if sade.startswith(">"):
            if paragraf:
                paragraf_bitir()
            alinti.append(sade.lstrip(">").strip())
            continue
        if alinti:
            paragraf_bitir()
        if sade.startswith(("—", "–")) and paragraf:
            paragraf_bitir()  # her replik kendi paragrafıdır
        paragraf.append(sade)
    paragraf_bitir()
    if parcalar and parcalar[0].startswith("<p>"):
        parcalar[0] = '<p class="ilk">' + parcalar[0][3:]
    if bloklar and bloklar[0][0] == "p":
        bloklar[0] = ("ilk", bloklar[0][1])
    return Bolum(baslik or varsayilan_baslik, "\n".join(parcalar), kaynak, bloklar)


def proje_bolumleri(proje: Path) -> list[Path]:
    klasor = proje / "metin"
    if not klasor.is_dir():
        raise DerlemeHatasi(f"bölüm klasörü yok: {klasor}")
    numarali = []
    for yol in klasor.iterdir():
        m = BOLUM_DOSYASI.match(yol.name)
        if m and yol.is_file():
            numarali.append((int(m.group(1)), yol))
    if not numarali:
        raise DerlemeHatasi(f"{klasor} içinde bolum-NNN_*.md dosyası yok")
    numarali.sort()
    gorulen: dict[int, Path] = {}
    for no, yol in numarali:
        if no in gorulen:
            raise DerlemeHatasi(f"{no}. bölüm için iki dosya var: {gorulen[no].name}, {yol.name}")
        gorulen[no] = yol
    return [yol for _, yol in numarali]


def proje_basligi(proje: Path) -> str:
    plan = proje / "plan" / "genel-plan.md"
    if plan.is_file():
        m = re.search(r"^#\s+(.+?)\s*(?:[—–-]\s*Genel Plan)?\s*$", dosya_oku.metin_oku(plan), re.M)
        if m:
            return m.group(1).strip()
    return proje.resolve().name.replace("-", " ").title()


def yayin_zamani() -> dt.datetime:
    kaynak = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if kaynak:
        try:
            return dt.datetime.fromtimestamp(int(kaynak), dt.timezone.utc)
        except (ValueError, OverflowError, OSError) as hata:
            raise DerlemeHatasi(f"SOURCE_DATE_EPOCH geçersiz: {kaynak!r}") from hata
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def xhtml_sayfa(baslik: str, govde: str, *, css: str = "stil.css") -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="tr" xml:lang="tr">\n'
        f'<head><meta charset="utf-8"/><title>{html.escape(re.sub(r"[*_]", "", baslik))}</title>'
        f'<link rel="stylesheet" type="text/css" href="{css}"/></head>\n<body>\n{govde}\n</body>\n</html>\n'
    )


def epub_yaz(hedef: Path, baslik: str, yazar: str, bolumler: list[Bolum], kapak: Path | None, zaman: dt.datetime) -> None:
    kimlik = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'ai-hikaye:' + baslik + '|' + yazar)}"
    degistirilme = zaman.strftime("%Y-%m-%dT%H:%M:%SZ")
    b_esc, y_esc = html.escape(baslik), html.escape(yazar)
    manifest = ['<item id="nav" href="icindekiler.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
                '<item id="stil" href="stil.css" media-type="text/css"/>',
                '<item id="kunye" href="kunye.xhtml" media-type="application/xhtml+xml"/>']
    omurga = []
    dosyalar: dict[str, str | bytes] = {}
    if kapak:
        uzanti = kapak.suffix.lower()
        dosyalar[f"OEBPS/kapak{uzanti}"] = kapak.read_bytes()
        manifest.append(f'<item id="kapak-gorsel" href="kapak{uzanti}" media-type="{KAPAK_TURLERI[uzanti]}" properties="cover-image"/>')
        manifest.append('<item id="kapak" href="kapak.xhtml" media-type="application/xhtml+xml"/>')
        omurga.append('<itemref idref="kapak" linear="yes"/>')
        dosyalar["OEBPS/kapak.xhtml"] = xhtml_sayfa(baslik, f'<div style="text-align:center"><img src="kapak{uzanti}" alt="{b_esc} kapağı" style="max-width:100%"/></div>')
    omurga.append('<itemref idref="kunye"/>')
    dosyalar["OEBPS/kunye.xhtml"] = xhtml_sayfa(baslik, f'<div class="kunye"><h1>{b_esc}</h1><p>{y_esc}</p></div>')
    nav_ogeleri, ncx_ogeleri = [], []
    for i, bolum in enumerate(bolumler, 1):
        ad = f"bolum-{i:03d}.xhtml"
        manifest.append(f'<item id="b{i:03d}" href="{ad}" media-type="application/xhtml+xml"/>')
        omurga.append(f'<itemref idref="b{i:03d}"/>')
        baslik_html = satir_ici(bolum.baslik)
        dosyalar[f"OEBPS/{ad}"] = xhtml_sayfa(bolum.baslik, f'<section epub:type="chapter"><h1>{baslik_html}</h1>\n{bolum.govde_html}</section>')
        nav_ogeleri.append(f'<li><a href="{ad}">{baslik_html}</a></li>')
        ncx_ogeleri.append(f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{html.escape(bolum.baslik)}</text></navLabel><content src="{ad}"/></navPoint>')
    dosyalar["OEBPS/icindekiler.xhtml"] = xhtml_sayfa(
        "İçindekiler", '<nav epub:type="toc" id="toc"><h1>İçindekiler</h1><ol>' + "".join(nav_ogeleri) + "</ol></nav>")
    dosyalar["OEBPS/toc.ncx"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
        f'<head><meta name="dtb:uid" content="{kimlik}"/></head><docTitle><text>{b_esc}</text></docTitle>'
        f'<navMap>{"".join(ncx_ogeleri)}</navMap></ncx>\n')
    dosyalar["OEBPS/stil.css"] = CSS
    dosyalar["OEBPS/icerik.opf"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="kimlik" xml:lang="tr">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'<dc:identifier id="kimlik">{kimlik}</dc:identifier>\n<dc:title>{b_esc}</dc:title>\n'
        f'<dc:creator>{y_esc}</dc:creator>\n<dc:language>tr</dc:language>\n'
        f'<meta property="dcterms:modified">{degistirilme}</meta>\n'
        + ('<meta name="cover" content="kapak-gorsel"/>\n' if kapak else "")
        + '</metadata>\n<manifest>\n' + "\n".join(manifest) + '\n</manifest>\n'
        '<spine toc="ncx">\n' + "\n".join(omurga) + '\n</spine>\n</package>\n')
    container = ('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="OEBPS/icerik.opf" media-type="application/oebps-package+xml"/>'
                 '</rootfiles></container>\n')
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(hedef.suffix + ".tmp")
    with zipfile.ZipFile(gecici, "w") as zf:
        bilgi = zipfile.ZipInfo("mimetype", SABIT_ZAMAN)
        bilgi.compress_type = zipfile.ZIP_STORED
        zf.writestr(bilgi, "application/epub+zip")
        for ad, icerik in [("META-INF/container.xml", container), *sorted(dosyalar.items())]:
            bilgi = zipfile.ZipInfo(ad, SABIT_ZAMAN)
            bilgi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(bilgi, icerik.encode("utf-8") if isinstance(icerik, str) else icerik)
    os.replace(gecici, hedef)


def html_yaz(hedef: Path, baslik: str, yazar: str, bolumler: list[Bolum]) -> None:
    icindekiler = "".join(f'<li><a href="#bolum-{i}">{satir_ici(b.baslik)}</a></li>' for i, b in enumerate(bolumler, 1))
    govde = "\n".join(f'<section id="bolum-{i}"><h1>{satir_ici(b.baslik)}</h1>\n{b.govde_html}</section>'
                      for i, b in enumerate(bolumler, 1))
    sayfa = ("<!DOCTYPE html>\n<html lang=\"tr\">\n<head>\n<meta charset=\"utf-8\"/>\n"
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>\n"
             f"<title>{html.escape(re.sub(r'[*_]', '', baslik))}</title>\n<style>\n{CSS}{HTML_EK_CSS}</style>\n</head>\n<body>\n"
             f'<header class="kunye"><h1>{html.escape(baslik)}</h1><p>{html.escape(yazar)}</p></header>\n'
             f'<nav class="icindekiler"><p><strong>İçindekiler</strong></p><ol>{icindekiler}</ol></nav>\n'
             f"{govde}\n</body>\n</html>\n")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(sayfa, encoding="utf-8")


def dosya_adi(baslik: str) -> str:
    tablo = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")
    ad = re.sub(r"[^a-z0-9]+", "-", baslik.translate(tablo).lower()).strip("-")
    return ad or "kitap"


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    kaynak = ayr.add_mutually_exclusive_group(required=True)
    kaynak.add_argument("--proje", type=Path, help="kitap klasörü (metin/bolum-NNN_*.md dosyaları okunur)")
    kaynak.add_argument("--dosya", type=Path, nargs="+", help="sırasıyla derlenecek Markdown dosyaları")
    ayr.add_argument("--baslik", help="kitap adı (varsayılan: plan/genel-plan.md başlığı ya da klasör adı)")
    ayr.add_argument("--yazar", default="", help="yazar adı (künye ve e-kitap üst verisi)")
    ayr.add_argument("--kapak", type=Path, help="kapak görseli (.jpg ya da .png)")
    ayr.add_argument("--bicim", nargs="+", choices=BICIMLER + ("hepsi",), default=["hepsi"],
                     help="üretilecek biçimler: epub, html, docx, odt, yazdir (A5 baskıya hazır HTML), pdf, txt, md "
                          "ya da hepsi (pdf hariç; varsayılan)")
    ayr.add_argument("--cikti", type=Path, help="çıktı klasörü (varsayılan: <proje>/yayin ya da ilk dosyanın klasörü)")
    ayr.add_argument("--taslak", action="store_true", help="bitmemiş metin işaretlerine rağmen derle")
    arg = ayr.parse_args(argv)
    try:
        yollar = proje_bolumleri(arg.proje) if arg.proje else list(arg.dosya)
        baslik = (arg.baslik or (proje_basligi(arg.proje) if arg.proje else yollar[0].parent.name.replace("-", " ").title())).strip()
        if not baslik:
            raise DerlemeHatasi("kitap adı boş olamaz")
        if arg.kapak and (not arg.kapak.is_file() or arg.kapak.suffix.lower() not in KAPAK_TURLERI):
            raise DerlemeHatasi(f"kapak görseli bulunamadı ya da .jpg/.png değil: {arg.kapak}")
        bolumler, isaretler = [], []
        for i, yol in enumerate(yollar, 1):
            ham = dosya_oku.metin_oku(yol)
            isaretler += [f"{yol}:{x['satir']}: {x['isaret']}" for x in metin_analizi.isaretleri_bul(ham)]
            bolumler.append(markdown_bolum(ham, f"{i}. Bölüm", str(yol)))
        if isaretler and not arg.taslak:
            print("Bitmemiş metin işaretleri bulundu; derleme durdu (taslak için --taslak):", file=sys.stderr)
            for satir in isaretler[:20]:
                print(f"  {satir}", file=sys.stderr)
            return 1
        cikti = arg.cikti or ((arg.proje / "yayin") if arg.proje else yollar[0].parent)
        yazar = arg.yazar.strip() or "Adı Belirtilmemiş Yazar"
        ad = dosya_adi(baslik)
        uretilen = []
        secilen = set(HEPSI if "hepsi" in arg.bicim else ()) | {b for b in arg.bicim if b != "hepsi"}
        zaman = yayin_zamani()
        if "epub" in secilen:
            epub_yaz(cikti / f"{ad}.epub", baslik, yazar, bolumler, arg.kapak, zaman)
            uretilen.append(cikti / f"{ad}.epub")
        if "html" in secilen:
            html_yaz(cikti / f"{ad}.html", baslik, yazar, bolumler)
            uretilen.append(cikti / f"{ad}.html")
        if "docx" in secilen:
            by.docx_yaz(cikti / f"{ad}.docx", baslik, yazar, bolumler, zaman)
            uretilen.append(cikti / f"{ad}.docx")
        if "odt" in secilen:
            by.odt_yaz(cikti / f"{ad}.odt", baslik, yazar, bolumler, zaman)
            uretilen.append(cikti / f"{ad}.odt")
        if "yazdir" in secilen or "pdf" in secilen:
            baski = by.yazdir_html(baslik, yazar, bolumler, zaman.year)
            if "yazdir" in secilen:
                (cikti / f"{ad}-baski.html").parent.mkdir(parents=True, exist_ok=True)
                (cikti / f"{ad}-baski.html").write_text(baski, encoding="utf-8")
                uretilen.append(cikti / f"{ad}-baski.html")
            if "pdf" in secilen:
                by.pdf_yaz(cikti / f"{ad}.pdf", baski)
                uretilen.append(cikti / f"{ad}.pdf")
        if "txt" in secilen:
            (cikti / f"{ad}.txt").parent.mkdir(parents=True, exist_ok=True)
            (cikti / f"{ad}.txt").write_text(by.txt_metni(baslik, yazar, bolumler), encoding="utf-8")
            uretilen.append(cikti / f"{ad}.txt")
        if "md" in secilen:
            (cikti / f"{ad}-tam.md").parent.mkdir(parents=True, exist_ok=True)
            (cikti / f"{ad}-tam.md").write_text(by.md_metni(baslik, yazar, bolumler), encoding="utf-8")
            uretilen.append(cikti / f"{ad}-tam.md")
    except (DerlemeHatasi, by.BelgeHatasi, dosya_oku.DosyaHatasi, OSError) as hata:
        print(f"hata: {hata_iletisi(hata)}", file=sys.stderr)
        return 2
    print(f"“{baslik}” derlendi: {len(bolumler)} bölüm.")
    for yol in uretilen:
        print(f"  {yol} ({yol.stat().st_size:,} bayt)".replace(",", "."))
    if not arg.yazar.strip():
        print("Not: --yazar verilmedi; künyede 'Adı Belirtilmemiş Yazar' yazıyor.")
    if isaretler:
        print(f"Uyarı: {len(isaretler)} bitmemiş işaretle taslak olarak derlendi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
