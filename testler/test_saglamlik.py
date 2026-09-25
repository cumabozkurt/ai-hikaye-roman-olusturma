"""Sağlamlık testleri: bozuk, eksik ya da yanlış kodlanmış girdilerde betikler yığın izi (traceback)
yerine Türkçe, tek satırlık bir hata iletisi vermelidir."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from conftest import calistir, modul_yukle

INGILIZCE = re.compile(r"Traceback|beklenmeyen hata|\b(Error|No such file|Expecting|codec|object has no)\b")


@pytest.fixture()
def bozuk(tmp_path: Path) -> dict[str, Path]:
    yollar = {
        "yok": tmp_path / "yok.md",
        "klasor": tmp_path / "klasor",
        "ikili": tmp_path / "ikili.md",
        "bozuk_json": tmp_path / "bozuk.json",
        "liste_json": tmp_path / "liste.json",
    }
    yollar["klasor"].mkdir()
    yollar["ikili"].write_bytes(bytes(range(256)) * 4)
    yollar["bozuk_json"].write_text('{"a":', encoding="utf-8")
    yollar["liste_json"].write_text("[1, 2]", encoding="utf-8")
    proje = tmp_path / "bozuk-proje"
    (proje / "takip").mkdir(parents=True)
    (proje / "takip" / "_takip-durumu.json").write_text("{", encoding="utf-8")
    yollar["bozuk_proje"] = proje
    liste_proje = tmp_path / "liste-proje"
    (liste_proje / "takip").mkdir(parents=True)
    (liste_proje / "takip" / "_takip-durumu.json").write_text("[]", encoding="utf-8")
    yollar["liste_proje"] = liste_proje
    return yollar


def _turkce_hata(sonuc) -> None:  # type: ignore[no-untyped-def]
    metin = sonuc.stderr + (sonuc.stdout if sonuc.returncode else "")
    assert sonuc.returncode in (1, 2), metin
    assert not INGILIZCE.search(metin), metin
    assert metin.strip(), "hata iletisi boş"


METIN_BETIKLERI = ["ai_kalip_denetle.py", "bozulma_denetle.py", "metin_olcum.py", "yazim_denetle.py",
                   "noktalama_duzelt.py", "turkce_uyum_denetle.py"]


@pytest.mark.parametrize("betik", METIN_BETIKLERI)
@pytest.mark.parametrize("tur", ["yok", "klasor", "ikili"])
def test_metin_betikleri_bozuk_dosyada_turkce_hata_verir(betik: str, tur: str, bozuk: dict[str, Path]) -> None:
    if betik == "turkce_uyum_denetle.py":
        from conftest import KOK
        sonuc = calistir(KOK / "betikler" / betik, bozuk[tur])
        if tur != "yok":  # klasör ya da ikili dosya: denetçi atlar ya da kodlama bulgusu verir
            assert "Traceback" not in sonuc.stderr
            return
    else:
        sonuc = calistir(betik, bozuk[tur])
    _turkce_hata(sonuc)


@pytest.mark.parametrize("komut", [
    ["sureklilik_denetle.py", "--proje", "{bozuk_proje}"],
    ["sureklilik_denetle.py", "--proje", "{liste_proje}"],
    ["takip_kaydet.py", "denetle", "--proje", "{bozuk_proje}"],
    ["hikayectl.py", "bolum", "kaydet", "--proje", "{klasor}", "--bolum", "1", "--girdi", "{bozuk_json}"],
    ["liste_tara.py", "--girdi", "{bozuk_json}"],
    ["liste_tara.py", "--girdi", "{liste_json}"],
    ["yazar_hafizasi.py", "kaydet", "--calisma-alani", "{klasor}", "--girdi", "{bozuk_json}"],
    ["cozumleme_calismasi.py", "kaydet", "--kok", "{klasor}", "--girdi", "{bozuk_json}"],
    ["plan_gorunumu.py", "--icindekiler", "{ikili}"],
    ["iliski_semasi.py", "--dosya", "{ikili}", "--cikti", "-"],
    ["metin_olcum.py", "--hedef", "-5", "{ikili}"],
    ["wattpad_planla.py", "takvim", "--proje", "{klasor}", "--baslangic", "2026-13-40"],
])
def test_bozuk_girdide_turkce_hata(komut: list[str], bozuk: dict[str, Path]) -> None:
    arg = [a.format(**{k: str(v) for k, v in bozuk.items()}) for a in komut[1:]]
    sonuc = calistir(komut[0], *arg)
    if komut[0] == "liste_tara.py" and "liste" in komut[-1]:
        # Geçerli JSON ama öyküler nesne değil: çökmeden boş rapor verir.
        assert sonuc.returncode == 0 and "Traceback" not in sonuc.stderr, sonuc.stderr
        return
    _turkce_hata(sonuc)


def test_metin_oku_kodlamalar(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    do = modul_yukle("dosya_oku.py")
    bom = tmp_path / "bom.md"
    bom.write_bytes("\ufeffŞimdi".encode("utf-8"))
    assert do.metin_oku(bom) == "Şimdi"
    eski = tmp_path / "ansi.txt"
    eski.write_bytes("Güzel bir gün, ışık ve şiir.".encode("cp1254"))
    assert do.metin_oku(eski) == "Güzel bir gün, ışık ve şiir."
    assert "Windows-1254" in capsys.readouterr().err
    ikili = tmp_path / "belge.docx"
    ikili.write_bytes(b"PK\x03\x04\x00\x00" + bytes(100))
    with pytest.raises(do.DosyaHatasi, match="ikili"):
        do.metin_oku(ikili)
    with pytest.raises(do.DosyaHatasi, match="klasör"):
        do.metin_oku(tmp_path)
    with pytest.raises(do.DosyaHatasi, match="bulunamadı"):
        do.metin_oku(tmp_path / "yok.md")


def test_json_nesne_oku(tmp_path: Path) -> None:
    do = modul_yukle("dosya_oku.py")
    assert do.json_nesne_oku(tmp_path / "yok.json", bos={}) == {}
    liste = tmp_path / "l.json"
    liste.write_text("[]", encoding="utf-8")
    with pytest.raises(do.DosyaHatasi, match="nesne"):
        do.json_nesne_oku(liste)
    bozuk = tmp_path / "b.json"
    bozuk.write_text('{"a": 1,}', encoding="utf-8")
    with pytest.raises(do.DosyaHatasi, match="satır 1"):
        do.json_nesne_oku(bozuk)
    iyi = tmp_path / "i.json"
    iyi.write_text(json.dumps({"ş": "ğ"}), encoding="utf-8")
    assert do.json_nesne_oku(iyi) == {"ş": "ğ"}


def test_hata_iletisi_turkce() -> None:
    ta = modul_yukle("turkce_argparse.py")
    try:
        json.loads("{")
    except json.JSONDecodeError as hata:
        assert ta.hata_iletisi(hata).startswith("geçersiz JSON (satır 1")
    assert "bulunamadı" in ta.hata_iletisi(FileNotFoundError(2, "x", "a.md"))
    assert ta.hata_iletisi(ValueError("en az bir gün verin")) == "en az bir gün verin"
    assert "tarih" in ta.hata_iletisi(ValueError("time data '2026-13-40' does not match format"))
    assert "beklenmeyen" in ta.hata_iletisi(KeyError("x"))


def _yardim(yol: Path, *alt: str) -> str:
    return calistir(yol, *alt, "--help").stdout


def test_butun_secenekler_turkce_yardimli() -> None:
    """Her betiğin her seçeneği (alt komutlar dahil) --help çıktısında bir açıklama taşımalı."""
    from conftest import BECERILER, KOK, PAYLASILAN
    adaylar = {p.name: p for p in [*PAYLASILAN.glob("*.py"), *BECERILER.glob("*/betikler/*.py"), *(KOK / "betikler").glob("*.py")]}
    eksik: list[str] = []
    for ad, yol in sorted(adaylar.items()):
        if ad in {"turkce_argparse.py", "turkce_kaliplar.py", "dosya_oku.py"}:
            continue
        metinler = [("", _yardim(yol))]
        i = 0
        while i < len(metinler):
            yolu, metin = metinler[i]
            alt = re.findall(r"^  \{([^}]+)\}", metin, re.M)
            if alt and len(yolu.split()) < 2 and not (yolu and yolu.split()[-1] in alt[0].split(",")):
                for a in alt[0].split(","):
                    metinler.append((f"{yolu} {a}".strip(), _yardim(yol, *f"{yolu} {a}".split())))
            i += 1
        for yolu, metin in metinler:
            assert "usage:" not in metin and "options:" not in metin, f"{ad} {yolu}: İngilizce argparse başlığı"
            satirlar = metin.split("\n")
            for j, satir in enumerate(satirlar):
                if re.match(r"^  --[-\w]+(?: [A-Z_]+(?: \[[A-Z_ .]+\])?)?\s*$", satir):
                    sonraki = satirlar[j + 1] if j + 1 < len(satirlar) else ""
                    if not sonraki.startswith("    "):
                        eksik.append(f"{ad} {yolu} {satir.strip()}")
    assert not eksik, "Yardım metni eksik seçenekler:\n" + "\n".join(eksik)
