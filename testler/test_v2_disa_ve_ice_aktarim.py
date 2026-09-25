"""2.0.0: e_kitap_derle yeni biçimleri (belge_yazicilar: DOCX, ODT, baskı HTML, PDF, TXT, MD) ve belge_ice_aktar."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from conftest import ORNEK_ROMAN, calistir, json_cikti, modul_yukle

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
SABIT_ZAMAN = {"SOURCE_DATE_EPOCH": "1700000000"}


def derle(hedef: Path, *bicim: str, ortam: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return calistir("e_kitap_derle.py", "--proje", ORNEK_ROMAN, "--yazar", "Ayşe Yılmaz", "--cikti", hedef,
                    "--bicim", *bicim, ortam={**SABIT_ZAMAN, **(ortam or {})})


@pytest.fixture(scope="module")
def ciktilar(tmp_path_factory: pytest.TempPathFactory) -> Path:
    hedef = tmp_path_factory.mktemp("yayin")
    sonuc = derle(hedef, "hepsi", "txt", "md")
    assert sonuc.returncode == 0, sonuc.stderr
    return hedef


def test_hepsi_bicimleri_uretir(ciktilar: Path) -> None:
    adlar = {p.name for p in ciktilar.iterdir()}
    assert {"saatcinin-kizi.epub", "saatcinin-kizi.html", "saatcinin-kizi.docx", "saatcinin-kizi.odt",
            "saatcinin-kizi-baski.html", "saatcinin-kizi.txt", "saatcinin-kizi-tam.md"} <= adlar


def test_docx_yapisi_ve_gonderim_bicimi(ciktilar: Path) -> None:
    with zipfile.ZipFile(ciktilar / "saatcinin-kizi.docx") as z:
        assert z.testzip() is None
        adlar = set(z.namelist())
        assert {"[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml", "word/header1.xml",
                "word/footer1.xml", "docProps/core.xml"} <= adlar
        belge = ET.fromstring(z.read("word/document.xml"))
        stiller = z.read("word/styles.xml").decode("utf-8")
        ust = z.read("word/header1.xml").decode("utf-8")
        alt = z.read("word/footer1.xml").decode("utf-8")
        for ad in adlar:
            if ad.endswith((".xml", ".rels")):
                ET.fromstring(z.read(ad))  # her parça iyi biçimli XML
    basliklar = [p for p in belge.iter(W + "p") if (s := p.find(f"{W}pPr/{W}pStyle")) is not None
                 and s.get(W + "val") == "Heading1"]
    assert len(basliklar) == 2
    boyut = belge.find(f".//{W}sectPr/{W}pgSz")
    assert boyut is not None and boyut.get(W + "w") == "11906" and boyut.get(W + "h") == "16838"  # A4
    assert "Times New Roman" in stiller and 'w:val="tr-TR"' in stiller and 'w:line="360"' in stiller
    assert "Yılmaz / Saatçinin Kızı" in ust and "PAGE" in alt
    metin = "".join(t.text or "" for t in belge.iter(W + "t"))
    assert "Kepenk, kırk günlük tozu Defne'nin" in metin and "İçerisi" in metin


def test_odt_yapisi(ciktilar: Path) -> None:
    with zipfile.ZipFile(ciktilar / "saatcinin-kizi.odt") as z:
        ilk = z.infolist()[0]
        assert ilk.filename == "mimetype" and ilk.compress_type == zipfile.ZIP_STORED
        assert z.read("mimetype") == b"application/vnd.oasis.opendocument.text"
        for ad in ("content.xml", "styles.xml", "meta.xml", "META-INF/manifest.xml"):
            ET.fromstring(z.read(ad))
        icerik = ET.fromstring(z.read("content.xml"))
    basliklar = [h for h in icerik.iter(TEXT + "h")]
    assert len(basliklar) >= 2
    tum = "".join(icerik.itertext())
    assert "Defne" in tum and "ğ" in tum


def test_baski_html_txt_ve_md(ciktilar: Path) -> None:
    baski = (ciktilar / "saatcinin-kizi-baski.html").read_text(encoding="utf-8")
    assert "@page" in baski and "148mm 210mm" in baski and 'lang="tr"' in baski
    assert baski.count("Durmuş Saatler") >= 1 and "font-variant: small-caps" not in baski
    txt = (ciktilar / "saatcinin-kizi.txt").read_text(encoding="utf-8")
    assert "Saatçinin Kızı" in txt and "**" not in txt and "Kepenk" in txt
    md = (ciktilar / "saatcinin-kizi-tam.md").read_text(encoding="utf-8")
    assert md.startswith("% Saatçinin Kızı\n% Ayşe Yılmaz\n") and md.count("\n# ") == 2


def test_docx_odt_belirlenimci(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    assert derle(a, "docx", "odt").returncode == 0 and derle(b, "docx", "odt").returncode == 0
    for ad in ("saatcinin-kizi.docx", "saatcinin-kizi.odt"):
        assert (a / ad).read_bytes() == (b / ad).read_bytes()


def test_belge_yazicilar_denetim_karakteri_ve_satir_ici() -> None:
    by = modul_yukle("belge_yazicilar.py")
    assert by.temiz("a\x00b\x0bc\ufffe") == "abc"
    parca = by.satir_ici_parcalar("Bir **kalın** ve *eğik* söz.")
    assert ("kalın", True, False) in parca and ("eğik", False, True) in parca
    assert by.sade_metin("**Kalın** *eğik*") == "Kalın eğik"


def test_pdf_tarayici_yoksa_anlasilir_hata(tmp_path: Path) -> None:
    by = modul_yukle("belge_yazicilar.py")
    if by.tarayici_bul():
        sonuc = derle(tmp_path, "pdf")
        assert sonuc.returncode == 0, sonuc.stderr
        pdf = (tmp_path / "saatcinin-kizi.pdf").read_bytes()
        assert pdf.startswith(b"%PDF") and len(pdf) > 2000
    else:
        sonuc = derle(tmp_path, "pdf", ortam={"PATH": str(tmp_path)})
        assert sonuc.returncode == 2 and "tarayıcı" in sonuc.stderr.lower()


def _epubcheck() -> Path | None:
    for aday in (os.environ.get("EPUBCHECK_JAR"), "/tmp/epubcheck-5.1.0/epubcheck.jar"):
        if aday and Path(aday).is_file():
            return Path(aday)
    return None


ZORUNLU = os.environ.get("HIKAYE_DOGRULAMA_ZORUNLU") == "1"  # CI doğrulama işinde araç yoksa atlamak yerine başarısız ol


def _arac_gerekli(var: bool, ad: str) -> None:
    if not var:
        if ZORUNLU:
            pytest.fail(f"{ad} bulunamadı ama HIKAYE_DOGRULAMA_ZORUNLU=1")
        pytest.skip(f"{ad} yok")


def test_epubcheck_hatasiz(ciktilar: Path) -> None:
    _arac_gerekli(_epubcheck() is not None and shutil.which("java") is not None, "EPUBCheck ya da Java")
    sonuc = subprocess.run(["java", "-jar", str(_epubcheck()), str(ciktilar / "saatcinin-kizi.epub")],
                           capture_output=True, text=True, timeout=180)
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    assert "No errors or warnings detected" in sonuc.stdout


@pytest.mark.parametrize("ad", ["saatcinin-kizi.docx", "saatcinin-kizi.odt"])
def test_libreoffice_acar_ve_metni_korur(ciktilar: Path, tmp_path: Path, ad: str) -> None:
    _arac_gerekli(shutil.which("soffice") is not None, "LibreOffice (soffice)")
    ev = tmp_path / "loev"
    ev.mkdir()
    sonuc = subprocess.run(["soffice", "--headless", f"-env:UserInstallation={ev.resolve().as_uri()}", "--convert-to",
                            "txt:Text (encoded):UTF8", "--outdir", str(tmp_path), str(ciktilar / ad)],
                           capture_output=True, text=True, timeout=240, env={**os.environ, "HOME": str(ev)})
    cikti = tmp_path / (Path(ad).stem + ".txt")
    assert cikti.is_file(), sonuc.stdout + sonuc.stderr
    metin = cikti.read_text(encoding="utf-8-sig")
    assert "Kepenk, kırk günlük tozu Defne'nin ayakkabılarına döktü." in metin
    assert "Kapağın İçi" in metin


# ---------------------------------------------------------------- belge_ice_aktar.py


@pytest.mark.parametrize("ad", ["saatcinin-kizi.docx", "saatcinin-kizi.odt", "saatcinin-kizi.epub",
                                "saatcinin-kizi.txt", "saatcinin-kizi-tam.md"])
def test_ice_aktar_gidis_donus(ciktilar: Path, tmp_path: Path, ad: str) -> None:
    onizle = calistir("belge_ice_aktar.py", "onizle", "--kaynak", ciktilar / ad, "--json")
    assert onizle.returncode == 0, onizle.stderr
    veri = json_cikti(onizle)
    assert veri["bolum_sayisi"] == 2
    assert [b["baslik"] for b in veri["bolumler"]] == ["Durmuş Saatler", "Kapağın İçi"]
    proje = tmp_path / "kitap"
    aktar = calistir("belge_ice_aktar.py", "aktar", "--kaynak", ciktilar / ad, "--proje", proje)
    assert aktar.returncode == 0, aktar.stderr
    dosyalar = sorted((proje / "metin").glob("bolum-*.md"))
    assert [d.name for d in dosyalar] == ["bolum-001_durmus-saatler.md", "bolum-002_kapagin-ici.md"]
    yeni = dosyalar[0].read_text(encoding="utf-8")
    assert yeni.startswith("# Bölüm 1: Durmuş Saatler\n\n")
    orijinal = (ORNEK_ROMAN / "metin" / "bolum-001_durmus-saatler.md").read_text(encoding="utf-8")
    sade = lambda m: re.sub(r"\s+", " ", re.sub(r"^#.*$", "", m, flags=re.M)).strip()  # noqa: E731
    assert sade(yeni) == sade(orijinal)
    rapor = json_cikti(calistir("belge_ice_aktar.py", "onizle", "--kaynak", ciktilar / ad, "--json"))
    assert rapor["kaynak_kelime"] > 600
    ikinci = calistir("belge_ice_aktar.py", "aktar", "--kaynak", ciktilar / ad, "--proje", proje)
    assert ikinci.returncode == 2 and "üzerine yazılmaz" in ikinci.stderr


def test_ice_aktar_turkce_desenler_cp1254_ve_on_metin(tmp_path: Path) -> None:
    kaynak = tmp_path / "taslak.txt"
    kaynak.write_bytes("Anneme\n\nBİRİNCİ BÖLÜM\n\nİlk metin burada.\n\nBÖLÜM İKİ: Yol\n\nYolda yürüdüler.\n\n"
                       "3.\n\nSon bölüm.\n".encode("cp1254"))
    ia = modul_yukle("belge_ice_aktar.py")
    plan = ia.plan_olustur(kaynak, None, False)
    assert [b.baslik for b in plan["bolumler"]] == ["", "Yol", ""] and plan["on_metin"] == ["Anneme"]
    rapor = ia.aktar(plan, tmp_path / "kitap")
    assert rapor["bolum_sayisi"] == 3 and (tmp_path / "kitap" / ".hikaye" / "ice-aktarma" / "on-metin.md").is_file()
    assert (tmp_path / "kitap" / "metin" / "bolum-002_yol.md").read_text(encoding="utf-8").startswith("# Bölüm 2: Yol")
    birlikte = ia.plan_olustur(kaynak, None, True)
    assert len(birlikte["bolumler"]) == 4


def test_ice_aktar_ozel_desen_ve_sinirsiz_metin(tmp_path: Path) -> None:
    kaynak = tmp_path / "t.md"
    kaynak.write_text("KISIM A\n\nbir iki\n\nKISIM B\n\nüç dört\n", encoding="utf-8")
    sonuc = calistir("belge_ice_aktar.py", "onizle", "--kaynak", kaynak, "--desen", r"^KISIM (?P<baslik>\w+)$", "--json")
    assert sonuc.returncode == 0 and [b["baslik"] for b in json_cikti(sonuc)["bolumler"]] == ["A", "B"]
    duz = tmp_path / "d.txt"
    duz.write_text("Sadece bir paragraf. Bölüm yok.\n", encoding="utf-8")
    assert calistir("belge_ice_aktar.py", "onizle", "--kaynak", duz).returncode == 1
    assert calistir("belge_ice_aktar.py", "aktar", "--kaynak", duz, "--proje", tmp_path / "p").returncode == 1
    assert calistir("belge_ice_aktar.py", "onizle", "--kaynak", kaynak, "--desen", "(").returncode == 2


def test_ice_aktar_kelime_dogrulamasi_dosya_yazdirmaz(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ia = modul_yukle("belge_ice_aktar.py")
    kaynak = tmp_path / "t.md"
    kaynak.write_text("# Bir\n\nüç dört beş\n\n# İki\n\naltı yedi\n", encoding="utf-8")
    plan = ia.plan_olustur(kaynak, None, False)
    plan["kaynak_kelime"] = 500
    with pytest.raises(ia.AktarmaHatasi, match="doğrulaması"):
        ia.aktar(plan, tmp_path / "kitap")
    assert not (tmp_path / "kitap" / "metin").exists()


@pytest.mark.parametrize("ad, icerik, ileti", [
    ("x.docx", b"zip degil", "zip"),
    ("x.doc", b"eski", "desteklenmeyen"),
    ("x.pdf", b"%PDF", "desteklenmeyen"),
])
def test_ice_aktar_bozuk_girdiler(tmp_path: Path, ad: str, icerik: bytes, ileti: str) -> None:
    yol = tmp_path / ad
    yol.write_bytes(icerik)
    sonuc = calistir("belge_ice_aktar.py", "onizle", "--kaynak", yol)
    assert sonuc.returncode == 2 and ileti in sonuc.stderr and "Traceback" not in sonuc.stderr


def test_ice_aktar_doctype_ve_eksik_parca_reddi(tmp_path: Path) -> None:
    kotu = tmp_path / "kotu.docx"
    with zipfile.ZipFile(kotu, "w") as z:
        z.writestr("word/document.xml", '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><x>&a;</x>')
    sonuc = calistir("belge_ice_aktar.py", "onizle", "--kaynak", kotu)
    assert sonuc.returncode == 2 and "DOCTYPE" in sonuc.stderr
    eksik = tmp_path / "eksik.epub"
    with zipfile.ZipFile(eksik, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
    sonuc = calistir("belge_ice_aktar.py", "onizle", "--kaynak", eksik)
    assert sonuc.returncode == 2 and "container.xml" in sonuc.stderr
    assert calistir("belge_ice_aktar.py", "onizle", "--kaynak", tmp_path).returncode == 2
