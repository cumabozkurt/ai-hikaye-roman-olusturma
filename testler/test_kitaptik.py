"""kitaptik_hazirla.py: Kitaptik (kitaptik.com) yayın denetimi ve toplu yükleme paketi."""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from conftest import KOK, calistir, json_cikti, modul_yukle

kh = modul_yukle("kitaptik_hazirla.py")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ZORUNLU = os.environ.get("HIKAYE_DOGRULAMA_ZORUNLU") == "1"


# ---------------------------------------------------------------- yardımcılar


def _proje(kok: Path, bolumler: list[tuple[str, str]], plan: str | None = None) -> Path:
    proje = kok / "kitap"
    (proje / "metin").mkdir(parents=True)
    for i, (baslik, govde) in enumerate(bolumler, 1):
        (proje / "metin" / f"bolum-{i:03d}_b{i}.md").write_text(f"# {baslik}\n\n{govde}\n", encoding="utf-8")
    if plan is not None:
        (proje / "plan").mkdir()
        (proje / "plan" / "genel-plan.md").write_text(plan, encoding="utf-8")
    return proje


def _bilgi(proje: Path, **alan: str) -> None:
    varsayilan = {"Kitap başlığı": "Deneme Kitabı", "Yazar adı": "Ayşe Yılmaz", "Kategori": "Roman",
                  "Alt kategoriler": "Aşk", "Etiketler": "aşk, istanbul", "Dil": "Türkçe",
                  "Yetişkin içerik (18+)": "hayır", "Kitap tamamlandı": "hayır", "PDF indirme": "evet",
                  "Ücretli": "hayır", "Fiyat (TL)": ""}
    aciklama = alan.pop("aciklama", "Genç bir saatçi, dedesinin dükkânında bütün saatlerin aynı dakikada durduğunu "
                                    "görür ve kırk yıllık bir sırrın peşine düşer. Ama bazı sırlar gömülü kalmak ister.")
    varsayilan.update(alan)
    satirlar = ["# Kitaptik Yayın Bilgileri", ""] + [f"- {k}: {v}" for k, v in varsayilan.items()]
    satirlar += ["", "## Açıklama", "", aciklama, "", "## Neden okumalı?", "", "Kısa bölümler, bol merak.", ""]
    (proje / "yayin").mkdir(exist_ok=True)
    (proje / "yayin" / "kitaptik.md").write_text("\n".join(satirlar), encoding="utf-8")


def _paragraflar(adet: int, kelime: int = 100) -> str:
    return "\n\n".join(" ".join(f"sözcük{i}_{j}" for j in range(kelime)) for i in range(adet))


def _png(g: int, y: int, hareketli: bool = False) -> bytes:
    def parca(tur: bytes, veri: bytes) -> bytes:
        return struct.pack(">I", len(veri)) + tur + veri + struct.pack(">I", zlib.crc32(tur + veri) & 0xFFFFFFFF)
    ihdr = parca(b"IHDR", struct.pack(">IIBBBBB", g, y, 8, 2, 0, 0, 0))
    actl = parca(b"acTL", struct.pack(">II", 2, 0)) if hareketli else b""
    return b"\x89PNG\r\n\x1a\n" + ihdr + actl + parca(b"IEND", b"")


def _jpeg(g: int, y: int) -> bytes:
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = b"\xff\xc0" + struct.pack(">HBHHB", 17, 8, y, g, 3) + b"\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


def _docx_basliklari(yol: Path) -> tuple[list[str], list[list[str]]]:
    """Başlık 1 metinleri ve her başlığın altındaki paragraf metinleri."""
    with zipfile.ZipFile(yol) as z:
        assert z.testzip() is None
        for ad in z.namelist():
            if ad.endswith(".xml") or ad.endswith(".rels"):
                ET.fromstring(z.read(ad))
        kok = ET.fromstring(z.read("word/document.xml"))
    basliklar: list[str] = []
    govdeler: list[list[str]] = []
    for p in kok.iter(f"{W}p"):
        stil = p.find(f"{W}pPr/{W}pStyle")
        metin = "".join(t.text or "" for t in p.iter(f"{W}t"))
        if stil is not None and stil.get(f"{W}val") == "Heading1":
            basliklar.append(metin)
            govdeler.append([])
        else:
            assert basliklar, "ilk Başlık 1'den önce metin olmamalı (Kitaptik onu ayrı bölüm sayar)"
            govdeler[-1].append(metin)
    return basliklar, govdeler


# ---------------------------------------------------------------- birim


def test_kategoriler_canli_siteyle_ayni_on_ana_kategori() -> None:
    assert list(kh.KATEGORILER) == ["Roman", "Öykü", "Şiir", "Deneme", "Mektup", "Sözler (Aforizma)",
                                    "Kişisel Gelişim", "Spiritüel (Dini)", "Dünya Klasikleri", "Diğer"]
    assert "Polisiye ve Gizem" in kh.KATEGORILER["Roman"]
    assert kh.kategori_adi("roman") == "Roman" and kh.kategori_adi("ÖYKÜ") == "Öykü"
    assert kh.kategori_adi("Bilimkurgu") is None
    sonuc = calistir("kitaptik_hazirla.py", "kategoriler", "--json")
    assert sonuc.returncode == 0 and json_cikti(sonuc)["Roman"] == kh.KATEGORILER["Roman"]
    assert "Roman:" in calistir("kitaptik_hazirla.py", "kategoriler").stdout


def test_js_uzunluk_ve_baslik_kisaltma() -> None:
    assert kh.js_uzunluk("Işık") == 4
    assert kh.js_uzunluk("a😀") == 3  # emoji UTF-16'da iki birim
    assert kh.js_uzunluk("I\u0307") == 1 and kh.js_uzunluk("s\u0327") == 1  # NFC: ş tek karakter
    uzun = "Bir " + "çok uzun kelimelerle dolu başlık " * 5
    kisa = kh.baslik_kisalt(uzun, 77)
    assert kh.js_uzunluk(kisa) <= 77 and kisa.endswith("…") and not kisa.endswith(" …")
    assert kh.baslik_kisalt("Kısa başlık", 77) == "Kısa başlık"
    tek = kh.baslik_kisalt("a" * 200, 77)
    assert kh.js_uzunluk(tek) == 77
    emojili = kh.baslik_kisalt("😀" * 60, 77)
    assert kh.js_uzunluk(emojili) <= 77


def test_etiket_kurali() -> None:
    kabul, uzun = kh.etiketleri_ayir("aşk, AŞK;#istanbul\npolisiye,, " + "x" * 41)
    assert kabul == ["aşk", "istanbul", "polisiye"]
    assert uzun == ["x" * 41]


def test_evet_hayir() -> None:
    assert kh.evet_hayir("Evet") is True and kh.evet_hayir("HAYIR") is False and kh.evet_hayir("açık") is True
    assert kh.evet_hayir("belki") is None


@pytest.mark.parametrize(("veri", "bicim", "g", "y", "hareketli"), [
    (_png(583, 827), "PNG", 583, 827, False),
    (_png(600, 900, hareketli=True), "PNG", 600, 900, True),
    (_jpeg(1200, 1800), "JPEG", 1200, 1800, False),
    (b"GIF89a" + struct.pack("<HH", 300, 450) + b"\x00" * 5 + b"\x21\xf9\x04" * 2, "GIF", 300, 450, True),
    (b"RIFF" + b"\x00" * 4 + b"WEBPVP8X" + struct.pack("<I", 10) + b"\x02\x00\x00\x00"
     + (582).to_bytes(3, "little") + (826).to_bytes(3, "little"), "WebP", 583, 827, True),
    (b"\x00\x00\x00\x1cftypavif" + b"\x00" * 20, "AVIF", None, None, False),
    (b"\x00\x00\x00\x18ftypheic" + b"\x00" * 20, "HEIC", None, None, False),
    (b"<svg xmlns='http://www.w3.org/2000/svg'/>", None, None, None, False),
])
def test_gorsel_basligi(veri: bytes, bicim: str | None, g: int | None, y: int | None, hareketli: bool) -> None:
    bilgi = kh.gorsel_bilgisi(veri)
    assert (bilgi["bicim"], bilgi["genislik"], bilgi["yukseklik"], bilgi["hareketli"]) == (bicim, g, y, hareketli)


def test_uzun_bolum_sahne_ayracinda_bolunur() -> None:
    bloklar = [("p", " ".join(["kelime"] * 100))] * 60 + [("ayrac", "")] + [("p", " ".join(["kelime"] * 100))] * 60
    gruplar = kh._bol(bloklar, 10_000)
    assert len(gruplar) == 2
    assert all(kh.kelime_say(g) <= 10_000 for g in gruplar)
    assert kh.kelime_say(gruplar[0]) == 6000  # ayraçta, yarıya en yakın yerde bölündü
    assert gruplar[1][0][0] == "ilk" and all(g[-1][0] != "ayrac" for g in gruplar)


# ---------------------------------------------------------------- örnek roman


def test_ornek_roman_baslat_denetle_paket(roman: Path, tmp_path: Path) -> None:
    denetim = calistir("kitaptik_hazirla.py", "denetle", "--proje", roman, "--json")
    assert denetim.returncode == 0, denetim.stdout + denetim.stderr
    rapor = json_cikti(denetim)
    assert rapor["ozet"]["kitaptik_bolumu"] == 2 and rapor["ozet"]["hata"] == 0 and rapor["ozet"]["uyari"] == 0
    assert rapor["kaynak"] == "https://kitaptik.com"

    kapak = tmp_path / "kapak.png"
    kapak.write_bytes(_png(583, 827))
    paket = calistir("kitaptik_hazirla.py", "paket", "--proje", roman, "--kapak", kapak, "--yazar", "Ayşe Yılmaz")
    assert paket.returncode == 0, paket.stdout + paket.stderr
    hedef = roman / "yayin" / "kitaptik"
    assert sorted(p.name for p in hedef.iterdir()) == ["karakterler.md", "kitap-bilgileri.md", "rapor.json",
                                                      "saatcinin-kizi-kitaptik.docx", "yayin-kontrol-listesi.md"]
    basliklar, govdeler = _docx_basliklari(hedef / "saatcinin-kizi-kitaptik.docx")
    assert basliklar == ["1. Bölüm — Durmuş Saatler", "2. Bölüm — Kapağın İçi"]
    assert govdeler[0][0].startswith("Kepenk")
    with zipfile.ZipFile(hedef / "saatcinin-kizi-kitaptik.docx") as z:
        belge = z.read("word/document.xml").decode()
        assert "Ayşe Yılmaz" in z.read("docProps/core.xml").decode()
    assert "IlkParagraf" not in belge and "Govde" not in belge  # içe aktarıcı özel biçemleri tanımaz

    karakterler = (hedef / "karakterler.md").read_text(encoding="utf-8")
    assert "## Defne Aras" in karakterler and "- Rol: Ana karakter" in karakterler
    assert "İstediği:" in karakterler and "Istediği" not in karakterler
    assert "Sırrı" not in karakterler  # spoiler alanları alınmaz
    liste = (hedef / "yayin-kontrol-listesi.md").read_text(encoding="utf-8")
    assert "Toplu Yükle" in liste and "otomatik yükleme yapmaz" in liste and "https://kitaptik.com" in liste
    rapor = json.loads((hedef / "rapor.json").read_text(encoding="utf-8"))
    assert rapor["ozet"]["kapak"]["genislik"] == 583 and not [b for b in rapor["bulgular"] if b["kimlik"].startswith("kapak")]
    bilgi_formu = (hedef / "kitap-bilgileri.md").read_text(encoding="utf-8")
    assert "| Kategori | Roman |" in bilgi_formu and "Polisiye ve Gizem, Aşk" in bilgi_formu

    # baslat: var olan dosyanın üzerine --zorla olmadan yazmaz; yazınca türden öneri üretir
    assert calistir("kitaptik_hazirla.py", "baslat", "--proje", roman).returncode == 2
    sonuc = calistir("kitaptik_hazirla.py", "baslat", "--proje", roman, "--zorla")
    assert sonuc.returncode == 0, sonuc.stderr
    bilgi = (roman / "yayin" / "kitaptik.md").read_text(encoding="utf-8")
    assert "- Kitap başlığı: Saatçinin Kızı" in bilgi and "- Kategori: Roman" in bilgi
    assert "- Alt kategoriler: Polisiye ve Gizem, Aşk" in bilgi
    assert "Dedesinin kırk yıllık saat dükkânını devralan Defne" in bilgi


def test_paket_ayni_girdiyle_ayni_docx(roman: Path, tmp_path: Path) -> None:
    ortam = {"SOURCE_DATE_EPOCH": "1758794400"}
    for ad in ("a", "b"):
        assert calistir("kitaptik_hazirla.py", "paket", "--proje", roman, "--cikti", tmp_path / ad,
                        ortam=ortam).returncode == 0
    assert (tmp_path / "a" / "saatcinin-kizi-kitaptik.docx").read_bytes() == \
        (tmp_path / "b" / "saatcinin-kizi-kitaptik.docx").read_bytes()


# ---------------------------------------------------------------- denetimler


def test_bilgi_hatalari_paketi_durdurur(tmp_path: Path) -> None:
    proje = _proje(tmp_path, [("Bir", "Merhaba dünya.")])
    _bilgi(proje, **{"Kategori": "Roman", "Alt kategoriler": "Aşk, Klasik Şiir, Gerilim, Dram",
                     "Dil": "İngilizce", "Kitap başlığı": "A", "Yetişkin içerik (18+)": "belki",
                     "Ücretli": "evet", "Fiyat (TL)": "5"}, aciklama="x" * 2501)
    sonuc = calistir("kitaptik_hazirla.py", "paket", "--proje", proje, "--json")
    assert sonuc.returncode == 1
    kimlikler = {b["kimlik"] for b in json_cikti(sonuc)["bulgular"] if b["duzey"] == "hata"}
    assert {"baslik-yok", "alt-kategori-gecersiz", "alt-kategori-fazla", "dil", "aciklama-uzun", "evet-hayir",
            "fiyat"} <= kimlikler
    assert not (proje / "yayin" / "kitaptik").exists()
    assert "Hatalar giderilmeden paket yazılmadı" in calistir("kitaptik_hazirla.py", "paket", "--proje", proje).stdout


def test_gecersiz_kategori_ve_etiket_uyarilari(tmp_path: Path) -> None:
    proje = _proje(tmp_path, [("Bir", "Merhaba dünya.")])
    _bilgi(proje, **{"Kategori": "Bilimkurgu", "Etiketler": ", ".join(f"etiket{i}" for i in range(31))})
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--json"))
    kimlikler = {b["kimlik"] for b in rapor["bulgular"]}
    assert {"kategori-gecersiz", "etiket-fazla"} <= kimlikler


def test_uzun_bolum_bolunur_ve_baslik_kisalir(tmp_path: Path) -> None:
    govde = _paragraflar(90) + "\n\n* * *\n\n" + _paragraflar(90)
    uzun_baslik = "Uzun Gecenin Sonunda Kıyıya Vuran Mektuplar ve Hiç Açılmamış Zarfların Sessiz Hikâyesi Üzerine"
    proje = _proje(tmp_path, [(uzun_baslik, govde), ("Kısa", "Son.")])
    _bilgi(proje)
    sonuc = calistir("kitaptik_hazirla.py", "paket", "--proje", proje, "--json")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    rapor = json_cikti(sonuc)
    assert rapor["ozet"]["kitaptik_bolumu"] == 3 and rapor["ozet"]["bolunen_bolum"] == 1
    assert {"bolum-uzun", "baslik-uzun"} <= {b["kimlik"] for b in rapor["bulgular"]}
    basliklar, govdeler = _docx_basliklari(proje / "yayin" / "kitaptik" / "deneme-kitabi-kitaptik.docx")
    assert len(basliklar) == 3
    assert basliklar[0].endswith("(1/2)") and basliklar[1].endswith("(2/2)") and basliklar[2] == "Kısa"
    assert all(kh.js_uzunluk(b) <= 77 for b in basliklar)
    for govde_p in govdeler:
        assert sum(len(p.split()) for p in govde_p) <= 10_000
    assert govdeler[1][0] != "* * *"


def test_tek_paragraf_siniri_asarsa_kullanim_hatasi(tmp_path: Path) -> None:
    proje = _proje(tmp_path, [("Bir", " ".join(["kelime"] * 10_001))])
    sonuc = calistir("kitaptik_hazirla.py", "denetle", "--proje", proje)
    assert sonuc.returncode == 2 and "tek paragraf" in sonuc.stderr


def test_bes_yuzden_fazla_bolum_birden_cok_docx(tmp_path: Path) -> None:
    proje = _proje(tmp_path, [(f"Bölüm {i}", f"Kısa metin {i}.") for i in range(1, 503)])
    _bilgi(proje)
    sonuc = calistir("kitaptik_hazirla.py", "paket", "--proje", proje, "--json")
    assert sonuc.returncode == 0, sonuc.stderr
    rapor = json_cikti(sonuc)
    assert "coklu-docx" in {b["kimlik"] for b in rapor["bulgular"]}
    hedef = proje / "yayin" / "kitaptik"
    assert len(_docx_basliklari(hedef / "deneme-kitabi-kitaptik-1.docx")[0]) == 500
    assert _docx_basliklari(hedef / "deneme-kitabi-kitaptik-2.docx")[0] == ["Bölüm 501", "Bölüm 502"]
    assert "Mevcut bölümlere ekle" in (hedef / "yayin-kontrol-listesi.md").read_text(encoding="utf-8")


def test_icerik_sinyalleri_18_arti_ve_tetikleyici_uyarisi(tmp_path: Path) -> None:
    sert = "Adam bağırdı: \"Siktir git!\" Kan her yeri kapladı, bıçak yine indi, kan sıçradı, kan aktı."
    proje = _proje(tmp_path, [("Bir", (sert + "\n\n") * 6), ("İki", "O gece intihar etmeyi düşündü."),
                              ("Üç", "[TW: İntihar]\n\nO gece intihar etmeyi düşündü.")])
    _bilgi(proje)
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--json"))
    bulgular = rapor["bulgular"]
    assert rapor["ozet"]["yetiskin_onerisi"] is True
    assert any(b["kimlik"] == "yetiskin-oneri" for b in bulgular)
    tw = [b for b in bulgular if b["kimlik"] == "tw-eksik"]
    assert [b["bolum"] for b in tw] == [2]  # uyarısı olan 3. bölüm işaretlenmez
    _bilgi(proje, **{"Yetişkin içerik (18+)": "evet"})
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--json"))
    assert not any(b["kimlik"] == "yetiskin-oneri" for b in rapor["bulgular"])


def test_temiz_metinde_yanlis_alarm_yok(roman: Path) -> None:
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", roman, "--json"))
    assert rapor["ozet"]["yetiskin_onerisi"] is False
    assert not {"tw-eksik", "cinsel-saldiri", "baglanti", "gorsel"} & {b["kimlik"] for b in rapor["bulgular"]}


def test_bitmemis_metin_gorsel_ve_baglanti(tmp_path: Path) -> None:
    proje = _proje(tmp_path, [("Bir", "Başladı. [TODO: sahneyi yaz]\n\n![harita](harita.png)\n\n"
                                      "Devamı için www.ornek-site.com adresine gelin.")])
    _bilgi(proje)
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--json"))
    duzey = {b["kimlik"]: b["duzey"] for b in rapor["bulgular"]}
    assert duzey["bitmemis"] == "hata" and duzey["gorsel"] == "uyari" and duzey["baglanti"] == "uyari"
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--json", "--taslak"))
    assert {b["kimlik"]: b["duzey"] for b in rapor["bulgular"]}["bitmemis"] == "uyari"


@pytest.mark.parametrize(("veri", "kimlik", "duzey"), [
    (_png(50, 80), "kapak-kucuk", "hata"),
    (_png(300, 450), "kapak-dusuk", "uyari"),
    (_jpeg(1600, 900), "kapak-yatay", "uyari"),
    (_png(600, 1400), "kapak-oran", "uyari"),
    (_png(600, 900, hareketli=True), "kapak-hareketli", "hata"),
    (b"<svg/>", "kapak-bicim", "hata"),
])
def test_kapak_denetimi(tmp_path: Path, veri: bytes, kimlik: str, duzey: str) -> None:
    proje = _proje(tmp_path, [("Bir", "Merhaba.")])
    _bilgi(proje)
    (proje / "kapak").mkdir()
    (proje / "kapak" / "kapak.png").write_bytes(veri)
    rapor = json_cikti(calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--json"))
    assert {b["kimlik"]: b["duzey"] for b in rapor["bulgular"]}.get(kimlik) == duzey


def test_kullanim_hatalari_cikis_2(tmp_path: Path) -> None:
    assert calistir("kitaptik_hazirla.py", "denetle", "--proje", tmp_path / "yok").returncode == 2
    bos = tmp_path / "bos"
    bos.mkdir()
    sonuc = calistir("kitaptik_hazirla.py", "paket", "--proje", bos)
    assert sonuc.returncode == 2 and "bölüm dosyası yok" in sonuc.stderr
    proje = _proje(tmp_path, [("Bir", "Merhaba.")])
    assert calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--bolum-siniri", "20000").returncode == 2
    assert calistir("kitaptik_hazirla.py", "denetle", "--proje", proje, "--kapak", tmp_path / "yok.png").returncode == 2
    assert calistir("kitaptik_hazirla.py", "baslat", "--proje", proje, "--ana-kategori", "Uzay").returncode == 2
    dosya = tmp_path / "dosya.txt"
    dosya.write_text("x", encoding="utf-8")
    assert calistir("kitaptik_hazirla.py", "paket", "--proje", proje, "--cikti", dosya).returncode == 2
    assert calistir("kitaptik_hazirla.py").returncode == 2


def test_baslat_oyku_ve_tur_eslemesi(tmp_path: Path) -> None:
    proje = _proje(tmp_path, [("Bir", "Merhaba.")], plan="# Kıyı — Genel Plan\n\n- Tür: fantastik, korku\n"
                                                        "- Tek cümlelik öz: Bir fener bekçisi denizden gelen sesi dinler.\n")
    assert calistir("kitaptik_hazirla.py", "baslat", "--proje", proje, "--ana-kategori", "öykü").returncode == 0
    bilgi = kh.bilgi_oku(proje)
    assert bilgi["baslik"] == "Kıyı" and bilgi["kategori"] == "Öykü"
    assert bilgi["aciklama"] == "Bir fener bekçisi denizden gelen sesi dinler."
    altlar = [a.strip() for a in bilgi["alt_kategoriler"].split(",") if a.strip()]
    assert altlar and all(kh.alt_kategori_adi("Öykü", a) for a in altlar)


# ---------------------------------------------------------------- mammoth ile bağımsız okuma


def _mammoth_ortami() -> dict[str, str] | None:
    if not shutil.which("node"):
        return None
    ortam = dict(os.environ)
    if os.environ.get("MAMMOTH_NODE_PATH"):
        ortam["NODE_PATH"] = os.environ["MAMMOTH_NODE_PATH"]
    sonuc = subprocess.run(["node", "-e", "require.resolve('mammoth')"], capture_output=True, env=ortam, timeout=60)
    return ortam if sonuc.returncode == 0 else None


def test_mammoth_bolumleri_kitaptik_gibi_okur(tmp_path: Path) -> None:
    ortam = _mammoth_ortami()
    if ortam is None:
        if ZORUNLU:
            pytest.fail("node ya da mammoth bulunamadı ama HIKAYE_DOGRULAMA_ZORUNLU=1 (MAMMOTH_NODE_PATH ayarlayın)")
        pytest.skip("node ya da mammoth yok")
    govde = "**Kalın** ve *eğik* söz.\n\n## Ara başlık\n\n> Alıntı satırı.\n\n" + _paragraflar(110) + \
        "\n\n* * *\n\n" + _paragraflar(110)
    proje = _proje(tmp_path, [("Çok Uzun Bir Bölüm Başlığı " * 4, govde), ("Işıklar ve Gölgeler 😀", "Son söz.")])
    _bilgi(proje)
    assert calistir("kitaptik_hazirla.py", "paket", "--proje", proje).returncode == 0
    docx = proje / "yayin" / "kitaptik" / "deneme-kitabi-kitaptik.docx"
    sonuc = subprocess.run(["node", str(KOK / "testler" / "araclar" / "kitaptik_docx_oku.js"), str(docx)],
                           capture_output=True, text=True, encoding="utf-8", env=ortam, timeout=120)
    assert sonuc.returncode == 0, sonuc.stderr
    okunan = json.loads(sonuc.stdout)
    beklenen = json.loads((proje / "yayin" / "kitaptik" / "rapor.json").read_text(encoding="utf-8"))["ozet"]["bolumler"]
    assert okunan["onsoz"] == "" and okunan["uyarilar"] == []
    assert [b["baslik"] for b in okunan["bolumler"]] == [b["baslik"] for b in beklenen]
    assert [b["kelime"] for b in okunan["bolumler"]] == [b["kelime"] for b in beklenen]
    assert all(b["baslik_uzunluk"] <= 77 and b["kelime"] <= 10_000 and b["h2"] == 0 for b in okunan["bolumler"])
