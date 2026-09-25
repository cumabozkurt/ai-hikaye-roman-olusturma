"""Öykü kapıları, Wattpad planlayıcı, yayınevi dosyası, sesli kitap ve kapak betikleri."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from conftest import calistir, json_cikti


def test_oyku_tasarim_ve_teslim_gecer(oyku: Path) -> None:
    assert calistir("oyku_denetle.py", "tasarim", oyku).returncode == 0
    sonuc = calistir("oyku_denetle.py", "teslim", oyku, "--json")
    assert sonuc.returncode == 0, sonuc.stdout


def test_oyku_teslim_sahne_sayisi_uyusmazsa_kalir(oyku: Path) -> None:
    metin = oyku / "metin.md"
    metin.write_text(metin.read_text(encoding="utf-8").replace("* * *", ""), encoding="utf-8")
    sonuc = calistir("oyku_denetle.py", "teslim", oyku, "--json")
    assert sonuc.returncode == 1 and "sahne" in sonuc.stdout.lower()


def test_oyku_eksik_klasor_hatali_girdi(tmp_path: Path) -> None:
    assert calistir("oyku_denetle.py", "tasarim", tmp_path / "yok").returncode == 2


def test_wattpad_denetle_ve_takvim(roman: Path, tmp_path: Path) -> None:
    denetim = json_cikti(calistir("wattpad_planla.py", "denetle", "--proje", roman, "--json", "--alt", 200, "--ust", 600))
    assert denetim
    takvim_md = tmp_path / "takvim.md"
    sonuc = calistir("wattpad_planla.py", "takvim", "--proje", roman, "--baslangic", "2026-10-02", "--gunler", "cuma,salı",
                     "--saat", "20:00", "--cikti", takvim_md)
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    icerik = takvim_md.read_text(encoding="utf-8")
    assert "Ekim" in icerik and ("Cuma" in icerik or "cuma" in icerik)
    assert "tampon" in (icerik + sonuc.stdout).lower()


def test_wattpad_bol_sahne_ayraclarindan(tmp_path: Path) -> None:
    paragraf = " ".join(["kelime"] * 120)
    sahneler = ["\n\n".join([paragraf] * 5) for _ in range(4)]
    dosya = tmp_path / "bolum-004_uzun.md"
    dosya.write_text("# Bölüm 4\n\n" + "\n\n* * *\n\n".join(sahneler) + "\n", encoding="utf-8")
    oneri = json_cikti(calistir("wattpad_planla.py", "bol", "--dosya", dosya, "--hedef", 1200, "--json"))
    assert oneri
    klasor = tmp_path / "parcalar"
    assert calistir("wattpad_planla.py", "bol", "--dosya", dosya, "--hedef", 1200, "--cikti", klasor).returncode == 0
    parcalar = sorted(klasor.glob("*.md"))
    assert len(parcalar) >= 2
    for p in parcalar:
        icerik = p.read_text(encoding="utf-8").strip()
        assert not icerik.startswith("* * *") and not icerik.endswith("* * *")
    assert dosya.read_text(encoding="utf-8").count("* * *") == 3, "kaynak metin değişmemeli"


def test_wattpad_gecersiz_gun(roman: Path) -> None:
    sonuc = calistir("wattpad_planla.py", "takvim", "--proje", roman, "--baslangic", "2026-10-02", "--gunler", "funday")
    assert sonuc.returncode != 0 and "Traceback" not in sonuc.stderr


def test_yayinevi_dosya_paketi(roman: Path, tmp_path: Path) -> None:
    cikti = tmp_path / "yayinevi"
    sonuc = calistir("dosya_paketi.py", "--proje", roman, "--yazar", "Deniz Ak", "--kelime-siniri", 400, "--tam", "--cikti", cikti)
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    paket = next(cikti.iterdir())
    for ad in ("kunye.md", "ornek-bolumler.md", "tam-metin.md", "sinopsis.md", "ust-yazi.md", "yazar-biyografisi.md", "denetim.json"):
        assert (paket / ad).is_file(), ad
    kunye = (paket / "kunye.md").read_text(encoding="utf-8")
    assert "Saatçinin Kızı" in kunye and "Deniz Ak" in kunye
    json.loads((paket / "denetim.json").read_text(encoding="utf-8"))
    ornek = (paket / "ornek-bolumler.md").read_text(encoding="utf-8")
    assert "Bölüm" in ornek or "#" in ornek
    (paket / "sinopsis.md").write_text("yazarın sinopsisi\n", encoding="utf-8")
    calistir("dosya_paketi.py", "--proje", roman, "--yazar", "Deniz Ak", "--cikti", cikti)
    assert (paket / "sinopsis.md").read_text(encoding="utf-8") == "yazarın sinopsisi\n", "var olan dosyanın üzerine yazılmamalı"


def test_sesli_kitap_hazirla(roman: Path, tmp_path: Path) -> None:
    cikti = tmp_path / "sesli"
    sonuc = calistir("sesli_kitap_hazirla.py", "--proje", roman, "--cikti", cikti, "--json")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    txt = sorted((cikti / "seslendirme").glob("*.txt"))
    assert len(txt) == 2
    icerik = txt[0].read_text(encoding="utf-8")
    assert "#" not in icerik and "**" not in icerik
    sure = (cikti / "sure.md").read_text(encoding="utf-8")
    assert "dakika" in sure.lower()
    telaffuz = (cikti / "telaffuz.md").read_text(encoding="utf-8")
    assert "Defne" in telaffuz or "Kuzguncuk" in telaffuz
    (cikti / "sure.md").write_text("elle\n", encoding="utf-8")
    calistir("sesli_kitap_hazirla.py", "--proje", roman, "--cikti", cikti)
    assert (cikti / "sure.md").read_text(encoding="utf-8") == "elle\n"
    calistir("sesli_kitap_hazirla.py", "--proje", roman, "--cikti", cikti, "--yeniden")
    assert (cikti / "sure.md").read_text(encoding="utf-8") != "elle\n"


def test_sesli_kitap_tek_dosya(oyku: Path, tmp_path: Path) -> None:
    sonuc = calistir("sesli_kitap_hazirla.py", "--dosya", oyku / "metin.md", "--cikti", tmp_path / "s")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    metin = next((tmp_path / "s" / "seslendirme").glob("*.txt")).read_text(encoding="utf-8")
    assert "[DURAKSAMA]" in metin


def test_kapak_istemi_ve_kuru_uretim(tmp_path: Path) -> None:
    istem = calistir("kapak_olustur.py", "istem", "--baslik", "Saatçinin Kızı", "--yazar", "Deniz Ak", "--tur", "polisiye",
                     "--platform", "wattpad")
    assert istem.returncode == 0 and "Saatçinin Kızı" in istem.stdout
    gizli = "sk-test-GIZLI-ANAHTAR-123456"
    kuru = calistir("kapak_olustur.py", "uret", "--baslik", "Saatçinin Kızı", "--yazar", "Deniz Ak", "--tur", "polisiye",
                    "--platform", "wattpad", "--cikti", tmp_path / "kapak", "--kuru", ortam={"GPT_IMAGE_API_KEY": gizli})
    assert kuru.returncode == 0, kuru.stdout + kuru.stderr
    assert gizli not in kuru.stdout + kuru.stderr
    assert not any(tmp_path.glob("kapak*.png"))


def test_kapak_anahtarsiz_uretim_anlasilir_hata(tmp_path: Path) -> None:
    sonuc = calistir("kapak_olustur.py", "uret", "--baslik", "X", "--yazar", "Y", "--tur", "polisiye", "--platform", "wattpad",
                     "--cikti", tmp_path / "k", ortam={"GPT_IMAGE_API_KEY": ""})
    assert sonuc.returncode != 0 and "GPT_IMAGE_API_KEY" in sonuc.stdout + sonuc.stderr
    assert "Traceback" not in sonuc.stderr


@pytest.mark.skipif(importlib.util.find_spec("PIL") is None, reason="Pillow kurulu değil")
def test_kapak_kirp(tmp_path: Path) -> None:
    from PIL import Image

    girdi = tmp_path / "kaynak.png"
    Image.new("RGB", (1024, 1536), "navy").save(girdi)
    cikti = tmp_path / "wattpad.png"
    assert calistir("kapak_olustur.py", "kirp", "--girdi", girdi, "--platform", "wattpad", "--cikti", cikti).returncode == 0
    with Image.open(cikti) as im:
        assert im.size[0] < im.size[1]
