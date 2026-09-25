"""2.0.0: kitap_proje, kurgu_plani, kurgu_ansiklopedisi, bilgi_ara, ipucu_defteri, donem_denetle, proje_durumu."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import calistir, json_cikti, modul_yukle


def yaz(yol: Path, metin: str) -> Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")
    return yol


# ---------------------------------------------------------------- kitap_proje.py


def test_kitap_proje_bolumler_ve_cift_numara(roman: Path) -> None:
    kp = modul_yukle("kitap_proje.py")
    bolumler = kp.bolumler(roman)
    assert [b.no for b in bolumler] == [1, 2]
    assert bolumler[0].kelime > 100 and bolumler[0].baslik
    assert kp.plan_hedefi(roman, 1) and kp.plan_hedefi(roman, 99) is None
    assert kp.kitap_basligi(roman) == "Saatçinin Kızı"
    yaz(roman / "metin" / "bolum-002_kopya.md", "# Kopya\n\nMetin.\n")
    with pytest.raises(kp.ProjeHatasi, match="iki dosya"):
        kp.bolumler(roman)


def test_kitap_proje_acik_ipuclari_sozluk_ve_liste(tmp_path: Path, roman: Path) -> None:
    kp = modul_yukle("kitap_proje.py")
    acik = kp.acik_ipuclari(roman)
    assert [i["id"] for i in acik] == ["F001", "F002", "F003", "F004"]
    liste = {"ipuclari": [{"id": "F9", "durum": "çözüldü"}, {"id": "F8", "durum": "ekili"}, "bozuk"]}
    assert [i["id"] for i in kp.acik_ipuclari(tmp_path, liste)] == ["F8"]
    yaz(tmp_path / "takip" / "_takip-durumu.json", "{bozuk")
    assert kp.takip_durumu(tmp_path) == {} and kp.acik_ipuclari(tmp_path) == []


def test_kitap_proje_bos_alan_sonraki_satiri_yutmaz(tmp_path: Path) -> None:
    """'- Göz rengi:' boşken bir sonraki satırın değeri alınmamalı (düzenli ifade satır sınırını aşmamalı)."""
    ka = modul_yukle("kurgu_ansiklopedisi.py")
    yol = yaz(tmp_path / "k.md", "# Ali\n\n- Göz rengi:\n- Saç rengi: kumral\n\n**Soru: cevap mı?**\n")
    kayit = ka.kayit_oku("karakter", yol)
    assert kayit.alanlar["göz rengi"] == "" and kayit.alanlar["saç rengi"] == "kumral"
    assert not any(k.startswith("soru") for k in kayit.alanlar)


# ---------------------------------------------------------------- kurgu_plani.py


def test_kurgu_plani_yontemler_ve_sablon(roman: Path) -> None:
    sonuc = calistir("kurgu_plani.py", "yontemler")
    assert sonuc.returncode == 0
    for ad in ("uc-perde", "kahramanin-yolculugu", "serim-dugum-cozum", "yedi-nokta", "kar-tanesi"):
        assert ad in sonuc.stdout
    (roman / "plan" / "yapi-uc-perde.md").unlink()  # örnek projede dolu hâli var; boş şablondan başla
    sonuc = calistir("kurgu_plani.py", "baslat", "--proje", roman, "--yontem", "uc-perde", "--bolum-sayisi", "40")
    assert sonuc.returncode == 0, sonuc.stderr
    metin = (roman / "plan" / "yapi-uc-perde.md").read_text(encoding="utf-8")
    assert metin.count("### ") == 9 and "- Bölüm sayısı: 40" in metin
    tekrar = calistir("kurgu_plani.py", "baslat", "--proje", roman, "--yontem", "uc-perde")
    assert tekrar.returncode == 2 and "üzerine yazılmadı" in tekrar.stderr


def test_kurgu_plani_denetim_vurus_konumu_ve_sirasi(roman: Path) -> None:
    kp = modul_yukle("kurgu_plani.py")
    (roman / "plan" / "yapi-uc-perde.md").unlink()
    kp.baslat(roman, "uc-perde", 40, None)
    yol = roman / "plan" / "yapi-uc-perde.md"
    metin = yol.read_text(encoding="utf-8")
    bolumler = metin.split("### ")
    # İlk vuruşu doldur ve 30. bölüme taşı (beklenen ~%0–10), ikinciyi 5. bölüme koy (sıra hatası).
    bolumler[1] = bolumler[1].replace("- Bölüm: 1", "- Bölüm: 30") + "Defne dükkânı açar.\n\n"
    bolumler[2] = __import__("re").sub(r"- Bölüm: \d+", "- Bölüm: 5", bolumler[2]) + "Saatler durmuştur.\n\n"
    yaz(yol, "### ".join(bolumler))
    kimlikler = {b["kimlik"] for b in kp.denetle(roman)["bulgular"]}
    assert {"vurus-konumu", "vurus-sirasi", "bos-vurus"} <= kimlikler


def test_kurgu_plani_kar_tanesi_ve_sahne_denetimi(roman: Path) -> None:
    kp = modul_yukle("kurgu_plani.py")
    kp.baslat(roman, "kar-tanesi", None, None)
    kar = roman / "plan" / "kar-tanesi.md"
    metin = kar.read_text(encoding="utf-8")
    uzun = " ".join(["kelime"] * 30) + "."
    metin = metin.replace("kim, ne istiyor, önünde ne var.\n", "kim, ne istiyor, önünde ne var.\n\n" + uzun + "\n", 1)
    metin = metin.replace("## 3. Ana karakter özetleri\n", "## 3. Ana karakter özetleri\n\nDefne: saatçi.\n", 1)
    yaz(kar, metin)
    yaz(roman / "plan" / "sahneler.md", "| # | Bölüm | Sahne | Bakış açısı | Mekân | Amaç | Çatışma | Sonuç | Değer | Durum |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | 1 | Açılış | Defne | Dükkân | Satmak | Saatler | Erteler | − → + | yazıldı |\n"
        "| 2 | 1 | Kerem | Defne | Dükkân |  | Kerem | Şüphe | + → + | taslak |\n"
        "| 3 | x | Hata | Kerem | Sokak | a | b | c | iyi | uçuyor |\n")
    kimlikler = [b["kimlik"] for b in kp.denetle(roman)["bulgular"]]
    for beklenen in ("oz-uzun", "atlanan-adim", "sahne-eksik", "duz-sahne", "sahne-bolumsuz", "deger-bicimi",
                     "durum-bilinmeyen", "sahnesiz-bolum"):
        assert beklenen in kimlikler, (beklenen, kimlikler)
    pano = calistir("kurgu_plani.py", "pano", "--proje", roman, "--html", roman / "pano.html")
    assert pano.returncode == 0 and "Açılış" in pano.stdout
    html = (roman / "pano.html").read_text(encoding="utf-8")
    assert "<html" in html and "Açılış" in html and "<script" not in html


# ---------------------------------------------------------------- kurgu_ansiklopedisi.py


@pytest.fixture()
def ansiklopedi(roman: Path) -> Path:
    ka = modul_yukle("kurgu_ansiklopedisi.py")
    ka.olustur(roman, "mekan", "Sabri'nin Bakkalı")
    yaz(roman / "kurgu" / "sozluk.md", "| Terim | Anlamı | Yanlış yazımlar |\n|---|---|---|\n"
        "| cep saati | Kapaklı saat | cepsaati |\n| Kuzguncuk | Semt | Kuzgunçuk |\n")
    yaz(roman / "kurgu" / "zaman-cizelgesi.md", "| Tarih | Olay | Kişiler | Bölüm |\n|---|---|---|---|\n"
        "| 1987 | Fotoğraf çekildi | Nuri Usta, Tahsin | 1 |\n| 2024 | Dükkân açıldı | Defne Aras, Zeynep Hanım | 1 |\n")
    return roman


def test_ansiklopedi_olustur_listele_ve_mulakat(ansiklopedi: Path) -> None:
    sonuc = calistir("kurgu_ansiklopedisi.py", "olustur", "--proje", ansiklopedi, "--tur", "karakter", "--ad", "Zeynep Hanım")
    assert sonuc.returncode == 0, sonuc.stderr
    dosya = ansiklopedi / "kurgu" / "karakterler" / "zeynep-hanim.md"
    assert "Karakter Mülakatı" in dosya.read_text(encoding="utf-8")
    tekrar = calistir("kurgu_ansiklopedisi.py", "olustur", "--proje", ansiklopedi, "--tur", "karakter", "--ad", "Zeynep Hanım")
    assert tekrar.returncode == 2
    liste = json_cikti(calistir("kurgu_ansiklopedisi.py", "listele", "--proje", ansiklopedi, "--json"))
    adlar = {k["ad"] for k in liste}
    assert {"Defne Aras", "Kerem Yalın", "Nuri Usta", "Saat dükkânı", "Sabri'nin Bakkalı", "Zeynep Hanım"} <= adlar


def test_ansiklopedi_dogrula_bilinmeyen_ad_ve_olum(ansiklopedi: Path) -> None:
    ka = modul_yukle("kurgu_ansiklopedisi.py")
    nuri = ansiklopedi / "kurgu" / "karakterler" / "nuri-usta.md"
    yaz(nuri, nuri.read_text(encoding="utf-8").replace("- Yaş: 78 (öldüğünde)", "- Yaş: yetmiş\n- Doğum yılı: 1990"))
    iletiler = " | ".join(b["ileti"] for b in ka.dogrula(ansiklopedi))
    assert "Tahsin" in iletiler  # zaman çizelgesinde kayıtsız ad
    assert "doğum" in iletiler.lower()  # 1987 olayı, 1990 doğumlu Nuri Usta
    assert "yetmiş" in iletiler or "sayı" in iletiler


def test_ansiklopedi_tutarlilik_sozluk_ve_ad_kaymasi(ansiklopedi: Path) -> None:
    ka = modul_yukle("kurgu_ansiklopedisi.py")
    bolum = ansiklopedi / "metin" / "bolum-003_deneme.md"
    yaz(bolum, "# Bölüm 3\n\nDefna dükkâna girdi. Kuzgunçuk sessizdi. Defne'nin elinde cepsaati vardı.\n")
    bulgular = ka.tutarlilik(ansiklopedi, 3)
    iletiler = " | ".join(b["ileti"] for b in bulgular)
    assert "Kuzgunçuk" in iletiler and "cepsaati" in iletiler and "Defna" in iletiler
    cli = calistir("kurgu_ansiklopedisi.py", "tutarlilik", "--proje", ansiklopedi, "--bolum", "3", "--json")
    assert cli.returncode == 1 and json_cikti(cli)


def test_ansiklopedi_dagilim_grafik_ve_baglam(ansiklopedi: Path) -> None:
    ka = modul_yukle("kurgu_ansiklopedisi.py")
    dg = ka.dagilim(ansiklopedi)
    defne = next(k for k in dg["kayitlar"] if k["ad"] == "Defne Aras")
    assert defne["gorunumler"].get(1) and defne["gorunumler"].get(2)
    html = calistir("kurgu_ansiklopedisi.py", "dagilim", "--proje", ansiklopedi, "--html", ansiklopedi / "d.html")
    assert html.returncode == 0 and "Defne Aras" in (ansiklopedi / "d.html").read_text(encoding="utf-8")
    mermaid = ka.grafik(ansiklopedi, bolum=2)
    assert "graph LR" in mermaid and "Defne" in mermaid
    dot = calistir("kurgu_ansiklopedisi.py", "grafik", "--proje", ansiklopedi, "--bicim", "dot")
    assert dot.returncode == 0 and dot.stdout.lstrip().startswith(("graph", "digraph"))
    paket = ka.baglam(ansiklopedi, 3, 12000)
    assert "Defne Aras" in paket and "F004" in paket
    kucuk = ka.baglam(ansiklopedi, 3, 1500)
    assert len(kucuk.encode("utf-8")) <= 1500 + 200
    yok = calistir("kurgu_ansiklopedisi.py", "baglam", "--proje", ansiklopedi, "--bolum", "44")
    assert yok.returncode == 2 and "planı yok" in yok.stderr


# ---------------------------------------------------------------- bilgi_ara.py


def test_bilgi_ara_turkce_govde_ve_ifade(roman: Path) -> None:
    ba = modul_yukle("bilgi_ara.py")
    assert ba.terimlere_ayir("Saatlerin") == ba.terimlere_ayir("saatleri")
    assert ba.terimlere_ayir("İSTANBUL'DA") == ba.terimlere_ayir("istanbul")
    sonuc = ba.ara(roman, "gizli kapak", adet=3)
    assert sonuc and "kapa" in sonuc[0]["metin"].lower() and sonuc[0]["satir"] > 0
    cli = calistir("bilgi_ara.py", "--proje", roman, "--sorgu", "\"cep saati\"", "--kapsam", "metin", "--json")
    assert cli.returncode == 0 and all(s["dosya"].startswith("metin/") for s in json_cikti(cli))
    bos = calistir("bilgi_ara.py", "--proje", roman, "--sorgu", "zzqqxx")
    assert bos.returncode == 1
    hatali = calistir("bilgi_ara.py", "--proje", roman, "--sorgu", "saat", "--adet", "0")
    assert hatali.returncode == 2


# ---------------------------------------------------------------- ipucu_defteri.py


def test_ipucu_defteri_son_anilma_ve_uyarilar(roman: Path) -> None:
    idf = modul_yukle("ipucu_defteri.py")
    r = idf.rapor(roman)
    assert r["planlanan_bolum"] == 60 and r["ozet"]["acik"] == 4 and r["ozet"]["hata"] == 0
    f3 = next(i for i in r["ipuclari"] if i["id"] == "F003")
    assert f3["son_anilma"] == 2
    durum = json.loads((roman / "takip" / "_takip-durumu.json").read_text(encoding="utf-8"))
    durum["ipuclari"]["F004"]["planlanan_cozum_bolumu"] = 2
    durum["ipuclari"]["F001"]["planlanan_cozum_bolumu"] = 90
    for n in range(5, 10):
        durum["ipuclari"][f"F10{n}"] = {"id": f"F10{n}", "ozet": f"Ek ipucu {n}", "durum": "ekili", "onem": "orta",
                                        "ekildigi_bolum": 1, "planlanan_cozum_bolumu": 30}
    yaz(roman / "takip" / "_takip-durumu.json", json.dumps(durum, ensure_ascii=False))
    kurallar = {b["kural"] for b in idf.rapor(roman, unutma=1)["bulgular"]}
    assert {"suresi-gecti", "plan-disi", "yigilma", "unutuldu"} <= kurallar
    cli = calistir("ipucu_defteri.py", "rapor", "--proje", roman)
    assert cli.returncode == 1 and "F004" in cli.stdout
    serit = calistir("ipucu_defteri.py", "serit", "--proje", roman)
    assert serit.returncode == 0 and "●" in serit.stdout and "○" in serit.stdout


def test_ipucu_defteri_takipsiz_proje(tmp_path: Path) -> None:
    (tmp_path / "metin").mkdir()
    sonuc = calistir("ipucu_defteri.py", "rapor", "--proje", tmp_path)
    assert sonuc.returncode == 0 and "ipucu yok" in sonuc.stdout
    assert calistir("ipucu_defteri.py", "rapor", "--proje", tmp_path / "yok").returncode == 2


# ---------------------------------------------------------------- donem_denetle.py


def test_donem_denetle_henuz_yok_ve_kalkti(tmp_path: Path) -> None:
    dd = modul_yukle("donem_denetle.py")
    metin = "Ahmet Bey fesini düzeltti, radyoyu açtı. Soyadı kanunu çıkınca Yılmaz soyadını aldı. Festivale gittiler."
    bulgular = dd.denetle_metin(metin, 1920, 1922)
    iletiler = " ".join(json.dumps(b, ensure_ascii=False) for b in bulgular)
    assert "radyo" in iletiler.lower() and "soyad" in iletiler.lower()
    assert "festival" not in iletiler.lower()  # 'fes' deseni 'festival' ile eşleşmemeli
    geç = dd.denetle_metin("Başında fesiyle sokağa çıktı.", 1935, 1935)
    assert geç and all(b["duzey"] == "uyari" for b in geç)
    assert not dd.denetle_metin("Başında fesiyle sokağa çıktı.", 1900, 1910)
    # 'radyo' deseni bilimsel terimlerle eşleşmemeli
    assert not dd.denetle_metin("Radyoaktif madde bulundu; radyolog ve radyografi.", 1920, 1920)


def test_donem_denetle_proje_yili_istisna_ve_cli(roman: Path) -> None:
    genel = roman / "plan" / "genel-plan.md"
    yaz(genel, genel.read_text(encoding="utf-8") + "\n- Dönem: 1919–1923\n")
    yaz(roman / "metin" / "bolum-003_x.md", "# Bölüm 3\n\nDefne cep telefonunu çıkardı, televizyon açıktı.\n")
    sonuc = calistir("donem_denetle.py", "--proje", roman, "--json")
    assert sonuc.returncode == 1
    veri = json_cikti(sonuc)
    assert veri["yil"] == [1919, 1923] and veri["bulgular"]
    yaz(roman / ".donem-istisnalari", "televizyon\ncep telefonu\n")
    temiz = calistir("donem_denetle.py", "--proje", roman, "--bolum", "3")
    assert temiz.returncode == 0, temiz.stdout
    assert calistir("donem_denetle.py", "--liste").returncode == 0
    assert calistir("donem_denetle.py", "--yil", "abc", "--dosya", genel).returncode == 2


# ---------------------------------------------------------------- proje_durumu.py


def test_proje_durumu_sonraki_adim_ve_yarim_bolum(roman: Path) -> None:
    pd = modul_yukle("proje_durumu.py")
    d = pd.durum_raporu(roman)
    assert d["sonraki_bolum"] == 3 and "3. bölümü yazın" in d["adimlar"][0]
    assert any("anlık görüntü" in u for u in d["uyarilar"])
    (roman / ".hikaye" / "calisma" / "bolum-003").mkdir(parents=True)
    d = pd.durum_raporu(roman)
    assert "yarım kalmış" in d["adimlar"][0]
    import shutil
    shutil.rmtree(roman / ".hikaye" / "calisma")
    yaz(roman / "metin" / "bolum-003_yeni.md", "# Bölüm 3\n\nYeni metin.\n")
    assert "takibe kaydedilmemiş" in pd.durum_raporu(roman)["adimlar"][0]
    (roman / "metin" / "bolum-003_yeni.md").unlink()
    (roman / "plan" / "bolum-plani_003.md").unlink()
    d = pd.durum_raporu(roman)
    assert "planı yok" in d["adimlar"][0] and "/kitaptik-yayimla" in d["adimlar"][1]
    (roman / "yayin" / "kitaptik").mkdir(parents=True)
    (roman / "yayin" / "kitaptik" / "rapor.json").write_text("{}", encoding="utf-8")
    assert not any("/kitaptik-yayimla" in a for a in pd.durum_raporu(roman)["adimlar"])
    cli = calistir("proje_durumu.py", "durum", "--proje", roman, "--json")
    assert cli.returncode == 0 and json_cikti(cli)["son_kaydedilen_bolum"] == 2


def test_proje_durumu_ozet_katmanlari_ve_sikistirma(roman: Path) -> None:
    pd = modul_yukle("proje_durumu.py")
    belge = pd.ozet_katmanlari(roman)
    assert "Dedesinin kırk yıllık saat dükkânını" in belge and "## Durmuş Saatler (1–20)" in belge
    kayitlar = roman / "takip" / "bolum-kayitlari"
    for n in range(3, 46):
        yaz(kayitlar / f"bolum-{n:03d}.md", f"# Bölüm {n}\n\n- Sonuç: {n}. bölümde Defne bir iz buldu. "
            + "Ayrıntı cümlesi uzun uzun devam eder. " * 6 + "\n")
    tam = pd.ozet_katmanlari(roman, sinir=200000)
    assert "## Geri Sayım (21–40)" in tam and "## Ayar (41–60)" in tam
    sikisik = pd.ozet_katmanlari(roman, sinir=6000)
    assert len(sikisik.encode("utf-8")) <= 6000
    assert "- 45: 45. bölümde Defne bir iz buldu. Ayrıntı" in sikisik  # son cilt tam kalır
    cli = calistir("proje_durumu.py", "ozet", "--proje", roman, "--cikti", roman / "takip" / "ozet.md")
    assert cli.returncode == 0 and (roman / "takip" / "ozet.md").is_file()
    assert calistir("proje_durumu.py", "ozet", "--proje", roman, "--sinir", "10").returncode == 2


def test_proje_durumu_yeni_kitap_iskeletten_genel_plana_yonlendirir(tmp_path: Path) -> None:
    kitap = tmp_path / "kitabim"
    (kitap / "metin").mkdir(parents=True)
    ilk = json_cikti(calistir("proje_durumu.py", "durum", "--proje", kitap, "--json"))
    assert any("/roman-planla" in a for a in ilk["adimlar"])
    assert calistir("kurgu_plani.py", "baslat", "--proje", kitap, "--yontem", "uc-perde").returncode == 0
    sonra = json_cikti(calistir("proje_durumu.py", "durum", "--proje", kitap, "--json"))
    # İskelet kurulduktan sonra aynı öneriyi tekrarlamaz, genel plana geçirir
    assert any("yapi-uc-perde.md" in a and "/roman-yaz" in a for a in sonra["adimlar"])
    assert not any("/roman-planla" in a for a in sonra["adimlar"])


def test_bilgi_ara_tirnaksiz_cok_sozcuklu_sorgu(roman: Path) -> None:
    sonuc = calistir("bilgi_ara.py", "--proje", roman, "--sorgu", "saatçi", "dükkanı", "--json")
    assert sonuc.returncode == 0 and json_cikti(sonuc)


def test_dagilim_genis_bolumde_sutunlar_karismaz(ansiklopedi: Path) -> None:
    ka = modul_yukle("kurgu_ansiklopedisi.py")
    v = ka.dagilim(ansiklopedi)
    v["uzunluk"] = {n: 12345 for n in v["bolumler"]}
    satir = ka.dagilim_metni(v).splitlines()
    kelime = next(s for s in satir if s.startswith("Kelime"))
    assert kelime.count("12.345") == len(v["bolumler"])
    tablo = [s for s in satir if s and not s.startswith(("Bakış", "Dikkat", "  -"))]
    # Kayıt ve kelime satırlarında bölüm sütunları aynı genişlikte
    assert len({len(s.split("   Toplam")[0]) for s in tablo[:1]} | {len(kelime)}) == 1


def test_proje_durumu_kayittan_sonra_degisen_bolumu_bildirir(roman: Path) -> None:
    temiz = json_cikti(calistir("proje_durumu.py", "durum", "--proje", roman, "--json"))
    assert temiz["degisen_bolumler"] == []
    bolum = sorted((roman / "metin").glob("bolum-002_*.md"))[0]
    bolum.write_text(bolum.read_text(encoding="utf-8") + "\nSonradan eklenen bir cümle.\n", encoding="utf-8")
    sonra = json_cikti(calistir("proje_durumu.py", "durum", "--proje", roman, "--json"))
    assert sonra["degisen_bolumler"] == [2]
    assert any(u.startswith("2. bölüm takibe kaydedildikten sonra değişmiş") for u in sonra["uyarilar"])


def test_kurgu_plani_etiketli_deger_planlandi_durumu_ve_olay_satiri(tmp_path: Path) -> None:
    kp = modul_yukle("kurgu_plani.py")
    kitap = tmp_path / "kitap"
    (kitap / "metin").mkdir(parents=True)
    assert calistir("kurgu_plani.py", "baslat", "--proje", kitap, "--yontem", "uc-perde", "--bolum-sayisi", "30").returncode == 0
    sablon = (kitap / "plan" / "yapi-uc-perde.md").read_text(encoding="utf-8")
    assert sablon.count("- Olay:") == 9  # boş Olay satırı vuruşu dolu saydırmaz
    assert kp.denetle(kitap)["ozet"]["yapilar"]["yapi-uc-perde.md"]["dolu"] == 0
    yaz(kitap / "plan" / "sahneler.md", "| # | Bölüm | Sahne | Bakış açısı | Mekân | Amaç | Çatışma | Sonuç | Değer | Durum |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | 1 | A | Defne | Dükkân | istek | engel | evet ama | güven + → korku − | planlandı |\n"
        "| 2 | 1 | B | Defne | Dükkân | istek | engel | hayır | umut+ -> umut+ | yazıldı |\n"
        "| 3 | 2 | C | Defne | Dükkân | istek | engel | hayır | çok iyi | yazıldı |\n")
    sonuc = json_cikti(calistir("kurgu_plani.py", "denetle", "--proje", kitap, "--json"))
    kodlar = [(b["kimlik"], b["ileti"]) for b in sonuc["bulgular"]]
    assert not any(k == "durum-bilinmeyen" for k, _ in kodlar)
    assert any(k == "duz-sahne" and "'B'" in m for k, m in kodlar)
    assert [m for k, m in kodlar if k == "deger-bicimi"] and all("satır 5" in m for k, m in kodlar if k == "deger-bicimi")


def test_ornek_roman_butun_v2_denetimlerinden_temiz_gecer(roman: Path) -> None:
    """Depodaki örnek proje, yeni kullanıcıya gösterilen 'doğru' hâldir: her denetim temiz olmalı."""
    for komut in (["kurgu_ansiklopedisi.py", "dogrula"], ["kurgu_ansiklopedisi.py", "tutarlilik"],
                  ["kurgu_plani.py", "denetle"]):
        sonuc = json_cikti(calistir(*komut, "--proje", roman, "--json"))
        bulgular = sonuc["bulgular"] if isinstance(sonuc, dict) else sonuc
        assert bulgular == [], (komut, bulgular)
    assert calistir("ipucu_defteri.py", "rapor", "--proje", roman).returncode == 0
    assert calistir("sureklilik_denetle.py", "--proje", roman).returncode == 0
    assert calistir("donem_denetle.py", "--proje", roman, "--yil", "2024").returncode == 0
    durum = json_cikti(calistir("proje_durumu.py", "durum", "--proje", roman, "--json"))
    assert durum["degisen_bolumler"] == [] and durum["sonraki_bolum"] == 3
