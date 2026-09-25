#!/usr/bin/env python3
"""Dönem uyumsuzluğu (anakronizm) denetimi: hikâyenin geçtiği yılda henüz olmayan ya da artık
kalkmış kavram, kurum, ad ve eşyaları bulur. Osmanlı'nın son dönemi ve erken Cumhuriyet
romanları için hazırlanmıştır; yakın dönem teknolojileri de listededir.

Kullanım::

    donem_denetle.py --yil 1925 --dosya metin/bolum-003_x.md [...]
    donem_denetle.py --proje KITAP [--bolum 3]       # yıl: plan/genel-plan.md "- Dönem: 1919–1923"
    donem_denetle.py --liste                          # denetlenen bütün kavramlar ve yılları

Yıl aralığı verildiğinde ("1919–1923"), henüz olmayanlar için aralığın sonu, kalkmış
olanlar için başı esas alınır. Proje kökündeki ``.donem-istisnalari`` dosyasına (her
satıra bir kavram) yazılanlar denetlenmez; ör. bir karakterin geleceği anlattığı bir
sahne. Bulgular bir tarih uzmanının yerini tutmaz, yazarı ilgili yere bakmaya çağırır;
yıllar resmî yasa ve kuruluş tarihleridir (açıklamada belirtilir).

Çıkış kodu: 0 bulgu yok ya da yalnızca uyarı, 1 henüz olmayan bir şey hikâye yılından en az 5 yıl sonra
ortaya çıkmışsa ("hata"), 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

H = "a-zçğıöşüâîû"
# (desen [Türkçe küçük harfli metinde], ilk yıl, açıklama). Desen kök olarak aranır; ekler serbesttir.
HENUZ_YOK: list[tuple[str, int, str]] = [
    (r"soyad", 1934, "Soyadı Kanunu (Kanun no. 2525, 21 Haziran 1934); öncesinde resmî soyadı yoktu, lakap ve baba adı kullanılırdı"),
    (r"atatürk", 1934, "Mustafa Kemal'e Atatürk soyadı 24 Kasım 1934'te verildi (Kanun no. 2587); öncesinde Gazi Mustafa Kemal Paşa"),
    (r"inönü", 1934, "İsmet Paşa İnönü soyadını 1934'te aldı (Soyadı Kanunu); öncesinde İsmet Paşa"),
    (r"bayan\b|bay [A-ZÇĞİÖŞÜa-zçğıöşü]", 1934, "Bay/Bayan hitapları 1934'te lakap ve unvanların kaldırılmasıyla yaygınlaştı (Kanun no. 2590)"),
    (r"cumhurbaşkan", 1923, "Cumhuriyet 29 Ekim 1923'te ilan edildi"),
    (r"(?:latin|yeni) harfler", 1928, "Harf Devrimi: Kanun no. 1353, 1 Kasım 1928"),
    (r"harf devrim|harf inkılab", 1928, "Harf Devrimi 1928"),
    (r"medeni kanun", 1926, "Türk Medeni Kanunu 17 Şubat 1926'da kabul edildi, 4 Ekim 1926'da yürürlüğe girdi"),
    (r"şapka kanun|şapka inkılab", 1925, "Şapka İktisası Hakkında Kanun (no. 671), 25 Kasım 1925"),
    (r"radyo(?!aktif|aktiv|loj|log|terapi|grafi|skopi)", 1927, "Türkiye'de düzenli radyo yayını İstanbul Radyosu ile 6 Mayıs 1927'de başladı"),
    (r"televizyon", 1952, "Türkiye'de ilk televizyon deneme yayını İTÜ, 1952; TRT yayını 31 Ocak 1968"),
    (r"\btrt\b", 1964, "TRT 1 Mayıs 1964'te kuruldu"),
    (r"telgraf", 1855, "Osmanlı'da ilk telgraf hattı 1855"),
    (r"telefon", 1911, "İstanbul'da ilk telefon santrali 1911; öncesinde çok sınırlı kullanım"),
    (r"sinema", 1896, "İstanbul'da ilk sinema gösterimi 1896 sonu"),
    (r"elektrikli tramvay", 1914, "İstanbul'da elektrikli tramvay Şubat 1914"),
    (r"tramvay", 1871, "İstanbul'da atlı tramvay 1871"),
    (r"tanzimat", 1839, "Tanzimat Fermanı 3 Kasım 1839"),
    (r"meşrutiyet", 1876, "I. Meşrutiyet 23 Aralık 1876"),
    (r"kurtuluş savaş|istiklal harb", 1919, "Millî Mücadele 1919'da başladı"),
    (r"milli piyango|millî piyango", 1939, "Millî Piyango adı 1939'dan (öncesinde Tayyare Piyangosu, 1926)"),
    (r"naylon", 1938, "Naylon 1938'de icat edildi, 1939'dan sonra piyasaya çıktı"),
    (r"penisilin", 1942, "Penisilin 1928'de bulundu, tedavide yaygın kullanımı 1940'ların başından sonra"),
    (r"bilgisayar", 1960, "Türkiye'de ilk bilgisayar 1960 (Karayolları)"),
    (r"kaset", 1963, "Ses kaseti 1963'te tanıtıldı"),
    (r"kredi kart", 1968, "Türkiye'de ilk kredi kartı 1968"),
    (r"boğaz(?:içi)? köprü", 1973, "Boğaziçi Köprüsü 30 Ekim 1973'te açıldı"),
    (r"bankamatik|\batm\b", 1982, "Türkiye'de ilk ATM 1982"),
    (r"fatih sultan mehmet köprü", 1988, "Fatih Sultan Mehmet Köprüsü 3 Temmuz 1988'de açıldı"),
    (r"internet", 1993, "Türkiye'nin internete bağlanması 12 Nisan 1993 (ODTÜ)"),
    (r"cep telefon", 1994, "Türkiye'de GSM hizmeti 1994"),
    (r"\bsms\b", 1994, "SMS, GSM ile birlikte 1990'ların ortasında"),
    (r"e-posta|\bemail\b|\be-mail\b", 1993, "E-posta Türkiye'de internetle birlikte (1993 sonrası) yaygınlaştı"),
    (r"facebook", 2004, "Facebook 2004"),
    (r"youtube", 2005, "YouTube 2005"),
    (r"twitter", 2006, "Twitter 2006"),
    (r"akıllı telefon|iphone", 2007, "iPhone 2007; akıllı telefonlar 2007 sonrası yaygınlaştı"),
    (r"whatsapp", 2009, "WhatsApp 2009"),
    (r"instagram", 2010, "Instagram 2010"),
    (r"\beuro\b|\bavro\b", 1999, "Avro 1999'da hesap birimi, 2002'de nakit oldu"),
]
# (desen, kalktığı yıl, açıklama): bu yıldan sonra geçerli/güncel bir kurum gibi anılması şüphelidir.
KALKTI: list[tuple[str, int, str]] = [
    (r"padişah|saltanat", 1922, "Saltanat 1 Kasım 1922'de kaldırıldı"),
    (r"halife\b|halifeli|hilafet", 1924, "Hilafet 3 Mart 1924'te kaldırıldı (Kanun no. 431)"),
    (r"şeyhülislam", 1922, "Şeyhülislamlık makamı 1922'de kaldırıldı"),
    (r"medrese", 1924, "Medreseler Tevhid-i Tedrisat Kanunu ile 1924'te kapatıldı (Kanun no. 430)"),
    (r"tekke|zaviye", 1925, "Tekke ve zaviyeler 30 Kasım 1925'te kapatıldı (Kanun no. 677)"),
    (r"fes(?:i|in|ini|inde|inden|iyle|e|le|ler|leri|lerini|leriyle|li|lı|siz|çi|çiler|ten|te|de|den)?(?![a-zçğıöşüâîû])", 1925, "Şapka Kanunu (25 Kasım 1925) sonrasında erkeklerin fes giymesi yasaklandı"),
    (r"rumi takvim|rumi tarih", 1926, "Uluslararası takvim 1 Ocak 1926'da yürürlüğe girdi (Kanun no. 698)"),
    (r"alaturka saat|ezani saat", 1926, "Uluslararası saat 1 Ocak 1926'da yürürlüğe girdi (Kanun no. 697); ezani saat camilerde sürdü"),
    (r"arşın|okka|dirhem", 1933, "Metrik sisteme geçiş: Ölçüler Kanunu (no. 1782, 1931), 1 Ocak 1933'ten itibaren zorunlu; halk ağzında bir süre yaşadı"),
    (r"\bytl\b|yeni türk lirası", 2009, "YTL 2005–2008 arasında kullanıldı, 1 Ocak 2009'da yeniden Türk lirası adı geldi"),
]
HATA_FARKI = 5


class DonemHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def yil_coz(deger: str) -> tuple[int, int]:
    yillar = [int(y) for y in re.findall(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)", deger)]
    if not yillar:
        raise DonemHatasi(f"yıl bulunamadı: {deger!r} (ör. 1925 ya da 1919–1923)")
    return min(yillar), max(yillar)


def proje_yili(proje: Path) -> tuple[int, int]:
    for goreli in ("plan/genel-plan.md", "kurgu/tur-konumu.md"):
        yol = proje / goreli
        if yol.is_file():
            m = re.search(r"^[ \t]*[-*][ \t]+\**(?:Dönem|Hikâye yılı|Hikaye yılı|Yıl)\**[ \t]*:[ \t]*(.+)$",
                          dosya_oku.metin_oku(yol, uyar=False), re.M | re.I)
            if m:
                try:
                    return yil_coz(m.group(1))
                except DonemHatasi:
                    continue
    raise DonemHatasi("hikâyenin yılı bulunamadı: plan/genel-plan.md içine '- Dönem: 1925' satırı ekleyin ya da --yil verin")


def istisnalar(proje: Path | None) -> set[str]:
    if proje is None or not (proje / ".donem-istisnalari").is_file():
        return set()
    return {tk.tr_kucuk(s.strip()) for s in dosya_oku.metin_oku(proje / ".donem-istisnalari", uyar=False).splitlines()
            if s.strip() and not s.lstrip().startswith("#")}


def denetle_metin(metin: str, bas: int, son: int, dosya: str = "<metin>", haric: set[str] | None = None) -> list[dict[str, Any]]:
    haric = haric or set()
    bulgular = []
    satirlar = kitap_proje.satir_koruyan_govde(metin.replace("\r\n", "\n")).split("\n")
    kurallar = [(d, y, a, "henuz") for d, y, a in HENUZ_YOK if y > son] + \
               [(d, y, a, "kalkti") for d, y, a in KALKTI if y < bas]
    derli = [(re.compile(rf"(?<![{H}])(?:{d})"), y, a, t) for d, y, a, t in kurallar]
    for no, satir in enumerate(satirlar, start=1):
        kucuk = tk.tr_kucuk(satir)
        for desen, yil, aciklama, tur in derli:
            for m in desen.finditer(kucuk):
                kelime_sonu = re.match(rf"[{H}]*", kucuk[m.end():]).group(0)
                eslesen = (m.group(0) + kelime_sonu).strip()
                if any(eslesen.startswith(h) or h.startswith(m.group(0).strip()) for h in haric):
                    continue
                fark = (yil - son) if tur == "henuz" else (bas - yil)
                bulgular.append({
                    "dosya": dosya, "satir": no, "ifade": satir[m.start():m.start() + len(eslesen)] or eslesen,
                    "tur": tur, "yil": yil, "aciklama": aciklama,
                    # Kalkmış kurumu anmak (ör. "eski medrese") doğal olabilir: yalnızca uyarı.
                    "duzey": "hata" if tur == "henuz" and fark >= HATA_FARKI else "uyari",
                    "ileti": (f"{yil} yılından önce yoktu" if tur == "henuz" else f"{yil} yılında kalktı/değişti")
                             + f"; hikâye {bas if bas == son else f'{bas}–{son}'}",
                })
    return bulgular


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Dönem uyumsuzluğu (anakronizm) denetimi.")
    ayr.add_argument("--yil", help="hikâyenin yılı ya da aralığı (ör. 1925 ya da 1919-1923)")
    ayr.add_argument("--dosya", type=Path, nargs="+", help="denetlenecek metin dosyaları")
    ayr.add_argument("--proje", type=Path, help="kitap klasörü (yıl ve bölümler buradan okunur)")
    ayr.add_argument("--bolum", type=int, help="yalnızca bu bölümü denetle (--proje ile)")
    ayr.add_argument("--liste", action="store_true", help="denetlenen kavramları ve yıllarını listele")
    ayr.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    arg = ayr.parse_args(argv)
    if arg.liste:
        for d, y, a in HENUZ_YOK:
            print(f"{y} öncesinde yok    {d:<40} {a}")
        for d, y, a in KALKTI:
            print(f"{y} sonrasında kalktı {d:<40} {a}")
        return 0
    try:
        if not arg.dosya and not arg.proje:
            raise DonemHatasi("--dosya ya da --proje gerekli")
        if arg.bolum is not None and not arg.proje:
            raise DonemHatasi("--bolum yalnızca --proje ile kullanılır")
        if arg.proje:
            kitap_proje.proje_klasoru(arg.proje)
        bas, son = yil_coz(arg.yil) if arg.yil else proje_yili(arg.proje)
        if arg.dosya:
            hedefler = [(str(y), dosya_oku.metin_oku(y)) for y in arg.dosya]
        else:
            bolumler = [b for b in kitap_proje.bolumler(arg.proje, zorunlu=True) if arg.bolum is None or b.no == arg.bolum]
            if not bolumler:
                raise DonemHatasi(f"{arg.bolum}. bölüm bulunamadı")
            hedefler = [(b.yol.name, b.metin) for b in bolumler]
        haric = istisnalar(arg.proje)
        bulgular = [b for ad, metin in hedefler for b in denetle_metin(metin, bas, son, ad, haric)]
    except (DonemHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    if arg.json:
        print(json.dumps({"yil": [bas, son], "bulgular": bulgular}, ensure_ascii=False, indent=2))
    else:
        donem = str(bas) if bas == son else f"{bas}–{son}"
        if not bulgular:
            print(f"Dönem denetimi ({donem}): uyumsuzluk bulunmadı.")
        for b in bulgular:
            isaret = "✗" if b["duzey"] == "hata" else "!"
            print(f"{isaret} {b['dosya']}:{b['satir']}: “{b['ifade']}” — {b['ileti']}. {b['aciklama']}.")
        if bulgular:
            print(f"\nToplam {len(bulgular)} bulgu (dönem: {donem}). Bilinçli kullanımları .donem-istisnalari dosyasına yazın.")
    return 1 if any(b["duzey"] == "hata" for b in bulgular) else 0


if __name__ == "__main__":
    sys.exit(main())
