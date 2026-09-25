"""Roman çözümleme betikleri, Wattpad liste taraması (çevrim dışı), çalışma masası ve CDP araçları."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from conftest import ORNEK_ROMAN, calistir, json_cikti, modul_yukle

PARAGRAF = "Kapı gıcırdadı ve rüzgâr içeri doldu. Eski saat duvarda tıkırdadı, sonra sustu. "


def _roman_metni() -> str:
    parcalar = ["İÇİNDEKİLER", "", "Bölüm 1", "Bölüm İki: Kapı", "3. Bölüm", "", "Önsöz", "", PARAGRAF * 3]
    basliklar = ["BÖLÜM 1", "Bölüm İki: Kapı", "3. Bölüm", "BÖLÜM 4", "Bölüm Beş", "BÖLÜM 6"]
    for i, baslik in enumerate(basliklar, start=1):
        parcalar += ["", baslik, "", (PARAGRAF + f"Bu {i}. bölümün cümlesi. ") * (10 + i)]
    parcalar += ["", "Epilog", "", PARAGRAF * 2]
    return "\n".join(parcalar) + "\n"


def _kutuphane(tmp_path: Path) -> Path:
    kok = tmp_path / "cozumleme-kutuphanesi" / "ornek-roman"
    (kok / "kaynak").mkdir(parents=True)
    (kok / "kaynak" / "metin.txt").write_text(_roman_metni(), encoding="utf-8")
    return kok


def test_bolum_dizini_turkce_basliklar_ve_icindekiler(tmp_path: Path) -> None:
    kok = _kutuphane(tmp_path)
    csv_yolu = kok / "bolum-dizini.csv"
    sonuc = calistir("bolum_dizini.py", "--kaynak", kok / "kaynak" / "metin.txt", "--cikti", csv_yolu)
    assert sonuc.returncode == 0, sonuc.stdout
    satirlar = list(csv.DictReader(csv_yolu.open(encoding="utf-8")))
    basliklar = [s["baslik"] for s in satirlar]
    turler = [s["tur"] for s in satirlar]
    assert sum(1 for t in turler if t == "bolum") == 6, "içindekiler bloğu atılmalı"
    assert basliklar.count("Kapı") == 1, "sayı sözcüklü başlık (Bölüm İki: Kapı) tanınmalı"
    assert [s["bolum"] for s in satirlar if s["tur"] == "bolum"] == [str(n) for n in range(1, 7)]
    assert any("Önsöz" in b for b in basliklar) and any("Epilog" in b for b in basliklar)
    ilk = csv_yolu.read_bytes()
    calistir("bolum_dizini.py", "--kaynak", kok / "kaynak" / "metin.txt", "--cikti", csv_yolu)
    assert csv_yolu.read_bytes() == ilk, "dizin belirlenimci olmalı"


def _grup(ilk: int, son: int) -> dict:
    return {"grup": {"ilk": ilk, "son": son}, "bolumler": [{
        "bolum": n, "ozet": f"{n}. bölümde kapı açılır.", "sahneler": [], "karakter_degisimleri": [],
        "ipuclari": [{"ipucu": "saat", "islem": "ekildi"}], "olaylar": [{"yazar_gercegi": "x", "okur_bilgisi": "gizli"}],
        "duygu": {"gerilim": 5, "baskin_duygu": "merak"}, "kanca": {"acilis": "kapı", "kapanis": "saat"},
        "olay_noktalari": [f"nokta {i}" for i in range(10)], "uslup_ornegi": ["Kısa bir cümle."]} for n in range(ilk, son + 1)]}


def test_cozumleme_calismasi_plan_kaydet_durum(tmp_path: Path) -> None:
    kok = _kutuphane(tmp_path)
    calistir("bolum_dizini.py", "--kaynak", kok / "kaynak" / "metin.txt", "--cikti", kok / "bolum-dizini.csv")
    plan = json_cikti(calistir("cozumleme_calismasi.py", "plan", "--kok", kok))
    assert plan["gruplar"], plan
    grup = plan["gruplar"][0]
    girdi = tmp_path / "grup.json"
    girdi.write_text(json.dumps(_grup(grup["ilk"], grup["son"]), ensure_ascii=False), encoding="utf-8")
    kayit = json_cikti(calistir("cozumleme_calismasi.py", "kaydet", "--kok", kok, "--girdi", girdi, "--aralik-ozeti", grup["aralik_ozeti"]))
    assert kayit["tamam"] and kayit["yazilan"], kayit
    tekrar = json_cikti(calistir("cozumleme_calismasi.py", "kaydet", "--kok", kok, "--girdi", girdi))
    assert tekrar["atlanan"] and not tekrar["yazilan"], "var olan özetin üzerine yazılmamalı"
    yanlis = json_cikti(calistir("cozumleme_calismasi.py", "kaydet", "--kok", kok, "--girdi", girdi, "--aralik-ozeti", "0" * 64))
    assert yanlis["tamam"] is False
    durum = calistir("cozumleme_calismasi.py", "durum", "--kok", kok)
    assert durum.returncode in (0, 1) and json_cikti(durum)
    inceleme = calistir("mevcut_varliklari_incele.py", "--kok", kok)
    assert json_cikti(inceleme)["karar"] == "devam_et"
    assert calistir("mevcut_varliklari_incele.py", "--kok", tmp_path / "yok").returncode == 2


def test_grup_semasi_uzun_alintiyi_reddeder() -> None:
    bd = modul_yukle("bolum_dizini.py")
    veri = _grup(4, 4)
    assert bd.grup_dogrula(veri) == []
    veri["bolumler"][0]["uslup_ornegi"] = [" ".join(["sözcük"] * 40)]
    veri["bolumler"][0]["olay_noktalari"] = ["tek"]
    sorunlar = bd.grup_dogrula(veri)
    assert any("telif" in s for s in sorunlar) and any("olay_noktalari" in s for s in sorunlar)
    assert bd.grup_dogrula(_grup(1, 5))


def test_iliski_semasi_mermaid(tmp_path: Path) -> None:
    sonuc = calistir("iliski_semasi.py", "--dosya", ORNEK_ROMAN / "kurgu" / "iliskiler.md", "--cikti", "-")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    assert "```mermaid" in sonuc.stdout and "Defne" in sonuc.stdout


def test_ilham_dizini_olustur_sorgula(tmp_path: Path) -> None:
    kutuphane = tmp_path / "kutuphane"
    dosya = kutuphane / "ornek" / "olay-orgusu" / "duygu-mekanizmalari.md"
    dosya.parent.mkdir(parents=True)
    dosya.write_text("# Duygu mekanizmaları\n\n## DM-001: Geç gelen itiraf\n\nEtiketler: aile, sır\n"
                     "Mekanizma: Okurun bildiği sırrı karakter en kötü anda öğrenir.\n\n"
                     "## DM-002: Ters köşe miras\n\nEtiketler: intikam\nMekanizma: Miras bir borç çıkar.\n", encoding="utf-8")
    assert calistir("ilham_dizini.py", "olustur", "--kutuphane", kutuphane).returncode == 0
    assert (kutuphane / "_ilham-dizini.json").is_file()
    sorgu = calistir("ilham_dizini.py", "sorgula", "--kutuphane", kutuphane, "--etiket", "aile")
    assert "Geç gelen itiraf" in sorgu.stdout and "Ters köşe" not in sorgu.stdout
    assert calistir("ilham_dizini.py", "kapsam", "--kutuphane", kutuphane).returncode == 0


def test_liste_tara_cevrim_disi(tmp_path: Path) -> None:
    kayit = {"stories": [
        {"title": "Saatçinin Kızı", "tags": ["polisiye", "gizem", "istanbul"], "readCount": 12000, "voteCount": 900,
         "numParts": 30, "completed": True, "mature": False, "url": "https://www.wattpad.com/story/1", "user": {"name": "a"},
         "description": "Kuzguncuk'ta bir saatçi dükkânı ve çözülmemiş bir cinayet."},
        {"title": "Kayıp Mektup", "tags": ["gizem", "aşk"], "readCount": 3000, "voteCount": 200, "numParts": 12,
         "completed": False, "url": "https://www.wattpad.com/story/2", "user": {"name": "b"},
         "description": "Eski bir konakta bulunan mektup her şeyi değiştirir."},
        {"title": "The Lost Letter", "tags": ["mystery"], "readCount": 99999, "voteCount": 10, "numParts": 5,
         "completed": True, "url": "https://www.wattpad.com/story/3", "user": {"name": "c"},
         "description": "An old letter changes everything."},
    ]}
    girdi = tmp_path / "kayit.json"
    girdi.write_text(json.dumps(kayit, ensure_ascii=False), encoding="utf-8")
    veri = json_cikti(calistir("liste_tara.py", "--girdi", girdi, "--json"))
    metin = json.dumps(veri, ensure_ascii=False)
    assert "Saatçinin Kızı" in metin and "The Lost Letter" not in metin
    rapor = tmp_path / "rapor.md"
    assert calistir("liste_tara.py", "--girdi", girdi, "--cikti", rapor).returncode == 0
    icerik = rapor.read_text(encoding="utf-8")
    assert "gizem" in icerik and "Saatçinin Kızı" in icerik
    hepsi = json_cikti(calistir("liste_tara.py", "--girdi", girdi, "--json", "--tum-diller"))
    assert "The Lost Letter" in json.dumps(hepsi, ensure_ascii=False)


def test_calisma_masasi_json(roman: Path) -> None:
    alan = roman.parent
    veri = json_cikti(calistir("calisma_masasi.py", "--calisma-alani", alan, "--json"))
    metin = json.dumps(veri, ensure_ascii=False)
    assert "Saatçinin Kızı" in metin or "saatcinin-kizi" in metin


def test_cdp_baslatici_kuru_calisir(tmp_path: Path) -> None:
    sonuc = calistir("cdp_chrome_baslat.py", "--kuru", "--profil", tmp_path / "profil", "--tarayici", sys.executable)
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr
    assert "--remote-debugging-port=9222" in sonuc.stdout and "127.0.0.1" in sonuc.stdout
    komut = " ".join(json_cikti(sonuc)["komut"])  # JSON çözülür: Windows yolundaki ters eğik çizgiler kaçışlıdır
    assert str(tmp_path / "profil") in komut


def test_cdp_istemci_tarayici_yokken_anlasilir_hata() -> None:
    sonuc = calistir("cdp_istemci.py", "--port", "9", "sekmeler")
    assert sonuc.returncode != 0
    assert "Traceback" not in sonuc.stderr
    assert "tarayıcı" in (sonuc.stdout + sonuc.stderr).lower() or "cdp" in (sonuc.stdout + sonuc.stderr).lower()
