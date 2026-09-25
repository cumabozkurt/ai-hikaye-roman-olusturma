#!/usr/bin/env python3
"""Kurgu ansiklopedisi (hikâye bilgi bankası): karakterler, mekânlar, nesneler, gruplar,
sözlük, zaman çizelgesi ve ilişkiler; tutarlılık denetimi, dağılım ve bağlam paketi.

Kayıtlar yazarın okuyup düzenleyebildiği Markdown dosyalarıdır::

    kurgu/karakterler/defne-aras.md   # "# Defne Aras" + "- Yaş: 27" gibi alan satırları
    kurgu/mekanlar/saatci-dukkani.md
    kurgu/nesneler/kirmizi-defter.md
    kurgu/gruplar/yalin-ailesi.md
    kurgu/sozluk.md                   # | Terim | Anlamı | Yanlış yazımlar |
    kurgu/zaman-cizelgesi.md          # | Tarih | Olay | Kişiler | Bölüm |
    kurgu/iliskiler.md                # | Kimden | Kime | İlişki | Bölüm | Not |

Kullanım::

    kurgu_ansiklopedisi.py olustur    --proje KITAP --tur karakter --ad "Defne Aras"
    kurgu_ansiklopedisi.py listele    --proje KITAP [--tur mekan]
    kurgu_ansiklopedisi.py dogrula    --proje KITAP            # kayıtların kendi içinde tutarlılığı
    kurgu_ansiklopedisi.py tutarlilik --proje KITAP [--bolum 7] # metin ile ansiklopedi karşılaştırması
    kurgu_ansiklopedisi.py dagilim    --proje KITAP [--html dagilim.html]
    kurgu_ansiklopedisi.py grafik     --proje KITAP [--bolum 12] [--bicim mermaid|dot]
    kurgu_ansiklopedisi.py baglam     --proje KITAP --bolum 8 [--sinir 12000]

``baglam``, yazılacak bölümün planında adı geçen kayıtları (ve aralarındaki
ilişkileri, sözlük terimlerini, zaman olaylarını, açık ipuçlarını) önem sırasıyla
tek bir bağlam paketinde toplar; uzun romanda modelin bütün ansiklopediyi değil,
bölüme gereken kısmını okumasını sağlar.

Çıkış kodu: 0 temiz, 1 "hata" düzeyinde bulgu var, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
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

TURLER = {
    "karakter": ("karakterler", "Karakter"),
    "mekan": ("mekanlar", "Mekân"),
    "nesne": ("nesneler", "Nesne"),
    "grup": ("gruplar", "Grup"),
    "dunya": ("dunya", "Dünya bilgisi"),
}
SABLONLAR = {
    "karakter": ["Diğer adlar", "Rol", "Yaş", "Doğum yılı", "Göz rengi", "Saç rengi", "Görünüş", "Meslek",
                 "İstediği", "İhtiyacı", "Korkusu", "Sırrı", "Yarası", "Ses", "Karakter yayı", "İlk görünüş",
                 "Öldüğü bölüm"],
    "mekan": ["Diğer adlar", "Tür", "Konum", "Dönem", "Duyusal imza", "Kimin mekânı", "İlk görünüş"],
    "nesne": ["Diğer adlar", "Sahibi", "Şu an nerede", "Önemi", "Kuralları", "İlk görünüş"],
    "grup": ["Diğer adlar", "Tür", "Üyeler", "Amacı", "Merkezi", "İlk görünüş"],
    "dunya": ["Diğer adlar", "Kapsam", "Kural", "İstisna", "Bedeli"],
}
MULAKAT = [
    "Sabah uyandığında ilk ne düşünür?",
    "En son ne zaman ağladı, neden?",
    "Kimseye söylemediği bir utancı var mı?",
    "Parası olsa ilk neye harcar, neden?",
    "Annesi ya da babası hakkında tek cümlede ne söyler?",
    "Tartışmada nasıl davranır: bağırır mı, susar mı, kaçar mı?",
    "Hangi sözcüğü sık kullanır, hangisini asla kullanmaz?",
    "Hikâye başladığında neyi yanlış biliyor?",
    "Kaybetmekten en çok neyi korkar?",
    "Romanın sonunda neyi feda etmeye hazır olacak?",
]
UNVANLAR = {"bey", "hanım", "hanim", "efendi", "paşa", "ağa", "usta", "hoca", "abla", "abi", "ağabey", "teyze",
            "amca", "dayı", "hala", "yenge", "bayan", "bay", "doktor", "dr", "hafız", "hacı", "molla", "kaptan",
            "komiser", "müdür", "başkomiser", "hâkim", "avukat", "sayın", "çavuş", "yüzbaşı", "binbaşı"}
TAKVIM = {"ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım",
          "aralık", "pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar"}
SIK_BUYUK = {"allah", "tanrı", "türkçe", "türk", "türkiye", "istanbul", "ankara", "izmir", "ramazan", "bayram",
             "kurban", "cumhuriyet", "i̇stanbul", "bölüm", "tamam", "evet", "hayır", "peki", "hadi", "ah", "of",
             "vay", "eyvah", "hey", "ya", "ne", "neden", "nasıl", "kim", "ama", "ve", "bir", "bu", "şu", "o"}
HARF = "a-zçğıöşüâîûA-ZÇĞİÖŞÜÂÎÛ"
BUYUK_KELIME = re.compile(rf"(?<![{HARF}'’])([A-ZÇĞİÖŞÜÂÎÛ][{HARF}]{{2,}})(?:['’][{HARF}]+)?")
CUMLE_BASI = re.compile(r"(?:^|[.!?…:;]\s+|[—–-]\s*|[\"“«(]\s*)$")
YUMUSAMA = {"p": "b", "ç": "c", "t": "d", "k": "ğ"}


class AnsiklopediHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


@dataclass
class Kayit:
    tur: str
    ad: str
    yol: Path
    alanlar: dict[str, str] = field(default_factory=dict)
    govde: str = ""

    @property
    def adlar(self) -> list[str]:
        diger = self.alanlar.get("diğer adlar", "")
        return [self.ad] + [a.strip() for a in re.split(r"[,;/]", diger) if a.strip() and a.strip() != "-"]

    def sayi_alani(self, anahtar: str) -> int | None:
        m = re.search(r"-?\d+", self.alanlar.get(anahtar, ""))
        return int(m.group()) if m else None


def slug(ad: str) -> str:
    cevir = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")
    ascii_ad = unicodedata.normalize("NFKD", ad.translate(cevir)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", ascii_ad.lower()).strip("-")
    return s[:60] or "kayit"


def anahtar(ad: str) -> str:
    return tk.tr_kucuk(ad.strip().strip("*").strip())


def kayit_oku(tur: str, yol: Path) -> Kayit:
    metin = dosya_oku.metin_oku(yol, uyar=False).replace("\r\n", "\n")
    baslik = re.search(r"^#\s+(.+?)\s*$", metin, re.M)
    ad = (baslik.group(1) if baslik else yol.stem.replace("-", " ").title()).split("—")[0].strip()
    alanlar: dict[str, str] = {}
    for m in re.finditer(r"^[ \t]*[-*][ \t]+\**([^:*\n]{1,40}?)\**[ \t]*:[ \t]*(.*?)[ \t]*$", metin, re.M):
        k = anahtar(m.group(1))
        if k not in alanlar:
            alanlar[k] = m.group(2).strip().strip("*").strip()
    return Kayit(tur, ad, yol, alanlar, metin)


def kayitlari_oku(proje: Path) -> list[Kayit]:
    kitap_proje.proje_klasoru(proje)
    sonuc = []
    for tur, (klasor, _) in TURLER.items():
        taban = proje / "kurgu" / klasor
        if taban.is_dir():
            for yol in sorted(taban.glob("*.md")):
                if yol.is_file():
                    sonuc.append(kayit_oku(tur, yol))
    return sonuc


def tablo_oku(yol: Path, beklenen: tuple[str, ...]) -> list[dict[str, str]]:
    """Markdown tablosunu okur; başlıklar Türkçe küçük harfe çevrilip beklenenlerle eşlenir."""
    if not yol.is_file():
        return []
    satirlar = [s.strip() for s in dosya_oku.metin_oku(yol, uyar=False).splitlines() if s.strip().startswith("|")]
    if len(satirlar) < 2:
        return []
    basliklar = [anahtar(h) for h in satirlar[0].strip("|").split("|")]
    sonuc = []
    for i, satir in enumerate(satirlar[1:], start=2):
        hucreler = [h.strip() for h in satir.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", h) for h in hucreler if h):
            continue
        kayit = {b: (hucreler[j] if j < len(hucreler) else "") for j, b in enumerate(basliklar)}
        kayit["_satir"] = str(i)
        if any(kayit.get(b) for b in beklenen):
            sonuc.append(kayit)
    return sonuc


def sozluk(proje: Path) -> list[dict[str, Any]]:
    sonuc = []
    for s in tablo_oku(proje / "kurgu" / "sozluk.md", ("terim",)):
        yanlis = [y.strip() for y in re.split(r"[,;]", s.get("yanlış yazımlar", "")) if y.strip() and y.strip() != "-"]
        sonuc.append({"terim": s.get("terim", ""), "anlam": s.get("anlamı", s.get("anlam", "")), "yanlis": yanlis})
    return [s for s in sonuc if s["terim"]]


def zaman_cizelgesi(proje: Path) -> list[dict[str, Any]]:
    sonuc = []
    for s in tablo_oku(proje / "kurgu" / "zaman-cizelgesi.md", ("olay", "tarih")):
        yil = re.search(r"(?<!\d)(1\d{3}|2\d{3})(?!\d)", s.get("tarih", ""))
        bolum = re.search(r"\d+", s.get("bölüm", ""))
        kisiler = [k.strip() for k in re.split(r"[,;]", s.get("kişiler", "")) if k.strip() and k.strip() != "-"]
        sonuc.append({"tarih": s.get("tarih", ""), "yil": int(yil.group()) if yil else None, "olay": s.get("olay", ""),
                      "kisiler": kisiler, "bolum": int(bolum.group()) if bolum else None, "satir": int(s["_satir"])})
    return sonuc


def iliskiler(proje: Path) -> list[dict[str, Any]]:
    sonuc = []
    for s in tablo_oku(proje / "kurgu" / "iliskiler.md", ("kimden", "kime")):
        bolum = re.search(r"\d+", s.get("bölüm", ""))
        sonuc.append({"kimden": s.get("kimden", ""), "kime": s.get("kime", ""), "iliski": s.get("ilişki", ""),
                      "bolum": int(bolum.group()) if bolum else 0, "not": s.get("not", ""), "satir": int(s["_satir"])})
    return [s for s in sonuc if s["kimden"] and s["kime"]]


# ---------------------------------------------------------------- ad eşleme

def _ad_deseni(ad: str) -> str:
    """Türkçe ekleri tolere eden (küçük harfli metinde aranacak) desen."""
    kucuk = anahtar(ad)
    kelimeler = kucuk.split()
    if not kelimeler:
        return r"(?!x)x"
    son = kelimeler[-1]
    govde = re.escape(son)
    if len(son) >= 3 and son[-1] in YUMUSAMA:  # kitap → kitabı, ağaç → ağacı
        govde = re.escape(son[:-1]) + f"[{son[-1]}{YUMUSAMA[son[-1]]}]"
    onceki = "".join(re.escape(k) + r"\s+" for k in kelimeler[:-1])
    return rf"(?<![{HARF}]){onceki}{govde}(?:['’][{HARF}]+|[{HARF}]{{0,5}})?(?![{HARF}])"


class AdEsleyici:
    """Kayıtların ad ve diğer adlarını metinde bulur. Karakterlerin tek başına ilk adı,
    başka bir kayıtla çakışmıyorsa (ör. "Defne Aras" → "Defne") ayrıca aranır."""

    def __init__(self, kayitlar: list[Kayit]) -> None:
        bicim_sayaci: Counter[str] = Counter()
        adaylar: list[tuple[Kayit, list[str]]] = []
        for k in kayitlar:
            if k.tur == "dunya":
                continue
            bicimler = list(k.adlar)
            if k.tur == "karakter" and " " in k.ad:
                ilk = k.ad.split()[0]
                if len(ilk) >= 3 and anahtar(ilk) not in UNVANLAR:
                    bicimler.append(ilk)
            adaylar.append((k, bicimler))
            for b in set(anahtar(x) for x in bicimler):
                bicim_sayaci[b] += 1
        self.desenler: list[tuple[Kayit, re.Pattern[str]]] = []
        for k, bicimler in adaylar:
            gecerli = [b for b in dict.fromkeys(bicimler) if b == k.ad or bicim_sayaci[anahtar(b)] == 1]
            gecerli.sort(key=len, reverse=True)
            self.desenler.append((k, re.compile("|".join(_ad_deseni(b) for b in gecerli))))

    def say(self, metin: str) -> Counter[str]:
        kucuk = tk.tr_kucuk(metin)
        return Counter({k.ad: len(d.findall(kucuk)) for k, d in self.desenler if d.search(kucuk)})

    def satirlarda(self, metin: str) -> list[tuple[int, str, str]]:
        """(satır no, kayıt adı, satır) üçlüleri."""
        sonuc = []
        for no, satir in enumerate(metin.splitlines(), start=1):
            kucuk = tk.tr_kucuk(satir)
            for k, d in self.desenler:
                if d.search(kucuk):
                    sonuc.append((no, k.ad, satir))
        return sonuc


def levenshtein(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 1:
        return 2
    onceki = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        simdi = [i]
        for j, cb in enumerate(b, 1):
            simdi.append(min(onceki[j] + 1, simdi[j - 1] + 1, onceki[j - 1] + (ca != cb)))
        onceki = simdi
    return onceki[-1]


def bulgu(duzey: str, kimlik: str, ileti: str, **ek: Any) -> dict[str, Any]:
    return {"duzey": duzey, "kimlik": kimlik, "ileti": ileti, **ek}


# ---------------------------------------------------------------- komutlar

def olustur(proje: Path, tur: str, ad: str) -> Path:
    kitap_proje.proje_klasoru(proje)
    ad = ad.strip()
    if not ad or len(ad) > 80 or "\n" in ad:
        raise AnsiklopediHatasi("--ad boş olamaz, en fazla 80 karakter ve tek satır olmalı")
    mevcut = {anahtar(a): k for k in kayitlari_oku(proje) for a in k.adlar}
    if anahtar(ad) in mevcut:
        raise AnsiklopediHatasi(f"'{ad}' zaten kayıtlı: {mevcut[anahtar(ad)].yol}")
    klasor = proje / "kurgu" / TURLER[tur][0]
    klasor.mkdir(parents=True, exist_ok=True)
    yol = klasor / f"{slug(ad)}.md"
    sira = 2
    while yol.exists():
        yol = klasor / f"{slug(ad)}-{sira}.md"
        sira += 1
    satirlar = [f"# {ad}", "", *(f"- {alan}: " for alan in SABLONLAR[tur]), "", "## Notlar", ""]
    if tur == "karakter":
        satirlar += ["## Karakter Mülakatı", "",
                     "Yanıtları karakterin ağzından, birinci tekil kişiyle yazın. Boş bırakılan soru sorun değildir.", ""]
        satirlar += [f"**{s}**\n\n" for s in MULAKAT]
    yol.write_text("\n".join(satirlar).rstrip() + "\n", encoding="utf-8", newline="\n")
    return yol


def dogrula(proje: Path) -> list[dict[str, Any]]:
    kayitlar = kayitlari_oku(proje)
    bulgular: list[dict[str, Any]] = []
    sahip: dict[str, Kayit] = {}
    for k in kayitlar:
        for ad in k.adlar:
            a = anahtar(ad)
            if a in sahip and sahip[a] is not k:
                bulgular.append(bulgu("hata", "cift-ad", f"'{ad}' iki kayıtta geçiyor: {sahip[a].yol.name} ve {k.yol.name}",
                                      dosya=str(k.yol)))
            sahip.setdefault(a, k)
        for alan in ("yaş", "doğum yılı", "öldüğü bölüm", "i̇lk görünüş", "ilk görünüş"):
            deger = k.alanlar.get(alan, "")
            if deger and deger not in ("-", "?", "—") and k.sayi_alani(alan) is None:
                bulgular.append(bulgu("uyari", "sayi-degil", f"{k.ad}: '{alan}' alanı sayı içermiyor: {deger!r}",
                                      dosya=str(k.yol)))
        yas, dogum = k.sayi_alani("yaş"), k.sayi_alani("doğum yılı")
        if yas is not None and not 0 <= yas <= 130:
            bulgular.append(bulgu("hata", "yas-araligi", f"{k.ad}: yaş {yas} olamaz", dosya=str(k.yol)))
        if k.tur == "karakter" and yas is not None and dogum is not None:
            k.alanlar.setdefault("_hikaye_yili", str(dogum + yas))
    karakter_adlari = {anahtar(a): k for k in kayitlar if k.tur == "karakter" for a in k.adlar}
    tum_adlar = {anahtar(a) for k in kayitlar for a in k.adlar}
    for il in iliskiler(proje):
        for taraf in ("kimden", "kime"):
            if anahtar(il[taraf]) not in tum_adlar:
                bulgular.append(bulgu("uyari", "iliski-bilinmeyen", f"iliskiler.md satır {il['satir']}: '{il[taraf]}' "
                                      "ansiklopedide kayıtlı değil (olustur komutuyla ekleyin)"))
        if anahtar(il["kimden"]) == anahtar(il["kime"]):
            bulgular.append(bulgu("hata", "iliski-kendisi", f"iliskiler.md satır {il['satir']}: '{il['kimden']}' kendisiyle ilişkili gösterilmiş"))
    for olay in zaman_cizelgesi(proje):
        for kisi in olay["kisiler"]:
            k = karakter_adlari.get(anahtar(kisi))
            if k is None:
                if anahtar(kisi) not in tum_adlar:
                    bulgular.append(bulgu("uyari", "zaman-bilinmeyen", f"zaman-cizelgesi.md satır {olay['satir']}: "
                                          f"'{kisi}' ansiklopedide kayıtlı değil"))
                continue
            dogum = k.sayi_alani("doğum yılı")
            if dogum is not None and olay["yil"] is not None and olay["yil"] < dogum:
                bulgular.append(bulgu("hata", "dogmadan-once", f"zaman-cizelgesi.md satır {olay['satir']}: {k.ad} "
                                      f"{dogum} doğumlu ama {olay['yil']} yılındaki olaya katılıyor: {olay['olay']}"))
            olum = k.sayi_alani("öldüğü bölüm")
            if olum is not None and olay["bolum"] is not None and olay["bolum"] > olum:
                bulgular.append(bulgu("hata", "olumden-sonra", f"zaman-cizelgesi.md satır {olay['satir']}: {k.ad} "
                                      f"{olum}. bölümde ölüyor ama {olay['bolum']}. bölümdeki olayda yer alıyor"))
    sozluk_terimleri: dict[str, str] = {}
    for s in sozluk(proje):
        for yanlis in s["yanlis"]:
            if anahtar(yanlis) == anahtar(s["terim"]):
                bulgular.append(bulgu("hata", "sozluk-kendisi", f"sozluk.md: '{s['terim']}' kendi yanlış yazımı olarak verilmiş"))
        if anahtar(s["terim"]) in sozluk_terimleri:
            bulgular.append(bulgu("uyari", "sozluk-cift", f"sozluk.md: '{s['terim']}' iki kez tanımlanmış"))
        sozluk_terimleri[anahtar(s["terim"])] = s["terim"]
    return bulgular


def _tanidik_kelimeler(kayitlar: list[Kayit], proje: Path) -> set[str]:
    tanidik = set(UNVANLAR) | TAKVIM | SIK_BUYUK
    for k in kayitlar:
        for ad in k.adlar:
            tanidik.update(anahtar(p) for p in ad.split())
    for s in sozluk(proje):
        tanidik.update(anahtar(p) for p in s["terim"].split())
    return tanidik


def tutarlilik(proje: Path, bolum: int | None = None) -> list[dict[str, Any]]:
    kayitlar = kayitlari_oku(proje)
    esleyici = AdEsleyici(kayitlar)
    tum_bolumler = kitap_proje.bolumler(proje)
    secili = [b for b in tum_bolumler if bolum is None or b.no == bolum]
    if bolum is not None and not secili:
        raise AnsiklopediHatasi(f"{bolum}. bölümün metin dosyası bulunamadı")
    bulgular: list[dict[str, Any]] = []
    kayit_adi = {k.ad: k for k in kayitlar}
    sozluk_listesi = sozluk(proje)
    tanidik = _tanidik_kelimeler(kayitlar, proje)
    bilinmeyen: Counter[str] = Counter()
    bilinmeyen_yer: dict[str, str] = {}
    ad_kelimeleri = {anahtar(p): p for k in kayitlar if k.tur != "dunya" for a in k.adlar for p in a.split()
                     if len(p) >= 4 and anahtar(p) not in UNVANLAR}
    for b in secili:
        govde = b.satir_govdesi
        for no, ad, satir in esleyici.satirlarda(govde):
            k = kayit_adi[ad]
            olum = k.sayi_alani("öldüğü bölüm")
            if olum is not None and b.no > olum:
                ani = any(s in tk.tr_kucuk(satir) for s in ("hatırla", "anı", "rahmetli", "mezar", "fotoğraf", "rüya",
                                                             "özle", "eskiden", "yıllar önce", "ölmüş", "ölen"))
                if not ani:
                    bulgular.append(bulgu("uyari", "olumden-sonra-gorunum", f"{b.yol.name}:{no}: {k.ad} {olum}. bölümde "
                                          "öldü; burada anı/fotoğraf bağlamı olmadan geçiyor", dosya=str(b.yol), satir=no))
            ilk = k.sayi_alani("ilk görünüş")
            if ilk is not None and b.no < ilk:
                bulgular.append(bulgu("uyari", "erken-gorunum", f"{b.yol.name}:{no}: {k.ad} için ilk görünüş "
                                      f"{ilk}. bölüm olarak planlanmış ama {b.no}. bölümde geçiyor",
                                      dosya=str(b.yol), satir=no))
        satirlar = govde.splitlines()
        for s in sozluk_listesi:
            for yanlis in s["yanlis"]:
                desen = re.compile(_ad_deseni(yanlis))
                for no, satir in enumerate(satirlar, start=1):
                    if desen.search(tk.tr_kucuk(satir)):
                        bulgular.append(bulgu("hata", "sozluk-yanlis", f"{b.yol.name}:{no}: '{yanlis}' yazılmış; "
                                              f"sözlükteki doğru biçim '{s['terim']}'", dosya=str(b.yol), satir=no))
        for no, satir in enumerate(satirlar, start=1):
            eslesmeler = list(BUYUK_KELIME.finditer(satir))
            atla = set()
            for i, m in enumerate(eslesmeler):
                if i in atla:
                    continue
                kelime = m.group(1)
                k = anahtar(kelime)
                if k in tanidik:
                    continue
                if CUMLE_BASI.search(satir[:m.start()]):
                    # Cümle başındaki büyük harf ad kanıtı değildir; yalnızca kayıtlı bir adın yanlış yazımı mı diye bak.
                    yakin = next((ad_kelimeleri[a] for a in ad_kelimeleri if a != k and len(k) >= 4
                                  and a[0] == k[0] and levenshtein(a, k) == 1), None)
                    if yakin:
                        bulgular.append(bulgu("uyari", "ad-kaymasi", f"{b.yol.name}:{no}: '{kelime}' ansiklopedideki "
                                              f"'{yakin}' adının yanlış yazımı olabilir", dosya=str(b.yol), satir=no))
                    continue
                j = i  # bitişik büyük harfli kelimeler tek ad sayılır: "Kara Kuzu"
                while j + 1 < len(eslesmeler) and satir[eslesmeler[j].end():eslesmeler[j + 1].start()] == " " \
                        and eslesmeler[j].group(0) == eslesmeler[j].group(1):
                    j += 1
                    atla.add(j)
                if j > i:
                    kelime = " ".join(e.group(1) for e in eslesmeler[i:j + 1])
                    bilinmeyen[kelime] += 1
                    bilinmeyen_yer.setdefault(kelime, f"{b.yol.name}:{no}")
                    continue
                yakin = next((ad_kelimeleri[a] for a in ad_kelimeleri if a != k and len(k) >= 4
                              and a[0] == k[0] and levenshtein(a, k) == 1), None)
                if yakin:
                    bulgular.append(bulgu("uyari", "ad-kaymasi", f"{b.yol.name}:{no}: '{kelime}' ansiklopedideki "
                                          f"'{yakin}' adının yanlış yazımı olabilir", dosya=str(b.yol), satir=no))
                    continue
                bilinmeyen[kelime] += 1
                bilinmeyen_yer.setdefault(kelime, f"{b.yol.name}:{no}")
    for kelime, adet in bilinmeyen.most_common(25):
        if adet >= 2:
            bulgular.append(bulgu("bilgi", "kayitsiz-ad", f"'{kelime}' {adet} kez geçiyor ama ansiklopedide yok "
                                  f"(ilk: {bilinmeyen_yer[kelime]}); kalıcı bir ad ise kaydedin"))
    return bulgular


def dagilim(proje: Path) -> dict[str, Any]:
    kayitlar = kayitlari_oku(proje)
    esleyici = AdEsleyici(kayitlar)
    bolumler = kitap_proje.bolumler(proje)
    matris: dict[str, dict[int, int]] = defaultdict(dict)
    bakis: dict[int, str] = {}
    uzunluk: dict[int, int] = {}
    for b in bolumler:
        uzunluk[b.no] = b.kelime
        for ad, adet in esleyici.say(b.govde).items():
            matris[ad][b.no] = adet
        plan = kitap_proje.plan_dosyasi(proje, b.no)
        if plan:
            m = re.search(r"^[ \t]*[-*][ \t]+\**(?:Bakış açısı|Anlatıcı|BA)\**[ \t]*:[ \t]*(.+)$", dosya_oku.metin_oku(plan, uyar=False),
                          re.M | re.I)
            if m:
                bakis[b.no] = m.group(1).strip()
    uyarilar = []
    numaralar = [b.no for b in bolumler]
    for k in kayitlar:
        if k.tur == "dunya":
            continue
        gorulen = matris.get(k.ad, {})
        rol = tk.tr_kucuk(k.alanlar.get("rol", ""))
        if k.tur == "karakter" and "ana" in rol and len(numaralar) >= 4:
            en_uzun = sira = 0
            bas = None
            for no in numaralar:
                if gorulen.get(no):
                    sira = 0
                else:
                    sira += 1
                    if sira > en_uzun:
                        en_uzun, bas = sira, no - sira + 1
            if en_uzun >= 4:
                uyarilar.append(f"{k.ad} (ana karakter) {bas}. bölümden itibaren {en_uzun} bölüm boyunca hiç geçmiyor")
        if numaralar and not gorulen and k.sayi_alani("ilk görünüş") is None:
            uyarilar.append(f"{k.ad} ({TURLER[k.tur][1].lower()}) hiçbir bölümde geçmiyor")
    return {"bolumler": numaralar, "uzunluk": uzunluk, "bakis_acisi": bakis,
            "kayitlar": [{"ad": k.ad, "tur": k.tur, "gorunumler": matris.get(k.ad, {})} for k in kayitlar if k.tur != "dunya"],
            "uyarilar": uyarilar}


def dagilim_metni(v: dict[str, Any]) -> str:
    if not v["bolumler"]:
        return "Henüz bölüm yok."
    gen = max(4, max((len(tk.tr_sayi(v["uzunluk"][n])) for n in v["bolumler"]), default=0) + 1)
    basliklar = "".join(f"{n:>{gen}}" for n in v["bolumler"])
    s = [f"{'Kayıt':<24}{basliklar}   Toplam"]
    for k in v["kayitlar"]:
        hucreler = "".join(f"{(k['gorunumler'].get(n) or '·'):>{gen}}" for n in v["bolumler"])
        s.append(f"{k['ad'][:23]:<24}{hucreler}   {sum(k['gorunumler'].values()):>6}")
    s.append(f"{'Kelime':<24}" + "".join(f"{tk.tr_sayi(v['uzunluk'][n]):>{gen}}" for n in v["bolumler"]))
    if v["bakis_acisi"]:
        s.append("Bakış açısı: " + ", ".join(f"{n}: {b}" for n, b in sorted(v["bakis_acisi"].items())))
    if v["uyarilar"]:
        s += ["", "Dikkat:"] + [f"  - {u}" for u in v["uyarilar"]]
    return "\n".join(s)


def dagilim_html(v: dict[str, Any], baslik: str) -> str:
    e = html.escape
    en_cok = max((a for k in v["kayitlar"] for a in k["gorunumler"].values()), default=1) or 1
    bas = "".join(f"<th>{n}</th>" for n in v["bolumler"])
    satirlar = []
    for k in v["kayitlar"]:
        hucreler = []
        for n in v["bolumler"]:
            adet = k["gorunumler"].get(n, 0)
            saydam = 0 if not adet else 0.25 + 0.75 * adet / en_cok
            hucreler.append(f"<td style='background:rgba(242,184,75,{saydam:.2f})' title='{e(k['ad'])}, {n}. bölüm: {adet}'>"
                            f"{adet or ''}</td>")
        satirlar.append(f"<tr><th class='ad'>{e(k['ad'])} <small>{e(TURLER[k['tur']][1])}</small></th>{''.join(hucreler)}</tr>")
    uyari = "".join(f"<li>{e(u)}</li>" for u in v["uyarilar"]) or "<li>Belirgin bir boşluk yok.</li>"
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><title>{e(baslik)} — Dağılım</title>
<style>body{{font-family:system-ui,sans-serif;background:#0b1526;color:#e8eef7;padding:24px}}
table{{border-collapse:collapse}} td,th{{border:1px solid #22385a;padding:4px 8px;text-align:center;min-width:28px}}
th.ad{{text-align:left;white-space:nowrap}} small{{color:#9fb0c8;font-weight:normal}}</style></head><body>
<h1>{e(baslik)} — bölümlere göre dağılım</h1><table><tr><th></th>{bas}</tr>{''.join(satirlar)}</table>
<h2>Dikkat</h2><ul>{uyari}</ul></body></html>
"""


def grafik(proje: Path, bolum: int | None = None, bicim: str = "mermaid") -> str:
    """İlişki grafiği; ``bolum`` verilirse o bölüme kadarki en son ilişki durumu gösterilir."""
    son: dict[tuple[str, str], dict[str, Any]] = {}
    for il in sorted(iliskiler(proje), key=lambda x: (x["bolum"], x["satir"])):
        if bolum is not None and il["bolum"] > bolum:
            continue
        son[(il["kimden"], il["kime"])] = il
    if not son:
        raise AnsiklopediHatasi("kurgu/iliskiler.md içinde (bu bölüme kadar) ilişki satırı yok")
    adlar = sorted({a for cift in son for a in cift})
    kimlik = {a: f"k{i}" for i, a in enumerate(adlar, 1)}
    temiz = lambda s: s.replace('"', "'").replace("|", "/")  # noqa: E731
    if bicim == "dot":
        s = ["digraph iliskiler {", '  graph [rankdir=LR, fontname="Helvetica"];', '  node [shape=box, style=rounded];']
        s += [f'  {kimlik[a]} [label="{temiz(a)}"];' for a in adlar]
        s += [f'  {kimlik[a]} -> {kimlik[b]} [label="{temiz(il["iliski"])}"];' for (a, b), il in son.items()]
        return "\n".join(s + ["}"])
    s = ["```mermaid", "graph LR"]
    s += [f'  {kimlik[a]}["{temiz(a)}"]' for a in adlar]
    s += [f'  {kimlik[a]} -->|"{temiz(il["iliski"]) or "ilişki"}"| {kimlik[b]}' for (a, b), il in son.items()]
    return "\n".join(s + ["```"])


def _acik_ipuclari(proje: Path) -> list[dict[str, Any]]:
    return kitap_proje.acik_ipuclari(proje)


def baglam(proje: Path, bolum: int, sinir: int = 12000) -> str:
    plan = kitap_proje.plan_dosyasi(proje, bolum)
    if plan is None:
        raise AnsiklopediHatasi(f"{bolum}. bölümün planı yok: plan/bolum-plani_{bolum:03d}.md")
    plan_metni = dosya_oku.metin_oku(plan, uyar=False)
    kayitlar = kayitlari_oku(proje)
    esleyici = AdEsleyici(kayitlar)
    sayim = esleyici.say(plan_metni)
    onceki = [b for b in kitap_proje.bolumler(proje) if b.no < bolum]
    son_paragraf = ""
    if onceki:
        paragraflar = [p.strip() for p in onceki[-1].govde.split("\n\n") if p.strip()]
        son_paragraf = paragraflar[-1] if paragraflar else ""
        for ad, adet in esleyici.say(son_paragraf).items():
            sayim[ad] += adet
    secilen = [k for k in kayitlar if k.ad in sayim]
    oncelik = {"karakter": 0, "mekan": 1, "nesne": 2, "grup": 3, "dunya": 4}
    secilen.sort(key=lambda k: (oncelik[k.tur], -sayim[k.ad], k.ad))
    adlar = {anahtar(a) for k in secilen for a in k.adlar}
    parcalar = [f"# Bağlam paketi — {bolum}. bölüm", "",
                f"Kaynak: {plan.name}. Planda ve önceki bölümün son paragrafında geçen {len(secilen)} kayıt; "
                "önem sırasıyla. Sınır aşılırsa son kayıtlar kısaltılır.", ""]
    if son_paragraf:
        parcalar += ["## Önceki bölümün son paragrafı", "", son_paragraf, ""]
    il_satir = [f"- {il['kimden']} → {il['kime']}: {il['iliski']} (bölüm {il['bolum'] or '?'})"
                for il in iliskiler(proje) if il["bolum"] <= bolum
                and anahtar(il["kimden"]) in adlar and anahtar(il["kime"]) in adlar]
    if il_satir:
        parcalar += ["## Aralarındaki ilişkiler", "", *il_satir[-15:], ""]
    olaylar = [f"- {o['tarih']}: {o['olay']}" for o in zaman_cizelgesi(proje)
               if any(anahtar(k) in adlar for k in o["kisiler"]) and (o["bolum"] is None or o["bolum"] <= bolum)]
    if olaylar:
        parcalar += ["## İlgili zaman olayları", "", *olaylar[-12:], ""]
    kucuk_plan = tk.tr_kucuk(plan_metni)
    terimler = [f"- **{s['terim']}**: {s['anlam']}" for s in sozluk(proje) if re.search(_ad_deseni(s["terim"]), kucuk_plan)]
    if terimler:
        parcalar += ["## Sözlük", "", *terimler, ""]
    ipuclari = [f"- {i.get('id', '?')}: {i.get('ozet', '')} (ekildiği bölüm {i.get('ekildigi_bolum', '?')}, "
                f"planlanan çözüm {i.get('planlanan_cozum_bolumu', '?')})" for i in _acik_ipuclari(proje)]
    if ipuclari:
        parcalar += ["## Açık ipuçları", "", *ipuclari[:15], ""]
    parcalar += ["## Kayıtlar", ""]
    metin = "\n".join(parcalar) + "\n"
    for k in secilen:
        kart = k.govde.split("## Karakter Mülakatı")[0].strip()
        kart = re.sub(r"^#\s+", f"### {TURLER[k.tur][1]}: ", kart, count=1)
        if len((metin + kart).encode("utf-8")) > sinir:
            alanlar = "; ".join(f"{a}: {d}" for a, d in k.alanlar.items() if d and not a.startswith("_"))
            kart = f"### {TURLER[k.tur][1]}: {k.ad}\n{alanlar[:300]}"
            if len((metin + kart).encode("utf-8")) > sinir:
                metin += f"\n(Sınır nedeniyle {len(secilen) - secilen.index(k)} kayıt atlandı.)\n"
                break
        metin += kart + "\n\n"
    return metin.rstrip() + "\n"


def bulgu_metni(bulgular: list[dict[str, Any]]) -> str:
    if not bulgular:
        return "Sorun bulunmadı."
    isaret = {"hata": "✗", "uyari": "!", "bilgi": "·"}
    s = [f"{isaret[b['duzey']]} [{b['kimlik']}] {b['ileti']}" for b in bulgular]
    say = Counter(b["duzey"] for b in bulgular)
    s.append(f"\nToplam: {say['hata']} hata, {say['uyari']} uyarı, {say['bilgi']} bilgi")
    return "\n".join(s)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Kurgu ansiklopedisi: kayıtlar, tutarlılık, dağılım, ilişki grafiği, bağlam paketi.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_o = alt.add_parser("olustur", help="şablondan yeni kayıt dosyası oluştur")
    p_o.add_argument("--tur", choices=tuple(TURLER), required=True, help="kayıt türü")
    p_o.add_argument("--ad", required=True, help="kaydın adı (ör. \"Defne Aras\")")
    p_l = alt.add_parser("listele", help="kayıtları listele")
    p_l.add_argument("--tur", choices=tuple(TURLER), help="yalnızca bu türü listele")
    p_d = alt.add_parser("dogrula", help="kayıtların kendi içindeki tutarlılığını denetle")
    p_t = alt.add_parser("tutarlilik", help="bölüm metinlerini ansiklopediyle karşılaştır")
    p_t.add_argument("--bolum", type=int, help="yalnızca bu bölümü denetle")
    p_g = alt.add_parser("dagilim", help="kayıtların bölümlere dağılımı")
    p_g.add_argument("--html", type=Path, help="ısı haritasını bu HTML dosyasına yaz")
    p_r = alt.add_parser("grafik", help="ilişki grafiği (Mermaid ya da Graphviz DOT)")
    p_r.add_argument("--bolum", type=int, help="bu bölüme kadarki ilişki durumunu göster")
    p_r.add_argument("--bicim", choices=("mermaid", "dot"), default="mermaid", help="çıktı biçimi")
    p_b = alt.add_parser("baglam", help="yazılacak bölüm için bağlam paketi üret")
    p_b.add_argument("--bolum", type=int, required=True, help="yazılacak bölümün numarası")
    p_b.add_argument("--sinir", type=int, default=12000, help="paketin en büyük boyutu (bayt, varsayılan 12000)")
    p_b.add_argument("--cikti", type=Path, help="paketi bu dosyaya yaz (varsayılan: standart çıktı)")
    for p in (p_o, p_l, p_d, p_t, p_g, p_r, p_b):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    for p in (p_l, p_d, p_t, p_g):
        p.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "olustur":
            print(f"Kayıt oluşturuldu: {olustur(arg.proje, arg.tur, arg.ad)}")
        elif arg.komut == "listele":
            kayitlar = [k for k in kayitlari_oku(arg.proje) if not arg.tur or k.tur == arg.tur]
            if arg.json:
                print(json.dumps([{"tur": k.tur, "ad": k.ad, "dosya": k.yol.as_posix(),
                                   "alanlar": {a: d for a, d in k.alanlar.items() if not a.startswith("_")}}
                                  for k in kayitlar], ensure_ascii=False, indent=2))
            else:
                for k in kayitlar:
                    ozet = ", ".join(f"{a}: {d}" for a, d in list(k.alanlar.items())[:4] if d and not a.startswith("_"))
                    print(f"{TURLER[k.tur][1]:<14} {k.ad:<28} {ozet[:70]}")
                print(f"\n{len(kayitlar)} kayıt" + ("" if kayitlar else " (olustur komutuyla ekleyin)"))
        elif arg.komut in ("dogrula", "tutarlilik"):
            bulgular = dogrula(arg.proje) if arg.komut == "dogrula" else tutarlilik(arg.proje, arg.bolum)
            print(json.dumps(bulgular, ensure_ascii=False, indent=2) if arg.json else bulgu_metni(bulgular))
            return 1 if any(b["duzey"] == "hata" for b in bulgular) else 0
        elif arg.komut == "dagilim":
            veri = dagilim(arg.proje)
            print(json.dumps(veri, ensure_ascii=False, indent=2) if arg.json else dagilim_metni(veri))
            if arg.html:
                arg.html.parent.mkdir(parents=True, exist_ok=True)
                arg.html.write_text(dagilim_html(veri, kitap_proje.kitap_basligi(arg.proje)), encoding="utf-8", newline="\n")
        elif arg.komut == "grafik":
            print(grafik(arg.proje, arg.bolum, arg.bicim))
        else:
            if arg.sinir < 1000:
                raise AnsiklopediHatasi("--sinir en az 1000 bayt olmalı")
            paket = baglam(arg.proje, arg.bolum, arg.sinir)
            if arg.cikti:
                arg.cikti.parent.mkdir(parents=True, exist_ok=True)
                arg.cikti.write_text(paket, encoding="utf-8", newline="\n")
                print(f"Bağlam paketi yazıldı: {arg.cikti} ({len(paket.encode('utf-8'))} bayt)")
            else:
                print(paket, end="")
    except (AnsiklopediHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
