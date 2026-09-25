#!/usr/bin/env python3
"""Word (DOCX), LibreOffice (ODT), EPUB, TXT ve Markdown taslaklarını bölümlere bölerek içeri aktarır.

Yalnızca Python standart kitaplığı kullanılır (pandoc ya da python-docx gerekmez).

Kullanım::

    belge_ice_aktar.py onizle --kaynak taslak.docx
    belge_ice_aktar.py aktar  --kaynak taslak.docx --proje KITAP [--desen REGEX] [--on-metin-bolum]

* Bölüm sınırları: belge başlıkları (Word "Başlık 1/Heading 1", ODT başlıkları, EPUB h1/h2,
  Markdown ``#``) ya da "Bölüm 3", "BÖLÜM ÜÇ", "3." gibi tek başına duran satırlar.
  ``--desen`` ile kendi düzenli ifadenizi verebilirsiniz.
* İtalik ``*…*``, kalın ``**…**`` olarak korunur. Yazarın cümlelerine dokunulmaz.
* İlk sınırdan önceki metin (ithaf, önsöz) ``.hikaye/ice-aktarma/on-metin.md`` dosyasına yazılır;
  ``--on-metin-bolum`` verilirse 1. bölüm sayılır.
* Kelime toplamı kaynakla karşılaştırılır; fark %1'i aşarsa hiçbir dosya yazılmaz.
* Var olan bölüm dosyalarının üzerine yazılmaz.

Çıkış kodu: 0 başarılı, 1 bölüm sınırı bulunamadı ya da doğrulama başarısız, 2 kullanım/dosya hatası.
"""

from __future__ import annotations

import argparse
import html.parser
import json
import posixpath
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import metin_olcum  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

EN_BUYUK_UYE = 64 * 1024 * 1024  # açılmış tek bir arşiv üyesi için üst sınır (zip bombasına karşı)
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
STYLE = "{urn:oasis:names:tc:opendocument:xmlns:style:1.0}"
FO = "{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"

SAYI_SOZCUKLERI = ("bir iki üç dört beş altı yedi sekiz dokuz on yirmi otuz kırk elli altmış yetmiş seksen doksan yüz "
                   "birinci ikinci üçüncü dördüncü beşinci altıncı yedinci sekizinci dokuzuncu onuncu").split()
_SAYI = r"(?:\d{1,4}|[IVXLC]{1,7}|(?:" + "|".join(SAYI_SOZCUKLERI) + r")(?:\s+(?:" + "|".join(SAYI_SOZCUKLERI) + r"))*)"
VARSAYILAN_DESEN = re.compile(
    r"^\s*(?:(?:bölüm|kısım|chapter)\s+" + _SAYI + r"|" + _SAYI + r"\s*\.?\s*(?:bölüm|kısım))"
    r"\s*(?:[:.\-–—]\s*(?P<baslik>.*\S))?\s*$|^\s*(?P<yalin>\d{1,4})\s*\.?\s*$",
    re.I,
)


class AktarmaHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe içeri aktarma hatası."""


@dataclass
class Paragraf:
    metin: str
    baslik_duzeyi: int = 0  # 0 = gövde paragrafı


def _uye_oku(arsiv: zipfile.ZipFile, ad: str) -> bytes:
    try:
        bilgi = arsiv.getinfo(ad)
    except KeyError as hata:
        raise AktarmaHatasi(f"arşivde beklenen parça yok: {ad}") from hata
    if bilgi.file_size > EN_BUYUK_UYE:
        raise AktarmaHatasi(f"arşiv parçası çok büyük ({bilgi.file_size} bayt): {ad}")
    with arsiv.open(bilgi) as f:
        veri = f.read(EN_BUYUK_UYE + 1)
    if len(veri) > EN_BUYUK_UYE:
        raise AktarmaHatasi(f"arşiv parçası çok büyük: {ad}")
    return veri


def _xml(veri: bytes, ad: str) -> ET.Element:
    if b"<!DOCTYPE" in veri or b"<!ENTITY" in veri:
        raise AktarmaHatasi(f"{ad}: DOCTYPE/ENTITY içeren XML güvenlik nedeniyle okunmaz")
    try:
        return ET.fromstring(veri)
    except ET.ParseError as hata:
        satir, sutun = getattr(hata, "position", (0, 0))
        raise AktarmaHatasi(f"{ad}: bozuk XML (satır {satir}, sütun {sutun}); belge hasarlı olabilir, "
                            "kaynak programda açıp yeniden kaydedin") from hata


def _sar(metin: str, italik: bool, kalin: bool) -> str:
    if not metin.strip() or not (italik or kalin):
        return metin
    bas = metin[: len(metin) - len(metin.lstrip())]
    son = metin[len(metin.rstrip()):]
    isaret = ("**" if kalin else "") + ("*" if italik else "")
    return f"{bas}{isaret}{metin.strip()}{isaret[::-1]}{son}"


def _birlestir(parcalar: list[str]) -> str:
    metin = "".join(parcalar)
    metin = re.sub(r"(\*+)(\s*)\1", r"\2", metin)  # **a****b** → **ab**
    return re.sub(r"[ \t]+", " ", metin).strip()


def _acik(ozellik: ET.Element | None, etiket: str) -> bool:
    if ozellik is None:
        return False
    e = ozellik.find(W + etiket)
    return e is not None and e.get(W + "val", "true").lower() not in {"0", "false", "none"}


def docx_oku(yol: Path) -> list[Paragraf]:
    with zipfile.ZipFile(yol) as arsiv:
        govde = _xml(_uye_oku(arsiv, "word/document.xml"), "word/document.xml")
        stiller: dict[str, int] = {}
        if "word/styles.xml" in arsiv.namelist():
            for stil in _xml(_uye_oku(arsiv, "word/styles.xml"), "word/styles.xml").iter(W + "style"):
                sid, ad = stil.get(W + "styleId", ""), stil.find(W + "name")
                adi = (ad.get(W + "val", "") if ad is not None else "").lower()
                duzey = stil.find(f"{W}pPr/{W}outlineLvl")
                if duzey is not None and (duzey.get(W + "val") or "").isdigit():
                    stiller[sid] = int(duzey.get(W + "val")) + 1
                elif m := re.match(r"(?:heading|başlık)\s*(\d)", adi):
                    stiller[sid] = int(m.group(1))
                elif adi in {"title", "konu başlığı"}:
                    stiller[sid] = 1
    sonuc: list[Paragraf] = []
    for p in govde.iter(W + "p"):
        ppr = p.find(W + "pPr")
        duzey = 0
        if ppr is not None:
            stil = ppr.find(W + "pStyle")
            sid = stil.get(W + "val", "") if stil is not None else ""
            duzey = stiller.get(sid, 0)
            if not duzey and (m := re.match(r"(?:heading|ba[sş]l[iı]k)\s*(\d)$", sid, re.I)):
                duzey = int(m.group(1))
            ol = ppr.find(W + "outlineLvl")
            if ol is not None and (ol.get(W + "val") or "").isdigit() and int(ol.get(W + "val")) < 9:
                duzey = int(ol.get(W + "val")) + 1
        parcalar: list[str] = []
        for r in p.iter(W + "r"):
            rpr = r.find(W + "rPr")
            yazi = []
            for e in r:
                if e.tag == W + "t":
                    yazi.append(e.text or "")
                elif e.tag in (W + "tab",):
                    yazi.append(" ")
                elif e.tag in (W + "br", W + "cr") and e.get(W + "type") != "page":
                    yazi.append(" ")
            parcalar.append(_sar("".join(yazi), _acik(rpr, "i"), _acik(rpr, "b")))
        metin = _birlestir(parcalar)
        if metin:
            sonuc.append(Paragraf(metin.strip("*").strip() if duzey else metin, duzey))
    return sonuc


def odt_oku(yol: Path) -> list[Paragraf]:
    with zipfile.ZipFile(yol) as arsiv:
        icerik = _xml(_uye_oku(arsiv, "content.xml"), "content.xml")
        stil_kok = _xml(_uye_oku(arsiv, "styles.xml"), "styles.xml") if "styles.xml" in arsiv.namelist() else None
    bicim: dict[str, tuple[bool, bool]] = {}
    for kok in (stil_kok, icerik):
        if kok is None:
            continue
        for stil in kok.iter(STYLE + "style"):
            ozellik = stil.find(STYLE + "text-properties")
            if ozellik is not None:
                bicim[stil.get(STYLE + "name", "")] = (ozellik.get(FO + "font-style") == "italic",
                                                      ozellik.get(FO + "font-weight") in {"bold", "700", "800", "900"})

    def yazi(e: ET.Element, italik: bool = False, kalin: bool = False) -> list[str]:
        parca: list[str] = [_sar(e.text or "", italik, kalin)] if e.text else []
        for c in e:
            if c.tag == TEXT + "span":
                i, k = bicim.get(c.get(TEXT + "style-name", ""), (False, False))
                parca += yazi(c, italik or i, kalin or k)
            elif c.tag == TEXT + "s":
                parca.append(" " * int(c.get(TEXT + "c", "1") if (c.get(TEXT + "c") or "1").isdigit() else 1))
            elif c.tag in (TEXT + "tab", TEXT + "line-break"):
                parca.append(" ")
            elif c.tag in (TEXT + "note", OFFICE + "annotation"):
                pass
            else:
                parca += yazi(c, italik, kalin)
            if c.tail:
                parca.append(_sar(c.tail, italik, kalin))
        return parca

    sonuc: list[Paragraf] = []
    govde = icerik.find(f"{OFFICE}body/{OFFICE}text")
    for e in (govde.iter() if govde is not None else []):
        if e.tag == TEXT + "h":
            duzey = e.get(TEXT + "outline-level", "1")
            metin = _birlestir(yazi(e)).strip("*").strip()
            if metin:
                sonuc.append(Paragraf(metin, int(duzey) if duzey.isdigit() else 1))
        elif e.tag == TEXT + "p":
            metin = _birlestir(yazi(e))
            if metin:
                sonuc.append(Paragraf(metin))
    return sonuc


class _HtmlParagraflari(html.parser.HTMLParser):
    BLOK = {"p", "div", "blockquote", "li", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraflar: list[Paragraf] = []
        self.tampon: list[str] = []
        self.duzey = 0
        self.italik = 0
        self.kalin = 0
        self.atla = 0

    def _bosalt(self) -> None:
        metin = _birlestir(self.tampon)
        if metin:
            self.paragraflar.append(Paragraf(metin.strip("*").strip() if self.duzey else metin, self.duzey))
        self.tampon, self.duzey = [], 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "head", "nav"}:
            self.atla += 1
        elif tag in self.BLOK:
            self._bosalt()
            if tag[0] == "h" and tag[1:].isdigit():
                self.duzey = int(tag[1:])
        elif tag in {"em", "i"}:
            self.italik += 1
            self.tampon.append("\x01")
        elif tag in {"strong", "b"}:
            self.kalin += 1
            self.tampon.append("\x02")
        elif tag == "br":
            self.tampon.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "head", "nav"}:
            self.atla = max(0, self.atla - 1)
        elif tag in self.BLOK:
            self._bosalt()
        elif tag in {"em", "i"}:
            self.italik = max(0, self.italik - 1)
            self.tampon.append("\x01")
        elif tag in {"strong", "b"}:
            self.kalin = max(0, self.kalin - 1)
            self.tampon.append("\x02")

    def handle_data(self, data: str) -> None:
        if not self.atla:
            self.tampon.append(data)

    def close(self) -> None:
        super().close()
        self._bosalt()
        for p in self.paragraflar:
            p.metin = _isaretleri_coz(p.metin)


def _isaretleri_coz(metin: str) -> str:
    def degistir(m: re.Match[str], isaret: str) -> str:
        ic = m.group(1)
        return _sar(ic, isaret == "*", isaret == "**") if ic.strip() else ic
    metin = re.sub("\x02(.*?)\x02", lambda m: degistir(m, "**"), metin, flags=re.S)
    metin = re.sub("\x01(.*?)\x01", lambda m: degistir(m, "*"), metin, flags=re.S)
    return re.sub(r"\s+", " ", metin.replace("\x01", "").replace("\x02", "")).strip()


def epub_oku(yol: Path) -> list[Paragraf]:
    with zipfile.ZipFile(yol) as arsiv:
        kap = _xml(_uye_oku(arsiv, "META-INF/container.xml"), "META-INF/container.xml")
        kok = next((e.get("full-path") for e in kap.iter() if e.tag.endswith("rootfile") and e.get("full-path")), None)
        if not kok:
            raise AktarmaHatasi("EPUB container.xml içinde OPF yolu yok")
        opf = _xml(_uye_oku(arsiv, kok), kok)
        taban = posixpath.dirname(kok)
        ogeler = {e.get("id"): e for e in opf.iter() if e.tag.endswith("}item")}
        sonuc: list[Paragraf] = []
        for ref in (e for e in opf.iter() if e.tag.endswith("}itemref")):
            oge = ogeler.get(ref.get("idref"))
            if oge is None or "nav" in (oge.get("properties") or "").split():
                continue
            if "html" not in (oge.get("media-type") or ""):
                continue
            ad = posixpath.normpath(posixpath.join(taban, oge.get("href", "")))
            ayr = _HtmlParagraflari()
            ayr.feed(_uye_oku(arsiv, ad).decode("utf-8", errors="replace"))
            ayr.close()
            sonuc += ayr.paragraflar
    return sonuc


def duz_metin_oku(yol: Path) -> list[Paragraf]:
    metin = metin_olcum.satir_sonlarini_duzelt(dosya_oku.metin_oku(yol))
    metin = metin_olcum.ON_BILGI.sub("", metin, count=1)
    sonuc: list[Paragraf] = []
    for blok in re.split(r"\n\s*\n", metin):
        satirlar = [s.strip() for s in blok.split("\n") if s.strip()]
        tampon: list[str] = []
        for s in satirlar:
            m = re.match(r"^(#{1,6})\s+(.+?)\s*#*$", s)
            if m or VARSAYILAN_DESEN.match(s):
                if tampon:
                    sonuc.append(Paragraf(" ".join(tampon)))
                    tampon = []
                sonuc.append(Paragraf(m.group(2), len(m.group(1))) if m else Paragraf(s))
            else:
                tampon.append(s)
        if tampon:
            sonuc.append(Paragraf(" ".join(tampon) if yol.suffix.lower() == ".md" else "\n".join(tampon)))
    return sonuc


OKUYUCULAR = {".docx": docx_oku, ".odt": odt_oku, ".epub": epub_oku, ".txt": duz_metin_oku, ".md": duz_metin_oku,
              ".markdown": duz_metin_oku}


def belge_oku(yol: Path) -> list[Paragraf]:
    if not yol.exists():
        raise AktarmaHatasi(f"kaynak bulunamadı: {yol}")
    if yol.is_dir():
        raise AktarmaHatasi(f"dosya bekleniyordu, klasör verildi: {yol}")
    okuyucu = OKUYUCULAR.get(yol.suffix.lower())
    if okuyucu is None:
        raise AktarmaHatasi(f"desteklenmeyen biçim: {yol.suffix or '(uzantısız)'}. Desteklenenler: "
                            + ", ".join(sorted(OKUYUCULAR)) + ". Eski .doc dosyasını Word'de .docx olarak kaydedin.")
    try:
        return okuyucu(yol)
    except zipfile.BadZipFile as hata:
        raise AktarmaHatasi(f"{yol.name} geçerli bir {yol.suffix} (zip) dosyası değil") from hata
    except (OSError, RuntimeError, NotImplementedError) as hata:  # şifreli arşiv vb.
        raise AktarmaHatasi(f"{yol.name} okunamadı: {hata}") from hata


@dataclass
class Bolum:
    baslik: str
    paragraflar: list[str]
    kaynak_satiri: str


def bolumle(paragraflar: list[Paragraf], desen: re.Pattern[str] | None = None) -> tuple[list[str], list[Bolum]]:
    duzeyler = sorted({p.baslik_duzeyi for p in paragraflar if p.baslik_duzeyi})
    sinir_duzeyi = None
    if duzeyler:
        # Kitap adı tek bir üst başlıksa (ör. Title) bölümler bir alt düzeydedir.
        for d in duzeyler:
            if sum(1 for p in paragraflar if p.baslik_duzeyi == d) >= 2:
                sinir_duzeyi = d
                break
    on_metin: list[str] = []
    bolumler_: list[Bolum] = []
    for p in paragraflar:
        yalin_eslesme = (desen or VARSAYILAN_DESEN).match(p.metin) if len(p.metin) <= 120 else None
        sinir = (sinir_duzeyi is not None and p.baslik_duzeyi == sinir_duzeyi) or (
            yalin_eslesme is not None and (desen is not None or p.baslik_duzeyi or sinir_duzeyi is None))
        if sinir:
            baslik = p.metin
            if yalin_eslesme is not None and desen is None:
                if yalin_eslesme.group("baslik"):
                    baslik = yalin_eslesme.group("baslik")
                elif yalin_eslesme.group("yalin") or re.fullmatch(VARSAYILAN_DESEN, p.metin):
                    baslik = ""
            elif desen is not None and yalin_eslesme is not None and "baslik" in (desen.groupindex or {}):
                baslik = yalin_eslesme.group("baslik") or ""
            bolumler_.append(Bolum(baslik.strip(), [], p.metin))
        elif bolumler_:
            bolumler_[-1].paragraflar.append(p.metin if not p.baslik_duzeyi else f"## {p.metin}")
        else:
            on_metin.append(p.metin if not p.baslik_duzeyi else f"# {p.metin}")
    # Kapak/ithaf sayfası başlığı: desene uymayan, kısa ve ardından desene uyan bölümler geliyorsa ön metindir.
    if desen is None:
        while len(bolumler_) >= 2 and not VARSAYILAN_DESEN.match(bolumler_[0].kaynak_satiri):
            uyan = sum(1 for b in bolumler_[1:] if VARSAYILAN_DESEN.match(b.kaynak_satiri))
            if uyan * 2 < len(bolumler_) - 1 or _kelime(bolumler_[0].paragraflar) >= 200:
                break
            ilk = bolumler_.pop(0)
            on_metin += [f"# {ilk.kaynak_satiri}"] + ilk.paragraflar
    return on_metin, bolumler_


def kisa_ad(baslik: str) -> str:
    cevir = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")
    ascii_ad = unicodedata.normalize("NFKD", baslik.translate(cevir)).encode("ascii", "ignore").decode()
    return "-".join(re.sub(r"[^a-z0-9]+", " ", ascii_ad.lower()).split()[:6])[:48].strip("-")


def _kelime(metinler: list[str]) -> int:
    return sum(metin_olcum.kelime_say(re.sub(r"[*#]", " ", m)) for m in metinler)


def plan_olustur(kaynak: Path, desen: str | None, on_metin_bolum: bool) -> dict:
    derli = None
    if desen:
        try:
            derli = re.compile(desen, re.I | re.M)
        except re.error as hata:
            raise AktarmaHatasi(f"--desen geçersiz düzenli ifade: {hata}") from hata
    paragraflar = belge_oku(kaynak)
    if not paragraflar:
        raise AktarmaHatasi(f"{kaynak.name} içinde metin bulunamadı")
    on_metin, bolumler_ = bolumle(paragraflar, derli)
    if on_metin_bolum and on_metin:
        bolumler_.insert(0, Bolum("", on_metin, "(ön metin)"))
        on_metin = []
    kaynak_kelime = _kelime([p.metin for p in paragraflar if not p.baslik_duzeyi and not
                             (bolumler_ and any(p.metin == b.kaynak_satiri for b in bolumler_))])
    return {"kaynak": str(kaynak), "on_metin": on_metin, "bolumler": bolumler_, "kaynak_kelime": kaynak_kelime}


def onizleme(plan: dict) -> dict:
    return {
        "kaynak": plan["kaynak"], "bolum_sayisi": len(plan["bolumler"]), "kaynak_kelime": plan["kaynak_kelime"],
        "on_metin_kelime": _kelime(plan["on_metin"]),
        "bolumler": [{"no": i, "sinir_satiri": b.kaynak_satiri, "baslik": b.baslik,
                      "kelime": _kelime([p for p in b.paragraflar if not p.startswith("## ")]),
                      "ilk_cumle": " ".join(next((p for p in b.paragraflar if not p.startswith("## ")), "").split())[:100]}
                     for i, b in enumerate(plan["bolumler"], 1)],
    }


def aktar(plan: dict, proje: Path) -> dict:
    bolumler_: list[Bolum] = plan["bolumler"]
    if not bolumler_:
        raise AktarmaHatasi("bölüm sınırı bulunamadı; 'onizle' çıktısına bakıp --desen ile sınırı tarif edin")
    metin_klasoru = proje / "metin"
    if metin_klasoru.is_dir() and any(re.match(r"bolum-\d+", y.name) for y in metin_klasoru.iterdir()):
        raise AktarmaHatasi(f"{metin_klasoru} içinde zaten bölüm dosyaları var; üzerine yazılmaz. Boş bir proje klasörü kullanın.")
    yazilacak: list[tuple[Path, str]] = []
    hane = max(3, len(str(len(bolumler_))))
    for no, b in enumerate(bolumler_, 1):
        ad = kisa_ad(b.baslik)
        dosya = metin_klasoru / (f"bolum-{no:0{hane}d}" + (f"_{ad}" if ad else "") + ".md")
        baslik = f"# Bölüm {no}" + (f": {b.baslik}" if b.baslik else "")
        yazilacak.append((dosya, baslik + "\n\n" + "\n\n".join(b.paragraflar).rstrip() + "\n"))
    yazilan_kelime = sum(_kelime([p for p in b.paragraflar if not p.startswith("## ")]) for b in bolumler_)
    toplam = yazilan_kelime + _kelime([p for p in plan["on_metin"] if not p.startswith("# ")])
    beklenen = plan["kaynak_kelime"]
    if beklenen and abs(toplam - beklenen) > max(2, beklenen * 0.01):
        raise AktarmaHatasi(f"kelime doğrulaması başarısız: kaynak {beklenen}, aktarılan {toplam}; hiçbir dosya yazılmadı")
    metin_klasoru.mkdir(parents=True, exist_ok=True)
    for dosya, icerik in yazilacak:
        dosya.write_text(icerik, encoding="utf-8", newline="\n")
    kayit_klasoru = proje / ".hikaye" / "ice-aktarma"
    kayit_klasoru.mkdir(parents=True, exist_ok=True)
    if plan["on_metin"]:
        (kayit_klasoru / "on-metin.md").write_text("\n\n".join(plan["on_metin"]) + "\n", encoding="utf-8", newline="\n")
    rapor = {"kaynak": plan["kaynak"], "bolum_sayisi": len(yazilacak), "kaynak_kelime": beklenen, "aktarilan_kelime": toplam,
             "dosyalar": [d.relative_to(proje).as_posix() for d, _ in yazilacak],
             "on_metin": bool(plan["on_metin"])}
    (kayit_klasoru / "rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return rapor


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="DOCX, ODT, EPUB, TXT ve Markdown taslaklarını bölümlere bölerek içeri aktarır.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_o = alt.add_parser("onizle", help="bulunan bölüm sınırlarını göster, dosya yazma")
    p_a = alt.add_parser("aktar", help="bölümleri proje/metin/ altına yaz")
    p_a.add_argument("--proje", type=Path, required=True, help="kitap klasörü (yoksa oluşturulur)")
    for p in (p_o, p_a):
        p.add_argument("--kaynak", type=Path, required=True, help="kaynak dosya (.docx, .odt, .epub, .txt, .md)")
        p.add_argument("--desen", help="bölüm sınırı için düzenli ifade (isteğe bağlı 'baslik' adlı grup)")
        p.add_argument("--on-metin-bolum", action="store_true", help="ilk sınırdan önceki metni 1. bölüm say")
        p.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    arg = ayr.parse_args(argv)
    try:
        plan = plan_olustur(arg.kaynak, arg.desen, arg.on_metin_bolum)
        if arg.komut == "onizle":
            veri = onizleme(plan)
            if arg.json:
                print(json.dumps(veri, ensure_ascii=False, indent=2))
            else:
                print(f"{veri['kaynak']}: {veri['bolum_sayisi']} bölüm, {veri['kaynak_kelime']} kelime"
                      + (f" (ön metin {veri['on_metin_kelime']} kelime)" if veri["on_metin_kelime"] else ""))
                for b in veri["bolumler"]:
                    print(f"  {b['no']:>3}. [{b['sinir_satiri'][:40]}] {b['baslik'] or '(başlıksız)'}: {b['kelime']} kelime — "
                          f"{b['ilk_cumle']}")
            return 0 if veri["bolum_sayisi"] else 1
        if arg.proje.exists() and not arg.proje.is_dir():
            raise AktarmaHatasi(f"proje klasörü bekleniyordu, dosya verildi: {arg.proje}")
        rapor = aktar(plan, arg.proje)
        if arg.json:
            print(json.dumps(rapor, ensure_ascii=False, indent=2))
        else:
            print(f"{rapor['bolum_sayisi']} bölüm aktarıldı ({rapor['aktarilan_kelime']} kelime, kaynak {rapor['kaynak_kelime']}).")
            print("Sıradaki adım: hikaye-ice-aktar becerisinin 3. adımı (tersine planlama).")
    except AktarmaHatasi as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 1 if "bölüm sınırı bulunamadı" in str(hata) or "doğrulaması" in str(hata) else 2
    except dosya_oku.DosyaHatasi as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
