"""1.1.0 ile gelen özellikler: metin_analizi, .yasak-kaliplar, e_kitap_derle ve eklenti değerlendirme paketi."""

from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from conftest import BECERILER, KOK, ORNEK_ROMAN, calistir, json_cikti, modul_yukle

# ---------------------------------------------------------------- metin_analizi.py


def test_metin_analizi_atesman_ve_hece() -> None:
    ma = modul_yukle("metin_analizi.py")
    assert ma.hece_say("kapı") == 2
    assert ma.hece_say("saatçi") == 3  # sa-at-çi
    assert ma.hece_say("İstanbul'da") == 4
    assert ma.hece_say("123") == 0
    s = ma.analiz_et("Ali eve geldi. Kapıyı açtı. Çay koydu.")
    # 3 cümle, 7 kelime, 14 hece → 198,825 − 40,175×14/7 − 2,61×7/3
    beklenen = 198.825 - 40.175 * (14 / 7) - 2.610 * (7 / 3)
    assert s["okunabilirlik"]["atesman"] == round(beklenen, 1)
    assert s["okunabilirlik"]["duzey"] == "çok kolay"
    assert ma.atesman_duzeyi(95) == "çok kolay" and ma.atesman_duzeyi(10) == "çok zor"


def test_metin_analizi_yanki_cumle_basi_ve_duyu() -> None:
    ma = modul_yukle("metin_analizi.py")
    metin = ("Defne kapıyı açtı. Defne içeri girdi. Defne lambayı yaktı. "
             "Eski merdiven gıcırdadı, merdiven yine gıcırdadı, merdivenin sesi kesildi.")
    s = ma.analiz_et(metin)
    assert s["cumle_basi"] and s["cumle_basi"][0]["kelime"] == "defne" and s["cumle_basi"][0]["sayi"] == 3
    koklar = {y["kok"]: y["sayi"] for y in s["yankilar"]}
    assert koklar.get("merdi") == 3
    assert s["duyular"]["işitme"] >= 3
    assert any("merdiven" in u for u in s["uyarilar"])
    with pytest.raises(ma.AnalizHatasi):
        ma.yankilari_bul("a b", pencere=1)


def test_metin_analizi_diyalog_orani_ve_bos_metin() -> None:
    ma = modul_yukle("metin_analizi.py")
    s = ma.analiz_et("— Geldin mi?\n\nKapı kapandı.\n\n— Geldim, dedi.")
    assert 0.5 < s["diyalog_orani"] < 1
    bos = ma.analiz_et("---\nbaslik: x\n---\n# Yalnızca başlık\n")
    assert bos["kelime"] == 0 and "boş" in bos["uyarilar"][0]


def test_metin_analizi_cli_isaret_ve_json(tmp_path: Path) -> None:
    temiz = tmp_path / "temiz.md"
    temiz.write_text("Kapı açıldı. İçeri serin bir rüzgâr girdi.\n", encoding="utf-8")
    sonuc = calistir("metin_analizi.py", temiz)
    assert sonuc.returncode == 0 and "Ateşman" in sonuc.stdout
    taslak = tmp_path / "taslak.md"
    taslak.write_text("Kapı açıldı. [TK: sokak adı] Sonra ⟦ana oturum doldurur⟧ geldi.\n", encoding="utf-8")
    sonuc = calistir("metin_analizi.py", taslak, "--json")
    assert sonuc.returncode == 1
    veri = json_cikti(sonuc)[str(taslak)]
    assert [i["isaret"][:3] for i in veri["isaretler"]] == ["[TK", "⟦an"]
    hatali = calistir("metin_analizi.py", temiz, "--pencere", "1")
    assert hatali.returncode == 2 and "pencere" in hatali.stderr
    assert calistir("metin_analizi.py", tmp_path / "yok.md").returncode == 2


def test_ornek_metinlerde_bitmemis_isaret_yok() -> None:
    dosyalar = sorted((ORNEK_ROMAN / "metin").glob("*.md")) + [KOK / "ornekler" / "oyku" / "son-vapur" / "metin.md"]
    sonuc = calistir("metin_analizi.py", *dosyalar)
    assert sonuc.returncode == 0, sonuc.stdout


# ---------------------------------------------------------------- .yasak-kaliplar


def test_kitaba_ozgu_yasak_kaliplar(tmp_path: Path) -> None:
    kitap = tmp_path / "kitap"
    (kitap / "metin").mkdir(parents=True)
    (kitap / ".yasak-kaliplar").write_text("# yorum\nKalbi yerinden fırlayacak => Tepkiyi bedenle gösterin.\ngözleri doldu\n", encoding="utf-8")
    bolum = kitap / "metin" / "bolum-001_x.md"
    bolum.write_text("Kalbi yerinden fırlayacak gibiydi. Sonra GÖZLERİ DOLDU.\n", encoding="utf-8")
    sonuc = calistir("ai_kalip_denetle.py", bolum, "--json")
    veri = json_cikti(sonuc)
    yasaklar = [b for b in veri["bulgular"] if b["kural"] == "kitap-yasagi"]
    assert len(yasaklar) == 2 and all(b["onem"] == "engelleyici" for b in yasaklar)
    assert yasaklar[0]["oneri"] == "Tepkiyi bedenle gösterin."
    assert "yasak listesinde" in yasaklar[1]["oneri"]
    assert sonuc.returncode == 1


# ---------------------------------------------------------------- e_kitap_derle.py

EK = BECERILER / "e-kitap-derle" / "betikler" / "e_kitap_derle.py"


def _epub_dogrula(yol: Path) -> zipfile.ZipFile:
    zf = zipfile.ZipFile(yol)
    ilk = zf.infolist()[0]
    assert ilk.filename == "mimetype" and ilk.compress_type == zipfile.ZIP_STORED
    assert zf.read("mimetype") == b"application/epub+zip"
    for ad in zf.namelist():
        if ad.endswith((".xhtml", ".opf", ".ncx", ".xml")):
            ET.fromstring(zf.read(ad))  # iyi biçimli XML
    opf = ET.fromstring(zf.read("OEBPS/icerik.opf"))
    ns = {"o": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
    for item in opf.findall("o:manifest/o:item", ns):
        assert f"OEBPS/{item.get('href')}" in zf.namelist()
    assert opf.find("o:metadata/dc:language", ns).text == "tr"
    return zf


def test_e_kitap_ornek_romandan_epub_ve_html(tmp_path: Path) -> None:
    ortam = {"SOURCE_DATE_EPOCH": "1790000000"}
    sonuc = calistir(EK, "--proje", ORNEK_ROMAN, "--yazar", "Örnek Yazar", "--cikti", tmp_path / "a", ortam=ortam)
    assert sonuc.returncode == 0, sonuc.stderr
    assert "Saatçinin Kızı" in sonuc.stdout and "2 bölüm" in sonuc.stdout
    zf = _epub_dogrula(tmp_path / "a" / "saatcinin-kizi.epub")
    bolum1 = zf.read("OEBPS/bolum-001.xhtml").decode("utf-8")
    assert "<h1>1. Bölüm — Durmuş Saatler</h1>" in bolum1
    assert '<p class="diyalog">— Açık mısınız?</p>' in bolum1
    assert "Örnek Yazar" in zf.read("OEBPS/icerik.opf").decode("utf-8")
    html = (tmp_path / "a" / "saatcinin-kizi.html").read_text(encoding="utf-8")
    assert '<html lang="tr">' in html and 'href="#bolum-2"' in html
    # Aynı girdi ve aynı SOURCE_DATE_EPOCH → bayt bayt aynı EPUB
    calistir(EK, "--proje", ORNEK_ROMAN, "--yazar", "Örnek Yazar", "--cikti", tmp_path / "b", "--bicim", "epub", ortam=ortam)
    assert (tmp_path / "a" / "saatcinin-kizi.epub").read_bytes() == (tmp_path / "b" / "saatcinin-kizi.epub").read_bytes()
    assert not (tmp_path / "b" / "saatcinin-kizi.html").exists()


def test_e_kitap_markdown_donusumu() -> None:
    ek = modul_yukle("e_kitap_derle.py")
    bolum = ek.markdown_bolum("---\nx: 1\n---\n# Başlık & <Son>\n\n> alıntı\n\nİlk **kalın** _eğik_ paragraf.\n— Bir.\n— İki.\n\n* * *\n\n## Ara\n\nSon.<!-- gizli -->\n", "Yedek", "k.md")
    assert bolum.baslik == "Başlık & <Son>"
    assert "<blockquote><p>alıntı</p></blockquote>" in bolum.govde_html
    assert "<strong>kalın</strong>" in bolum.govde_html and "<em>eğik</em>" in bolum.govde_html
    assert bolum.govde_html.count('class="diyalog"') == 2
    assert '<hr class="sahne"/>' in bolum.govde_html and "<h2>Ara</h2>" in bolum.govde_html
    assert "gizli" not in bolum.govde_html
    assert ek.markdown_bolum("Başlıksız metin.", "3. Bölüm", "k.md").baslik == "3. Bölüm"
    assert ek.dosya_adi("Saatçinin Kızı: İkinci Cilt") == "saatcinin-kizi-ikinci-cilt"
    assert ek.dosya_adi("!!!") == "kitap"


def test_e_kitap_bitmemis_isaret_kapak_ve_hatalar(tmp_path: Path) -> None:
    taslak = tmp_path / "oyku.md"
    taslak.write_text("# Öykü\n\nBurada [DOLDUR: mekân] var.\n", encoding="utf-8")
    dur = calistir(EK, "--dosya", taslak, "--cikti", tmp_path / "c")
    assert dur.returncode == 1 and "[DOLDUR" in dur.stderr and not (tmp_path / "c").exists()
    gecti = calistir(EK, "--dosya", taslak, "--cikti", tmp_path / "c", "--taslak", "--bicim", "epub")
    assert gecti.returncode == 0 and "taslak" in gecti.stdout
    import struct
    import zlib

    def parca(tur: bytes, veri: bytes) -> bytes:
        return struct.pack(">I", len(veri)) + tur + veri + struct.pack(">I", zlib.crc32(tur + veri) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + parca(b"IHDR", struct.pack(">IIBBBBB", 2, 3, 8, 2, 0, 0, 0)) + \
        parca(b"IDAT", zlib.compress(b"\x00" + b"\xff\x00\x00" * 2) * 1) + parca(b"IEND", b"")
    kapak = tmp_path / "kapak.png"
    kapak.write_bytes(png)
    kapakli = calistir(EK, "--dosya", taslak, "--taslak", "--kapak", kapak, "--baslik", "Kapaklı", "--cikti", tmp_path / "d")
    assert kapakli.returncode == 0, kapakli.stderr
    zf = _epub_dogrula(tmp_path / "d" / "kapakli.epub")
    assert "OEBPS/kapak.png" in zf.namelist() and 'properties="cover-image"' in zf.read("OEBPS/icerik.opf").decode()
    for arg, parca_metin in [(("--proje", tmp_path / "yok"), "bölüm klasörü yok"),
                             (("--dosya", taslak, "--kapak", taslak), "kapak görseli"),
                             (("--dosya", tmp_path / "yok.md"), "bulunamadı"),
                             (("--dosya", taslak, "--baslik", "  "), "boş olamaz")]:
        sonuc = calistir(EK, *arg)
        assert sonuc.returncode == 2 and parca_metin in sonuc.stderr, (arg, sonuc.stderr)
    bozuk = calistir(EK, "--dosya", taslak, "--taslak", "--cikti", tmp_path / "e", ortam={"SOURCE_DATE_EPOCH": "abc"})
    assert bozuk.returncode == 2 and "SOURCE_DATE_EPOCH" in bozuk.stderr


def test_e_kitap_cift_bolum_numarasi_reddedilir(tmp_path: Path) -> None:
    kitap = tmp_path / "kitap"
    shutil.copytree(ORNEK_ROMAN, kitap)
    (kitap / "metin" / "bolum-001_kopya.md").write_text("# Kopya\n\nMetin.\n", encoding="utf-8")
    sonuc = calistir(EK, "--proje", kitap)
    assert sonuc.returncode == 2 and "iki dosya" in sonuc.stderr


# ---------------------------------------------------------------- evals/ (claude plugin eval)

CASE_ALANLARI = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
                 "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
GRADER_ALANLARI = {"type", "weight", "arm", "pattern", "flags", "match", "target", "tool", "input_match", "min", "max",
                   "before", "after", "path", "exists", "criteria", "focus", "baseline_file"}
GRADER_TURLERI = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}


def _on_bilgi(yol: Path) -> tuple[dict[str, str], str]:
    metin = yol.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", metin, re.S)
    assert m, f"{yol}: ön bilgi yok"
    alanlar = {}
    for satir in m.group(1).splitlines():
        anahtar, _, deger = satir.partition(":")
        alanlar[anahtar.strip()] = deger.strip()
    return alanlar, m.group(2)


def test_degerlendirme_paketi_gecerli_ve_her_beceriyi_kapsiyor() -> None:
    kok = KOK / "evals"
    vakalar = sorted(p.parent for p in kok.glob("*/prompt.md"))
    assert len(vakalar) >= 23
    tetiklenen: set[str] = set()
    olumsuz = 0
    for vaka in vakalar:
        alanlar, govde = _on_bilgi(vaka / "prompt.md")
        assert set(alanlar) <= CASE_ALANLARI, f"{vaka.name}: bilinmeyen alan {set(alanlar) - CASE_ALANLARI}"
        assert govde.strip(), f"{vaka.name}: istem boş"
        assert int(alanlar.get("max_turns", "10")) <= 200
        graders = sorted((vaka / "graders").glob("*.md"))
        assert graders, f"{vaka.name}: değerlendirici yok"
        for g in graders:
            g_alan, g_govde = _on_bilgi(g)
            assert set(g_alan) <= GRADER_ALANLARI, f"{g}: bilinmeyen alan {set(g_alan) - GRADER_ALANLARI}"
            assert g_alan["type"] in GRADER_TURLERI
            if g_alan["type"] == "llm":
                assert "PASS" in g_govde and "FAIL" in g_govde
            if g_alan["type"] == "regex":
                desen = g_alan["pattern"].strip('"').replace("\\\\", "\\")
                re.compile(desen)
            if g_alan["type"] == "tool_used" and g_alan.get("tool") == "Skill":
                if g_alan.get("max") == "0":
                    assert g_alan.get("arm") == "both" and g_alan.get("min") == "0"
                    olumsuz += 1
                else:
                    m = re.search(r"\?([a-z0-9-]+)\"'$", g_alan["input_match"])
                    assert m, g_alan["input_match"]
                    tetiklenen.add(m.group(1))
    beceriler = {p.parent.name for p in BECERILER.glob("*/SKILL.md")}
    assert beceriler <= tetiklenen, f"değerlendirmesi olmayan beceriler: {sorted(beceriler - tetiklenen)}"
    assert olumsuz >= 3
    assert "evals/results/" in (KOK / ".gitignore").read_text(encoding="utf-8")


def test_tur_kartlarinda_oz_denetim_sorulari() -> None:
    kartlar = [p for p in (KOK / "paylasilan" / "kaynaklar" / "tur-kartlari").glob("*.md") if p.name != "README.md"]
    assert len(kartlar) == 14
    for kart in kartlar:
        metin = kart.read_text(encoding="utf-8")
        assert "## Öz denetim soruları" in metin, kart.name
        assert len(re.findall(r"^\d\. .+\?$", metin, re.M)) >= 3, kart.name


# ---------------------------------------------------------------- terminal_gorseli.py ve README görselleri


def test_terminal_gorseli_svg_gecerli(tmp_path: Path) -> None:
    tg = modul_yukle("terminal_gorseli.py")
    satirlar = tg.satirlari_hazirla("python3 x.py <a&b>", "a.md:1:1\t[engelleyici] kural\t(alıntı)\n\t→ öneri\n" + "ş" * 250)
    assert satirlar[0].startswith("$ ") and max(len(s) for s in satirlar) <= tg.GENISLIK_KARAKTER + 8
    svg = tg.svg_uret("Başlık & deneme", satirlar)
    kok = ET.fromstring(svg)
    assert kok.tag.endswith("svg") and "&lt;a&amp;b&gt;" in svg
    assert tg.renk("x [engelleyici] y") == tg.RENKLER["engelleyici"] and tg.renk("  ✓ tamam") == tg.RENKLER["✓"]
    liste = calistir("terminal_gorseli.py", "--liste")
    assert liste.returncode == 0 and "terminal-e-kitap.svg" in liste.stdout
    uret = calistir("terminal_gorseli.py", "--cikti", tmp_path)
    assert uret.returncode == 0, uret.stderr
    yz = (tmp_path / "terminal-yz-tadi.svg").read_text(encoding="utf-8")
    assert "Toplam 10 bulgu" in yz and "engelleyici" in yz
    assert "saatcinin-kizi.epub" in (tmp_path / "terminal-e-kitap.svg").read_text(encoding="utf-8")


def test_readme_gorselleri_var_ve_gecerli() -> None:
    readme = (KOK / "README.md").read_text(encoding="utf-8")
    yerel = re.findall(r'(?:src="|\]\()(docs/gorseller/[^")]+)', readme)
    assert len(set(yerel)) >= 4, yerel
    for yol in set(yerel):
        dosya = KOK / yol
        assert dosya.is_file(), yol
        if dosya.suffix == ".svg":
            ET.fromstring(dosya.read_text(encoding="utf-8"))


def test_yazim_denetimi_yanlis_alarm_duzeltmeleri(tmp_path: Path) -> None:
    """Kendi belgelerimizde bulunan yanlış alarmlar: özel ada gelen -ki, kısaltma ve sıra sayısından sonra küçük harf."""
    dosya = tmp_path / "metin.md"
    dosya.write_text("Türkiye'deki savcılık, İzmir’deki ev.\nBu doğru (ör. karakterin sesi) ve 1–[N]. bölümler hazır. XIX. yüzyıl.\n"
                     "O dediki gel. bu yanlış.\nİstanbullu ve Ankaralı iki yazar İstanbulda buluştu.\n", encoding="utf-8")
    veri = json_cikti(calistir("yazim_denetle.py", dosya, "--json"))
    bulgular = veri["bulgular"] if isinstance(veri, dict) else veri
    kurallar = sorted((b["satir"], b["kural"]) for b in bulgular)
    assert kurallar == [(3, "cumle-basi-kucuk"), (3, "ki-bitisik"), (4, "kesme-isareti")], kurallar
