"""2.0.0 uçtan uca senaryo: bir yazarın kurulumdan e-kitaba kadar bütün iş akışı, yalnızca komut satırı araçlarıyla.

Her adım, bir yapay zekâ ajanının becerilerde yazan komutları çalıştırdığı sırayla yürütülür; bir adımın çıktısı
sonrakinin girdisidir. Amaç tek tek araçları değil, aralarındaki sözleşmeleri (dosya biçimleri, çıkış kodları,
takip kaydı) denemektir.
"""

from __future__ import annotations

import datetime as dt
import http.client
import json
import shutil
import threading
import zipfile
from pathlib import Path

from conftest import BECERILER, ORNEK_ISLEMLER, ORNEK_ROMAN, calistir, json_cikti, modul_yukle

KUR = BECERILER / "hikaye-kurulum" / "betikler" / "kur.py"


def yaz(yol: Path, metin: str) -> Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")
    return yol


def tamam(sonuc, *kodlar: int) -> str:  # noqa: ANN001
    kodlar = kodlar or (0,)
    assert sonuc.returncode in kodlar, f"çıkış {sonuc.returncode}\nSTDOUT:\n{sonuc.stdout}\nSTDERR:\n{sonuc.stderr}"
    assert "Traceback" not in sonuc.stderr, sonuc.stderr
    return sonuc.stdout


def test_yazarin_bastan_sona_is_akisi(tmp_path: Path) -> None:
    alan = tmp_path / "calisma"
    kitap = alan / "saatcinin-kizi"
    alan.mkdir()

    # 1. Kurulum
    tamam(calistir(KUR, "--proje", alan, "--ev", "claude"))
    assert (alan / ".hikaye-kurulu").is_file() and (alan / ".claude" / "agents" / "bolum-hakemi.md").is_file()

    # 2. Planlama: genel plan ve kurgu hazır (ajan yazar); yapı ve sahne kartları betikle
    shutil.copytree(ORNEK_ROMAN / "plan", kitap / "plan")
    shutil.copytree(ORNEK_ROMAN / "kurgu", kitap / "kurgu")
    for ad in ("yapi-uc-perde.md", "sahneler.md"):  # planlamayı yazar sıfırdan yapıyor
        (kitap / "plan" / ad).unlink()
    (alan / ".aktif-kitap").write_text("saatcinin-kizi\n", encoding="utf-8")
    tamam(calistir("kurgu_plani.py", "baslat", "--proje", kitap, "--yontem", "uc-perde", "--bolum-sayisi", 60))
    tamam(calistir("kurgu_plani.py", "sahneler", "--proje", kitap))
    yaz(kitap / "plan" / "sahneler.md", "| # | Bölüm | Sahne | Bakış açısı | Mekân | Amaç | Çatışma | Sonuç | Değer | Durum |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | 1 | Duran saatler | Defne | Dükkân | Satmak | Saatler 03.14'te | Erteler | − → + | planlandı |\n"
        "| 2 | 1 | Kerem gelir | Defne | Dükkân | Saati korumak | Fotoğraf | Şüphe | + → − | planlandı |\n"
        "| 3 | 2 | Gizli kapak | Defne | Tezgâh | Anlamak | Kerem ısrar eder | Tarih bulunur | − → + | planlandı |\n")
    denetim = json_cikti(calistir("kurgu_plani.py", "denetle", "--proje", kitap, "--json"))
    assert not [b for b in denetim["bulgular"] if b["duzey"] == "hata"], denetim

    # 3. Ansiklopedi ve takip başlangıcı
    tamam(calistir("kurgu_ansiklopedisi.py", "olustur", "--proje", kitap, "--tur", "mekan", "--ad", "Aras Saat Dükkânı"))
    yaz(kitap / "kurgu" / "sozluk.md", "| Terim | Anlamı | Yanlış yazımlar |\n|---|---|---|\n| cep saati | Kapaklı saat | cepsaati |\n")
    assert json_cikti(calistir("takip_kaydet.py", "baslat", "--proje", kitap, "--girdi", ORNEK_ISLEMLER / "baslangic.json"))["tamam"]
    durum = json_cikti(calistir("proje_durumu.py", "durum", "--proje", kitap, "--json"))
    assert durum["sonraki_bolum"] == 1 and "1. bölümü yazın" in durum["adimlar"][0]

    # 4. Hedef ve başlangıç çizgisi
    gun1 = dt.date(2030, 3, 1)
    tamam(calistir("yazim_istatistik.py", "hedef", "--proje", kitap, "--toplam", 130000, "--gunluk", 500))
    tamam(calistir("yazim_istatistik.py", "kaydet", "--proje", kitap, "--bugun", gun1.isoformat()))

    # 5. Bölüm 1: bağlam paketi → yaz → kapılar → denetimler → kayıt → anlık görüntü
    paket = tamam(calistir("kurgu_ansiklopedisi.py", "baglam", "--proje", kitap, "--bolum", 1))
    assert "Defne Aras" in paket
    yaz(kitap / "metin" / "bolum-001_durmus-saatler.md",
        (ORNEK_ROMAN / "metin" / "bolum-001_durmus-saatler.md").read_text(encoding="utf-8"))
    kapilar = json_cikti(calistir("hikayectl.py", "bolum", "denetle", "--proje", kitap, "--bolum", 1))
    assert kapilar["tamam"], kapilar
    tamam(calistir("ai_kalip_denetle.py", kitap / "metin" / "bolum-001_durmus-saatler.md"), 0, 1)
    tamam(calistir("yazim_denetle.py", kitap / "metin" / "bolum-001_durmus-saatler.md"), 0, 1)
    tamam(calistir("sureklilik_denetle.py", "--proje", kitap, "--bolum", 1))
    kayit = json_cikti(calistir("hikayectl.py", "bolum", "kaydet", "--proje", kitap, "--bolum", 1,
                                "--girdi", ORNEK_ISLEMLER / "islem-001.json"))
    assert kayit["tamam"], kayit
    tamam(calistir("anlik_goruntu.py", "al", "--proje", kitap, "--not", "1. bölüm kaydı"))

    # 6. Bölüm 2: ses izi ve yazar kontrollü revizyon döngüsü
    tamam(calistir("ses_izi.py", "cikar", "--proje", kitap, "--bolumler", "1"))
    taslak_dir = kitap / ".hikaye" / "calisma" / "bolum-002"
    ornek2 = (ORNEK_ROMAN / "metin" / "bolum-002_kapagin-ici.md").read_text(encoding="utf-8")
    t1 = yaz(taslak_dir / "taslak-1.md", ornek2.replace("Defne kadife keseyi kendine doğru çekti.",
                                                        "Defne derin bir nefes aldı. Sanki zaman durmuştu. "
                                                        "Defne kadife keseyi kendine doğru çekti. [TK]"))
    olc1 = json_cikti(calistir("revizyon_dongusu.py", "olc", "--proje", kitap, "--bolum", 2, "--dosya", t1, "--json"))
    t2 = yaz(taslak_dir / "taslak-2.md", ornek2)
    olc2 = json_cikti(calistir("revizyon_dongusu.py", "olc", "--proje", kitap, "--bolum", 2, "--dosya", t2, "--json"))
    assert olc1["bitmemis_isaret"] == 1 and olc2["bitmemis_isaret"] == 0
    assert olc2["puanlar"]["yz_kaliplari"] >= olc1["puanlar"]["yz_kaliplari"] and "ses" in olc2["puanlar"]
    tamam(calistir("revizyon_dongusu.py", "rubrik", "--proje", kitap, "--bolum", 2))
    olcutler = ("plan_sadakati", "gerilim", "karakter", "somutluk", "diyalog", "dil")
    h1 = yaz(taslak_dir / "hakem-1.json", json.dumps({"olcutler": dict.fromkeys(olcutler, 7),
                                                      "plan_maddeleri": [{"madde": "Ana olay", "durum": "tamam"}],
                                                      "oneriler": ["Klişeleri çıkar", "[TK] işaretini doldur"]}))
    h2 = yaz(taslak_dir / "hakem-2.json", json.dumps({"olcutler": dict.fromkeys(olcutler, 8.5),
                                                      "plan_maddeleri": [{"madde": "Ana olay", "durum": "tamam"}]}))
    k1 = json_cikti(calistir("revizyon_dongusu.py", "kaydet", "--proje", kitap, "--bolum", 2, "--dosya", t1, "--hakem", h1,
                             "--json"))
    assert k1["karar"] == "devam"
    assert "Klişeleri çıkar" in tamam(calistir("revizyon_dongusu.py", "brief", "--proje", kitap, "--bolum", 2))
    k2 = json_cikti(calistir("revizyon_dongusu.py", "kaydet", "--proje", kitap, "--bolum", 2, "--dosya", t2, "--hakem", h2,
                             "--json"))
    assert k2["karar"] == "dur-hedef" and k2["toplam"] > k1["toplam"]
    tamam(calistir("revizyon_dongusu.py", "kabul", "--proje", kitap, "--bolum", 2, "--tur", 2, "--yazar-onayladi"))
    bolum2 = next((kitap / "metin").glob("bolum-002*.md"))
    assert bolum2.read_text(encoding="utf-8") == ornek2
    kayit = json_cikti(calistir("hikayectl.py", "bolum", "kaydet", "--proje", kitap, "--bolum", 2,
                                "--girdi", ORNEK_ISLEMLER / "islem-002.json"))
    assert kayit["tamam"], kayit

    # 7. Bölüm 3 için iki taslak: turnuva
    for e, ek in (("A", "Kerem kapıda bekliyordu."), ("B", "Sokak boştu.")):
        yaz(kitap / ".hikaye" / "calisma" / "bolum-003" / f"{e}.md", f"# Bölüm 3\n\n{ek} Defne kepengi indirdi.\n")
    tamam(calistir("turnuva.py", "baslat", "--proje", kitap, "--ad", "bolum-03", "--tek-yonlu",
                   "--aday", "A=.hikaye/calisma/bolum-003/A.md", "--aday", "B=.hikaye/calisma/bolum-003/B.md"))
    assert "A" in tamam(calistir("turnuva.py", "sirada", "--proje", kitap, "--ad", "bolum-03"))
    tamam(calistir("turnuva.py", "sonuc", "--proje", kitap, "--ad", "bolum-03", "--mac", 1, "--kazanan", "A",
                   "--gerekce", "Gerilim daha yüksek"))
    sira = json_cikti(calistir("turnuva.py", "siralama", "--proje", kitap, "--ad", "bolum-03", "--json"))
    assert sira["siralama"][0]["etiket"] == "A" and sira["oynanan"] == sira["toplam"] == 1

    # 8. Süreklilik, ansiklopedi, ipuçları, dönem
    tamam(calistir("sureklilik_denetle.py", "--proje", kitap))
    tamam(calistir("kurgu_ansiklopedisi.py", "dogrula", "--proje", kitap), 0, 1)
    tutarlilik = json_cikti(calistir("kurgu_ansiklopedisi.py", "tutarlilik", "--proje", kitap, "--json"))
    assert not [b for b in tutarlilik if b["duzey"] == "hata"], tutarlilik
    ipucu = json_cikti(calistir("ipucu_defteri.py", "rapor", "--proje", kitap, "--json"))
    assert ipucu["ozet"]["acik"] == 4 and ipucu["ozet"]["hata"] == 0
    donem = json_cikti(calistir("donem_denetle.py", "--proje", kitap, "--yil", "2024", "--json"))
    assert donem["yil"] == [2024, 2024]

    # 9. İstatistik ve durum
    tamam(calistir("yazim_istatistik.py", "kaydet", "--proje", kitap, "--bugun", (gun1 + dt.timedelta(days=1)).isoformat()))
    pano = json_cikti(calistir("yazim_istatistik.py", "pano", "--proje", kitap, "--json", "--bugun",
                               (gun1 + dt.timedelta(days=1)).isoformat()))
    assert pano["bugun_yazilan"] == pano["toplam_kelime"] > 600 and pano["seri_gun"] == 1
    durum = json_cikti(calistir("proje_durumu.py", "durum", "--proje", kitap, "--json"))
    assert durum["son_kaydedilen_bolum"] == 2 and durum["sonraki_bolum"] == 3
    assert any("3. bölüm" in a for a in durum["adimlar"])
    ozet = tamam(calistir("proje_durumu.py", "ozet", "--proje", kitap))
    assert "Durmuş Saatler (1–20)" in ozet and "- 2:" in ozet

    # 10. Sürümler: fark ve geri alma
    tamam(calistir("anlik_goruntu.py", "al", "--proje", kitap, "--not", "2. bölüm"))
    fark = json_cikti(calistir("anlik_goruntu.py", "fark", "--proje", kitap, "--a", "son~1", "--b", "son", "--json"))
    assert any(d.startswith("metin/bolum-002") for d in fark["ozet"]["eklenen_dosya"])
    tamam(calistir("anlik_goruntu.py", "dogrula", "--proje", kitap))

    # 11. Yayın: bütün biçimler, sonra DOCX'i yeni projeye geri al
    yayin = kitap / "yayin"
    tamam(calistir("e_kitap_derle.py", "--proje", kitap, "--yazar", "Ayşe Yılmaz", "--bicim", "hepsi", "txt"))
    for ad in ("saatcinin-kizi.epub", "saatcinin-kizi.docx", "saatcinin-kizi.odt"):
        with zipfile.ZipFile(yayin / ad) as z:
            assert z.testzip() is None
    ikinci = tmp_path / "geri-alinan"
    tamam(calistir("belge_ice_aktar.py", "aktar", "--kaynak", yayin / "saatcinin-kizi.docx", "--proje", ikinci))
    kp = modul_yukle("kitap_proje.py")
    assert [b.kelime for b in kp.bolumler(ikinci)] == [b.kelime for b in kp.bolumler(kitap)]

    # 12. Çalışma masası: bütün sekmelerin verisi hatasız ve sunucu yalnızca yerel
    masa = json_cikti(calistir("calisma_masasi.py", "--calisma-alani", alan, "--json"))
    k = masa["kitaplar"][0]
    assert k["aktif"] and k["bolum_sayisi"] == 2
    for sekme, veri in k["ayrinti"].items():
        assert not (isinstance(veri, dict) and "hata" in veri), (sekme, veri)
    assert k["ayrinti"]["sahneler"] and k["ayrinti"]["surumler"] and k["ayrinti"]["donguler"][0]["bolum"] == 2
    cm = modul_yukle("calisma_masasi.py")
    sunucu = cm.sunucu_olustur(alan, 0)
    is_parcacigi = threading.Thread(target=sunucu.serve_forever, daemon=True)
    is_parcacigi.start()
    try:
        port = sunucu.server_address[1]
        for host, beklenen in (("127.0.0.1", 200), ("kotu.example", 403)):
            baglanti = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            baglanti.request("GET", "/", headers={"Host": f"{host}:{port}"})
            yanit = baglanti.getresponse()
            govde = yanit.read().decode("utf-8")
            assert yanit.status == beklenen
            if beklenen == 200:
                assert "Çalışma Masası" in govde and "Sahneler" in govde and "connect-src 'self'" in yanit.getheader(
                    "Content-Security-Policy")
            baglanti.close()
        baglanti = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        baglanti.request("GET", "/api/durum", headers={"Host": f"localhost:{port}"})
        assert json.loads(baglanti.getresponse().read())["kitaplar"][0]["ad"] == "Saatçinin Kızı"
        baglanti.close()
    finally:
        sunucu.shutdown()
        sunucu.server_close()
