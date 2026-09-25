"""2.0.0: revizyon_dongusu, turnuva, ses_izi, anlik_goruntu, yazim_istatistik."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from conftest import calistir, json_cikti, modul_yukle


def yaz(yol: Path, metin: str) -> Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")
    return yol


def hakem_json(yol: Path, puan: float = 8.0, durum: str = "tamam") -> Path:
    olcutler = {k: puan for k in ("plan_sadakati", "gerilim", "karakter", "somutluk", "diyalog", "dil")}
    return yaz(yol, json.dumps({"olcutler": olcutler, "plan_maddeleri": [{"madde": "Ana olay", "durum": durum}],
                                "guclu": ["kanca"], "zayif": [], "oneriler": ["Sonu sıkılaştır"]}, ensure_ascii=False))


# ---------------------------------------------------------------- revizyon_dongusu.py


def test_dongu_mekanik_olcum_ve_kapi(roman: Path) -> None:
    rd = modul_yukle("revizyon_dongusu.py")
    metin = (roman / "metin" / "bolum-001_durmus-saatler.md").read_text(encoding="utf-8")
    olcum = rd.mekanik_olc(metin, roman, 1)
    assert set(olcum["puanlar"]) >= {"yz_kaliplari", "ritim", "tekrar", "uzunluk"}
    assert all(0 <= v <= 10 for v in olcum["puanlar"].values()) and 0 <= olcum["mekanik"] <= 10
    assert olcum["bitmemis_isaret"] == 0
    kotu = rd.mekanik_olc(metin + "\n\n[TK] buraya sahne gelecek. Sanki bir şey değişmişti; derin bir nefes aldı.\n", roman, 1)
    assert kotu["bitmemis_isaret"] >= 1


def test_dongu_turlar_karar_brief_ve_kabul(roman: Path, tmp_path: Path) -> None:
    rd = modul_yukle("revizyon_dongusu.py")
    kaynak = (roman / "metin" / "bolum-002_kapagin-ici.md").read_text(encoding="utf-8")
    t1 = yaz(tmp_path / "t1.md", kaynak)
    rubrik = calistir("revizyon_dongusu.py", "rubrik", "--proje", roman, "--bolum", 2)
    assert rubrik.returncode == 0 and "plan_sadakati" in rubrik.stdout and "Açığa" in rubrik.stdout
    k1 = rd.kaydet(roman, 2, t1, hakem_json(tmp_path / "h1.json", 6.0, "eksik"), "ilk", 8.0, 4)
    assert k1["tur"] == 1 and k1["karar"] == "devam" and k1["acik_plan_maddesi"] == 1
    # tur kopyası her platformda LF satır sonuyla yazılmalı; aksi hâlde Windows'ta özet tutmaz
    assert b"\r" not in (roman / ".hikaye" / "dongu" / "bolum-002" / "tur-01.md").read_bytes()
    with pytest.raises(rd.DonguHatasi, match="aynı"):
        rd.kaydet(roman, 2, t1, hakem_json(tmp_path / "h1.json", 6.0, "eksik"), "", 8.0, 4)
    t2 = yaz(tmp_path / "t2.md", kaynak + "\nDefne kapağı kapattı.\n")
    k2 = rd.kaydet(roman, 2, t2, hakem_json(tmp_path / "h2.json", 9.5), "ikinci", 8.0, 4)
    assert k2["karar"] == "dur-hedef" and k2["en_iyi_tur"] == 2
    assert "Sonu sıkılaştır" in rd.brief(roman, 2)
    durum = json_cikti(calistir("revizyon_dongusu.py", "durum", "--proje", roman, "--bolum", 2, "--json"))
    assert len(durum) == 2 and durum[-1]["karar"] == "dur-hedef"
    red = calistir("revizyon_dongusu.py", "kabul", "--proje", roman, "--bolum", 2, "--tur", 2)
    assert red.returncode == 2 and "onay" in red.stderr
    kabul = calistir("revizyon_dongusu.py", "kabul", "--proje", roman, "--bolum", 2, "--tur", 2, "--yazar-onayladi")
    assert kabul.returncode == 0, kabul.stderr
    assert (roman / "metin" / "bolum-002_kapagin-ici.md").read_text(encoding="utf-8").endswith("Defne kapağı kapattı.\n")
    anliklar = list((roman / ".hikaye" / "anliklar" / "kayitlar").glob("*.json"))
    assert anliklar, "kabul öncesi anlık görüntü alınmalı"


def test_dongu_plato_ve_tur_siniri() -> None:
    rd = modul_yukle("revizyon_dongusu.py")
    tur = lambda n, t: {"tur": n, "toplam": t, "bitmemis_isaret": 0, "acik_plan_maddesi": 0}  # noqa: E731
    assert rd.karar_ver([tur(1, 6.0), tur(2, 6.1), tur(3, 6.15)], 9.0, 10) == "dur-plato"
    assert rd.karar_ver([tur(1, 5.0), tur(2, 6.0)], 9.0, 2) == "dur-tur-siniri"
    assert rd.karar_ver([tur(1, 5.0), tur(2, 7.0)], 9.0, 5) == "devam"
    kapili = [{"tur": 1, "toplam": 9.5, "bitmemis_isaret": 2, "acik_plan_maddesi": 0}]
    assert rd.karar_ver(kapili, 8.0, 5) == "devam"


@pytest.mark.parametrize("icerik, ileti", [
    ({"olcutler": {}}, "eksik ölçüt"),
    ({"olcutler": {k: 11 for k in ("plan_sadakati", "gerilim", "karakter", "somutluk", "diyalog", "dil")}}, "1 ile 10"),
    ({"olcutler": {k: True for k in ("plan_sadakati", "gerilim", "karakter", "somutluk", "diyalog", "dil")}}, "1 ile 10"),
    ({"olcutler": {k: 5 for k in ("plan_sadakati", "gerilim", "karakter", "somutluk", "diyalog", "dil")},
      "plan_maddeleri": [{"durum": "belki"}]}, "durum"),
])
def test_dongu_hakem_dogrulama_hatalari(icerik: dict, ileti: str) -> None:
    rd = modul_yukle("revizyon_dongusu.py")
    with pytest.raises(rd.DonguHatasi, match=ileti):
        rd.hakem_dogrula(icerik)


# ---------------------------------------------------------------- turnuva.py


def test_turnuva_elo_sirasi_ve_degisen_dosya(roman: Path, tmp_path: Path) -> None:
    for e in "ABC":
        yaz(roman / ".hikaye" / "adaylar" / f"{e}.md", f"# Bölüm 3\n\nTaslak {e} metni.\n")
    arg = [f"--aday={e}=.hikaye/adaylar/{e}.md" for e in "ABC"]
    bas = calistir("turnuva.py", "baslat", "--proje", roman, "--ad", "bolum-03", *arg)
    assert bas.returncode == 0, bas.stderr
    t = modul_yukle("turnuva.py")
    veri = t.oku(roman, "bolum-03")
    assert len(veri["maclar"]) == 6  # 3 eşleşme × 2 sıra
    for mac in veri["maclar"]:
        kazanan = "A" if "A" in (mac["sol"], mac["sag"]) else "B"
        t.sonuc_kaydet(roman, "bolum-03", mac["no"], kazanan, "gerekçe")
    sira = t.siralama(t.oku(roman, "bolum-03"))
    assert [s["etiket"] for s in sira] == ["A", "B", "C"] and sira[0]["galibiyet"] == 4
    assert calistir("turnuva.py", "sirada", "--proje", roman, "--ad", "bolum-03").returncode == 1  # bitti
    yaz(roman / ".hikaye" / "adaylar" / "A.md", "değişti")
    with pytest.raises(t.TurnuvaHatasi, match="değişti"):
        t.sonuc_kaydet(roman, "bolum-03", 1, "berabere")


def test_turnuva_gecersiz_girdiler(roman: Path) -> None:
    yaz(roman / "a.md", "a")
    assert calistir("turnuva.py", "baslat", "--proje", roman, "--ad", "x", "--aday", "A=a.md").returncode == 2
    assert calistir("turnuva.py", "baslat", "--proje", roman, "--ad", "../kotu", "--aday", "A=a.md",
                    "--aday", "B=a.md").returncode == 2
    assert calistir("turnuva.py", "baslat", "--proje", roman, "--ad", "x", "--aday", "A=yok.md",
                    "--aday", "B=a.md").returncode == 2
    assert calistir("turnuva.py", "siralama", "--proje", roman, "--ad", "olmayan").returncode == 2


# ---------------------------------------------------------------- ses_izi.py


def test_ses_izi_profil_ve_sapma(roman: Path, tmp_path: Path) -> None:
    si = modul_yukle("ses_izi.py")
    cikar = calistir("ses_izi.py", "cikar", "--proje", roman)
    assert cikar.returncode == 0, cikar.stderr
    profil = json.loads((roman / "kurgu" / "ses-izi.json").read_text(encoding="utf-8"))
    assert profil["kelime"] > 150 and {"cumle_ort", "diyalog_orani", "zarf_fiil"} <= set(profil["ortalama"])
    ayni = si.karsilastir(profil, (roman / "metin" / "bolum-001_durmus-saatler.md").read_text(encoding="utf-8"))
    uzun = " ".join(["Adam uzun ve dolambaçlı bir yolda, kimseye bir şey söylemeden, eski evlerin arasından, "
                     "rüzgârın getirdiği tozlu kokuları içine çekerek ve geçmişi düşünerek yürüdü" + " durdu" * 5 + "."] * 20)
    farkli = si.karsilastir(profil, uzun)
    assert ayni["benzerlik"] > farkli["benzerlik"] and farkli["sapmalar"]
    kisa = calistir("ses_izi.py", "cikar", "--dosya", yaz(tmp_path / "k.md", "Kısa metin."))
    assert kisa.returncode == 2 and "kısa" in kisa.stderr
    karsi = calistir("ses_izi.py", "karsilastir", "--proje", roman, "--dosya", yaz(tmp_path / "u.md", uzun), "--json")
    assert karsi.returncode in (0, 1) and "benzerlik" in json_cikti(karsi)
    bozuk = calistir("ses_izi.py", "karsilastir", "--profil", yaz(tmp_path / "p.json", "[]"), "--dosya", tmp_path / "u.md")
    assert bozuk.returncode == 2


def test_ses_izi_turkce_zarf_fiil_ve_aralik() -> None:
    si = modul_yukle("ses_izi.py")
    oz = si.ozellikler("Eve gelince oturdu. Kapıyı açıp baktı. Gülerek konuştu. Yürürken düşündü. " * 10)
    assert oz["zarf_fiil"] > 0
    assert si._bolum_araligi("1-3,7") == {1, 2, 3, 7}
    with pytest.raises(si.SesHatasi):
        si._bolum_araligi("5-2")


# ---------------------------------------------------------------- anlik_goruntu.py


def test_anlik_al_fark_geri_yukle_ve_dogrula(roman: Path) -> None:
    ag = modul_yukle("anlik_goruntu.py")
    ilk = ag.anlik_al(roman, "ilk")
    assert ilk and ilk["dosya_sayisi"] > 10 and ilk["metin_kelime"] > 500
    assert ag.anlik_al(roman) is None  # değişiklik yok
    bolum = roman / "metin" / "bolum-001_durmus-saatler.md"
    eski = bolum.read_text(encoding="utf-8")
    bolum.write_text(eski.replace("Kepenk", "Demir kepenk"), encoding="utf-8")
    ikinci = ag.anlik_al(roman, "ikinci", zaman=dt.datetime(2030, 1, 1, 10, 0, 0))
    assert ikinci and ikinci["yeni_nesne"] == 1
    fark = ag.fark_hesapla(roman, "son~1", "son", kelime=True)
    assert fark["ozet"]["degisen_dosya"] == ["metin/bolum-001_durmus-saatler.md"] and fark["ozet"]["eklenen_kelime"] == 2
    assert fark["ozet"]["silinen_kelime"] == 1
    assert "[-Kepenk,-] {+Demir kepenk,+}" in "\n".join(fark["ayrinti"])
    bolum.write_text("bozuldu", encoding="utf-8")
    sonuc = ag.geri_yukle(roman, "son~1", dosya="metin/bolum-001_durmus-saatler.md")
    assert bolum.read_text(encoding="utf-8") == eski and sonuc
    assert len(ag.kayitlar(roman)) == 3  # güvenlik görüntüsü alındı
    assert ag.dogrula(roman) == []
    nesne = next(p for p in (roman / ".hikaye" / "anliklar" / "nesneler").rglob("*") if p.is_file())
    nesne.write_bytes(b"kurcalandi")
    assert ag.dogrula(roman)
    assert calistir("anlik_goruntu.py", "dogrula", "--proje", roman).returncode == 1


def test_anlik_guvenlik_ve_temizlik(roman: Path) -> None:
    ag = modul_yukle("anlik_goruntu.py")
    for i in range(4):
        (roman / "notlar").mkdir(exist_ok=True)
        yaz(roman / "notlar" / "n.md", f"not {i}")
        ag.anlik_al(roman, f"{i}", zaman=dt.datetime(2030, 1, 1, 10, 0, i))
    with pytest.raises(ag.AnlikHatasi, match="güvensiz|dışına"):
        ag._guvenli_hedef(roman.resolve(), "../disari.md")
    with pytest.raises(ag.AnlikHatasi):
        ag._guvenli_hedef(roman.resolve(), "/etc/passwd")
    hepsi = calistir("anlik_goruntu.py", "geri-yukle", "--proje", roman, "--kimlik", "son~1", "--hepsi")
    assert hepsi.returncode == 2 and "onay" in hepsi.stderr
    sonuc = ag.temizle(roman, 2)
    assert len(ag.kayitlar(roman)) == 2 and sonuc
    assert ag.dogrula(roman) == []
    with pytest.raises(ag.AnlikHatasi):
        ag.kimlik_coz(roman, "son~9")
    assert calistir("anlik_goruntu.py", "fark", "--proje", roman, "--a", "yok-boyle").returncode == 2


# ---------------------------------------------------------------- yazim_istatistik.py


def test_istatistik_hedef_kayit_seri_ve_tahmin(roman: Path) -> None:
    yi = modul_yukle("yazim_istatistik.py")
    yi.hedef_ayarla(roman, 10000, "2030-01-31", 500)
    gun = dt.date(2030, 1, 1)
    yi.kaydet(roman, gun)  # başlangıç çizgisi
    bolum = roman / "metin" / "bolum-003_yeni.md"
    for i in range(1, 4):
        yaz(bolum, "# Bölüm 3\n\n" + "kelime " * (300 * i) + "\n")
        yi.kaydet(roman, gun + dt.timedelta(days=i))
    v = yi.pano_verisi(roman, gun + dt.timedelta(days=3))
    assert v["seri_gun"] == 3 and v["bugun_yazilan"] == 300 and v["son_7_gun_ortalama"] == round(900 / 7)
    assert v["kalan_kelime"] == 10000 - v["toplam_kelime"] and v["tahmini_bitis"] > "2030-01-04"
    assert v["gereken_gunluk"] > 0 and v["gunluk_hedef_yuzde"] == 60
    assert next(b for b in v["bolumler"] if b["no"] == 1)["hedef"]
    html = calistir("yazim_istatistik.py", "pano", "--proje", roman, "--html", roman / "p.html", "--bugun", "2030-01-04")
    assert html.returncode == 0 and "<svg" in (roman / "p.html").read_text(encoding="utf-8")


def test_istatistik_tahmin_korumasi_ve_turkce_bicim(roman: Path) -> None:
    yi = modul_yukle("yazim_istatistik.py")
    yi.hedef_ayarla(roman, 2_000_000, None, 700)
    gun = dt.date(2030, 3, 1)
    yi.kaydet(roman, gun)
    bolum = roman / "metin" / "bolum-003_yeni.md"
    yaz(bolum, "# Bölüm 3\n\n" + "kelime " * 20 + "\n")
    yi.kaydet(roman, gun + dt.timedelta(days=1))
    v = yi.pano_verisi(roman, gun + dt.timedelta(days=1))
    assert "tahmini_bitis" not in v and not v.get("tahmini_bitis_uzak")  # tek günlük veriyle tahmin yok
    metin = yi.metin_panosu(v)
    assert "en az 3 gününde" in metin and "tamamlanan %3" in metin and "'i)" not in metin
    for i in range(2, 5):  # dört gün, günde 20 kelime: 2 milyon kelime on yıldan uzun sürer
        yaz(bolum, "# Bölüm 3\n\n" + "kelime " * (20 * i) + "\n")
        yi.kaydet(roman, gun + dt.timedelta(days=i))
    v = yi.pano_verisi(roman, gun + dt.timedelta(days=4))
    assert v.get("tahmini_bitis_uzak") and "tahmini_bitis" not in v
    assert "on yıldan uzun" in yi.metin_panosu(v)
    assert yi.yuzde(1.5) == "%1,5" and yi.yuzde(100) == "%100"


@pytest.mark.parametrize("arg", [["--toplam", "5"], ["--bitis", "31-12-2030"], ["--gunluk", "0"], []])
def test_istatistik_gecersiz_hedef(roman: Path, arg: list[str]) -> None:
    assert calistir("yazim_istatistik.py", "hedef", "--proje", roman, *arg).returncode == 2


def test_istatistik_bozuk_defter(roman: Path) -> None:
    yaz(roman / ".hikaye" / "istatistik.json", "{bozuk")
    sonuc = calistir("yazim_istatistik.py", "pano", "--proje", roman)
    assert sonuc.returncode == 2 and "istatistik.json" in sonuc.stderr
