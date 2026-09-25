#!/usr/bin/env python3
"""Ses izi (üslup parmak izi): yazarın ya da kitabın sesini sayısal bir profile çevirir ve yeni
bölümün bu sesten nerede ayrıldığını gösterir.

Ölçülenler (Türkçeye özgü göstergeler dahil): cümle ve paragraf uzunluğu, cümle
uzunluğu değişkenliği, diyalog oranı, kelime uzunluğu, kelime çeşitliliği (100
kelimelik kayan pencerede tür/örnek oranı), 1000 kelimede noktalama (virgül, noktalı
virgül, üç nokta, ünlem, soru, uzun çizgi), bağlaç ve işlev sözcükleri (ve, ama, ancak,
çünkü, sanki, bile, belki, ki, de/da) ve zarf-fiil yoğunluğu (-ken, -ince, -ip, -arak).

Kullanım::

    ses_izi.py cikar      --dosya bolum-001.md bolum-002.md [--cikti kurgu/ses-izi.json]
    ses_izi.py cikar      --proje KITAP [--bolumler 1-5]      # varsayılan çıktı: KITAP/kurgu/ses-izi.json
    ses_izi.py karsilastir --profil kurgu/ses-izi.json --dosya taslak.md [--esik 70] [--json]
    ses_izi.py karsilastir --proje KITAP --dosya taslak.md

Benzerlik puanı (0–100) sezgiseldir: özelliklerin profile uzaklığının (z puanı)
ortalamasından hesaplanır. Bir kalite yargısı değil, "bu bölüm kitabın geri kalanı
gibi mi okunuyor?" sorusunun ölçüsüdür. Profil çıkarmak için en az 1500 kelime önerilir.

Çıkış kodu: 0 başarılı, 1 benzerlik --esik değerinin altında, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402
import metin_analizi  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

PARCA_KELIME = 400
EN_AZ_KELIME = 150
ISLEV = ("ve", "ama", "fakat", "ancak", "çünkü", "sanki", "bile", "belki", "ki", "de", "da", "gibi", "hiç", "artık")
ZARF_FIIL = re.compile(r"(?:ken|[ıiuü]nc[ae]|[ıiuü]p|[ae]r[ae]k)$")
ACIKLAMA = {
    "cumle_ort": ("ortalama cümle uzunluğu", "kelime"),
    "cumle_degiskenlik": ("cümle uzunluğu değişkenliği", "oran"),
    "paragraf_ort": ("ortalama paragraf uzunluğu", "kelime"),
    "diyalog_orani": ("diyalog oranı", "oran"),
    "kelime_uzunlugu": ("ortalama kelime uzunluğu", "harf"),
    "cesitlilik": ("kelime çeşitliliği", "oran"),
    "virgul": ("virgül", "1000 kelimede"),
    "noktali_virgul": ("noktalı virgül", "1000 kelimede"),
    "uc_nokta": ("üç nokta", "1000 kelimede"),
    "unlem": ("ünlem", "1000 kelimede"),
    "soru": ("soru işareti", "1000 kelimede"),
    "uzun_cizgi": ("uzun çizgi (anlatı içinde)", "1000 kelimede"),
    "zarf_fiil": ("zarf-fiil (-ken, -ince, -ip, -arak)", "1000 kelimede"),
}
ACIKLAMA.update({f"islev_{k}": (f"'{k}' kullanımı", "1000 kelimede") for k in ISLEV})


class SesHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def ozellikler(ham: str) -> dict[str, float]:
    metin = metin_analizi.govde(ham)
    kelimeler = [tk.tr_kucuk(k) for k in tk.KELIME.findall(metin)]
    n = len(kelimeler)
    if n == 0:
        raise SesHatasi("metinde ölçülecek kelime yok")
    uzunluklar = [len(tk.KELIME.findall(c)) for c in metin_analizi.cumleler(metin)] or [n]
    ort = statistics.fmean(uzunluklar)
    paragraflar = [p for p in metin.split("\n") if p.strip()]
    diyalog = sum(len(tk.KELIME.findall(p)) for p in paragraflar if tk.diyalog_satiri_mi(p))
    pencere = 100
    if n > pencere:
        adim = max(1, (n - pencere) // 50)
        oranlar = [len(set(kelimeler[i:i + pencere])) / pencere for i in range(0, n - pencere + 1, adim)]
        cesitlilik = statistics.fmean(oranlar)
    else:
        cesitlilik = len(set(kelimeler)) / n
    binde = 1000 / n
    anlati = "\n".join(p for p in paragraflar if not tk.diyalog_satiri_mi(p))
    sonuc = {
        "cumle_ort": ort,
        "cumle_degiskenlik": (statistics.pstdev(uzunluklar) / ort) if ort else 0.0,
        "paragraf_ort": n / max(1, len(paragraflar)),
        "diyalog_orani": diyalog / n,
        "kelime_uzunlugu": statistics.fmean(len(k.split("'")[0]) for k in kelimeler),
        "cesitlilik": cesitlilik,
        "virgul": metin.count(",") * binde,
        "noktali_virgul": metin.count(";") * binde,
        "uc_nokta": (metin.count("…") + metin.count("...")) * binde,
        "unlem": metin.count("!") * binde,
        "soru": metin.count("?") * binde,
        "uzun_cizgi": len(re.findall(r"\S\s*[—–]\s*\S", anlati)) * binde,
        "zarf_fiil": sum(1 for k in kelimeler if len(k) > 4 and ZARF_FIIL.search(k.split("'")[0])) * binde,
    }
    sayac = {k: 0 for k in ISLEV}
    for k in kelimeler:
        if k in sayac:
            sayac[k] += 1
    sonuc.update({f"islev_{k}": v * binde for k, v in sayac.items()})
    return {k: round(v, 4) for k, v in sonuc.items()}


def parcalara_bol(ham: str) -> list[str]:
    """Metni ~400 kelimelik paragraf gruplarına böler (değişkenlik tahmini için)."""
    paragraflar = [p for p in metin_analizi.govde(ham).split("\n") if p.strip()]
    parcalar, tampon, sayi = [], [], 0
    for p in paragraflar:
        tampon.append(p)
        sayi += len(tk.KELIME.findall(p))
        if sayi >= PARCA_KELIME:
            parcalar.append("\n".join(tampon))
            tampon, sayi = [], 0
    if tampon and (sayi >= EN_AZ_KELIME or not parcalar):
        parcalar.append("\n".join(tampon))
    elif tampon:
        parcalar[-1] += "\n" + "\n".join(tampon)
    return parcalar


def profil_cikar(metinler: list[tuple[str, str]]) -> dict[str, Any]:
    toplam_metin = "\n\n".join(m for _, m in metinler)
    toplam_kelime = len(tk.KELIME.findall(metin_analizi.govde(toplam_metin)))
    if toplam_kelime < EN_AZ_KELIME:
        raise SesHatasi(f"profil için metin çok kısa ({toplam_kelime} kelime; en az {EN_AZ_KELIME}, önerilen 1500)")
    genel = ozellikler(toplam_metin)
    parca_degerleri = [ozellikler(p) for p in parcalara_bol(toplam_metin)]
    sapma = {}
    for k, v in genel.items():
        degerler = [p[k] for p in parca_degerleri]
        s = statistics.pstdev(degerler) if len(degerler) >= 2 else 0.0
        taban = max(abs(v) * 0.15, 0.02 if k in ("cumle_degiskenlik", "diyalog_orani", "cesitlilik") else 0.3)
        sapma[k] = round(max(s, taban), 4)  # çok az örnekte aşırı duyarlılığı önler
    return {"sema_surumu": 1, "kaynaklar": [a for a, _ in metinler], "kelime": toplam_kelime,
            "parca": len(parca_degerleri), "ortalama": genel, "sapma": sapma,
            "uyari": "Profil 1500 kelimeden kısa metinden çıkarıldı; güvenilirliği düşük." if toplam_kelime < 1500 else ""}


def karsilastir(profil: dict[str, Any], ham: str) -> dict[str, Any]:
    try:
        ort, sap = profil["ortalama"], profil["sapma"]
        if not isinstance(ort, dict) or not isinstance(sap, dict) or not ort:
            raise TypeError
    except (KeyError, TypeError):
        raise SesHatasi("profil dosyası geçersiz: 'ortalama' ve 'sapma' alanları bekleniyordu") from None
    olcum = ozellikler(ham)
    n = max(1, len(tk.KELIME.findall(metin_analizi.govde(ham))))
    satirlar = []
    for k, v in olcum.items():
        if k not in ort or not isinstance(ort[k], (int, float)) or not isinstance(sap.get(k, 1.0), (int, float)):
            continue
        s = float(sap.get(k) or 1.0)
        seyrek = ACIKLAMA.get(k, ("", ""))[1] == "1000 kelimede"
        if seyrek:  # sayım özellikleri: kısa metinde Poisson belirsizliği sapmayı büyütür
            beklenen = max(1.0, ort[k] * n / 1000)
            s = max(s, math.sqrt(beklenen) * 1000 / n)
        z = (v - ort[k]) / s if s else 0.0
        adet = round(v * n / 1000) if seyrek else None
        satirlar.append({"ozellik": k, "profil": ort[k], "bolum": v, "z": round(z, 2), "adet": adet})
    if not satirlar:
        raise SesHatasi("profil ile ölçüm arasında ortak özellik yok")
    ortalama_z = statistics.fmean(min(4.0, abs(x["z"])) for x in satirlar)
    benzerlik = round(100 * math.exp(-ortalama_z / 1.5))
    sapmalar = sorted((x for x in satirlar if abs(x["z"]) >= 2 and (x["adet"] is None or x["z"] < 0 or x["adet"] >= 3)),
                      key=lambda x: -abs(x["z"]))
    return {"benzerlik": benzerlik, "ozellikler": satirlar, "sapmalar": sapmalar}


def sapma_cumlesi(x: dict[str, Any]) -> str:
    ad, birim = ACIKLAMA.get(x["ozellik"], (x["ozellik"], ""))
    yon = "belirgin biçimde yüksek" if x["z"] > 0 else "belirgin biçimde düşük"
    return (f"{ad} {yon}: profil {tk.tr_ondalik(x['profil'], 2)} → bu metin {tk.tr_ondalik(x['bolum'], 2)} "
            f"{birim} (z = {tk.tr_ondalik(x['z'], 1)})")


def _bolum_araligi(deger: str) -> set[int]:
    sonuc: set[int] = set()
    for parca in deger.split(","):
        m = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*", parca)
        if not m:
            raise SesHatasi(f"geçersiz bölüm aralığı: {deger!r} (ör. 1-5 ya da 1,3,7)")
        bas, son = int(m.group(1)), int(m.group(2) or m.group(1))
        if son < bas or son - bas > 5000:
            raise SesHatasi(f"geçersiz bölüm aralığı: {deger!r}")
        sonuc.update(range(bas, son + 1))
    return sonuc


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Ses izi: üslup profili çıkar ve yeni metni profille karşılaştır.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_c = alt.add_parser("cikar", help="örnek metinlerden ses profili çıkar")
    kaynak = p_c.add_mutually_exclusive_group(required=True)
    kaynak.add_argument("--dosya", type=Path, nargs="+", help="örnek metin dosyaları")
    kaynak.add_argument("--proje", type=Path, help="kitap klasörü (bölümlerden çıkarır)")
    p_c.add_argument("--bolumler", help="yalnızca bu bölümler (ör. 1-5 ya da 1,3,7)")
    p_c.add_argument("--cikti", type=Path, help="profil dosyası (varsayılan: <proje>/kurgu/ses-izi.json ya da stdout)")
    p_k = alt.add_parser("karsilastir", help="bir metni ses profiliyle karşılaştır")
    p_k.add_argument("--profil", type=Path, help="profil JSON dosyası")
    p_k.add_argument("--proje", type=Path, help="kitap klasörü (profil: kurgu/ses-izi.json)")
    p_k.add_argument("--dosya", type=Path, required=True, help="karşılaştırılacak metin")
    p_k.add_argument("--esik", type=int, help="benzerlik bu değerin altındaysa çıkış kodu 1")
    p_k.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "cikar":
            if arg.proje:
                secim = _bolum_araligi(arg.bolumler) if arg.bolumler else None
                bolumler = [b for b in kitap_proje.bolumler(arg.proje, zorunlu=True) if secim is None or b.no in secim]
                if not bolumler:
                    raise SesHatasi("seçilen aralıkta bölüm yok")
                metinler = [(b.yol.name, b.metin) for b in bolumler]
            else:
                if arg.bolumler:
                    raise SesHatasi("--bolumler yalnızca --proje ile kullanılır")
                metinler = [(y.name, dosya_oku.metin_oku(y)) for y in arg.dosya]
            profil = profil_cikar(metinler)
            hedef = arg.cikti or (arg.proje / "kurgu" / "ses-izi.json" if arg.proje else None)
            veri = json.dumps(profil, ensure_ascii=False, indent=1)
            if hedef:
                hedef.parent.mkdir(parents=True, exist_ok=True)
                hedef.write_text(veri + "\n", encoding="utf-8", newline="\n")
                print(f"Ses izi yazıldı: {hedef} ({profil['kelime']} kelime, {profil['parca']} parça)")
                if profil["uyari"]:
                    print(f"uyarı: {profil['uyari']}", file=sys.stderr)
            else:
                print(veri)
        else:
            if not arg.profil and not arg.proje:
                raise SesHatasi("--profil ya da --proje gerekli")
            yol = arg.profil or arg.proje / "kurgu" / "ses-izi.json"
            try:
                profil = dosya_oku.json_nesne_oku(yol)
            except dosya_oku.DosyaHatasi as hata:
                raise SesHatasi(f"{hata}. Önce 'cikar' komutuyla profil oluşturun.") from None
            sonuc = karsilastir(profil, dosya_oku.metin_oku(arg.dosya))
            if arg.json:
                print(json.dumps(sonuc, ensure_ascii=False, indent=2))
            else:
                print(f"Ses benzerliği: {sonuc['benzerlik']}/100")
                if sonuc["sapmalar"]:
                    print("Profilden belirgin sapmalar:")
                    for x in sonuc["sapmalar"][:8]:
                        print(f"  - {sapma_cumlesi(x)}")
                else:
                    print("Belirgin sapma yok; metin profilin sesine yakın.")
            if arg.esik is not None and sonuc["benzerlik"] < arg.esik:
                return 1
    except (SesHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
