"""Takip durumu, hikayectl kapıları, plan denetimi, yazar istemi, süreklilik ve yazar hafızası."""

from __future__ import annotations

import filecmp
import json
import shutil
from pathlib import Path

from conftest import ORNEK_ISLEMLER, ORNEK_ROMAN, calistir, json_cikti


def _bos_takipli(roman: Path) -> Path:
    shutil.rmtree(roman / "takip")
    sonuc = calistir("takip_kaydet.py", "baslat", "--proje", roman, "--girdi", ORNEK_ISLEMLER / "baslangic.json")
    assert json_cikti(sonuc)["tamam"], sonuc.stdout
    return roman


def _klasorler_ayni(a: Path, b: Path) -> bool:
    karsi = filecmp.dircmp(a, b)
    if karsi.left_only or karsi.right_only or karsi.diff_files or karsi.funny_files:
        return False
    return all(_klasorler_ayni(a / alt, b / alt) for alt in karsi.common_dirs)


def test_bolum_kaydi_ornek_takibi_birebir_uretir(roman: Path) -> None:
    _bos_takipli(roman)
    for no in (1, 2):
        sonuc = calistir("hikayectl.py", "bolum", "kaydet", "--proje", roman, "--bolum", no,
                         "--girdi", ORNEK_ISLEMLER / f"islem-00{no}.json")
        veri = json_cikti(sonuc)
        assert veri["tamam"] and veri["son_kaydedilen_bolum"] == no, sonuc.stdout
    assert _klasorler_ayni(roman / "takip", ORNEK_ROMAN / "takip")
    assert not (roman / ".hikaye" / "calisma" / "bolum-002").exists()


def test_eski_revizyonlu_islem_reddedilir(roman: Path) -> None:
    _bos_takipli(roman)
    islem = ORNEK_ISLEMLER / "islem-001.json"
    assert json_cikti(calistir("takip_kaydet.py", "uygula", "--proje", roman, "--girdi", islem))["tamam"]
    ikinci = json_cikti(calistir("takip_kaydet.py", "uygula", "--proje", roman, "--girdi", islem))
    assert ikinci["tamam"] is False and "değişmiş" in ikinci["hata"]


def test_gecersiz_islem_durumu_bozmaz(roman: Path, tmp_path: Path) -> None:
    once = (roman / "takip" / "_takip-durumu.json").read_bytes()
    bozuk = tmp_path / "bozuk.json"
    bozuk.write_text(json.dumps({"sema_surumu": 1, "kip": "ekle", "bolum": 3}), encoding="utf-8")
    sonuc = calistir("takip_kaydet.py", "uygula", "--proje", roman, "--girdi", bozuk)
    assert json_cikti(sonuc)["tamam"] is False
    assert (roman / "takip" / "_takip-durumu.json").read_bytes() == once


def test_takip_denetle_elle_bozulan_gorunumu_yakalar(roman: Path) -> None:
    assert json_cikti(calistir("takip_kaydet.py", "denetle", "--proje", roman))["tamam"]
    ipucu = roman / "takip" / "ipuclari.md"
    ipucu.write_text(ipucu.read_text(encoding="utf-8") + "\nelle eklenen satır\n", encoding="utf-8")
    sonuc = json_cikti(calistir("takip_kaydet.py", "denetle", "--proje", roman))
    assert sonuc["tamam"] is False and sonuc["sorunlar"]


def test_takip_goster(roman: Path) -> None:
    veri = json_cikti(calistir("takip_kaydet.py", "goster", "--proje", roman))
    assert veri["kitap_adi"] == "Saatçinin Kızı" and veri["son_kaydedilen_bolum"] == 2


def test_bolum_denetle_metin_yoksa_kalir(roman: Path) -> None:
    sonuc = calistir("hikayectl.py", "bolum", "denetle", "--proje", roman, "--bolum", 3)
    veri = json_cikti(sonuc)
    assert sonuc.returncode == 1 and veri["tamam"] is False
    kapilar = {k["kapi"]: k["tamam"] for k in veri["kapilar"]}
    assert kapilar["plan-sozlesmesi"] is True and kapilar["metin-dosyasi"] is False


def test_uzunluk_olc_ve_kontrol(roman: Path) -> None:
    dosya = next((roman / "metin").glob("bolum-001_*.md"))
    olc = json_cikti(calistir("hikayectl.py", "uzunluk", "olc", "--dosya", dosya))
    assert olc["olcu"] == "gorunur_kelime_v1" and olc["kelime"] > 300
    kontrol = calistir("hikayectl.py", "uzunluk", "kontrol", "--dosya", dosya, "--hedef", 340)
    assert kontrol.returncode == 0, kontrol.stdout
    uzak = calistir("hikayectl.py", "uzunluk", "kontrol", "--dosya", dosya, "--hedef", 3000)
    assert uzak.returncode != 0


def test_plan_sozlesmesi_ve_kopya(roman: Path, tmp_path: Path) -> None:
    assert calistir("plan_denetle.py", "sozlesme", "--proje", roman, "--bolum", 3).returncode == 0
    eksik = tmp_path / "bolum-plani_009.md"
    eksik.write_text("# Bölüm 9\n\nHedef uzunluk: 2000 kelime\n", encoding="utf-8")
    assert calistir("plan_denetle.py", "sozlesme", eksik).returncode == 1
    plan = roman / "plan" / "bolum-plani_001.md"
    metin = next((roman / "metin").glob("bolum-001_*.md"))
    assert calistir("plan_denetle.py", "kopya", "--plan", plan, "--metin", metin).returncode == 0
    kopya = tmp_path / "kopya.md"
    kopya.write_text(plan.read_text(encoding="utf-8"), encoding="utf-8")
    assert calistir("plan_denetle.py", "kopya", "--plan", plan, "--metin", kopya).returncode == 1


def test_yazar_istemi_calisma_klasorune_yazilir(roman: Path) -> None:
    sonuc = calistir("yazar_istemi_olustur.py", "--proje", roman, "--bolum", 3, "--cikti")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    istem = roman / ".hikaye" / "calisma" / "bolum-003" / "yazar-istemi.md"
    assert istem.is_file()
    icerik = istem.read_text(encoding="utf-8")
    assert "Saatçinin Kızı" in icerik or "Defne" in icerik


def test_sureklilik_denetimi_ornekte_temiz_ve_olu_karakteri_yakalar(roman: Path) -> None:
    sonuc = calistir("sureklilik_denetle.py", "--proje", roman, "--bolum", 2, "--json")
    veri = json_cikti(sonuc)
    engelleyici = [b for b in veri.get("bulgular", []) if b.get("onem") == "engelleyici" or b.get("duzey") == "hata"]
    assert not engelleyici, sonuc.stdout
    durum_yolu = roman / "takip" / "_takip-durumu.json"
    durum = json.loads(durum_yolu.read_text(encoding="utf-8"))
    durum["karakterler"]["Defne Aras"]["yasam_durumu"] = "öldü"
    durum_yolu.write_text(json.dumps(durum, ensure_ascii=False, indent=2), encoding="utf-8")
    sonuc = calistir("sureklilik_denetle.py", "--proje", roman, "--bolum", 2, "--json")
    assert "olu-karakter" in sonuc.stdout, sonuc.stdout


def test_plan_gorunumu_icindekiler(roman: Path) -> None:
    cilt = roman / "plan" / "cilt-plani_1.md"
    sonuc = calistir("plan_gorunumu.py", cilt, "--icindekiler")
    assert sonuc.returncode == 0 and sonuc.stdout.strip()
    assert calistir("plan_gorunumu.py", cilt, "--denetle").returncode in (0, 1)


def test_yazar_hafizasi_dongusu(tmp_path: Path) -> None:
    alan = tmp_path / "alan"
    alan.mkdir()
    assert json_cikti(calistir("yazar_hafizasi.py", "baslat", "--calisma-alani", alan))["tamam"]
    islem = tmp_path / "h.json"
    islem.write_text(json.dumps({"sema_surumu": 1, "islem_kimligi": "2026-09-25-01", "islemler": [
        {"eylem": "hatirla", "iddia": "Diyaloglarda argo kullanma", "tur": "anlatim_uslubu",
         "kapsam": {"duzey": "genel"}, "kaynak": "yazar_acikca", "kanit": "Argo istemiyorum, dedi.", "onem": "yuksek"}]},
        ensure_ascii=False), encoding="utf-8")
    kayit = json_cikti(calistir("yazar_hafizasi.py", "kaydet", "--calisma-alani", alan, "--girdi", islem))
    assert kayit["tamam"], kayit
    sorgu = calistir("yazar_hafizasi.py", "sorgula", "--calisma-alani", alan, "--tur", "anlatim_uslubu")
    assert "argo" in sorgu.stdout.lower()
    assert json_cikti(calistir("yazar_hafizasi.py", "denetle", "--calisma-alani", alan))["tamam"]
    kanitsiz = tmp_path / "k.json"
    kanitsiz.write_text(json.dumps({"sema_surumu": 1, "islem_kimligi": "2026-09-25-02", "islemler": [
        {"eylem": "hatirla", "iddia": "Model tahmini", "tur": "anlatim_uslubu", "kapsam": {"duzey": "genel"},
         "kaynak": "model_cikarimi", "kanit": "yok"}]}), encoding="utf-8")
    assert calistir("yazar_hafizasi.py", "kaydet", "--calisma-alani", alan, "--girdi", kanitsiz).returncode != 0
