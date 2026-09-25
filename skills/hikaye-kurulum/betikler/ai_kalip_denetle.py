#!/usr/bin/env python3
"""Türkçe metinde "yapay zekâ tadı" veren kalıpları bulur ve raporlar.

Bu bir yazım denetleyicisidir (lint), yapay zekâ dedektörü değildir. Amaç,
okurun "bunu makine yazmış" hissine kapıldığı bilinen kalıpları satır ve sütun
numarasıyla göstermek ve bir düzeltme yönü önermektir. Metni asla kendisi
değiştirmez: güvenli düzeltme bağlama bağlıdır.

Önem düzeyleri:
  engelleyici  Üretim ve temizlik sırasında mutlaka düzeltilmesi gerekenler.
  uyari        Yoğunluk ya da tercih meselesi; işlevli bir kullanım korunabilir.

Kitap kökündeki ``.yz-beyaz-liste`` dosyasında her satıra yazılan birebir
ifadeler (yazarın bilinçli üslup tercihleri) taramadan çıkarılır.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

ENGELLEYICI = "engelleyici"
UYARI = "uyari"
UZUN_PARAGRAF_KELIME = 180
KESIK_CUMLE_DIZISI = 6
KESIK_CUMLE_KELIME = 4
KLISE_ESIGI_1000 = 4.0      # 1000 kelimede klişe sayısı
BENZETME_ESIGI_1000 = 12.0  # 1000 kelimede benzetme işareti
TIRE_ESIGI_1000 = 3.0       # anlatıda cümle içi uzun tire
SON_PENCERE_SATIR = 6


@dataclass
class Bulgu:
    dosya: str
    satir: int
    sutun: int
    onem: str
    kural: str
    alinti: str
    oneri: str


def _alinti(satir: str, bas: int, son: int) -> str:
    return satir[max(0, bas - 10): min(len(satir), son + 10)].strip()


def beyaz_liste_yukle(dosya: Path) -> list[str]:
    for klasor in [dosya.parent, *dosya.parents][:4]:
        aday = klasor / ".yz-beyaz-liste"
        if aday.is_file():
            return [s.strip() for s in aday.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#")]
    return []


def maskele(metin: str, beyaz: list[str]) -> str:
    for ifade in beyaz:
        metin = metin.replace(ifade, " " * len(ifade))
    return metin


def _cumleler(metin: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<=[.!?…])\s+", metin) if c.strip()]


def denetle_metin(metin: str, dosya: str = "<metin>", beyaz: list[str] | None = None) -> list[Bulgu]:
    metin = maskele(metin.replace("\r\n", "\n"), beyaz or [])
    satirlar = metin.split("\n")
    bulgular: list[Bulgu] = []
    kelime_sayisi = max(1, len(tk.KELIME.findall(metin)))

    def ekle(no: int, bas: int, son: int, onem: str, kural: str, oneri: str) -> None:
        bulgular.append(Bulgu(dosya, no, bas + 1, onem, kural, _alinti(satirlar[no - 1], bas, son), oneri))

    klise_sayisi = benzetme_sayisi = tire_sayisi = 0
    ilk_klise: tuple[int, int, int] | None = None
    ilk_benzetme: tuple[int, int, int] | None = None
    ilk_tire: tuple[int, int, int] | None = None
    icerik_satirlari = [i for i, s in enumerate(satirlar, 1) if s.strip() and not s.lstrip().startswith("#")]
    son_pencere = set(icerik_satirlari[-SON_PENCERE_SATIR:])

    for no, ham in enumerate(satirlar, 1):
        if not ham.strip() or ham.lstrip().startswith(("#", ">", "|")):
            continue
        diyalog = tk.diyalog_satiri_mi(ham)
        anlati = tk.tirnak_disi(ham)
        kucuk = tk.tr_kucuk(ham)
        kucuk_anlati = tk.tr_kucuk(anlati)

        # 1) "X değil, Y" / "sadece X değildi; bir Y'ydi" dönüşü (engelleyici)
        for m in re.finditer(r"\b(?:sadece|yalnızca|basit\s+bir|bu\s+bir)\b[^.!?\n]{1,60}?\bdeğil(?:di|dir|miş|mişti)?\b\s*[,;:—–]", kucuk_anlati):
            ekle(no, m.start(), m.end(), ENGELLEYICI, "degil-ama-donusu",
                 "Olumsuz kurulumu silin; asıl şeyi doğrudan söyleyin ya da eylemle gösterin.")
        for m in re.finditer(r"\bdeğil(?:di|dir)?\s*[,;—–]\s*(?:aksine\s+|tam\s+tersine\s+)?[^.!?\n]{2,50}?(?:ydi|ydı|ydu|ydü|idi|ıydı|iydi|dır|dir)\b", kucuk_anlati):
            if not re.search(r"\b(?:sadece|yalnızca|basit\s+bir|bu\s+bir)\b", kucuk_anlati[max(0, m.start() - 70):m.start()]):
                ekle(no, m.start(), m.end(), UYARI, "degil-ama-donusu",
                     "'X değil, Y' karşıtlığı tekrar ediyorsa birini silin; Y'yi doğrudan yazın.")

        # 2) bir yandan ... diğer/öte yandan (engelleyici)
        m = re.search(r"\bbir\s+yandan\b.*?\b(?:diğer|öte|öbür)\s+yandan\b", kucuk)
        if m:
            ekle(no, m.start(), m.end(), ENGELLEYICI, "bir-yandan-diger-yandan",
                 "Mekanik paralellik. İki şeyi aynı anda gösterin: 'Çayı karıştırırken gözü kapıdaydı.'")

        # 3) Olumsuzluk dizisi: "Korku yoktu. Tereddüt yoktu." / "ne X ne Y ne Z"
        if re.search(r"(?:\b\w+\s+yoktu\b[.,;]\s*){2,}\w+", kucuk_anlati) or re.search(r"\bne\s+\w+(?:\s+\w+)?\s+ne\s+\w+(?:\s+\w+)?\s+ne\s+\w+", kucuk_anlati):
            ekle(no, 0, min(len(ham), 60), ENGELLEYICI, "olumsuzluk-dizisi",
                 "Olmayanları saymak yerine olanı yazın: 'Elleri titremiyordu' yerine hareketi gösterin.")

        # 4) Ses karşıtlığı: "Sesi alçaktı ama / yüksek değildi ama ..."
        m = re.search(r"\bsesi\s+(?:alçak|yüksek|kısık|sakin|yumuşak)(?:tı|ti|tu|tü|dı|di)?(?:\s+değildi)?\s*(?:,|;)?\s*(?:ama|fakat|ancak|yine\s+de)\b", kucuk_anlati)
        if m:
            ekle(no, m.start(), m.end(), ENGELLEYICI, "ses-karsitligi",
                 "Kalıp karşıtlık. Sesin etkisini dinleyenin tepkisiyle gösterin.")

        # 5) Fragman kapanışı (yalnızca son satırlarda, engelleyici)
        if no in son_pencere:
            for ifade in tk.FRAGMAN_KAPANIS:
                i = kucuk.find(ifade)
                if i >= 0:
                    ekle(no, i, i + len(ifade), ENGELLEYICI, "fragman-kapanis",
                         "Bölümü özetleyip geleceği müjdeleyen cümleyi silin; somut bir eylem ya da replikle bitirin.")

        # 6) Klişe yoğunluğu ve 7) benzetme yoğunluğu (sayılır, sonra değerlendirilir)
        for ifade in tk.KLISE_IFADELER:
            for m in re.finditer(re.escape(ifade), kucuk_anlati):
                klise_sayisi += 1
                ilk_klise = ilk_klise or (no, m.start(), m.end())
        for m in tk.BENZETME_ISARETLERI.finditer(kucuk_anlati):
            benzetme_sayisi += 1
            ilk_benzetme = ilk_benzetme or (no, m.start(), m.end())

        # 8) "adeta" ve "sanki" zinciri: aynı cümlede birlikte ya da biri iki kez
        for cumle in _cumleler(kucuk_anlati):
            if (cumle.count("adeta") + cumle.count("sanki")) >= 2:
                i = kucuk_anlati.find(cumle)
                ekle(no, max(0, i), max(0, i) + min(len(cumle), 50), UYARI, "adeta-sanki-zinciri",
                     "Tek cümlede birden fazla 'adeta/sanki' var. Benzetmelerden birini seçin, diğerini silin.")

        # 9) Soyut doldurucular ve 10) çeviri kalkları
        for ifade in tk.SOYUT_DOLGU:
            for m in re.finditer(rf"\b{re.escape(ifade)}\b", kucuk_anlati):
                ekle(no, m.start(), m.end(), UYARI, "soyut-dolgu",
                     f"'{ifade}' anlatımı bulanıklaştırıyor; somut bir ayrıntıyla değiştirin ya da silin.")
        for ifade, oneri in tk.CEVIRI_KALKLARI.items():
            for m in re.finditer(rf"\b{re.escape(ifade)}\b", kucuk):
                ekle(no, m.start(), m.end(), UYARI, "ceviri-kalki", f"İngilizceden çeviri kokuyor; deneyin: {oneri}")
        for desen, oneri in tk.EDILGEN_DESENLER:
            for m in re.finditer(desen, kucuk_anlati):
                ekle(no, m.start(), m.end(), UYARI, "edilgen-ceviri-yapisi", oneri)

        # 11) Yığılmış sıfatlar: "karanlık, soğuk ve ürkütücü bir"
        for m in re.finditer(rf"\b[{tk.HARF}]+,\s+[{tk.HARF}]+(?:,\s+[{tk.HARF}]+)*\s+ve\s+[{tk.HARF}]+\s+bir\b", kucuk_anlati):
            ekle(no, m.start(), m.end(), UYARI, "yigilmis-sifat",
                 "Sıfat yığını. En keskin tek sıfatı bırakın ya da niteliği bir ayrıntıyla gösterin.")

        # 12) Anlatıda cümle içi uzun tire (diyalog çizgisi hariç)
        govde = ham.lstrip()
        bas_kayma = len(ham) - len(govde)
        if diyalog and govde[:1] in "—–":
            govde = govde[1:]
            bas_kayma += 1
        for m in re.finditer(r"\S\s*[—–]\s*\S", tk.tirnak_disi(govde)):
            if diyalog:
                continue  # konuşma içindeki ara söz tireleri doğaldır
            tire_sayisi += 1
            ilk_tire = ilk_tire or (no, bas_kayma + m.start(), bas_kayma + m.end())

        # 13) Uzun paragraf
        pk = len(tk.KELIME.findall(ham))
        if pk > UZUN_PARAGRAF_KELIME and not diyalog:
            ekle(no, 0, 40, UYARI, "uzun-paragraf",
                 f"{pk} kelimelik paragraf. Telefonda okunan metinde sahne ya da odak değiştiği yerden bölün.")

        # 14) Tırnakla vurgu: anlatıda 1-3 kelimelik tırnaklı ifadeler
        if not diyalog:
            vurgular = re.findall(r"[\"“'‘]([^\"”'’]{1,25})[\"”'’]", ham)
            if len([v for v in vurgular if 1 <= len(v.split()) <= 3]) >= 2:
                ekle(no, 0, 40, UYARI, "tirnakla-vurgu",
                     "Anlatıda kısa sözcükleri tırnakla vurgulamak yapay durur; vurguyu cümle kuruluşuyla verin.")

    # Kesik cümle dizisi (anlatıda art arda çok kısa cümleler)
    dizi = 0
    for no, ham in enumerate(satirlar, 1):
        if not ham.strip() or tk.diyalog_satiri_mi(ham) or ham.lstrip().startswith("#"):
            dizi = 0
            continue
        for cumle in _cumleler(ham):
            dizi = dizi + 1 if len(tk.KELIME.findall(cumle)) <= KESIK_CUMLE_KELIME else 0
            if dizi == KESIK_CUMLE_DIZISI:
                ekle(no, 0, 40, UYARI, "kesik-cumle-dizisi",
                     "Art arda çok kısa cümleler telgraf gibi okunuyor; bazılarını bağlaçlarla birleştirin.")

    # Yoğunluk kuralları
    olcek = 1000 / kelime_sayisi
    if ilk_klise and klise_sayisi * olcek >= KLISE_ESIGI_1000 and klise_sayisi >= 3:
        no, b, s = ilk_klise
        ekle(no, b, s, UYARI, "klise-yogunlugu",
             f"{klise_sayisi} klişe (1.000 kelimede {tk.tr_ondalik(klise_sayisi * olcek)}). Her birini karaktere özgü bir tepkiyle değiştirin.")
    if ilk_benzetme and benzetme_sayisi * olcek >= BENZETME_ESIGI_1000 and benzetme_sayisi >= 5:
        no, b, s = ilk_benzetme
        ekle(no, b, s, UYARI, "benzetme-yogunlugu",
             f"{benzetme_sayisi} benzetme işareti (1.000 kelimede {tk.tr_ondalik(benzetme_sayisi * olcek)}). En güçlü birkaçını bırakın.")
    if ilk_tire and tire_sayisi * olcek >= TIRE_ESIGI_1000 and tire_sayisi >= 2:
        no, b, s = ilk_tire
        ekle(no, b, s, ENGELLEYICI, "tire-yogunlugu",
             f"Anlatıda {tire_sayisi} cümle içi uzun tire. Türkçede virgül, iki nokta ya da yeni cümle kullanın.")
    bulgular.sort(key=lambda b: (b.satir, b.sutun, b.kural))
    return bulgular


def denetle_dosya(yol: Path) -> list[Bulgu]:
    return denetle_metin(yol.read_text(encoding="utf-8"), str(yol), beyaz_liste_yukle(yol))


def ozet(bulgular: list[Bulgu]) -> dict[str, int]:
    return {
        "toplam": len(bulgular),
        ENGELLEYICI: sum(1 for b in bulgular if b.onem == ENGELLEYICI),
        UYARI: sum(1 for b in bulgular if b.onem == UYARI),
    }


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("dosyalar", nargs="+", type=Path)
    ayr.add_argument("--json", action="store_true", help="bulguları JSON olarak yaz")
    ayr.add_argument("--basarisiz", choices=("engelleyici", "hepsi"), default="hepsi",
                     help="hangi bulgu çıkış kodunu 1 yapsın (varsayılan: hepsi)")
    arg = ayr.parse_args(argv)
    bulgular: list[Bulgu] = []
    for yol in arg.dosyalar:
        if not yol.is_file():
            print(f"Dosya bulunamadı: {yol}", file=sys.stderr)
            return 2
        bulgular.extend(denetle_dosya(yol))
    if arg.json:
        print(json.dumps({"ozet": ozet(bulgular), "bulgular": [asdict(b) for b in bulgular]}, ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b.dosya}:{b.satir}:{b.sutun}\t[{b.onem}] {b.kural}\t({b.alinti})\n\t→ {b.oneri}")
        o = ozet(bulgular)
        print(f"Toplam {o['toplam']} bulgu: {o[ENGELLEYICI]} engelleyici, {o[UYARI]} uyarı.")
    if arg.basarisiz == "engelleyici":
        return 1 if any(b.onem == ENGELLEYICI for b in bulgular) else 0
    return 1 if bulgular else 0


if __name__ == "__main__":
    sys.exit(main())
