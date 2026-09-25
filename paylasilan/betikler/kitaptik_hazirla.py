#!/usr/bin/env python3
"""Kitaptik (https://kitaptik.com) için yayın hazırlığı: denetim, toplu yükleme DOCX'i ve yayın paketi.

Kitaptik, Türkçe kitap yazma ve okuma platformudur. Bu betik bitmiş (ya da yayımlanmaya hazır)
bir roman projesini Kitaptik'in yazar ekranına uygun hâle getirir; **siteye giriş yapmaz, dosya
yüklemez**. Yükleme ve yayımlama yazarın kendi hesabından elle yapılır.

Kullanım::

    kitaptik_hazirla.py kategoriler [--json]
    kitaptik_hazirla.py baslat   --proje KITAP [--ana-kategori Roman] [--zorla]
    kitaptik_hazirla.py denetle  --proje KITAP [--kapak KAPAK] [--bolum-siniri 10000] [--json]
    kitaptik_hazirla.py paket    --proje KITAP [--cikti KLASOR] [--kapak KAPAK] [--yazar "Ad Soyad"]
                                 [--bolum-siniri 10000] [--taslak] [--json]

Sınırlar ve biçimler (25 Eylül 2026'da Kitaptik'in yazar ekranı ve yardım sayfalarıyla doğrulandı;
değişebilir, yayımlamadan önce sitede kontrol edin):

* Toplu içe aktarma yalnızca Word ``.docx`` kabul eder (eski ``.doc`` değil), dosya en çok 20 MB.
  Word'deki her **Başlık 1** yeni bölüm sayılır; alt başlıklar kalın paragrafa, görseller atılır.
* Bölüm başına en çok 10.000 kelime, bölüm başlığı en çok 77 karakter; tek seferde en çok 500,
  kitapta en çok 1.200 bölüm.
* Kitap açıklaması 2.500, "Neden okumalı?" 333, ek telif notu 1.000 karakter; en çok 3 alt kategori
  (hepsi aynı ana kategoriden); etiket başına 40 karakter, en çok 30 etiket; dil: Türkçe.
* Kapak: JPEG, PNG, WebP, HEIC ya da AVIF; en çok 20 MB, hareketsiz, en az 100×100 piksel;
  önerilen ölçü 583×827 piksel (dikey).

Alt komutlar:

* ``kategoriler``: Kitaptik'in ana ve alt kategorileri.
* ``baslat``: ``yayin/kitaptik.md`` yayın bilgisi dosyasını projeden önerilerle oluşturur.
* ``denetle``: yayın bilgisi, bölüm uzunlukları, başlıklar, kapak ve Topluluk Kuralları açısından
  dikkat gerektiren içerik sinyallerini raporlar (anahtar sözcük taraması; karar yazarındır).
* ``paket``: ``yayin/kitaptik/`` altına toplu yükleme DOCX'i (gerekirse birkaç parça), kitap
  bilgileri formu, karakter kartları, yayın kontrol listesi ve ``rapor.json`` yazar.

Çıkış kodu: 0 sorun yok, 1 hata düzeyinde bulgu var (paket yazılmaz), 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import struct
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import belge_yazicilar as by  # noqa: E402
import dosya_oku  # noqa: E402
import e_kitap_derle  # noqa: E402
import kitap_proje  # noqa: E402
import kurgu_ansiklopedisi as ka  # noqa: E402
import metin_analizi  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

SITE = "https://kitaptik.com"
DOGRULAMA_TARIHI = "25 Eylül 2026"
BILGI_DOSYASI = Path("yayin") / "kitaptik.md"

SINIR = {
    "bolum_kelime": 10_000,
    "bolum_basligi": 77,
    "toplu_bolum": 500,
    "kitap_bolum": 1_200,
    "docx_bayt": 20 * 1024 * 1024,
    "kitap_basligi_en_az": 2,
    "kitap_basligi_en_fazla": 255,
    "aciklama": 2_500,
    "neden_okumali": 333,
    "telif_notu": 1_000,
    "etiket_uzunluk": 40,
    "etiket_sayisi": 30,
    "alt_kategori": 3,
    "kapak_bayt": 20 * 1024 * 1024,
    "kapak_en_az": 100,
    "ucretli_en_az_fiyat": 10,
    "ucretli_en_az_bolum": 4,
}
KAPAK_ONERILEN = (583, 827)
ONERILEN_ETIKET_UST = 15
KISA_ACIKLAMA = 150

KATEGORILER: dict[str, list[str]] = {
    "Roman": ["Aşk", "Genç Kurgu", "Fan Kurgu", "Fantastik", "Bilim Kurgu", "Korku", "Gerilim", "Polisiye ve Gizem",
              "Macera", "Tarihi", "Toplumsal", "Psikolojik", "Dram", "Mizah"],
    "Öykü": ["Durum Öyküsü", "Olay Öyküsü", "Küçürek Öykü", "Bağlantılı Öyküler", "Aşk Öyküleri",
             "Korku ve Doğaüstü Öyküler", "Polisiye Öyküler", "Bilim Kurgu Öyküleri", "Fantastik Öyküler",
             "Tarihî Öyküler", "Mizah ve Hiciv Öyküleri", "Masalsı Öyküler", "Deneysel Öykü"],
    "Şiir": ["Serbest Şiir", "Hece Ölçüsü Şiiri", "Âşık Tarzı Halk Şiiri", "Divan / Aruz Şiiri",
             "Sone ve Kalıp Biçimler", "Haiku ve Kısa Şiir", "Mensur Şiir", "Epik Şiir ve Destan",
             "Satirik Şiir (Taşlama)", "Dinî-Tasavvufi Şiir", "Çocuk Şiiri ve Tekerleme", "Şarkı Sözü ve Rap Sözleri",
             "Akrostiş ve Deneysel Şiir"],
    "Deneme": ["Klasik Deneme", "Edebî Deneme", "Felsefî Deneme", "Eleştiri ve İnceleme", "Gezi Yazısı (Seyahatname)",
               "Portre Yazıları", "Sohbet Yazıları", "Röportaj ve Mülakat", "Köşe Yazısı Derlemesi", "Günlük (Günce)",
               "Toplumsal ve Politik Deneme", "İnanç ve Maneviyat Denemeleri"],
    "Mektup": ["Mektup-Roman", "Edebî Mektuplaşma", "Yazar Mektupları", "Açık Mektup", "Öğüt Mektupları"],
    "Sözler (Aforizma)": ["Aforizma", "Hikemî Sözler (Vecize)", "Epigram", "Fragmanlar", "Not Defteri Yazıları",
                          "Alıntı Derlemesi", "Atasözü ve Deyim Derlemeleri", "Nükte ve Latife",
                          "Kişisel Sözlük (Tanımlar)", "Duvar Yazıları ve Sloganlar"],
    "Kişisel Gelişim": ["Motivasyon ve İlham", "Alışkanlık, Disiplin ve Hedefler", "Üretkenlik ve Zaman Yönetimi",
                        "Özgüven ve Kendini Tanıma", "Duygusal Zeka ve Duygu Yönetimi",
                        "Stres, Kaygı ve Zihinsel Dayanıklılık", "İletişim ve Sosyal Beceriler", "İlişkiler ve Aile",
                        "Ebeveynlik ve Çocuk Yetiştirme", "Kariyer ve İş Hayatı",
                        "Para Yönetimi ve Finansal Okuryazarlık", "Sağlıklı Yaşam ve Zindelik", "Yaratıcılık ve Yazarlık"],
    "Spiritüel (Dini)": ["Kur'an, Tefsir ve Meal", "Hadis ve Sünnet", "İlmihal ve İbadet Rehberi",
                         "İman, Akaid ve Kelam", "Siyer ve Peygamber Kıssaları", "Dua, Zikir ve Münacat",
                         "Tasavvuf ve Mistisizm", "Dinî Hikâye ve Menkıbeler", "Vaaz ve İrşat Yazıları",
                         "Dinler Tarihi ve Karşılaştırmalı Din", "Din Felsefesi ve İnanç Sorgulamaları",
                         "Meditasyon ve Mindfulness", "Modern Maneviyat ve İçsel Yolculuk"],
    "Dünya Klasikleri": ["Türk Klasikleri", "Rus Klasikleri", "İngiliz Klasikleri", "Fransız Klasikleri",
                         "Amerikan Klasikleri", "Alman Klasikleri", "İtalyan Klasikleri",
                         "İspanyol ve Latin Amerika Klasikleri", "İskandinav ve Kuzey Avrupa Klasikleri",
                         "Antik Yunan ve Latin Klasikleri", "Orta Doğu ve Fars Klasikleri", "Hint ve Uzak Doğu Klasikleri",
                         "Orta ve Doğu Avrupa Klasikleri", "Diğer Avrupa Klasikleri"],
    "Diğer": ["Tarih", "Biyografi ve Anı", "Bilim ve Doğa", "Psikoloji ve İnsan Davranışı", "Felsefe ve Düşünce",
              "Toplum ve Siyaset", "Teknoloji ve Yazılım", "Eğitim ve Ders Notları", "Sağlık ve Beslenme",
              "Ekonomi ve Girişimcilik", "Çocuk ve Gençlik", "Sanat ve Müzik", "Tiyatro ve Senaryo", "Yemek ve Mutfak"],
}
KATEGORI_TAKMA_ADLARI = {"öykü/hikâye": "Öykü", "öykü / hikâye": "Öykü", "hikâye": "Öykü", "hikaye": "Öykü",
                         "öyküler": "Öykü", "sözler": "Sözler (Aforizma)", "aforizma": "Sözler (Aforizma)",
                         "spiritüel": "Spiritüel (Dini)", "dini": "Spiritüel (Dini)", "klasikler": "Dünya Klasikleri"}

# Tür sözcüğü → (Roman alt kategorisi, Öykü alt kategorisi, önerilen etiket). Sıra önceliktir.
TUR_ESLEME: list[tuple[str, str, str | None, str]] = [
    (r"polisiye|gizem|dedektif|cinayet|suç", "Polisiye ve Gizem", "Polisiye Öyküler", "polisiye"),
    (r"psikolojik gerilim|gerilim|thriller", "Gerilim", "Polisiye Öyküler", "gerilim"),
    (r"korku|dehşet|doğaüstü|gotik", "Korku", "Korku ve Doğaüstü Öyküler", "korku"),
    (r"bilim ?kurgu|distopya|ütopya|uzay", "Bilim Kurgu", "Bilim Kurgu Öyküleri", "bilim kurgu"),
    (r"fantastik|büyü|ejderha|mitoloji", "Fantastik", "Fantastik Öyküler", "fantastik"),
    (r"osmanlı|cumhuriyet|tarih[iî]?|dönem romanı", "Tarihi", "Tarihî Öyküler", "tarihi roman"),
    (r"romantik|romans|aşk", "Aşk", "Aşk Öyküleri", "aşk"),
    (r"genç kurgu|genç yetişkin|gençlik", "Genç Kurgu", None, "genç kurgu"),
    (r"hayran kurgu|fan ?kurgu|fanfik", "Fan Kurgu", None, "hayran kurgu"),
    (r"macera|aksiyon", "Macera", None, "macera"),
    (r"mizah|komedi|hiciv", "Mizah", "Mizah ve Hiciv Öyküleri", "mizah"),
    (r"aile|dram", "Dram", None, "dram"),
    (r"psikolojik", "Psikolojik", None, "psikolojik"),
    (r"toplumsal|köy romanı|göç", "Toplumsal", None, "toplumsal"),
]

ROLLER = ("Ana karakter", "Yardımcı", "Düşman", "Anlatıcı", "Diğer")
ROL_ESLEME = [(r"ana karakter|başkahraman|kahraman|baş karakter|protagonist", "Ana karakter"),
              (r"düşman|karşı güç|kötü|antagonist|hasım", "Düşman"),
              (r"anlatıcı", "Anlatıcı"),
              (r"yardımcı|yan karakter|destek|sırdaş|akıl hocası", "Yardımcı")]
SPOILER_ALANLARI = {"sırrı", "öldüğü bölüm", "yarası", "karakter yayı"}
TANITIM_ALANLARI = ("meslek", "görünüş", "istediği", "ses")

# İçerik sinyalleri. Anahtar sözcük taraması ipucudur; bağlamı anlamaz, karar yazarındır.
# Sözcükler Kitaptik Topluluk Kuralları'nın madde başlıklarına göre bu paket için yazılmıştır.
SINYALLER: dict[str, tuple[str, str]] = {
    "argo": (r"\b(?:siktir\w*|sikey\w*|siker\w*|sikiş\w*|amına|amk|orospu\w*|piç(?:ler|lik|in|i)?|yavşak\w*|"
             r"pezevenk\w*|göt(?:ü|ün|üne|ünü|veren)?|ibne\w*)\b",
             "ağır argo ve küfür"),
    "cinsellik": (r"\b(?:seviş\w*|orgazm\w*|penis\w*|vajina\w*|erekte\w*|cinsel ilişki\w*|çırılçıplak)\b",
                  "ayrıntılı cinsellik"),
    "siddet": (r"\b(?:işkence\w*|boğazını kes\w*|kafasını kes\w*|bağırsak\w*|parçalanmış|kan gölü\w*|"
               r"beynini dağıt\w*|kurşunladı\w*)\b",
               "aşırı şiddet"),
    "madde": (r"\b(?:eroin\w*|kokain\w*|uyuşturucu\w*|esrar(?!engiz)\w*|bonzai\w*|metamfetamin\w*|ecstasy)\b",
              "madde kullanımı"),
    "tecavuz": (r"\b(?:tecavüz\w*|ırzına geç\w*)\b", "cinsel saldırı"),
    "intihar": (r"\b(?:intihar\w*|kendini öldür\w*|bileklerini kes\w*|kendine zarar\w*|canına kıy\w*|"
                r"kendini as(?:tı|acak|mak)\w*|anoreksi\w*|bulimi\w*)\b",
                "intihar ve kendine zarar"),
}
YETISKIN_ESIKLERI = {"argo": 5, "cinsellik": 3, "siddet": 4, "madde": 3, "tecavuz": 1}
TW_DESENI = re.compile(r"\[\s*(?:TW|CW)\s*:|tetikleyici uyarı|içerik uyarısı", re.I)
URL_DESENI = re.compile(r"https?://|\bwww\.[a-z0-9-]+\.", re.I)
GORSEL_DESENI = re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)")
TABLO_DESENI = re.compile(r"^\s*\|.*\|\s*$\n^\s*\|?\s*:?-{3,}", re.M)


class KitaptikHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


@dataclass
class Parca:
    """Kitaptik'e tek bölüm olarak gidecek metin (uzun bölümler birden çok parçaya bölünür)."""

    baslik: str
    bloklar: list[tuple[str, str]]
    kaynak_no: int
    kaynak_dosya: str
    sira: int = 1
    toplam: int = 1

    @property
    def kelime(self) -> int:
        return kelime_say(self.bloklar)


@dataclass
class Rapor:
    bulgular: list[dict[str, Any]] = field(default_factory=list)
    ozet: dict[str, Any] = field(default_factory=dict)

    def ekle(self, duzey: str, kimlik: str, ileti: str, **ek: Any) -> None:
        self.bulgular.append({"duzey": duzey, "kimlik": kimlik, "ileti": ileti, **ek})

    def sayi(self, duzey: str) -> int:
        return sum(1 for b in self.bulgular if b["duzey"] == duzey)

    def sozluk(self) -> dict[str, Any]:
        return {"ozet": {**self.ozet, "hata": self.sayi("hata"), "uyari": self.sayi("uyari"), "bilgi": self.sayi("bilgi")},
                "bulgular": self.bulgular, "kaynak": SITE, "dogrulama_tarihi": DOGRULAMA_TARIHI}


# ---------------------------------------------------------------- yardımcılar


def nfc(metin: str) -> str:
    return unicodedata.normalize("NFC", metin)


def js_uzunluk(metin: str) -> int:
    """Tarayıcının (JavaScript) saydığı karakter sayısı: UTF-16 kod birimi. Emoji iki sayılır."""
    return len(nfc(metin).encode("utf-16-le")) // 2


def kelime_say(bloklar: list[tuple[str, str]]) -> int:
    """Kitaptik'in saydığı gibi: biçim işaretleri atılır, boşluklarla ayrılan her parça bir kelimedir."""
    toplam = 0
    for tur, metin in bloklar:
        toplam += 3 if tur == "ayrac" else len(by.sade_metin(metin).split())
    return toplam


def kucuk(metin: str) -> str:
    return tk.tr_kucuk(nfc(metin))


def baslik_kisalt(baslik: str, sinir: int) -> str:
    baslik = nfc(re.sub(r"\s+", " ", baslik).strip())
    if js_uzunluk(baslik) <= sinir:
        return baslik
    kelimeler = baslik.split(" ")
    sonuc = ""
    for k in kelimeler:
        aday = f"{sonuc} {k}".strip()
        if js_uzunluk(aday) + 1 > sinir:
            break
        sonuc = aday
    if not sonuc:  # tek, çok uzun sözcük
        sonuc = baslik
        while js_uzunluk(sonuc) + 1 > sinir:
            sonuc = sonuc[:-1]
    return sonuc.rstrip(" ,;:—–-") + "…"


def etiketleri_ayir(metin: str) -> tuple[list[str], list[str]]:
    """Kitaptik'in etiket kuralı: virgül, # ya da noktalı virgül ayırır; büyük-küçük harf farkı yok sayılır.

    Döndürür: (kabul edilenler, 40 karakteri aştığı için düşecekler)."""
    kabul: list[str] = []
    uzun: list[str] = []
    gorulen: set[str] = set()
    for ham in re.split(r"[,\n;#]+", metin or ""):
        etiket = nfc(ham.strip())
        if not etiket:
            continue
        anahtar = kucuk(etiket)
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        if js_uzunluk(anahtar) > SINIR["etiket_uzunluk"]:
            uzun.append(etiket)
            continue
        kabul.append(etiket)
    return kabul, uzun


def kategori_adi(ad: str) -> str | None:
    ad = nfc(ad.strip())
    if not ad:
        return None
    for ana in KATEGORILER:
        if kucuk(ana) == kucuk(ad):
            return ana
    return KATEGORI_TAKMA_ADLARI.get(kucuk(ad))


def alt_kategori_adi(ana: str, ad: str) -> str | None:
    for alt in KATEGORILER.get(ana, []):
        if kucuk(alt) == kucuk(ad.strip()):
            return alt
    return None


# ---------------------------------------------------------------- yayın bilgisi dosyası

ALANLAR = {
    "kitap başlığı": "baslik", "kategori": "kategori", "alt kategoriler": "alt_kategoriler", "etiketler": "etiketler",
    "yetişkin içerik (18+)": "yetiskin", "kitap tamamlandı": "tamamlandi", "pdf indirme": "pdf_indirme", "dil": "dil",
    "ücretli": "ucretli", "fiyat (tl)": "fiyat", "yazar adı": "yazar",
}
BOLUMLER = {"açıklama": "aciklama", "neden okumalı?": "neden_okumali", "neden okumalı": "neden_okumali",
            "telif notu": "telif_notu"}
EVET = {"evet", "e", "var", "açık", "true", "1"}
HAYIR = {"hayır", "hayir", "h", "yok", "kapalı", "false", "0"}


def evet_hayir(deger: str) -> bool | None:
    d = kucuk(deger.strip())
    if d in EVET:
        return True
    if d in HAYIR:
        return False
    return None


def bilgi_oku(proje: Path) -> dict[str, Any] | None:
    yol = proje / BILGI_DOSYASI
    if not yol.is_file():
        return None
    ham = dosya_oku.metin_oku(yol, uyar=False)
    ham = re.sub(r"<!--.*?-->", "", ham, flags=re.S)
    bilgi: dict[str, Any] = {"_ham_alanlar": {}}
    bolum: str | None = None
    parcalar: dict[str, list[str]] = {}
    for satir in ham.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", satir)
        if m:
            bolum = BOLUMLER.get(kucuk(m.group(1)).rstrip(":"))
            if bolum:
                parcalar.setdefault(bolum, [])
            continue
        if bolum:
            parcalar[bolum].append(satir)
            continue
        m = re.match(r"^\s*[-*]\s*([^:]+?)\s*:\s*(.*?)\s*$", satir)
        if m and kucuk(m.group(1)) in ALANLAR:
            anahtar = ALANLAR[kucuk(m.group(1))]
            bilgi[anahtar] = m.group(2)
            bilgi["_ham_alanlar"][anahtar] = m.group(2)
    for anahtar, satirlar in parcalar.items():
        bilgi[anahtar] = nfc("\n".join(satirlar).strip())
    return bilgi


def tur_metni(proje: Path) -> str:
    parcalar = []
    for yol, desen in ((proje / "plan" / "genel-plan.md", r"^\s*[-*]\s*Tür\s*:\s*(.+)$"),
                       (proje / "kurgu" / "tur-konumu.md", r"^\s*[-*]\s*(?:Ana|Yan) tür\s*:\s*(.+)$")):
        if yol.is_file():
            try:
                parcalar += re.findall(desen, dosya_oku.metin_oku(yol, uyar=False), re.M | re.I)
            except dosya_oku.DosyaHatasi:
                continue
    return " ".join(parcalar)


def kategori_oner(tur: str, ana: str = "Roman") -> tuple[str, list[str], list[str]]:
    """Tür metninden (ana kategori, en çok 3 alt kategori, etiket önerileri) çıkarır."""
    kucuk_tur = kucuk(tur)
    altlar: list[str] = []
    etiketler: list[str] = []
    for desen, roman_alt, oyku_alt, etiket in TUR_ESLEME:
        if re.search(desen, kucuk_tur):
            alt = roman_alt if ana == "Roman" else oyku_alt if ana == "Öykü" else None
            if alt and alt not in altlar:
                altlar.append(alt)
            if etiket not in etiketler:
                etiketler.append(etiket)
    return ana, altlar[:SINIR["alt_kategori"]], etiketler


def ozu_bul(proje: Path) -> str:
    yol = proje / "plan" / "genel-plan.md"
    if not yol.is_file():
        return ""
    try:
        metin = dosya_oku.metin_oku(yol, uyar=False)
    except dosya_oku.DosyaHatasi:
        return ""
    m = re.search(r"^\s*[-*]\s*Tek cümlelik öz\s*:\s*(.+)$", metin, re.M | re.I)
    return m.group(1).strip() if m else ""


def baslat(proje: Path, ana_kategori: str | None = None, zorla: bool = False) -> Path:
    kitap_proje.proje_klasoru(proje)
    yol = proje / BILGI_DOSYASI
    if yol.exists() and not zorla:
        raise KitaptikHatasi(f"{yol} zaten var; üzerine yazmak için --zorla kullanın")
    ana = kategori_adi(ana_kategori) if ana_kategori else "Roman"
    if ana is None:
        raise KitaptikHatasi(f"bilinmeyen ana kategori: {ana_kategori!r}. Liste: kitaptik_hazirla.py kategoriler")
    ana, altlar, etiketler = kategori_oner(tur_metni(proje), ana)
    oz = ozu_bul(proje)
    bolumler = kitap_proje.bolumler(proje)
    satirlar = [
        "# Kitaptik Yayın Bilgileri", "",
        f"> Bu dosyayı `kitaptik_hazirla.py denetle` ve `paket` okur. Alanlar Kitaptik'in \"Kitap Bilgileri\" formuyla aynı",
        f"> sıradadır. Sınırlar {DOGRULAMA_TARIHI} tarihinde doğrulandı; yayımlamadan önce sitede kontrol edin.", "",
        f"- Kitap başlığı: {kitap_proje.kitap_basligi(proje)}",
        "- Yazar adı: ",
        f"- Kategori: {ana}",
        f"- Alt kategoriler: {', '.join(altlar)}",
        f"- Etiketler: {', '.join(etiketler)}",
        "- Dil: Türkçe",
        "- Yetişkin içerik (18+): hayır",
        "- Kitap tamamlandı: hayır",
        "- PDF indirme: evet",
        "- Ücretli: hayır",
        "- Fiyat (TL): ",
        "",
        "## Açıklama",
        "",
        "<!-- Kitabın arka kapak yazısı: en çok 2.500 karakter. Sonu vermeyin; merak uyandırın. -->",
        oz,
        "",
        "## Neden okumalı?",
        "",
        "<!-- En çok 333 karakter: okura bu kitabı neden seçmesi gerektiğini tek paragrafta söyleyin. -->",
        "",
        "## Telif notu",
        "",
        "<!-- İsteğe bağlı, en çok 1.000 karakter: lisans, alıntı izinleri, atıf koşulları. -->",
        "",
    ]
    if not bolumler:
        satirlar.insert(4, "> Henüz bölüm yok; Kitaptik'te en az bir bölümü olan kitap yayımlanabilir.")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("\n".join(satirlar), encoding="utf-8", newline="\n")
    return yol


# ---------------------------------------------------------------- bölümler


def bolum_parcalari(proje: Path, sinir: int) -> tuple[list[Parca], list[dict[str, Any]]]:
    """Bölümleri okur, sınırı aşanları sahne ayraçlarına yakın yerlerden böler."""
    parcalar: list[Parca] = []
    sorunlar: list[dict[str, Any]] = []
    for b in kitap_proje.bolumler(proje, zorunlu=True):
        bol = e_kitap_derle.markdown_bolum(b.metin, b.baslik, b.yol.name)
        bloklar = [(t, nfc(m)) for t, m in bol.bloklar]
        if not bloklar:
            sorunlar.append({"duzey": "hata", "kimlik": "bos-bolum", "ileti": f"{b.yol.name}: bölümde metin yok",
                             "bolum": b.no})
            continue
        for tur, metin in bloklar:
            if tur != "ayrac" and len(by.sade_metin(metin).split()) > sinir:
                raise KitaptikHatasi(f"{b.yol.name}: tek paragraf {sinir} kelimeden uzun; paragrafı bölün")
        gruplar = _bol(bloklar, sinir)
        for i, grup in enumerate(gruplar, 1):
            parcalar.append(Parca(nfc(bol.baslik), grup, b.no, b.yol.name, i, len(gruplar)))
    return parcalar, sorunlar


def _bol(bloklar: list[tuple[str, str]], sinir: int) -> list[list[tuple[str, str]]]:
    toplam = kelime_say(bloklar)
    if toplam <= sinir:
        return [bloklar]
    hedef = toplam / math.ceil(toplam / sinir)
    gruplar: list[list[tuple[str, str]]] = []
    simdiki: list[tuple[str, str]] = []
    sayac = 0
    for blok in bloklar:
        k = kelime_say([blok])
        if simdiki and (sayac + k > sinir or (blok[0] == "ayrac" and sayac >= hedef * 0.85)
                        or (sayac >= hedef and blok[0] != "ayrac" and sayac + k > hedef * 1.15)):
            gruplar.append(simdiki)
            simdiki, sayac = [], 0
        if blok[0] == "ayrac" and not simdiki:
            continue  # yeni parça sahne ayracıyla başlamaz
        simdiki.append(blok)
        sayac += k
    if simdiki:
        gruplar.append(simdiki)
    # Sondaki ayraçları temizle; ilk blok "ilk paragraf" biçimini alsın.
    temiz = []
    for g in gruplar:
        while g and g[-1][0] == "ayrac":
            g.pop()
        if g:
            if g[0][0] == "p":
                g[0] = ("ilk", g[0][1])
            temiz.append(g)
    return temiz


def parca_basligi(p: Parca, sinir: int) -> str:
    ek = f" ({p.sira}/{p.toplam})" if p.toplam > 1 else ""
    return baslik_kisalt(p.baslik, sinir - js_uzunluk(ek)) + ek


# ---------------------------------------------------------------- içerik sinyalleri


def icerik_sinyalleri(metin: str) -> dict[str, list[tuple[int, str]]]:
    govde = kitap_proje.satir_koruyan_govde(metin)
    sonuc: dict[str, list[tuple[int, str]]] = {}
    for no, satir in enumerate(govde.split("\n"), 1):
        kucuk_satir = kucuk(satir)
        for ad, (desen, _) in SINYALLER.items():
            for m in re.finditer(desen, kucuk_satir):
                sonuc.setdefault(ad, []).append((no, m.group(0)))
    return sonuc


def tw_var(metin: str) -> bool:
    govde = [s for s in metin.split("\n") if s.strip() and not s.lstrip().startswith("#")]
    return any(TW_DESENI.search(s) for s in govde[:5])


# ---------------------------------------------------------------- kapak


def kapak_bul(proje: Path) -> Path | None:
    for ad in ("kapak.jpg", "kapak.jpeg", "kapak.png", "kapak.webp"):
        yol = proje / "kapak" / ad
        if yol.is_file():
            return yol
    return None


def gorsel_bilgisi(veri: bytes) -> dict[str, Any]:
    """Başlıktan biçim, boyut ve hareketlilik okur (yalnızca standart kütüphane)."""
    if veri[:8] == b"\x89PNG\r\n\x1a\n" and len(veri) >= 24:
        genislik, yukseklik = struct.unpack(">II", veri[16:24])
        return {"bicim": "PNG", "genislik": genislik, "yukseklik": yukseklik, "hareketli": b"acTL" in veri[:4096]}
    if veri[:3] == b"\xff\xd8\xff":
        i = 2
        while i + 9 < len(veri):
            if veri[i] != 0xFF:
                i += 1
                continue
            isaret = veri[i + 1]
            if isaret in (0xD8, 0x01) or 0xD0 <= isaret <= 0xD7:
                i += 2
                continue
            boy = struct.unpack(">H", veri[i + 2:i + 4])[0]
            if isaret in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                yukseklik, genislik = struct.unpack(">HH", veri[i + 5:i + 9])
                return {"bicim": "JPEG", "genislik": genislik, "yukseklik": yukseklik, "hareketli": False}
            i += 2 + boy
        return {"bicim": "JPEG", "genislik": None, "yukseklik": None, "hareketli": False}
    if veri[:4] == b"RIFF" and veri[8:12] == b"WEBP" and len(veri) >= 30:
        parca = veri[12:16]
        if parca == b"VP8X":
            genislik = 1 + int.from_bytes(veri[24:27], "little")
            yukseklik = 1 + int.from_bytes(veri[27:30], "little")
            return {"bicim": "WebP", "genislik": genislik, "yukseklik": yukseklik, "hareketli": bool(veri[20] & 0x02)}
        if parca == b"VP8 " and veri[23:26] == b"\x9d\x01\x2a":
            genislik, yukseklik = struct.unpack("<HH", veri[26:30])
            return {"bicim": "WebP", "genislik": genislik & 0x3FFF, "yukseklik": yukseklik & 0x3FFF, "hareketli": False}
        if parca == b"VP8L" and veri[20] == 0x2F:
            b = int.from_bytes(veri[21:25], "little")
            return {"bicim": "WebP", "genislik": (b & 0x3FFF) + 1, "yukseklik": ((b >> 14) & 0x3FFF) + 1, "hareketli": False}
        return {"bicim": "WebP", "genislik": None, "yukseklik": None, "hareketli": False}
    if veri[:6] in (b"GIF87a", b"GIF89a") and len(veri) >= 10:
        genislik, yukseklik = struct.unpack("<HH", veri[6:10])
        return {"bicim": "GIF", "genislik": genislik, "yukseklik": yukseklik, "hareketli": veri.count(b"\x21\xf9\x04") > 1}
    if veri[4:8] == b"ftyp":
        marka = veri[8:12]
        if marka in (b"avif", b"avis"):
            return {"bicim": "AVIF", "genislik": None, "yukseklik": None, "hareketli": marka == b"avis"}
        if marka in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"mif1", b"msf1"):
            return {"bicim": "HEIC", "genislik": None, "yukseklik": None, "hareketli": marka in (b"hevc", b"msf1")}
    return {"bicim": None, "genislik": None, "yukseklik": None, "hareketli": False}


def kapak_denetle(yol: Path, rapor: Rapor) -> dict[str, Any]:
    if not yol.is_file():
        raise KitaptikHatasi(f"kapak dosyası bulunamadı: {yol}")
    boyut = yol.stat().st_size
    with yol.open("rb") as f:
        veri = f.read(min(boyut, 4 * 1024 * 1024))
    bilgi = {**gorsel_bilgisi(veri), "bayt": boyut, "dosya": str(yol)}
    if bilgi["bicim"] is None:
        rapor.ekle("hata", "kapak-bicim", f"{yol.name}: kapak JPEG, PNG, WebP, HEIC ya da AVIF olmalı (SVG ve diğerleri kabul edilmez)")
        return bilgi
    if bilgi["bicim"] == "GIF":
        rapor.ekle("uyari", "kapak-gif", f"{yol.name}: GIF kapak için uygun değil; JPEG ya da PNG kullanın")
    if bilgi["hareketli"]:
        rapor.ekle("hata", "kapak-hareketli", f"{yol.name}: hareketli görsel kapak olamaz; sabit bir görsel kullanın")
    if boyut > SINIR["kapak_bayt"]:
        rapor.ekle("hata", "kapak-buyuk", f"{yol.name}: {boyut / 1048576:.1f} MB; en çok 20 MB olmalı".replace(".", ",", 1))
    g, y = bilgi["genislik"], bilgi["yukseklik"]
    if g and y:
        if g < SINIR["kapak_en_az"] or y < SINIR["kapak_en_az"]:
            rapor.ekle("hata", "kapak-kucuk", f"{yol.name}: {g}×{y} piksel; en az 100×100 olmalı")
        elif g < KAPAK_ONERILEN[0] or y < KAPAK_ONERILEN[1]:
            rapor.ekle("uyari", "kapak-dusuk", f"{yol.name}: {g}×{y} piksel; önerilen en az {KAPAK_ONERILEN[0]}×{KAPAK_ONERILEN[1]}")
        oran = g / y
        hedef = KAPAK_ONERILEN[0] / KAPAK_ONERILEN[1]
        if g >= y:
            rapor.ekle("uyari", "kapak-yatay", f"{yol.name}: kapak yatay ya da kare; Kitaptik kapakları dikey gösterir "
                                               f"(önerilen {KAPAK_ONERILEN[0]}×{KAPAK_ONERILEN[1]})")
        elif abs(oran - hedef) / hedef > 0.12:
            rapor.ekle("uyari", "kapak-oran", f"{yol.name}: en-boy oranı {oran:.2f}; önerilen yaklaşık {hedef:.2f} "
                                              f"({KAPAK_ONERILEN[0]}×{KAPAK_ONERILEN[1]}), kenarlar kırpılabilir".replace(".", ","))
    else:
        rapor.ekle("bilgi", "kapak-olcu", f"{yol.name}: {bilgi['bicim']} ölçüsü okunamadı; yüklemeden önce en az 100×100 "
                                          f"ve önerilen {KAPAK_ONERILEN[0]}×{KAPAK_ONERILEN[1]} olduğunu kontrol edin")
    return bilgi


# ---------------------------------------------------------------- denetim


def denetle(proje: Path, kapak: Path | None = None, sinir: int = SINIR["bolum_kelime"], taslak: bool = False) -> tuple[Rapor, list[Parca], dict[str, Any] | None]:
    kitap_proje.proje_klasoru(proje)
    if not 100 <= sinir <= SINIR["bolum_kelime"]:
        raise KitaptikHatasi(f"--bolum-siniri 100 ile {SINIR['bolum_kelime']} arasında olmalı")
    rapor = Rapor()
    bilgi = bilgi_oku(proje)
    parcalar, sorunlar = bolum_parcalari(proje, sinir)
    for s in sorunlar:
        rapor.bulgular.append(s)
    bolumler = kitap_proje.bolumler(proje)

    # Bölümler ve başlıklar
    bolunen = sorted({p.kaynak_no for p in parcalar if p.toplam > 1})
    for no in bolunen:
        ilk = next(p for p in parcalar if p.kaynak_no == no)
        kelime = sum(p.kelime for p in parcalar if p.kaynak_no == no)
        rapor.ekle("uyari", "bolum-uzun", f"{ilk.kaynak_dosya}: {tk.tr_sayi(kelime)} kelime; Kitaptik sınırı "
                                          f"{tk.tr_sayi(SINIR['bolum_kelime'])}. Pakette {ilk.toplam} parçaya bölünecek "
                                          f"(\"{parca_basligi(ilk, SINIR['bolum_basligi'])}\" …)", bolum=no)
    for b in {p.kaynak_no: p for p in parcalar}.values():
        uzunluk = js_uzunluk(b.baslik)
        if uzunluk > SINIR["bolum_basligi"] - (len(f" ({b.toplam}/{b.toplam})") if b.toplam > 1 else 0):
            rapor.ekle("uyari", "baslik-uzun", f"{b.kaynak_dosya}: bölüm başlığı {uzunluk} karakter; Kitaptik en çok "
                                               f"{SINIR['bolum_basligi']} kabul eder. Pakette \"{parca_basligi(b, SINIR['bolum_basligi'])}\" "
                                               "olarak kısaltılacak; isterseniz başlığı kendiniz kısaltın", bolum=b.kaynak_no)
    if len(parcalar) > SINIR["kitap_bolum"]:
        rapor.ekle("hata", "cok-bolum", f"{tk.tr_sayi(len(parcalar))} bölüm; Kitaptik'te bir kitap en çok "
                                        f"{tk.tr_sayi(SINIR['kitap_bolum'])} bölüm olabilir. Kitabı ciltlere ayırın")
    elif len(parcalar) > SINIR["toplu_bolum"]:
        rapor.ekle("bilgi", "coklu-docx", f"{tk.tr_sayi(len(parcalar))} bölüm; tek seferde en çok "
                                          f"{SINIR['toplu_bolum']} bölüm içe aktarılır. Paket birden çok DOCX üretir; ilkini "
                                          "normal, sonrakileri \"Mevcut bölümlere ekle\" seçeneğiyle yükleyin")

    # İçerik: bitmemiş işaretler, görsel, tablo, bağlantı, sinyaller
    toplam_sinyal: dict[str, int] = {}
    for b in bolumler:
        metin = b.metin
        isaretler = metin_analizi.isaretleri_bul(kitap_proje.satir_koruyan_govde(metin))
        if isaretler:
            ilk = isaretler[0]
            rapor.ekle("uyari" if taslak else "hata", "bitmemis",
                       f"{b.yol.name}:{ilk['satir']}: bitmemiş metin işareti {ilk['isaret']} (toplam {len(isaretler)}); "
                       "yayımlamadan önce doldurun", bolum=b.no)
        if GORSEL_DESENI.search(metin):
            rapor.ekle("uyari", "gorsel", f"{b.yol.name}: bölümde görsel var; Kitaptik Word'den içe aktarırken görselleri atar",
                       bolum=b.no)
        if TABLO_DESENI.search(metin):
            rapor.ekle("uyari", "tablo", f"{b.yol.name}: tablo düz metne dönüşür; gerekiyorsa paragraf olarak yazın", bolum=b.no)
        if URL_DESENI.search(kitap_proje.satir_koruyan_govde(metin)):
            rapor.ekle("uyari", "baglanti", f"{b.yol.name}: bölümde bağlantı var. Topluluk Kuralları 4.2: bölümler reklam ya da "
                                            "başka siteye yönlendirme için kullanılamaz; kendi sosyal medya hesabınızı ya da "
                                            "basılı kitabınızı tanıtmanız serbesttir", bolum=b.no)
        sinyaller = icerik_sinyalleri(metin)
        for ad, bulunan in sinyaller.items():
            toplam_sinyal[ad] = toplam_sinyal.get(ad, 0) + len(bulunan)
        if "intihar" in sinyaller and not tw_var(kitap_proje.satir_koruyan_govde(metin)):
            no, sozcuk = sinyaller["intihar"][0]
            rapor.ekle("uyari", "tw-eksik", f"{b.yol.name}:{no}: \"{sozcuk}\" geçiyor. Konu işleniyorsa Topluluk Kuralları 2.3 "
                                            "bölüm başına [TW: İntihar] gibi bir uyarı ister; teşvik eden, yücelten ya da yöntem "
                                            "anlatan içerik yasaktır", bolum=b.no)
        if "tecavuz" in sinyaller:
            no, _ = sinyaller["tecavuz"][0]
            rapor.ekle("uyari", "cinsel-saldiri", f"{b.yol.name}:{no}: cinsel saldırı geçiyor. Topluluk Kuralları 2.2: travma "
                                                  "olarak işlenebilir, yüceltilemez ya da erotikleştirilemez; sahneyi gözden "
                                                  "geçirin ve kitabı 18+ işaretleyin", bolum=b.no)
    yetiskin_nedenleri = [SINYALLER[ad][1] for ad, esik in YETISKIN_ESIKLERI.items() if toplam_sinyal.get(ad, 0) >= esik]

    # Yayın bilgisi
    if bilgi is None:
        rapor.ekle("uyari", "bilgi-yok", f"{BILGI_DOSYASI.as_posix()} yok; kitap bilgilerini hazırlamak için "
                                         "'kitaptik_hazirla.py baslat --proje …' çalıştırın")
    else:
        _bilgi_denetle(bilgi, rapor, len(parcalar), yetiskin_nedenleri)
    if bilgi is None and yetiskin_nedenleri:
        rapor.ekle("uyari", "yetiskin-oneri", "Metinde yetişkin içerik sinyalleri var (" + ", ".join(yetiskin_nedenleri)
                   + "); Kitaptik'te \"Yetişkin İçerik (18+)\" anahtarını açmayı düşünün")

    # Kapak
    kapak_yolu = kapak or kapak_bul(proje)
    kapak_bilgisi = kapak_denetle(kapak_yolu, rapor) if kapak_yolu else None
    if kapak_yolu is None:
        rapor.ekle("bilgi", "kapak-yok", "kapak bulunamadı (kapak/kapak.jpg); kapak, okurun listede ilk gördüğü şeydir. "
                                         "Önerilen ölçü 583×827 piksel; /kapak-tasarla becerisine bakın")

    rapor.ozet = {
        "kitap": (bilgi or {}).get("baslik") or kitap_proje.kitap_basligi(proje),
        "bolum_dosyasi": len(bolumler),
        "kitaptik_bolumu": len(parcalar),
        "bolunen_bolum": len(bolunen),
        "toplam_kelime": sum(p.kelime for p in parcalar),
        "en_uzun_parca": max((p.kelime for p in parcalar), default=0),
        "docx_sayisi": max(1, math.ceil(len(parcalar) / SINIR["toplu_bolum"])) if parcalar else 0,
        "icerik_sinyalleri": toplam_sinyal,
        "yetiskin_onerisi": bool(yetiskin_nedenleri),
        "kapak": kapak_bilgisi,
    }
    return rapor, parcalar, bilgi


def _bilgi_denetle(bilgi: dict[str, Any], rapor: Rapor, bolum_sayisi: int, yetiskin_nedenleri: list[str]) -> None:
    baslik = nfc(str(bilgi.get("baslik") or "").strip())
    if js_uzunluk(baslik) < SINIR["kitap_basligi_en_az"]:
        rapor.ekle("hata", "baslik-yok", "Kitap başlığı en az 2 karakter olmalı")
    elif js_uzunluk(baslik) > SINIR["kitap_basligi_en_fazla"]:
        rapor.ekle("hata", "kitap-basligi-uzun", f"Kitap başlığı {js_uzunluk(baslik)} karakter; en çok 255 olmalı")

    ana = kategori_adi(str(bilgi.get("kategori") or ""))
    if not str(bilgi.get("kategori") or "").strip():
        rapor.ekle("hata", "kategori-yok", "Kategori seçilmemiş; Kitaptik'te kategori zorunludur")
    elif ana is None:
        rapor.ekle("hata", "kategori-gecersiz", f"Kategori '{bilgi['kategori']}' Kitaptik'te yok. Geçerli ana kategoriler: "
                   + ", ".join(KATEGORILER))
    altlar = [a.strip() for a in re.split(r"[,;]", str(bilgi.get("alt_kategoriler") or "")) if a.strip()]
    if ana:
        gecersiz = [a for a in altlar if alt_kategori_adi(ana, a) is None]
        if gecersiz:
            rapor.ekle("hata", "alt-kategori-gecersiz", f"'{ana}' altında olmayan alt kategori: {', '.join(gecersiz)}. "
                                                        "Liste: kitaptik_hazirla.py kategoriler")
    if len(altlar) > SINIR["alt_kategori"]:
        rapor.ekle("hata", "alt-kategori-fazla", f"{len(altlar)} alt kategori; en çok 3 seçilebilir")
    if ana and not altlar:
        rapor.ekle("bilgi", "alt-kategori-yok", "Alt kategori seçilmemiş; alt kategori, okurun kitabı kategori sayfasında "
                                                "bulmasını kolaylaştırır")

    etiketler, uzun = etiketleri_ayir(str(bilgi.get("etiketler") or ""))
    if uzun:
        rapor.ekle("uyari", "etiket-uzun", f"40 karakteri aşan etiketleri Kitaptik kaydetmez: {', '.join(uzun)}")
    if len(etiketler) > SINIR["etiket_sayisi"]:
        rapor.ekle("uyari", "etiket-fazla", f"{len(etiketler)} etiket; yalnızca ilk 30'u kaydedilir")
    elif len(etiketler) > ONERILEN_ETIKET_UST:
        rapor.ekle("uyari", "etiket-yigini", f"{len(etiketler)} etiket. Topluluk Kuralları 4.1 kitapla ilgisiz etiket "
                                             "yığmayı yasaklar; az ve isabetli etiket seçin")
    elif not etiketler:
        rapor.ekle("bilgi", "etiket-yok", "Etiket yok; birkaç isabetli etiket aramada bulunmayı kolaylaştırır")

    dil = str(bilgi.get("dil") or "Türkçe").strip()
    if kucuk(dil) != "türkçe":
        rapor.ekle("hata", "dil", f"Dil '{dil}'; Kitaptik'te şu an yalnızca Türkçe seçilebilir")

    aciklama = str(bilgi.get("aciklama") or "")
    if not aciklama:
        rapor.ekle("uyari", "aciklama-yok", "Açıklama boş; okurun kitabı açıp açmamaya karar verdiği ilk metin budur")
    elif js_uzunluk(aciklama) > SINIR["aciklama"]:
        rapor.ekle("hata", "aciklama-uzun", f"Açıklama {tk.tr_sayi(js_uzunluk(aciklama))} karakter; en çok 2.500 olmalı")
    elif js_uzunluk(aciklama) < KISA_ACIKLAMA:
        rapor.ekle("uyari", "aciklama-kisa", f"Açıklama {js_uzunluk(aciklama)} karakter; birkaç cümleyle kahramanı, "
                                             "çatışmayı ve merak sorusunu anlatın")
    for anahtar, sinir, ad in (("neden_okumali", SINIR["neden_okumali"], "\"Neden okumalı?\""),
                               ("telif_notu", SINIR["telif_notu"], "Telif notu")):
        uzunluk = js_uzunluk(str(bilgi.get(anahtar) or ""))
        if uzunluk > sinir:
            rapor.ekle("hata", f"{anahtar.replace('_', '-')}-uzun", f"{ad} {tk.tr_sayi(uzunluk)} karakter; en çok "
                                                                    f"{tk.tr_sayi(sinir)} olmalı")
    if not str(bilgi.get("neden_okumali") or ""):
        rapor.ekle("bilgi", "neden-okumali-yok", "\"Neden okumalı?\" boş; en çok 333 karakterlik bir davet yazın")

    for anahtar, ad in (("yetiskin", "Yetişkin içerik (18+)"), ("tamamlandi", "Kitap tamamlandı"),
                        ("pdf_indirme", "PDF indirme"), ("ucretli", "Ücretli")):
        ham = str(bilgi.get(anahtar) or "").strip()
        if ham and evet_hayir(ham) is None:
            rapor.ekle("hata", "evet-hayir", f"'{ad}' alanı 'evet' ya da 'hayır' olmalı, '{ham}' yazılmış")
    yetiskin = evet_hayir(str(bilgi.get("yetiskin") or ""))
    if yetiskin_nedenleri and yetiskin is not True:
        rapor.ekle("uyari", "yetiskin-oneri", "Metinde yetişkin içerik sinyalleri var (" + ", ".join(yetiskin_nedenleri)
                   + "). Topluluk Kuralları 2.1'e göre bu tür içerik 18+ işaretlenmeli; yanlış işaretleme kitabın "
                   "kaldırılmasına yol açabilir. Tarama anahtar sözcüklere dayanır, karar sizindir")
    if evet_hayir(str(bilgi.get("tamamlandi") or "")) and bolum_sayisi == 0:
        rapor.ekle("hata", "tamamlandi-bolumsuz", "Kitap tamamlandı işaretlenemez: en az bir yayımlanmış bölüm gerekir")

    if evet_hayir(str(bilgi.get("ucretli") or "")):
        fiyat_ham = str(bilgi.get("fiyat") or "").strip().replace(",", ".")
        try:
            fiyat = float(fiyat_ham)
        except ValueError:
            fiyat = -1.0
        if fiyat < SINIR["ucretli_en_az_fiyat"]:
            rapor.ekle("hata", "fiyat", f"Ücretli kitap için fiyat en az {SINIR['ucretli_en_az_fiyat']} TL olmalı "
                                        f"(yazılan: '{bilgi.get('fiyat') or ''}')")
        if bolum_sayisi < SINIR["ucretli_en_az_bolum"]:
            rapor.ekle("uyari", "ucretli-bolum", f"Ücretli kitap için Kitaptik yayımlanmış bölüm sayısında alt sınır uygular "
                                                 f"(varsayılan {SINIR['ucretli_en_az_bolum']}); bu kitapta {bolum_sayisi} bölüm var")
        rapor.ekle("bilgi", "ucretli-kosul", "Ücretli kitaptan telif kazanmak için aktif Kitaptik Premium üyeliği ve en az bir "
                                             "yayımlanmış kitap gerekir; yazar payı %40 (25 Eylül 2026). Güncel koşullar: "
                                             f"{SITE}/nasil-para-kazanilir")


# ---------------------------------------------------------------- DOCX


def _kosular(metin: str, kalin: bool = False, italik: bool = False) -> str:
    kosular = []
    for parca, k, i in by.satir_ici_parcalar(metin, kalin, italik):
        rpr = ("<w:b/>" if k else "") + ("<w:i/>" if i else "")
        rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
        kosular.append(f'<w:r>{rpr}<w:t xml:space="preserve">{by.x(parca)}</w:t></w:r>')
    return "".join(kosular)


def _paragraf(metin: str, stil: str | None = None, kalin: bool = False, italik: bool = False, ortali: bool = False) -> str:
    """Gövde paragrafları Word'ün "Normal" biçemini kullanır; içe aktarıcı özel biçem adlarını tanımaz."""
    ppr = (f'<w:pStyle w:val="{stil}"/>' if stil else "") + ('<w:jc w:val="center"/>' if ortali else "")
    return f'<w:p><w:pPr>{ppr}</w:pPr>{_kosular(metin, kalin, italik)}</w:p>' if ppr else f"<w:p>{_kosular(metin, kalin, italik)}</w:p>"


def kitaptik_docx_yaz(hedef: Path, baslik: str, yazar: str, parcalar: list[Parca], zaman: dt.datetime,
                      baslik_siniri: int = SINIR["bolum_basligi"]) -> None:
    """Kitaptik'in "Word'den toplu içe aktar" ekranına uygun DOCX.

    Kapak sayfası ve üst bilgi yoktur (ilk Başlık 1'den önceki metin ayrı bölüm sayılırdı). Her parça bir
    Başlık 1 ile başlar; ara başlıklar kalın paragraf, alıntılar italik, sahne ayracı "* * *" olur."""
    govde = []
    for p in parcalar:
        govde.append(_paragraf(parca_basligi(p, baslik_siniri), "Heading1"))
        for tur, metin in p.bloklar:
            if tur == "ayrac":
                govde.append(_paragraf("* * *", ortali=True))
            elif tur == "h2":
                govde.append(_paragraf(metin, kalin=True))
            elif tur == "alinti":
                govde.append(_paragraf(metin, italik=True))
            else:
                govde.append(_paragraf(metin))
    W, XB = by.W, by.XML_BAS
    belge = (XB + f'<w:document xmlns:w="{W}"><w:body>' + "".join(govde)
             + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1418" w:right="1418" w:bottom="1418" '
             'w:left="1418" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr></w:body></w:document>')
    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    turler = (XB + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              f'<Override PartName="/word/document.xml" ContentType="{ct}.document.main+xml"/>'
              f'<Override PartName="/word/styles.xml" ContentType="{ct}.styles+xml"/>'
              '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
              "</Types>")
    kok = (XB + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
           f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="word/document.xml"/>'
           '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
           'Target="docProps/core.xml"/></Relationships>')
    belge_iliski = (XB + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    f'<Relationship Id="rIdStil" Type="{rel}/styles" Target="styles.xml"/></Relationships>')
    cekirdek = (XB + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                f"<dc:title>{by.x(baslik)}</dc:title><dc:creator>{by.x(yazar)}</dc:creator><dc:language>tr-TR</dc:language>"
                f'<dcterms:created xsi:type="dcterms:W3CDTF">{by._utc(zaman)}</dcterms:created>'
                f'<dcterms:modified xsi:type="dcterms:W3CDTF">{by._utc(zaman)}</dcterms:modified></cp:coreProperties>')
    by._zip_yaz(hedef, [("[Content_Types].xml", turler.encode()), ("_rels/.rels", kok.encode()),
                        ("word/document.xml", belge.encode()), ("word/_rels/document.xml.rels", belge_iliski.encode()),
                        ("word/styles.xml", by.docx_stilleri().encode()), ("docProps/core.xml", cekirdek.encode())], zaman)


def docx_gruplari(parcalar: list[Parca]) -> list[list[Parca]]:
    boy = SINIR["toplu_bolum"]
    return [parcalar[i:i + boy] for i in range(0, len(parcalar), boy)]


# ---------------------------------------------------------------- paket


def _alan(bilgi: dict[str, Any] | None, anahtar: str, varsayilan: str = "") -> str:
    return str((bilgi or {}).get(anahtar) or varsayilan).strip()


def kitap_bilgileri_md(bilgi: dict[str, Any] | None, rapor: Rapor, proje: Path) -> str:
    etiketler, _ = etiketleri_ayir(_alan(bilgi, "etiketler"))
    yetiskin = evet_hayir(_alan(bilgi, "yetiskin", "hayır"))
    s = ["# Kitaptik: Kitap Bilgileri", "",
         f"Kitaptik'te **Yaz → Hikaye Yaz → Yeni Kitap** ekranındaki alanlara sırayla kopyalayın ({SITE}/yaz).", "",
         "| Alan | Değer |", "|---|---|",
         f"| Kitap Başlığı | {_alan(bilgi, 'baslik', kitap_proje.kitap_basligi(proje))} |",
         f"| Kategori | {kategori_adi(_alan(bilgi, 'kategori')) or '(seçin)'} |",
         f"| Alt kategoriler (en çok 3) | {_alan(bilgi, 'alt_kategoriler') or '(isteğe bağlı)'} |",
         f"| Dil | {_alan(bilgi, 'dil', 'Türkçe')} |",
         f"| Etiketler | {', '.join(etiketler) or '(isteğe bağlı)'} |",
         f"| Kitap Tamamlandı | {'açık' if evet_hayir(_alan(bilgi, 'tamamlandi', 'hayır')) else 'kapalı'} (ilk bölüm yayımlandıktan sonra açılabilir) |",
         f"| İndirme Aktif (PDF) | {'açık' if evet_hayir(_alan(bilgi, 'pdf_indirme', 'evet')) is not False else 'kapalı'} |",
         f"| Yetişkin İçerik (18+) | {'açık' if yetiskin else 'kapalı'}{' (denetim 18+ öneriyor)' if rapor.ozet.get('yetiskin_onerisi') and not yetiskin else ''} |",
         "", "## Açıklama", "", _alan(bilgi, "aciklama") or "(boş)", "",
         f"_{tk.tr_sayi(js_uzunluk(_alan(bilgi, 'aciklama')))} / 2.500 karakter_", "",
         "## Neden okumalı?", "", _alan(bilgi, "neden_okumali") or "(boş)", "",
         f"_{js_uzunluk(_alan(bilgi, 'neden_okumali'))} / 333 karakter_", "",
         "## Telif hakkı (isteğe bağlı)", "", _alan(bilgi, "telif_notu") or "(boş)", ""]
    if evet_hayir(_alan(bilgi, "ucretli")):
        s += ["## Ücretli kitap", "", f"- Fiyat: {_alan(bilgi, 'fiyat')} TL (en az {SINIR['ucretli_en_az_fiyat']} TL)",
              "- Ücretli ayarı kitap yayımlandıktan sonra kitap ayarlarından yapılır; aktif Premium üyelik ister.", ""]
    return "\n".join(s)


def _bas_harf_buyuk(metin: str) -> str:
    """Türkçe baş harf: "istediği" → "İstediği" (str.capitalize "Istediği" yazar)."""
    if not metin:
        return metin
    ilk = {"i": "İ", "ı": "I"}.get(metin[0], metin[0].upper())
    return ilk + metin[1:]


def karakter_kartlari_md(proje: Path) -> tuple[str, int]:
    try:
        kayitlar = [k for k in ka.kayitlari_oku(proje) if k.tur == "karakter"]
    except (ka.AnsiklopediHatasi, dosya_oku.DosyaHatasi):
        kayitlar = []
    s = ["# Kitaptik: Karakter Kartları", "",
         "Kitabın \"Karakterler ve Tanıtım\" bölümüne eklenebilir. Rol seçenekleri: " + ", ".join(ROLLER) + ".",
         "Sırlar, yaralar ve ölüm bilgisi spoiler olmasın diye alınmadı.", ""]
    for k in kayitlar:
        parcalar = k.ad.split()
        if len(parcalar) > 1 and ka.anahtar(parcalar[-1]) not in ka.UNVANLAR:
            ad, soyad = " ".join(parcalar[:-1]), parcalar[-1]
        else:
            ad, soyad = k.ad, ""
        rol_ham = k.alanlar.get("rol", "")
        rol = next((r for desen, r in ROL_ESLEME if re.search(desen, kucuk(rol_ham))), "Diğer")
        if not rol_ham or rol_ham == "-":
            rol_satiri = "(seçin: " + ", ".join(ROLLER) + ")"
        else:
            rol_satiri = rol + (f" (özel rol: {rol_ham[:60]})" if rol == "Diğer" else "")
        aciklama = "; ".join(f"{_bas_harf_buyuk(alan)}: {k.alanlar[alan]}" for alan in TANITIM_ALANLARI
                             if k.alanlar.get(alan) and k.alanlar[alan] != "-")
        s += [f"## {k.ad}", "", f"- Ad: {ad[:120]}", f"- Soyad: {soyad[:120]}", f"- Rol: {rol_satiri}",
              f"- Açıklama: {aciklama or '(yazın)'}", ""]
    if not kayitlar:
        s.append("Kurgu ansiklopedisinde karakter kaydı yok (kurgu/karakterler/). /kurgu-ansiklopedisi ile ekleyebilirsiniz.")
    return "\n".join(s) + "\n", len(kayitlar)


def kontrol_listesi_md(rapor: Rapor, docx_adlari: list[str]) -> str:
    o = rapor.ozet
    ilk = docx_adlari[0] if docx_adlari else "(DOCX üretilmedi)"
    s = ["# Kitaptik Yayın Kontrol Listesi", "",
         f"Adımlar Kitaptik'in {DOGRULAMA_TARIHI} tarihli yardım sayfalarına göre yazıldı ({SITE}/nasil-yazar-olunur, "
         f"{SITE}/yardim-merkezi/kullanim-kilavuzu). Ekranlar değişmiş olabilir.", "",
         "## Yüklemeden önce", "",
         f"- [ ] Denetimde hata yok (şu an: {o.get('hata', rapor.sayi('hata'))} hata, {rapor.sayi('uyari')} uyarı; `rapor.json`).",
         "- [ ] Yazım ve yapay zekâ tadı denetimi yapıldı (/yazim-denetle, /yz-tadi-gider).",
         f"- [ ] Topluluk Kuralları okundu ({SITE}/sayfa/topluluk-kurallari): 18+ işareti, tetikleyici uyarıları, "
         "şarkı sözlerinden en çok 1-2 dize, telif ve izinsiz çeviri kuralları.",
         "- [ ] Kapak hazır: JPEG/PNG/WebP, dikey, önerilen 583×827 piksel, en çok 20 MB; çıplaklık ve aşırı kan yok, "
         "başkasının çizimi izinsiz kullanılmadı.", "",
         "## Kitaptik'te", "",
         "- [ ] Ücretsiz üye olun ve e-posta adresinizi doğrulayın; profil fotoğrafı ve biyografiyi doldurun.",
         "- [ ] Üst menüden **Yaz → Hikaye Yaz**, ardından **Yeni Kitap**.",
         "- [ ] `kitap-bilgileri.md` içindeki alanları doldurun, kapağı yükleyin, **taslak olarak kaydedin**.",
         f"- [ ] Kitabın **Bölümler** sekmesinde **Toplu Yükle** düğmesiyle `{ilk}` dosyasını yükleyin "
         "(her Başlık 1 bir bölüm olur); **İçe Aktar** ile onaylayın.",
         ]
    if len(docx_adlari) > 1:
        s.append(f"- [ ] Kalan dosyaları ({', '.join(docx_adlari[1:])}) sırayla **Mevcut bölümlere ekle** seçeneğiyle yükleyin.")
    s += [f"- [ ] Önizlemede {o.get('kitaptik_bolumu', 0)} bölüm göründüğünü, başlıkları ve kelime sayılarını kontrol edin.",
          "- [ ] Metin 18+ içeriyorsa kitap bilgilerinde **Yetişkin İçerik (18+)** anahtarını açın.",
          "- [ ] **Bölümler** sekmesinde **Yayınla**: kitap, taslak bölümleriyle birlikte okura açılır.",
          "- [ ] Kitap bittiyse **Kitap Tamamlandı** anahtarını açın.", "",
          "## Yayımladıktan sonra", "",
          "- [ ] Karakter kartlarını (`karakterler.md`) kitabın karakter bölümüne ekleyin.",
          "- [ ] Yeni bölümleri düzenli aynı gün ve saatte yayımlayın; takipçilerinize bildirim gider.",
          "- [ ] Kitabın istatistik sayfasından okunma, beğeni ve yorumları izleyin; yorumlara yanıt verin.",
          f"- [ ] Kazanç isterseniz: aktif Premium üyelik ve en az bir yayımlanmış kitap şartı; okur aboneliği, destek ve "
          f"ücretli kitaptan yazar payı %40. Güncel koşullar: {SITE}/nasil-para-kazanilir", "",
          "Bu paket Kitaptik'e otomatik yükleme yapmaz; bütün adımlar sizin hesabınızdan elle yapılır.", ""]
    return "\n".join(s)


def paket(proje: Path, cikti: Path | None, kapak: Path | None, yazar: str | None, sinir: int,
          taslak: bool = False) -> tuple[Rapor, list[Path]]:
    rapor, parcalar, bilgi = denetle(proje, kapak, sinir, taslak)
    if rapor.sayi("hata"):
        return rapor, []
    hedef = cikti or (proje / "yayin" / "kitaptik")
    if hedef.exists() and not hedef.is_dir():
        raise KitaptikHatasi(f"çıktı yolu bir dosya: {hedef}")
    hedef.mkdir(parents=True, exist_ok=True)
    baslik = _alan(bilgi, "baslik", kitap_proje.kitap_basligi(proje))
    yazar_adi = (yazar or _alan(bilgi, "yazar")).strip()
    zaman = e_kitap_derle.yayin_zamani()
    ad = e_kitap_derle.dosya_adi(baslik)
    gruplar = docx_gruplari(parcalar)
    yazilan: list[Path] = []
    docx_adlari: list[str] = []
    for i, grup in enumerate(gruplar, 1):
        dosya = hedef / (f"{ad}-kitaptik.docx" if len(gruplar) == 1 else f"{ad}-kitaptik-{i}.docx")
        kitaptik_docx_yaz(dosya, baslik, yazar_adi, grup, zaman)
        if dosya.stat().st_size > SINIR["docx_bayt"]:
            raise KitaptikHatasi(f"{dosya.name} 20 MB'ı aşıyor; kitabı ciltlere ayırın")
        yazilan.append(dosya)
        docx_adlari.append(dosya.name)
    for dosya_adi, icerik in (("kitap-bilgileri.md", kitap_bilgileri_md(bilgi, rapor, proje)),
                              ("karakterler.md", karakter_kartlari_md(proje)[0]),
                              ("yayin-kontrol-listesi.md", kontrol_listesi_md(rapor, docx_adlari))):
        yol = hedef / dosya_adi
        yol.write_text(icerik, encoding="utf-8", newline="\n")
        yazilan.append(yol)
    rapor.ozet["dosyalar"] = [p.name for p in yazilan]
    rapor.ozet["bolumler"] = [{"baslik": parca_basligi(p, SINIR["bolum_basligi"]), "kelime": p.kelime,
                               "kaynak": p.kaynak_dosya} for p in parcalar]
    yol = hedef / "rapor.json"
    yol.write_text(json.dumps(rapor.sozluk(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    yazilan.append(yol)
    return rapor, yazilan


# ---------------------------------------------------------------- çıktı


ISARET = {"hata": "✗", "uyari": "!", "bilgi": "·"}


def rapor_metni(rapor: Rapor, yazilan: list[Path] | None = None) -> str:
    o = rapor.ozet
    s = [f"Kitaptik yayın denetimi: {o.get('kitap', '')}",
         f"  {o.get('bolum_dosyasi', 0)} bölüm dosyası → Kitaptik'te {o.get('kitaptik_bolumu', 0)} bölüm, "
         f"{tk.tr_sayi(o.get('toplam_kelime', 0))} kelime (en uzun bölüm {tk.tr_sayi(o.get('en_uzun_parca', 0))})"]
    if o.get("bolunen_bolum"):
        s.append(f"  {o['bolunen_bolum']} bölüm {tk.tr_sayi(SINIR['bolum_kelime'])} kelime sınırı için bölünecek")
    s.append("")
    for duzey in ("hata", "uyari", "bilgi"):
        for b in rapor.bulgular:
            if b["duzey"] == duzey:
                s.append(f"{ISARET[duzey]} {b['ileti']}")
    if not rapor.bulgular:
        s.append("✓ Sorun bulunmadı.")
    s += ["", f"Toplam: {rapor.sayi('hata')} hata, {rapor.sayi('uyari')} uyarı, {rapor.sayi('bilgi')} bilgi."]
    if yazilan:
        s += ["", "Yazılan dosyalar:"] + [f"  {p}" for p in yazilan]
        s.append("Sıradaki adım: yayin-kontrol-listesi.md dosyasını izleyerek Kitaptik'te yayımlayın.")
    elif yazilan is not None and rapor.sayi("hata"):
        s.append("Hatalar giderilmeden paket yazılmadı.")
    return "\n".join(s)


def kategoriler_metni() -> str:
    s = [f"Kitaptik kategorileri ({DOGRULAMA_TARIHI}; kitap en çok 3 alt kategori seçebilir, hepsi aynı ana kategoriden):", ""]
    for ana, altlar in KATEGORILER.items():
        s.append(f"{ana}: " + ", ".join(altlar))
    return "\n".join(s)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Kitaptik (kitaptik.com) için yayın denetimi ve toplu yükleme paketi. "
                                              "Siteye bağlanmaz, yükleme yapmaz.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_k = alt.add_parser("kategoriler", help="Kitaptik'in ana ve alt kategorileri")
    p_k.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_b = alt.add_parser("baslat", help="yayin/kitaptik.md yayın bilgisi dosyasını oluşturur")
    p_b.add_argument("--ana-kategori", help="Kitaptik ana kategorisi (varsayılan: Roman)")
    p_b.add_argument("--zorla", action="store_true", help="var olan dosyanın üzerine yaz")
    p_d = alt.add_parser("denetle", help="yayın bilgisi, bölümler, kapak ve içerik denetimi")
    p_p = alt.add_parser("paket", help="toplu yükleme DOCX'i, kitap bilgileri, karakter kartları ve kontrol listesi")
    p_p.add_argument("--cikti", type=Path, help="çıktı klasörü (varsayılan: KITAP/yayin/kitaptik)")
    p_p.add_argument("--yazar", help="DOCX üst verisindeki yazar adı (varsayılan: yayın bilgisindeki 'Yazar adı')")
    for p in (p_d, p_p):
        p.add_argument("--kapak", type=Path, help="kapak görseli (varsayılan: KITAP/kapak/kapak.jpg|png|webp)")
        p.add_argument("--bolum-siniri", type=int, default=SINIR["bolum_kelime"],
                       help="bölüm başına en çok kelime (varsayılan ve üst sınır 10000)")
        p.add_argument("--taslak", action="store_true", help="bitmemiş metin işaretlerini hata değil uyarı say")
        p.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    for p in (p_b, p_d, p_p):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "kategoriler":
            print(json.dumps(KATEGORILER, ensure_ascii=False, indent=2) if arg.json else kategoriler_metni())
            return 0
        if arg.komut == "baslat":
            yol = baslat(arg.proje, arg.ana_kategori, arg.zorla)
            print(f"Oluşturuldu: {yol}\nAçıklama ve \"Neden okumalı?\" bölümlerini doldurun, sonra: "
                  f"kitaptik_hazirla.py denetle --proje {arg.proje}")
            return 0
        if arg.komut == "denetle":
            rapor, _, _ = denetle(arg.proje, arg.kapak, arg.bolum_siniri, arg.taslak)
            print(json.dumps(rapor.sozluk(), ensure_ascii=False, indent=2) if arg.json else rapor_metni(rapor))
            return 1 if rapor.sayi("hata") else 0
        rapor, yazilan = paket(arg.proje, arg.cikti, arg.kapak, arg.yazar, arg.bolum_siniri, arg.taslak)
        if arg.json:
            print(json.dumps({**rapor.sozluk(), "yazilan": [str(p) for p in yazilan]}, ensure_ascii=False, indent=2))
        else:
            print(rapor_metni(rapor, yazilan))
        return 1 if rapor.sayi("hata") else 0
    except (KitaptikHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi, e_kitap_derle.DerlemeHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
