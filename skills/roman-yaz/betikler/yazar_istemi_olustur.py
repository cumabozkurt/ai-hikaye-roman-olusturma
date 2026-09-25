#!/usr/bin/env python3
"""anlati-yazari alt ajanına verilecek istem (prompt) iskeletini belirlenimci olarak kurar.

Kullanım::

    yazar_istemi_olustur.py --proje KITAP --bolum 7 [--cikti [DOSYA]]

``--cikti`` yol almazsa istem ``KITAP/.hikaye/calisma/bolum-007/yazar-istemi.md``
dosyasına yazılır. Geçici dosyalar yalnızca bu kitap içi çalışma klasörüne gider
(sistem /tmp'si ya da metin/ klasörü değil); ``hikayectl.py bolum kaydet``
başarılı olunca klasör silinir.

Çıktının ``===`` çizgisinden önceki kısmı istemdir (ana oturum yalnızca boş
yuvaları doldurur, kalanını değiştirmez); sonrası denetim raporudur.

Betik belirlenimci kısmı yapar: sabit giriş, konum, başlık satırı, plan yolu,
üslup dosyası, önceki bölümün son satırları, bağlam kartı denetimi. Yargı
isteyen sekiz yuvayı ana oturum doldurur.

Çıkış: 0 iskelet üretildi; 2 zorunlu girdi eksik ya da geçersiz.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metin_olcum  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

SON_KARAKTER = 400
YUVA = "⟦ana oturum doldurur⟧"
BAGLAM_BASLIKLARI = ("Şu Anki Konum", "Kalıcı Kısıtlar", "Ana Karakterlerin Durumu", "Açık İpuçları",
                     "Son Üç Bölüm", "Sonraki Bölüm Sözleri", "Süreklilik Riskleri")
YUVALAR = ("Yürütme düzeni", "Bu bölümün niyeti", "Başvurulacak teknikler", "Bölüm notları (bağlam kartından süzülmüş)",
           "Sahnedeki karakterler", "Tür düzyazı kartı", "Okunması zorunlu kurgu dosyaları", "Yazar tercihleri")


def calisma_klasoru(proje: Path, bolum: int) -> Path:
    return proje / ".hikaye" / "calisma" / f"bolum-{bolum:03d}"


def oku(yol: Path) -> str | None:
    try:
        return yol.read_text(encoding="utf-8").lstrip("\ufeff")
    except (OSError, UnicodeError):
        return None


def dolu_mu(metin: str | None) -> bool:
    if not metin:
        return False
    govde = re.sub(r"^#{1,6}[^\n]*", "", metin, flags=re.M)
    govde = re.sub(r"\[doldurulacak\]|yapılacak|belirsiz|todo|tbd", "", govde, flags=re.I)
    return bool(re.sub(r"[\s_#*\[\]{}.,;:\-—|>]", "", govde))


def onceki_son(proje: Path, bolum: int) -> tuple[str | None, str]:
    if bolum <= 1:
        return None, "ilk bölüm; önceki bölüm yok"
    try:
        yol = metin_olcum.bolum_dosyasi_bul(proje / "metin", bolum - 1, plan=False)
    except metin_olcum.OlcumHatasi as hata:
        return None, f"önceki bölüm bulunamadı: {hata}"
    satirlar = [s for s in metin_olcum.gorunur_govde(oku(yol) or "").splitlines() if s.strip()]
    secilen: list[str] = []
    toplam = 0
    for satir in reversed(satirlar):
        if toplam >= SON_KARAKTER and secilen:
            break
        secilen.insert(0, satir)
        toplam += len(satir)
    return "\n".join(f"> {s}" for s in secilen), str(yol)


def olustur(proje: Path, bolum: int) -> tuple[str, list[str], bool]:
    rapor: list[str] = []
    zorunlu_eksik = False
    try:
        plan = metin_olcum.bolum_dosyasi_bul(proje / "plan", bolum, plan=True)
    except metin_olcum.OlcumHatasi as hata:
        return "", [f"HATA bölüm planı: {hata}"], True
    plan_metni = oku(plan) or ""
    try:
        hedef = metin_olcum.plandan_hedef(plan_metni)
        bant = metin_olcum.bantlari_hesapla(hedef)
        rapor.append(f"tamam hedef uzunluk: {hedef} kelime")
    except metin_olcum.OlcumHatasi as hata:
        return "", [f"HATA hedef uzunluk: {hata}"], True
    baslik_m = re.search(r"^#\s*\d+\.\s*Bölüm Planı\s*[—:-]\s*(.+)$", plan_metni, re.M)
    baslik = baslik_m.group(1).strip() if baslik_m else ""
    rapor.append("tamam başlık: " + baslik if baslik else "uyarı: plan başlığında bölüm adı yok ('# 7. Bölüm Planı — Ad')")

    baglam_yolu = proje / "takip" / "baglam.md"
    baglam = oku(baglam_yolu)
    if baglam is None:
        if bolum > 1:
            zorunlu_eksik = True
            rapor.append("HATA bağlam kartı yok: takip_kaydet.py ile takibi başlatın")
        else:
            rapor.append("bilgi: ilk bölüm; bağlam kartı henüz yok")
    else:
        eksik = [b for b in BAGLAM_BASLIKLARI if f"## {b}" not in baglam]
        rapor.append("tamam bağlam kartı" if not eksik else "HATA bağlam kartında eksik başlık: " + ", ".join(eksik))
        zorunlu_eksik |= bool(eksik)
    durum = proje / "takip" / "_takip-durumu.json"
    if durum.exists() and bolum > 1:
        try:
            son = json.loads(durum.read_text(encoding="utf-8")).get("son_kaydedilen_bolum", 0)
        except (OSError, ValueError):
            son = -1
        if son < bolum - 1:
            zorunlu_eksik = True
            rapor.append(f"HATA önceki bölüm takibe kaydedilmemiş (son kayıt: {son}); önce 'hikayectl.py bolum kaydet'")
    ton = proje / "kurgu" / "ton.md"
    ton_notu = f"`{ton}` dosyasını baştan sona oku ve üslubu ona göre kur." if dolu_mu(oku(ton)) else \
        "Üslup dosyası yok ya da boş: kurgu/tur-konumu.md ve tür düzyazı kartına göre yaz; ana oturum bunu yazara bildirsin."
    rapor.append("tamam üslup dosyası" if dolu_mu(oku(ton)) else "uyarı: kurgu/ton.md boş ya da yok")
    son_satirlar, son_kaynak = onceki_son(proje, bolum)
    rapor.append(("tamam önceki bölüm sonu: " if son_satirlar else "bilgi: ") + son_kaynak)

    parcalar = [
        f"Sen anlati-yazari alt ajanısın. `{proje.name}` kitabının {bolum}. bölümünün ilk taslağını yazacaksın.",
        "",
        "## Konum",
        f"- Proje klasörü: `{proje}`",
        f"- Yazılacak dosya: `{proje / 'metin' / f'bolum-{bolum:03d}_{metin_olcum_dosya_adi(baslik)}.md'}`",
        f"- İlk satır birebir: `# {bolum}. Bölüm — {baslik or YUVA}`",
        f"- Bölüm planı (tamamını oku): `{plan}`",
        f"- Hedef uzunluk: {hedef} kelime (iç bant {bant['ic']['alt']}–{bant['ic']['ust']}; "
        f"sert sınır {bant['sert']['alt']}–{bant['sert']['ust']})",
        "",
        "## Üslup",
        f"- {ton_notu}",
        "",
        "## Önceki bölümün sonu",
        son_satirlar or "(ilk bölüm)",
        "",
        "## Bağlam kartı",
        f"- `{baglam_yolu}` (yalnızca aşağıdaki notlarda süzülen kısım bu bölüm için geçerlidir)",
        "",
    ]
    for yuva in YUVALAR:
        parcalar += [f"### {yuva}", YUVA, ""]
    parcalar += [
        "## Sabit kurallar",
        "- Paragraflar arasında bir boş satır bırak; diyalog satır başında konuşma çizgisiyle (—) başlar.",
        "- Planın 'Bu bölümde açığa çıkmayacaklar' alanındaki hiçbir bilgiyi metne sızdırma.",
        "- Plan cümlelerini metne aktarma; her olayı sahne, eylem ve diyalogla göster.",
        "- `kaynaklar/yz-tadi.md` içindeki yasaklı kalıplardan kaçın; klişeyi somut ayrıntıyla değiştir.",
        "- TDK yazımına uy: bağlaç 'de/da' ve 'ki' ayrı, soru eki 'mı/mi' ayrı yazılır; özel ada gelen ek kesmeyle ayrılır.",
        "- Bölüm sonu kancasını plandaki türde kur; fragman cümlesiyle ('her şey değişecekti') bitirme.",
        "- Yazdıktan sonra dosyayı kaydet ve yanıt olarak yalnızca dosya yolunu ve kelime sayısını bildir.",
    ]
    return "\n".join(parcalar) + "\n", rapor, zorunlu_eksik


def metin_olcum_dosya_adi(baslik: str) -> str:
    tablo = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")
    sade = re.sub(r"[^a-z0-9]+", "-", baslik.translate(tablo).lower()).strip("-")
    return sade[:40] or "baslik"


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--proje", required=True, type=Path)
    ayr.add_argument("--bolum", required=True, type=int)
    ayr.add_argument("--cikti", nargs="?", const="", default=None)
    arg = ayr.parse_args(argv)
    istem, rapor, eksik = olustur(arg.proje, arg.bolum)
    if not istem or eksik:
        print("\n".join(rapor), file=sys.stderr)
        return 2
    if arg.cikti is not None:
        hedef = Path(arg.cikti) if arg.cikti else calisma_klasoru(arg.proje, arg.bolum) / "yazar-istemi.md"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(istem, encoding="utf-8")
        rapor.append(f"istem kaydedildi: {hedef}")
    print(istem + "\n===\n" + "\n".join(rapor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
