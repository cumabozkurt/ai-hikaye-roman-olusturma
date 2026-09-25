"""Metin ölçümü, yapay zekâ kalıbı, bozulma, TDK yazım ve noktalama denetçileri."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import ORNEK_OYKU, ORNEK_ROMAN, calistir, json_cikti, modul_yukle


def test_kelime_sayimi_turkce_ekleri_tek_sayar() -> None:
    mo = modul_yukle("metin_olcum.py")
    metin = "---\nbaslik: x\n---\n# Başlık\n\nAli'nin yarı-resmî mektubu geldi. <!-- not -->"
    assert mo.kelime_say(metin) == 4


def test_hedef_uzunluk_turkce_sayi_bicimleri() -> None:
    mo = modul_yukle("metin_olcum.py")
    assert mo.hedef_coz("- **Hedef uzunluk:** 2.200 kelime (±%15)") == 2200
    assert mo.hedef_coz("Hedef uzunluk: 3 000 kelime") == 3000
    with pytest.raises(mo.OlcumHatasi):
        mo.hedef_coz("Hedef yok")


def test_ai_kalip_denetcisi_kliseyi_bulur(tmp_path: Path) -> None:
    dosya = tmp_path / "b.md"
    dosya.write_text("Bu sadece bir oyun değildi, bir savaştı.\n\nBir yandan korkuyor, diğer yandan merak ediyordu.\n",
                     encoding="utf-8")
    sonuc = calistir("ai_kalip_denetle.py", dosya, "--json")
    assert sonuc.returncode == 1
    assert json_cikti(sonuc)
    assert "degil-ama-donusu" in sonuc.stdout and "bir-yandan-diger-yandan" in sonuc.stdout


def test_ai_kalip_beyaz_liste(tmp_path: Path) -> None:
    mod = modul_yukle("ai_kalip_denetle.py")
    metin = "Bu sadece bir oyun değildi, bir savaştı. Sonra kapıyı açtı.\n"
    once = mod.denetle_metin(metin)
    assert once, "klişe bulunmalı"
    (tmp_path / ".yz-beyaz-liste").write_text("Bu sadece bir oyun değildi, bir savaştı\n", encoding="utf-8")
    dosya = tmp_path / "m.md"
    dosya.write_text(metin, encoding="utf-8")
    assert len(mod.denetle_dosya(dosya)) < len(once)


def test_ornek_metinler_temiz() -> None:
    for dosya in [*sorted((ORNEK_ROMAN / "metin").glob("*.md")), ORNEK_OYKU / "metin.md"]:
        assert calistir("bozulma_denetle.py", dosya).returncode == 0, dosya
        assert calistir("ai_kalip_denetle.py", dosya).returncode == 0, dosya
        assert calistir("yazim_denetle.py", dosya).returncode == 0, dosya


def test_bozulma_yarim_metin_ve_tekrar(tmp_path: Path) -> None:
    dosya = tmp_path / "b.md"
    satir = "Kapı açıldı ve içeri soğuk bir rüzgâr doldu, perdeler havalandı."
    dosya.write_text("\n\n".join([satir] * 6) + "\n\nBir yapay zekâ olarak ben de ve", encoding="utf-8")
    sonuc = calistir("bozulma_denetle.py", dosya, "--json")
    assert sonuc.returncode == 1, sonuc.stdout


def test_yazim_denetle_tdk_hatalari(tmp_path: Path) -> None:
    dosya = tmp_path / "y.md"
    dosya.write_text("Herkez geldi. Birşey söylemedi. İstanbulda yaşıyor. Dediki gelecek.\n", encoding="utf-8")  # turkce-uyum: yoksay
    sonuc = calistir("yazim_denetle.py", dosya, "--json")
    assert sonuc.returncode == 1
    for beklenen in ("herkes", "bir şey", "İstanbul'da"):
        assert beklenen in sonuc.stdout


def test_yazim_denetle_diyalogda_gayriresmi_serbest(tmp_path: Path) -> None:
    dosya = tmp_path / "d.md"
    dosya.write_text("— Napıyon be abi, dedi.\n", encoding="utf-8")
    sonuc = calistir("yazim_denetle.py", dosya)
    assert sonuc.returncode == 0, sonuc.stdout


def test_noktalama_duzelt(tmp_path: Path) -> None:
    dosya = tmp_path / "n.md"
    dosya.write_text("- Geldin mi ?  dedi.Sonra...... sustu\n", encoding="utf-8")
    assert calistir("noktalama_duzelt.py", dosya, "--yaz").returncode == 0
    metin = dosya.read_text(encoding="utf-8")
    assert metin.startswith("— Geldin mi?")
    assert "......" not in metin and "..." in metin
    assert "dedi. Sonra" in metin


def test_turkce_kucuk_harf_donusumu() -> None:
    tk = modul_yukle("turkce_kaliplar.py")
    fonk = getattr(tk, "tr_kucuk", None) or getattr(tk, "kucuk_harf", None)
    assert fonk is not None
    assert fonk("IŞIK İzmir") == "ışık izmir"
