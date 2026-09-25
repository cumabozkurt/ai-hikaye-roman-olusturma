"""Kitap derleyicisinin ek biçimleri: DOCX, ODT, yazdırmaya hazır HTML, PDF, düz metin, Markdown.

Yalnızca standart kütüphane: DOCX (Office Open XML) ve ODT (OpenDocument) dosyaları
``zipfile`` ile elle kurulur. Çıktılar Word, LibreOffice Writer ve Google Dokümanlar'da
açılır; ``SOURCE_DATE_EPOCH`` verildiğinde bayt bayt yeniden üretilebilir.

Yayınevine gönderim için DOCX/ODT "el yazması" biçimi: A4, Times New Roman 12 punto,
1,5 satır aralığı, 2,5 cm kenar boşluğu, iki yana yaslı paragraflar, ilk satır girintisi,
her bölüm yeni sayfada, üst bilgide yazar ve kitap adı, alt bilgide sayfa numarası.
"""

from __future__ import annotations

import datetime as dt
import html
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable
from xml.sax.saxutils import escape as xml_kacis

KONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
SATIR_ICI = re.compile(r"(\*\*.+?\*\*|(?<![\w*])\*(?!\s).+?(?<!\s)\*(?![\w*])|(?<![\w_])_(?!\s).+?(?<!\s)_(?![\w_]))")
KELIME = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+(?:['’][A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+)*")


class BelgeHatasi(ValueError):
    """Beklenen kullanım hatası (Türkçe ileti)."""


def temiz(metin: str) -> str:
    return KONTROL.sub("", metin)


def x(metin: str) -> str:
    return xml_kacis(temiz(metin), {'"': "&quot;"})


def satir_ici_parcalar(metin: str, kalin: bool = False, italik: bool = False) -> list[tuple[str, bool, bool]]:
    """``**kalın**`` ve ``*italik*`` / ``_italik_`` işaretlerini (metin, kalın, italik) parçalarına ayırır."""
    sonuc: list[tuple[str, bool, bool]] = []
    for parca in SATIR_ICI.split(metin):
        if not parca:
            continue
        if parca.startswith("**") and parca.endswith("**") and len(parca) > 4:
            sonuc += satir_ici_parcalar(parca[2:-2], True, italik)
        elif len(parca) > 2 and parca[0] == parca[-1] and parca[0] in "*_" and SATIR_ICI.fullmatch(parca):
            sonuc += satir_ici_parcalar(parca[1:-1], kalin, True)
        else:
            sonuc.append((parca, kalin, italik))
    return sonuc


def sade_metin(metin: str) -> str:
    return "".join(p for p, _, _ in satir_ici_parcalar(metin))


def kelime_sayisi(bolumler: Iterable[Any]) -> int:
    return sum(len(KELIME.findall(sade_metin(m))) for b in bolumler for _, m in b.bloklar)


def _zip_yaz(hedef: Path, dosyalar: list[tuple[str, bytes]], zaman: dt.datetime, ilk_sikistirmasiz: bool = False) -> None:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    damga = (max(1980, zaman.year), zaman.month, zaman.day, zaman.hour, zaman.minute, zaman.second)
    gecici = hedef.with_name(hedef.name + ".gecici")
    with zipfile.ZipFile(gecici, "w") as z:
        for i, (ad, veri) in enumerate(dosyalar):
            bilgi = zipfile.ZipInfo(ad, damga)
            bilgi.compress_type = zipfile.ZIP_STORED if (ilk_sikistirmasiz and i == 0) else zipfile.ZIP_DEFLATED
            bilgi.external_attr = 0o644 << 16
            z.writestr(bilgi, veri)
    os.replace(gecici, hedef)


def _utc(zaman: dt.datetime) -> str:
    return zaman.strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ DOCX

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_BAS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
DOCX_STILLER = {"p": "Govde", "diyalog": "Govde", "ilk": "IlkParagraf", "h2": "Heading2", "alinti": "Alinti",
                "ayrac": "Ayrac"}


def _w_kosular(metin: str) -> str:
    kosular = []
    for parca, kalin, italik in satir_ici_parcalar(metin):
        rpr = ("<w:b/>" if kalin else "") + ("<w:i/>" if italik else "")
        rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
        kosular.append(f'<w:r>{rpr}<w:t xml:space="preserve">{x(parca)}</w:t></w:r>')
    return "".join(kosular)


def _w_p(stil: str, metin: str = "", ham: str | None = None) -> str:
    icerik = ham if ham is not None else _w_kosular(metin)
    return f'<w:p><w:pPr><w:pStyle w:val="{stil}"/></w:pPr>{icerik}</w:p>'


def docx_stilleri() -> str:
    def stil(kimlik: str, ad: str, ppr: str = "", rpr: str = "", temel: str = "Normal", sonraki: str = "Govde") -> str:
        return (f'<w:style w:type="paragraph" w:styleId="{kimlik}"><w:name w:val="{ad}"/><w:basedOn w:val="{temel}"/>'
                f'<w:next w:val="{sonraki}"/><w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>')
    return (XML_BAS + f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr>'
            '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
            '<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="tr-TR" w:eastAsia="tr-TR" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
            + stil("Govde", "Gövde Metni", '<w:ind w:firstLine="709"/><w:jc w:val="both"/>')
            + stil("IlkParagraf", "İlk Paragraf", '<w:jc w:val="both"/>')
            + stil("Heading1", "heading 1", '<w:keepNext/><w:pageBreakBefore/><w:spacing w:before="2400" w:after="720"/>'
                   '<w:jc w:val="center"/><w:outlineLvl w:val="0"/>', '<w:b/><w:sz w:val="32"/><w:szCs w:val="32"/>',
                   sonraki="IlkParagraf")
            + stil("Heading2", "heading 2", '<w:keepNext/><w:spacing w:before="360" w:after="240"/><w:outlineLvl w:val="1"/>',
                   '<w:b/><w:sz w:val="26"/><w:szCs w:val="26"/>', sonraki="IlkParagraf")
            + stil("Title", "Title", '<w:spacing w:before="3600" w:after="480"/><w:jc w:val="center"/>',
                   '<w:b/><w:sz w:val="44"/><w:szCs w:val="44"/>', sonraki="Subtitle")
            + stil("Subtitle", "Subtitle", '<w:spacing w:after="240"/><w:jc w:val="center"/>', '<w:sz w:val="28"/>')
            + stil("Ortali", "Ortalı", '<w:jc w:val="center"/>')
            + stil("Ayrac", "Sahne Ayracı", '<w:spacing w:before="240" w:after="240"/><w:jc w:val="center"/>',
                   sonraki="IlkParagraf")
            + stil("Alinti", "Alıntı", '<w:ind w:left="709" w:right="709"/><w:jc w:val="both"/>', "<w:i/>")
            + stil("UstBilgi", "header", '<w:jc w:val="right"/>', '<w:sz w:val="20"/>')
            + stil("AltBilgi", "footer", '<w:jc w:val="center"/>', '<w:sz w:val="20"/>')
            + "</w:styles>")


def docx_yaz(hedef: Path, baslik: str, yazar: str, bolumler: list[Any], zaman: dt.datetime) -> None:
    kelime = kelime_sayisi(bolumler)
    yuvarlak = max(100, round(kelime, -2))
    govde = [_w_p("Title", baslik), _w_p("Subtitle", yazar),
             _w_p("Ortali", f"Yaklaşık {yuvarlak:,} kelime".replace(",", "."))]
    for b in bolumler:
        govde.append(_w_p("Heading1", b.baslik))
        for tur, metin in b.bloklar:
            govde.append(_w_p("Ayrac", "* * *") if tur == "ayrac" else _w_p(DOCX_STILLER[tur], metin))
    soyad = yazar.split()[-1] if yazar.split() else yazar
    belge = (XML_BAS + f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>' + "".join(govde)
             + '<w:sectPr><w:headerReference w:type="default" r:id="rIdUst"/><w:footerReference w:type="default" r:id="rIdAlt"/>'
             '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" '
             'w:header="709" w:footer="709" w:gutter="0"/><w:titlePg/></w:sectPr></w:body></w:document>')
    ust = (XML_BAS + f'<w:hdr xmlns:w="{W}">' + _w_p("UstBilgi", f"{soyad} / {sade_metin(baslik)}")
           + "</w:hdr>")
    sayfa = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
             '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>')
    alt = XML_BAS + f'<w:ftr xmlns:w="{W}">' + _w_p("AltBilgi", ham=sayfa) + "</w:ftr>"
    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml"
    turler = (XML_BAS + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              f'<Override PartName="/word/document.xml" ContentType="{ct}.document.main+xml"/>'
              f'<Override PartName="/word/styles.xml" ContentType="{ct}.styles+xml"/>'
              f'<Override PartName="/word/settings.xml" ContentType="{ct}.settings+xml"/>'
              f'<Override PartName="/word/header1.xml" ContentType="{ct}.header+xml"/>'
              f'<Override PartName="/word/footer1.xml" ContentType="{ct}.footer+xml"/>'
              '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
              '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
              "</Types>")
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    kok_iliski = (XML_BAS + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="word/document.xml"/>'
                  '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                  f'<Relationship Id="rId3" Type="{rel}/extended-properties" Target="docProps/app.xml"/></Relationships>')
    belge_iliski = (XML_BAS + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    f'<Relationship Id="rIdStil" Type="{rel}/styles" Target="styles.xml"/>'
                    f'<Relationship Id="rIdAyar" Type="{rel}/settings" Target="settings.xml"/>'
                    f'<Relationship Id="rIdUst" Type="{rel}/header" Target="header1.xml"/>'
                    f'<Relationship Id="rIdAlt" Type="{rel}/footer" Target="footer1.xml"/></Relationships>')
    ayarlar = (XML_BAS + f'<w:settings xmlns:w="{W}"><w:defaultTabStop w:val="709"/>'
               '<w:themeFontLang w:val="tr-TR"/></w:settings>')
    cekirdek = (XML_BAS + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                f"<dc:title>{x(baslik)}</dc:title><dc:creator>{x(yazar)}</dc:creator><dc:language>tr-TR</dc:language>"
                f'<dcterms:created xsi:type="dcterms:W3CDTF">{_utc(zaman)}</dcterms:created>'
                f'<dcterms:modified xsi:type="dcterms:W3CDTF">{_utc(zaman)}</dcterms:modified></cp:coreProperties>')
    uygulama = (XML_BAS + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
                f"<Application>ai-hikaye-roman-olusturma</Application><Words>{kelime}</Words></Properties>")
    _zip_yaz(hedef, [("[Content_Types].xml", turler.encode()), ("_rels/.rels", kok_iliski.encode()),
                     ("word/document.xml", belge.encode()), ("word/_rels/document.xml.rels", belge_iliski.encode()),
                     ("word/styles.xml", docx_stilleri().encode()), ("word/settings.xml", ayarlar.encode()),
                     ("word/header1.xml", ust.encode()), ("word/footer1.xml", alt.encode()),
                     ("docProps/core.xml", cekirdek.encode()), ("docProps/app.xml", uygulama.encode())], zaman)


# ------------------------------------------------------------------ ODT

ODF_AD = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
          'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
          'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
          'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
          'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
          'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
          'xmlns:dc="http://purl.org/dc/elements/1.1/" office:version="1.3"')
ODT_STILLER = {"p": "Govde", "diyalog": "Govde", "ilk": "Ilk", "h2": "Ara_20_Baslik", "alinti": "Alinti", "ayrac": "Ayrac"}


def _o_parcalar(metin: str) -> str:
    stil = {(True, False): "Kalin", (False, True): "Italik", (True, True): "KalinItalik"}
    sonuc = []
    for parca, kalin, italik in satir_ici_parcalar(metin):
        if kalin or italik:
            sonuc.append(f'<text:span text:style-name="{stil[(kalin, italik)]}">{x(parca)}</text:span>')
        else:
            sonuc.append(x(parca))
    return "".join(sonuc)


def odt_yaz(hedef: Path, baslik: str, yazar: str, bolumler: list[Any], zaman: dt.datetime) -> None:
    kelime = kelime_sayisi(bolumler)
    govde = [f'<text:p text:style-name="Kitap_20_Adi">{x(baslik)}</text:p>',
             f'<text:p text:style-name="Ortali">{x(yazar)}</text:p>',
             f'<text:p text:style-name="Ortali">{x(f"Yaklaşık {max(100, round(kelime, -2)):,} kelime".replace(",", "."))}</text:p>']
    for b in bolumler:
        govde.append(f'<text:h text:style-name="Bolum_20_Basligi" text:outline-level="1">{_o_parcalar(b.baslik)}</text:h>')
        for tur, metin in b.bloklar:
            if tur == "ayrac":
                govde.append('<text:p text:style-name="Ayrac">* * *</text:p>')
            elif tur == "h2":
                govde.append(f'<text:h text:style-name="Ara_20_Baslik" text:outline-level="2">{_o_parcalar(metin)}</text:h>')
            else:
                govde.append(f'<text:p text:style-name="{ODT_STILLER[tur]}">{_o_parcalar(metin)}</text:p>')
    icerik = (XML_BAS.replace(' standalone="yes"', "") + f"<office:document-content {ODF_AD}><office:automatic-styles>"
              '<style:style style:name="Kalin" style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>'
              '<style:style style:name="Italik" style:family="text"><style:text-properties fo:font-style="italic"/></style:style>'
              '<style:style style:name="KalinItalik" style:family="text"><style:text-properties fo:font-weight="bold" '
              'fo:font-style="italic"/></style:style></office:automatic-styles><office:body><office:text>'
              + "".join(govde) + "</office:text></office:body></office:document-content>")

    def pstil(ad: str, gorunen: str, ppr: str = "", tpr: str = "", ust: str = "Standard") -> str:
        return (f'<style:style style:name="{ad}" style:display-name="{gorunen}" style:family="paragraph" '
                f'style:parent-style-name="{ust}"><style:paragraph-properties {ppr}/><style:text-properties {tpr}/></style:style>')
    soyad = yazar.split()[-1] if yazar.split() else yazar
    stiller = (XML_BAS.replace(' standalone="yes"', "") + f"<office:document-styles {ODF_AD}>"
               '<office:font-face-decls><style:font-face style:name="Times New Roman" svg:font-family="&apos;Times New Roman&apos;" '
               'style:font-family-generic="roman"/></office:font-face-decls><office:styles>'
               '<style:default-style style:family="paragraph"><style:paragraph-properties fo:line-height="150%"/>'
               '<style:text-properties style:font-name="Times New Roman" fo:font-size="12pt" fo:language="tr" '
               'fo:country="TR"/></style:default-style>'
               '<style:style style:name="Standard" style:family="paragraph" style:class="text"/>'
               + pstil("Govde", "Gövde Metni", 'fo:text-indent="1.25cm" fo:text-align="justify"')
               + pstil("Ilk", "İlk Paragraf", 'fo:text-align="justify"')
               + pstil("Ortali", "Ortalı", 'fo:text-align="center"')
               + pstil("Kitap_20_Adi", "Kitap Adı", 'fo:text-align="center" fo:margin-top="6cm" fo:margin-bottom="0.8cm"',
                       'fo:font-size="22pt" fo:font-weight="bold"')
               + pstil("Bolum_20_Basligi", "Bölüm Başlığı", 'fo:text-align="center" fo:break-before="page" '
                       'fo:margin-top="4cm" fo:margin-bottom="1.2cm" fo:keep-with-next="always"',
                       'fo:font-size="16pt" fo:font-weight="bold"')
               + pstil("Ara_20_Baslik", "Ara Başlık", 'fo:margin-top="0.6cm" fo:margin-bottom="0.4cm" fo:keep-with-next="always"',
                       'fo:font-size="13pt" fo:font-weight="bold"')
               + pstil("Ayrac", "Sahne Ayracı", 'fo:text-align="center" fo:margin-top="0.4cm" fo:margin-bottom="0.4cm"')
               + pstil("Alinti", "Alıntı", 'fo:margin-left="1.25cm" fo:margin-right="1.25cm" fo:text-align="justify"',
                       'fo:font-style="italic"')
               + pstil("Ust_20_Bilgi", "Üst Bilgi", 'fo:text-align="end"', 'fo:font-size="10pt"')
               + pstil("Alt_20_Bilgi", "Alt Bilgi", 'fo:text-align="center"', 'fo:font-size="10pt"')
               + '</office:styles><office:automatic-styles><style:page-layout style:name="SayfaA4">'
               '<style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" fo:margin-top="2cm" '
               'fo:margin-bottom="2cm" fo:margin-left="2.5cm" fo:margin-right="2.5cm"/>'
               '<style:header-style><style:header-footer-properties fo:min-height="0cm" fo:margin-bottom="0.5cm"/></style:header-style>'
               '<style:footer-style><style:header-footer-properties fo:min-height="0cm" fo:margin-top="0.5cm"/></style:footer-style>'
               '</style:page-layout></office:automatic-styles><office:master-styles>'
               '<style:master-page style:name="Standard" style:page-layout-name="SayfaA4">'
               f'<style:header><text:p text:style-name="Ust_20_Bilgi">{x(soyad)} / {x(baslik)}</text:p></style:header>'
               '<style:footer><text:p text:style-name="Alt_20_Bilgi"><text:page-number text:select-page="current">1'
               "</text:page-number></text:p></style:footer></style:master-page></office:master-styles></office:document-styles>")
    meta = (XML_BAS.replace(' standalone="yes"', "") + f"<office:document-meta {ODF_AD}><office:meta>"
            f"<dc:title>{x(baslik)}</dc:title><dc:creator>{x(yazar)}</dc:creator><dc:language>tr-TR</dc:language>"
            f"<meta:generator>ai-hikaye-roman-olusturma</meta:generator><dc:date>{_utc(zaman)}</dc:date>"
            f'<meta:document-statistic meta:word-count="{kelime}"/></office:meta></office:document-meta>')
    manifest = (XML_BAS.replace(' standalone="yes"', "")
                + '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">'
                '<manifest:file-entry manifest:full-path="/" manifest:version="1.3" '
                'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
                '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
                '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>'
                '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/></manifest:manifest>')
    _zip_yaz(hedef, [("mimetype", b"application/vnd.oasis.opendocument.text"), ("META-INF/manifest.xml", manifest.encode()),
                     ("content.xml", icerik.encode()), ("styles.xml", stiller.encode()), ("meta.xml", meta.encode())],
             zaman, ilk_sikistirmasiz=True)


# ------------------------------------------------------------------ yazdırmaya hazır HTML ve PDF

YAZDIR_CSS = """@page { size: 148mm 210mm; margin: 18mm 15mm 20mm 17mm;
  @bottom-center { content: counter(page); font: 9pt Georgia, serif; color: #444; } }
@page :first { @bottom-center { content: none; } }
@page :left { margin-left: 15mm; margin-right: 17mm; }
html { font-family: "Libertinus Serif", "Gentium Book Plus", Georgia, "Times New Roman", serif; font-size: 10.5pt;
  line-height: 1.45; color: #111; hyphens: auto; -webkit-hyphens: auto; }
body { margin: 0; }
.kapak { height: 170mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }
.kapak h1 { font-size: 22pt; font-weight: normal; letter-spacing: .04em; margin: 0 0 8mm; }
.kapak p { font-size: 12pt; margin: 0; text-indent: 0; }
.kunye { break-before: page; height: 170mm; display: flex; flex-direction: column; justify-content: flex-end;
  font-size: 8.5pt; color: #333; }
.kunye p { text-indent: 0; text-align: left; margin: 0 0 1.5mm; }
nav.icindekiler { break-before: page; }
nav.icindekiler h2 { font-weight: normal; text-align: center; font-size: 13pt; margin: 20mm 0 8mm; }
nav.icindekiler ol { list-style: none; padding: 0; } nav.icindekiler li { margin: 0 0 2.5mm; }
h1.bolum { break-before: page; font-weight: normal; font-size: 15pt; text-align: center; margin: 30mm 0 12mm; }
h2 { font-size: 11pt; margin: 6mm 0 3mm; break-after: avoid; }
p { margin: 0; text-indent: 1.2em; text-align: justify; orphans: 2; widows: 2; }
p.ilk { text-indent: 0; }  /* küçük büyük harf (small-caps) Türkçe i/İ ayrımını bozduğu için kullanılmaz */
p.ayrac { text-indent: 0; text-align: center; margin: 4mm 0; letter-spacing: .5em; }
blockquote { margin: 3mm 8mm; font-style: italic; } blockquote p { text-indent: 0; }
@media screen { body { background: #e9e5dc; } main { background: #fff; max-width: 118mm; margin: 12mm auto; padding: 18mm 16mm;
  box-shadow: 0 2px 12px rgba(0,0,0,.15); } }
"""


def _h_satir(metin: str) -> str:
    sonuc = []
    for parca, kalin, italik in satir_ici_parcalar(temiz(metin)):
        p = html.escape(parca, quote=False)
        if italik:
            p = f"<em>{p}</em>"
        if kalin:
            p = f"<strong>{p}</strong>"
        sonuc.append(p)
    return "".join(sonuc)


def yazdir_html(baslik: str, yazar: str, bolumler: list[Any], yil: int) -> str:
    parcalar = [f'<section class="kapak"><h1>{_h_satir(baslik)}</h1><p>{html.escape(yazar)}</p></section>',
                f'<section class="kunye"><p><strong>{_h_satir(baslik)}</strong></p><p>{html.escape(yazar)}</p>'
                f"<p>© {yil} {html.escape(yazar)}. Bütün hakları saklıdır.</p></section>",
                '<nav class="icindekiler"><h2>İçindekiler</h2><ol>'
                + "".join(f'<li><a href="#b{i}">{_h_satir(b.baslik)}</a></li>' for i, b in enumerate(bolumler, 1))
                + "</ol></nav>"]
    for i, b in enumerate(bolumler, 1):
        parcalar.append(f'<h1 class="bolum" id="b{i}">{_h_satir(b.baslik)}</h1>')
        for tur, metin in b.bloklar:
            if tur == "ayrac":
                parcalar.append('<p class="ayrac">* * *</p>')
            elif tur == "h2":
                parcalar.append(f"<h2>{_h_satir(metin)}</h2>")
            elif tur == "alinti":
                parcalar.append(f"<blockquote><p>{_h_satir(metin)}</p></blockquote>")
            else:
                sinif = ' class="ilk"' if tur == "ilk" else ""
                parcalar.append(f"<p{sinif}>{_h_satir(metin)}</p>")
    return ('<!DOCTYPE html>\n<html lang="tr">\n<head>\n<meta charset="utf-8">\n'
            f"<title>{html.escape(sade_metin(baslik))}</title>\n<style>\n{YAZDIR_CSS}</style>\n</head>\n<body>\n<main>\n"
            + "\n".join(parcalar) + "\n</main>\n</body>\n</html>\n")


def tarayici_bul() -> str | None:
    for ad in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"):
        yol = shutil.which(ad)
        if yol:
            return yol
    for yol in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if Path(yol).is_file():
            return yol
    return None


PDF_SURE_SINIRI = 90  # saniye


def _pdf_tamam(hedef: Path) -> bool:
    try:
        veri = hedef.read_bytes()
    except OSError:
        return False
    return len(veri) > 500 and veri.startswith(b"%PDF") and b"%%EOF" in veri[-1024:]


def _tarayici_calistir(komut: list[str], hedef: Path) -> None:
    """Tarayıcıyı çalıştırır; PDF tamamlanınca süreç kendiliğinden kapanmasa da bekletmez.

    Bazı sistemlerde (özellikle macOS) başsız tarayıcı PDF'yi yazdıktan sonra açık kalabiliyor.
    Dosya tamamlanıp boyutu sabitlenince süreç kapatılır; toplam süre PDF_SURE_SINIRI ile sınırlıdır.
    """
    if hedef.exists():
        hedef.unlink()
    try:
        surec = subprocess.Popen(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as hata:
        raise BelgeHatasi(f"tarayıcı başlatılamadı: {hata.__class__.__name__}") from None
    son = time.monotonic() + PDF_SURE_SINIRI
    onceki = -1
    try:
        while time.monotonic() < son:
            if surec.poll() is not None:
                return
            if _pdf_tamam(hedef):
                boyut = hedef.stat().st_size
                if boyut == onceki:
                    return
                onceki = boyut
            time.sleep(0.5)
        if not _pdf_tamam(hedef):
            raise BelgeHatasi(f"tarayıcı {PDF_SURE_SINIRI} saniyede PDF üretemedi; 'yazdir' HTML çıktısını elle yazdırın")
    finally:
        if surec.poll() is None:
            surec.terminate()
            try:
                surec.wait(timeout=10)
            except subprocess.TimeoutExpired:
                surec.kill()
                surec.wait(timeout=10)


def pdf_yaz(hedef: Path, html_metni: str) -> None:
    tarayici = tarayici_bul()
    if tarayici is None:
        raise BelgeHatasi("PDF için Chrome, Chromium ya da Edge bulunamadı. 'yazdir' biçimiyle üretilen HTML'yi "
                          "tarayıcıda açıp Yazdır → PDF olarak kaydet seçeneğini kullanın.")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as gecici:
        kaynak = Path(gecici) / "kitap.html"
        kaynak.write_text(html_metni, encoding="utf-8", newline="\n")
        komut = [tarayici, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run",
                 "--no-default-browser-check", "--disable-extensions", "--use-mock-keychain", "--password-store=basic",
                 f"--user-data-dir={Path(gecici) / 'profil'}", f"--print-to-pdf={hedef.resolve()}", kaynak.resolve().as_uri()]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            komut.insert(1, "--no-sandbox")
        _tarayici_calistir(komut, hedef)
    if not hedef.is_file() or hedef.stat().st_size < 500 or not hedef.read_bytes().startswith(b"%PDF"):
        raise BelgeHatasi("tarayıcı PDF dosyası üretmedi; 'yazdir' HTML çıktısını elle yazdırın")


# ------------------------------------------------------------------ düz metin ve Markdown

def txt_metni(baslik: str, yazar: str, bolumler: list[Any]) -> str:
    s = [sade_metin(baslik), yazar, ""]
    for b in bolumler:
        s += ["", "", sade_metin(b.baslik), ""]
        for tur, metin in b.bloklar:
            s.append("* * *" if tur == "ayrac" else sade_metin(metin))
            s.append("")
    return temiz("\n".join(s)).strip() + "\n"


def md_metni(baslik: str, yazar: str, bolumler: list[Any]) -> str:
    s = [f"% {baslik}", f"% {yazar}", ""]
    for b in bolumler:
        s += [f"# {b.baslik}", ""]
        for tur, metin in b.bloklar:
            s.append({"ayrac": "* * *", "h2": f"## {metin}", "alinti": f"> {metin}"}.get(tur, metin))
            s.append("")
    return temiz("\n".join(s)).strip() + "\n"
