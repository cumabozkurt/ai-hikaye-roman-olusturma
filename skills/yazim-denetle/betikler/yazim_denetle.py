#!/usr/bin/env python3
"""TDK Yazım Kılavuzu'na dayalı Türkçe yazım ve biçem denetleyicisi.

Denetlenenler:
  * yazim-hatasi      sık yapılan yazım yanlışları (herkez → herkes, birşey → bir şey)
  * de-da-bitisik     bağlaç "de/da"nın bitişik yazılması (bende öyle → ben de öyle)
  * ki-bitisik        bağlaç "ki"nin bitişik yazılması (dediki → dedi ki)
  * soru-eki-bitisik  soru eki "mı/mi"nin bitişik yazılması (geliyormusun → geliyor musun)
  * kesme-isareti     özel ada gelen ekin kesmeyle ayrılmaması (İstanbulda → İstanbul'da)
  * gayriresmi        konuşma dili biçimleri (yalnızca anlatıda uyarı; diyalogda serbest)
  * cumle-basi-kucuk  noktadan sonra küçük harfle başlayan cümle
  * yz-yogunlugu      yapay zekâ klişe yoğunluğu özeti (ai_kalip_denetle ile)

"hata" düzeyindeki bulgular çıkış kodunu 1 yapar; "uyari" düzeyindekiler yapmaz
(``--kati`` ile uyarılar da başarısız sayılır).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

H = tk.HARF

OZEL_ADLAR = (
    "Türkiye", "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Trabzon", "Eskişehir",
    "Kapadokya", "Anadolu", "Karadeniz", "Ege", "Akdeniz", "Boğaziçi", "Kadıköy", "Beyoğlu", "Üsküdar",
    "Avrupa", "Asya", "Almanya", "Fransa", "İngiltere", "Amerika", "Rusya", "Yunanistan", "Atatürk",
    "Wattpad", "Instagram", "Netflix", "Google", "Ayşe", "Fatma", "Mehmet", "Ahmet", "Mustafa", "Zeynep",
)
_EKLER = r"(?:da|de|ta|te|dan|den|tan|ten|a|e|ya|ye|ı|i|u|ü|yı|yi|yu|yü|ın|in|un|ün|nın|nin|nun|nün|la|le|yla|yle|lı|li|lu|lü|daki|deki|dır|dir|dur|dür)"
KESME_DESENI = re.compile(rf"\b({'|'.join(map(re.escape, OZEL_ADLAR))}){_EKLER}\b")
KI_FIIL = re.compile(
    rf"^(?:[{H}]+(?:yor|yorum|yorsun|yoruz|dı|di|du|dü|tı|ti|tu|tü|mış|miş|muş|müş|malı|meli|acak|ecek|sın|sin|sun|sün)|öyle|şöyle|böyle|de|der|sanır|bil)ki$",
    re.I,
)
SOYLEME = re.compile(r"(?:de(?:di|dim|din|dik|diler|mişti|miş|yip|r|rken)|diye|sor(?:du|ar|muştu)|bağır|fısılda|mırıldan|söyle|seslen|haykır|gülümse)", re.I)
KI_ISTISNA = re.compile(r"(?:mki|nki|şimdiki|evveliki|beriki|öteki)$", re.I)
SORU_SAHIS = re.compile(rf"\b(sen|ben|o|bu|şu|biz|siz|var|yok|doğru|tamam|gerçek|iyi|kötü|emin|hazır|burası|orası)(mı|mi|mu|mü|mısın|misin|musun|müsün|mıyım|miyim)\b", re.I)


@dataclass
class Bulgu:
    dosya: str
    satir: int
    sutun: int
    duzey: str
    kural: str
    bulunan: str
    oneri: str


def _anlati(satir: str) -> str:
    """Diyalog satırlarını ve tırnak içini çıkararak anlatı kısmını döndürür."""
    if tk.diyalog_satiri_mi(satir):
        return ""
    return tk.tirnak_disi(satir)


def denetle_metin(metin: str, dosya: str = "<metin>", *, yz_ozeti: bool = True) -> list[Bulgu]:
    bulgular: list[Bulgu] = []
    kod_blogu = False
    on_bilgi = metin.startswith("---\n")
    for no, satir in enumerate(metin.replace("\r\n", "\n").split("\n"), 1):
        if on_bilgi:
            if no > 1 and satir.strip() == "---":
                on_bilgi = False
            continue
        if satir.strip().startswith("```"):
            kod_blogu = not kod_blogu
            continue
        if kod_blogu or satir.lstrip().startswith(("#", "|", "<!--")):
            continue
        kucuk = tk.tr_kucuk(satir)

        def ekle(m_bas: int, duzey: str, kural: str, bulunan: str, oneri: str) -> None:
            bulgular.append(Bulgu(dosya, no, m_bas + 1, duzey, kural, bulunan, oneri))

        for yanlis, dogru in tk.YAZIM_HATALARI.items():
            for m in re.finditer(rf"(?<![{H}]){re.escape(yanlis)}(?![{H}])", kucuk):
                ekle(m.start(), "hata", "yazim-hatasi", satir[m.start():m.end()], f"TDK'ya göre: “{dogru}”")
        for m in tk.DE_DA_BAGLAC_IPUCU.finditer(satir):
            kelime = tk.tr_kucuk(m.group(1))
            ekle(m.start(), "hata", "de-da-bitisik", m.group(0), f"Bağlaç olan “de/da” ayrı yazılır: “{tk.DE_DA_HATALI.get(kelime, kelime)}”")
        for m in re.finditer(rf"[{H}]+", satir):
            kelime = tk.tr_kucuk(m.group(0))
            if (kelime.endswith("ki") and kelime not in tk.KI_BITISIK and not tk.KI_ILGI_EKI.match(kelime)
                    and not KI_ISTISNA.search(kelime) and KI_FIIL.match(kelime)):
                ekle(m.start(), "hata", "ki-bitisik", m.group(0), f"Bağlaç olan “ki” ayrı yazılır: “{m.group(0)[:-2]} ki”")
        for m in tk.SORU_EKI_BITISIK.finditer(satir):
            govde, ek = m.group(1), m.group(2)
            butun = tk.tr_kucuk(m.group(0))
            sonrasi = satir[m.end():m.end() + 30]
            kisisel = len(ek) > 2
            if butun in tk.SORU_EKI_ISTISNA or len(govde) < 4:
                continue
            if kisisel or re.match(r"^[^.!]*\?", sonrasi):
                ekle(m.start(), "hata", "soru-eki-bitisik", m.group(0), f"Soru eki ayrı yazılır: “{govde} {ek}”")
        for m in SORU_SAHIS.finditer(satir):
            if tk.tr_kucuk(m.group(0)) in tk.SORU_EKI_ISTISNA:
                continue
            if re.match(r"^[^.!]*\?", satir[m.end():m.end() + 30]):
                ekle(m.start(), "hata", "soru-eki-bitisik", m.group(0), f"Soru eki ayrı yazılır: “{m.group(1)} {m.group(2)}”")
        for m in KESME_DESENI.finditer(satir):
            ek = m.group(0)[len(m.group(1)):]
            ekle(m.start(), "hata", "kesme-isareti", m.group(0), f"Özel ada gelen ek kesmeyle ayrılır: “{m.group(1)}'{ek}”")
        anlati = tk.tr_kucuk(_anlati(satir))
        for gayri, dogru in tk.GAYRIRESMI.items():
            for m in re.finditer(rf"(?<![{H}]){re.escape(gayri)}(?![{H}])", anlati):
                ekle(m.start(), "uyari", "gayriresmi", gayri, f"Anlatıda ölçünlü dil: “{dogru}” (diyalogda bilinçli kullanım serbesttir)")
        for m in re.finditer(r"(?<![.\d])[.!?]\s+([a-zçğıöşü])", satir):
            onceki = satir[max(0, m.start() - 4):m.start() + 1]
            if re.search(r"\b(?:vb|vs|bkz|Dr|Prof|Av|Sn|No)\.$", onceki):
                continue
            if satir[m.start()] in "?!" and SOYLEME.match(satir[m.start(1):]):
                continue
            ekle(m.start(1) - 1, "uyari", "cumle-basi-kucuk", satir[m.start():m.start() + 12], "Cümle büyük harfle başlar.")
    if yz_ozeti:
        try:
            import ai_kalip_denetle as akd
            kelime = len(tk.KELIME.findall(metin))
            if kelime < 300:
                raise ValueError('özet için metin kısa')
            yz = [b for b in akd.denetle_metin(metin, dosya)]
            yogunluk = round(len(yz) * 1000 / kelime, 1)
            if yogunluk >= 6:
                derece = "yüksek"
            elif yogunluk >= 3:
                derece = "orta"
            else:
                derece = ""
            if derece:
                bulgular.append(Bulgu(dosya, 0, 0, "uyari", "yz-yogunlugu", f"1.000 kelimede {tk.tr_ondalik(yogunluk)}",
                                      f"Yapay zekâ klişe yoğunluğu {derece}; yz-tadi-gider becerisini çalıştırın."))
        except (ImportError, ValueError):  # özet isteğe bağlıdır
            pass
    return bulgular


def denetle_dosya(yol: Path, **kw: bool) -> list[Bulgu]:
    return denetle_metin(dosya_oku.metin_oku(yol), str(yol), **kw)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("dosyalar", nargs="+", type=Path)
    ayr.add_argument("--json", action="store_true")
    ayr.add_argument("--kati", action="store_true", help="uyarıları da başarısız say")
    ayr.add_argument("--yz-ozeti-yok", action="store_true")
    arg = ayr.parse_args(argv)
    bulgular = [b for y in arg.dosyalar for b in denetle_dosya(y, yz_ozeti=not arg.yz_ozeti_yok)]
    if arg.json:
        print(json.dumps([asdict(b) for b in bulgular], ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b.dosya}:{b.satir}:{b.sutun}\t[{b.duzey}] {b.kural}\t“{b.bulunan}” → {b.oneri}")
        hata = sum(b.duzey == "hata" for b in bulgular)
        print(f"Toplam {len(bulgular)} bulgu ({hata} hata, {len(bulgular) - hata} uyarı).")
    if any(b.duzey == "hata" for b in bulgular) or (arg.kati and bulgular):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
