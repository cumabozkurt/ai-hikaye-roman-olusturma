#!/usr/bin/env python3
"""Kurgu planı: yapı yöntemleri (kar tanesi, üç perde, kahramanın yolculuğu, serim-düğüm-çözüm,
yedi nokta), sahne kartları ve mantar pano görünümü.

Kullanım::

    kurgu_plani.py yontemler
    kurgu_plani.py baslat  --proje KITAP --yontem uc-perde [--bolum-sayisi 30] [--hedef-kelime 80000]
    kurgu_plani.py sahneler --proje KITAP                # plan/sahneler.md şablonunu oluşturur
    kurgu_plani.py denetle --proje KITAP [--json]
    kurgu_plani.py pano    --proje KITAP [--html pano.html]

Dosyalar:

* ``plan/yapi-<yontem>.md``: her vuruş için ``### Ad`` başlığı, ``- Bölüm:`` satırı
  ve serbest açıklama. Yöntem dosyası yazarındır; araç yalnızca şablon kurar ve denetler.
* ``plan/kar-tanesi.md``: kar tanesi yönteminin on adımı (``## 1. Tek cümlelik öz`` ...).
* ``plan/sahneler.md``: sahne kartları tablosu
  ``| # | Bölüm | Sahne | Bakış açısı | Mekân | Amaç | Çatışma | Sonuç | Değer | Durum |``.
  ``Değer`` sahnenin başındaki ve sonundaki duygusal yükü gösterir (ör. ``+ → −`` ya da ``güven + → korku −``).

Çıkış kodu: 0 temiz, 1 "hata" düzeyinde bulgu var, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
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

# (ad, kitaptaki konumu yüzde olarak, yazara soru)
YONTEMLER: dict[str, dict[str, Any]] = {
    "uc-perde": {
        "ad": "Üç perde",
        "aciklama": "Kurulum (%25), karşı karşıya geliş (%50), çözüm (%25). En yaygın ticari roman iskeleti.",
        "vuruslar": [
            ("Açılış görüntüsü", 1, "Kahramanın değişmeden önceki dünyası tek bir sahnede nasıl görünüyor?"),
            ("Kışkırtıcı olay", 10, "Hangi olay kahramanın düzenini geri dönülmez biçimde bozuyor?"),
            ("Birinci dönüm noktası", 25, "Kahraman hangi kararla eski dünyasından çıkıp maceraya giriyor?"),
            ("İlk sıkıştırma", 37, "Karşı güç gücünü ilk kez nasıl gösteriyor?"),
            ("Orta nokta", 50, "Kahraman ne öğreniyor, ne kazanıyor ya da ne kaybediyor ki oyunun kuralları değişiyor?"),
            ("İkinci sıkıştırma", 62, "Karşı güç kahramanı hangi yeni baskıyla köşeye sıkıştırıyor?"),
            ("Her şeyin kaybedildiği an", 75, "Kahraman en dipte neyi kaybediyor?"),
            ("Doruk", 88, "Son yüzleşmede kahraman neyi seçiyor, neyi feda ediyor?"),
            ("Kapanış görüntüsü", 99, "Açılış görüntüsünün aynası: dünya ve kahraman nasıl değişti?"),
        ],
    },
    "kahramanin-yolculugu": {
        "ad": "Kahramanın yolculuğu",
        "aciklama": "Mitlerdeki ortak yapıdan türeyen on iki aşama; macera, fantastik ve gençlik romanında güçlü.",
        "vuruslar": [
            ("Olağan dünya", 1, "Kahraman macera öncesinde nasıl yaşıyor, neyi eksik?"),
            ("Maceraya çağrı", 8, "Onu harekete geçmeye zorlayan davet ya da tehdit ne?"),
            ("Çağrının reddi", 12, "Neden önce hayır diyor? Korkusu ne?"),
            ("Bilge ile karşılaşma", 17, "Ona kim yol gösteriyor, ne veriyor?"),
            ("Eşiği geçiş", 25, "Geri dönüşü olmayan adım hangisi?"),
            ("Sınavlar, dostlar, düşmanlar", 35, "Yeni dünyanın kuralları neler, kim yanında kim karşısında?"),
            ("En derin mağaraya yaklaşma", 45, "En büyük tehlikeye hazırlanırken ne planlıyor?"),
            ("Büyük sınav", 55, "Ölümle (gerçek ya da simgesel) nerede yüz yüze geliyor?"),
            ("Ödül", 65, "Sınavdan ne kazanıyor?"),
            ("Dönüş yolu", 75, "Ödülle dönerken karşı güç nasıl peşine düşüyor?"),
            ("Yeniden doğuş", 88, "Son sınavda eski benliğini nasıl geride bırakıyor?"),
            ("İksirle dönüş", 98, "Olağan dünyaya ne getiriyor, dünya nasıl değişiyor?"),
        ],
    },
    "serim-dugum-cozum": {
        "ad": "Serim, düğüm, çözüm",
        "aciklama": "Türk edebiyat eğitiminin bilinen üç bölümlü yapısı; öykü ve kısa romanda sade bir iskelet.",
        "vuruslar": [
            ("Serim: kişiler ve yer", 1, "Okur kimi, nerede, hangi düzen içinde tanıyor?"),
            ("Serim: ilk kıvılcım", 15, "Düzeni bozan ilk olay ne?"),
            ("Düğüm: gerilimin yükselişi", 35, "Çatışma hangi adımlarla büyüyor?"),
            ("Düğüm: en yüksek nokta", 70, "Merak ve gerilim en çok nerede birikiyor?"),
            ("Çözüm: düğümün çözülmesi", 85, "Sorun nasıl çözülüyor ya da neden çözülemiyor?"),
            ("Çözüm: son durum", 98, "Kişiler ve dünya son sayfada nerede kalıyor?"),
        ],
    },
    "yedi-nokta": {
        "ad": "Yedi nokta",
        "aciklama": "Sondan başa kurulan yedi noktalı yapı: önce son durumu, sonra karşıtı olan başlangıcı belirlersiniz.",
        "vuruslar": [
            ("Başlangıç durumu", 1, "Sonun tam karşıtı olan başlangıç durumu ne?"),
            ("Birinci dönüş", 20, "Hikâyeyi başlatan çatışma nasıl ortaya çıkıyor?"),
            ("Birinci sıkıştırma", 35, "Kahramanı harekete geçmeye zorlayan baskı ne?"),
            ("Orta nokta", 50, "Kahraman tepki vermekten eyleme nasıl geçiyor?"),
            ("İkinci sıkıştırma", 65, "Her şey neden daha da kötüleşiyor, planlar nasıl çöküyor?"),
            ("İkinci dönüş", 80, "Çözüm için gereken son parça (bilgi, güç, karar) nasıl ele geçiyor?"),
            ("Son durum", 98, "Kahraman nasıl değişmiş olarak bitiriyor?"),
        ],
    },
}
KAR_TANESI = [
    ("Tek cümlelik öz", "Romanı en fazla 25 kelimelik tek cümleyle anlatın: kim, ne istiyor, önünde ne var."),
    ("Tek paragraflık özet", "Beş cümle: kurulum, üç büyük dönüm (felaket) ve son."),
    ("Ana karakter özetleri", "Her ana karakter için: hikâye çizgisi (tek cümle), istediği, ihtiyacı, çatışması, sonunda ne öğrendiği."),
    ("Bir sayfalık özet", "2. adımdaki her cümleyi bir paragrafa genişletin."),
    ("Karakterlerin kendi gözünden hikâye", "Her ana karakter için hikâyeyi onun bakışından yarım sayfa anlatın."),
    ("Dört sayfalık özet", "4. adımdaki her paragrafı bir sayfaya genişletin."),
    ("Karakter kayıtları", "Kurgu ansiklopedisinde her karakterin kaydını tamamlayın (kurgu_ansiklopedisi.py olustur)."),
    ("Sahne listesi", "plan/sahneler.md tablosunda bütün sahneleri sıralayın (kurgu_plani.py sahneler)."),
    ("Bölüm planları", "Her bölüm için plan/bolum-plani_NNN.md yazın (bölüm planı şablonu)."),
    ("İlk taslak", "Bölüm bölüm yazmaya başlayın; bu dosya artık yalnızca başvuru kaynağıdır."),
]
SAHNE_BASLIKLARI = ["#", "Bölüm", "Sahne", "Bakış açısı", "Mekân", "Amaç", "Çatışma", "Sonuç", "Değer", "Durum"]
DURUMLAR = {"fikir", "planlandı", "taslak", "yazıldı", "revize", "tamam", "çıkarıldı"}
TOLERANS = 8  # vuruşun hedef konumundan yüzde puan sapması


class PlanHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def bulgu(duzey: str, kimlik: str, ileti: str) -> dict[str, str]:
    return {"duzey": duzey, "kimlik": kimlik, "ileti": ileti}


def yapi_sablonu(yontem: str, bolum_sayisi: int | None, hedef_kelime: int | None) -> str:
    y = YONTEMLER[yontem]
    s = [f"# Yapı: {y['ad']}", "", f"> {y['aciklama']}", ""]
    if bolum_sayisi:
        s.append(f"- Bölüm sayısı: {bolum_sayisi}")
    if hedef_kelime:
        s.append(f"- Hedef kelime: {hedef_kelime}")
    s += ["", "Her vuruşun `Olay:` satırına ya da altına 2–5 cümle yazın. `Bölüm:` satırı vuruşun hangi bölümde gerçekleştiğini gösterir; "
          "denetim bunu kitaptaki beklenen konumla karşılaştırır.", ""]
    for ad, yuzde, soru in y["vuruslar"]:
        s.append(f"### {ad}")
        s.append("")
        s.append(f"- Hedef konum: %{yuzde}")
        tahmin = max(1, round(bolum_sayisi * yuzde / 100)) if bolum_sayisi else None
        s.append(f"- Bölüm: {tahmin if tahmin else ''}".rstrip())
        if hedef_kelime:
            s.append(f"- Yaklaşık kelime konumu: {round(hedef_kelime * yuzde / 100)}")
        s += [f"- Soru: {soru}", "- Olay:", "", ""]
    return "\n".join(s).rstrip() + "\n"


def kar_tanesi_sablonu() -> str:
    s = ["# Kar Tanesi Planı", "",
         "> Küçük bir çekirdekten başlayıp her adımda planı genişletin. Adımları sırayla doldurun; "
         "boş adım sonraki adımın temelini zayıflatır.", ""]
    for i, (ad, aciklama) in enumerate(KAR_TANESI, 1):
        s += [f"## {i}. {ad}", "", f"> {aciklama}", "", "", ""]
    return "\n".join(s).rstrip() + "\n"


def sahne_sablonu() -> str:
    return ("# Sahne Kartları\n\n"
            "> Her satır bir sahne. Amaç: bakış açısı karakterinin sahnede istediği. Çatışma: önündeki engel. "
            "Sonuç: sahne nasıl bitiyor (çoğunlukla 'evet ama' ya da 'hayır, üstelik'). "
            "Değer: sahne başındaki ve sonundaki duygusal yük (ör. `+ → −` ya da `güven + → korku −`). "
            f"Durum: {', '.join(sorted(DURUMLAR))}.\n\n"
            "| " + " | ".join(SAHNE_BASLIKLARI) + " |\n|" + "---|" * len(SAHNE_BASLIKLARI) + "\n"
            "| 1 | 1 | Açılış | Ana karakter | Ana mekân | ... | ... | ... | − → + | fikir |\n")


def _dosya_yaz(yol: Path, icerik: str) -> Path:
    if yol.exists():
        raise PlanHatasi(f"dosya zaten var, üzerine yazılmadı: {yol}")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(icerik, encoding="utf-8")
    return yol


def baslat(proje: Path, yontem: str, bolum_sayisi: int | None, hedef_kelime: int | None) -> Path:
    kitap_proje.proje_klasoru(proje)
    if bolum_sayisi is not None and not 1 <= bolum_sayisi <= 2000:
        raise PlanHatasi("--bolum-sayisi 1 ile 2000 arasında olmalı")
    if hedef_kelime is not None and not 1000 <= hedef_kelime <= 2_000_000:
        raise PlanHatasi("--hedef-kelime 1.000 ile 2.000.000 arasında olmalı")
    if yontem == "kar-tanesi":
        return _dosya_yaz(proje / "plan" / "kar-tanesi.md", kar_tanesi_sablonu())
    return _dosya_yaz(proje / "plan" / f"yapi-{yontem}.md", yapi_sablonu(yontem, bolum_sayisi, hedef_kelime))


def _bolumler_md(metin: str, seviye: str) -> list[tuple[str, str]]:
    parcalar = re.split(rf"^{seviye}\s+(.+?)\s*$", metin, flags=re.M)
    return [(parcalar[i].strip(), parcalar[i + 1]) for i in range(1, len(parcalar) - 1, 2)]


def _serbest_metin(govde: str) -> str:
    """Alan satırları, alıntılar ve yorumlar dışındaki yazar metni."""
    satirlar = []
    for s in govde.splitlines():
        s = s.strip()
        if s.startswith("- Olay:"):
            s = s[len("- Olay:"):].strip()
        if s and not s.startswith((">", "- Hedef konum", "- Bölüm:", "- Yaklaşık", "- Soru:", "<!--")):
            satirlar.append(s)
    return " ".join(satirlar).strip()


def sahneleri_oku(proje: Path) -> list[dict[str, Any]]:
    yol = proje / "plan" / "sahneler.md"
    if not yol.is_file():
        return []
    satirlar = [s.strip() for s in dosya_oku.metin_oku(yol, uyar=False).splitlines() if s.strip().startswith("|")]
    if not satirlar:
        return []
    basliklar = [tk.tr_kucuk(h.strip()) for h in satirlar[0].strip("|").split("|")]
    sahneler = []
    for no, satir in enumerate(satirlar[1:], start=2):
        hucre = [h.strip() for h in satir.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", h) for h in hucre if h):
            continue
        k = {b: (hucre[i] if i < len(hucre) else "") for i, b in enumerate(basliklar)}
        bolum = re.search(r"\d+", k.get("bölüm", ""))
        sahneler.append({"satir": no, "sira": k.get("#", ""), "bolum": int(bolum.group()) if bolum else None,
                         "sahne": k.get("sahne", ""), "bakis": k.get("bakış açısı", ""), "mekan": k.get("mekân", k.get("mekan", "")),
                         "amac": k.get("amaç", ""), "catisma": k.get("çatışma", ""), "sonuc": k.get("sonuç", ""),
                         "deger": k.get("değer", ""), "durum": tk.tr_kucuk(k.get("durum", ""))})
    return sahneler


def _bos(deger: str) -> bool:
    return not deger or deger.strip() in ("...", "…", "-", "—", "?")


def denetle(proje: Path) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    bulgular: list[dict[str, str]] = []
    plan = proje / "plan"
    yazilan = kitap_proje.bolumler(proje)
    bolum_sayisi_gercek = max((b.no for b in yazilan), default=0)
    ozet: dict[str, Any] = {"yapilar": {}, "kar_tanesi": None, "sahne": 0}
    for yol in sorted(plan.glob("yapi-*.md")) if plan.is_dir() else []:
        metin = dosya_oku.metin_oku(yol, uyar=False)
        m = re.search(r"^[ \t]*-[ \t]*Bölüm sayısı[ \t]*:[ \t]*(\d+)", metin, re.M)
        toplam = int(m.group(1)) if m else None
        vuruslar = _bolumler_md(metin, "###")
        dolu = 0
        onceki_bolum = 0
        for ad, govde in vuruslar:
            if _serbest_metin(govde):
                dolu += 1
            else:
                bulgular.append(bulgu("uyari", "bos-vurus", f"{yol.name}: '{ad}' vuruşu boş"))
            hb = re.search(r"^[ \t]*-[ \t]*Bölüm[ \t]*:[ \t]*(\d+)", govde, re.M)
            hy = re.search(r"^[ \t]*-[ \t]*Hedef konum[ \t]*:[ \t]*%?[ \t]*(\d+)", govde, re.M)
            if hb:
                no = int(hb.group(1))
                if no < onceki_bolum:
                    bulgular.append(bulgu("hata", "vurus-sirasi", f"{yol.name}: '{ad}' ({no}. bölüm) bir önceki vuruştan "
                                          f"({onceki_bolum}. bölüm) önce geliyor"))
                onceki_bolum = max(onceki_bolum, no)
                referans = toplam or None
                if referans and hy:
                    gercek = 100 * no / referans
                    if abs(gercek - int(hy.group(1))) > TOLERANS + 100 / referans:
                        bulgular.append(bulgu("uyari", "vurus-konumu", f"{yol.name}: '{ad}' kitabın %{round(gercek)} "
                                              f"noktasında; bu yöntemde beklenen yaklaşık %{hy.group(1)}"))
                if toplam and no > toplam:
                    bulgular.append(bulgu("hata", "vurus-kapsam-disi", f"{yol.name}: '{ad}' {no}. bölümde ama kitap "
                                          f"{toplam} bölüm"))
        ozet["yapilar"][yol.name] = {"vurus": len(vuruslar), "dolu": dolu}
    kar = plan / "kar-tanesi.md"
    if kar.is_file():
        adimlar = _bolumler_md(dosya_oku.metin_oku(kar, uyar=False), "##")
        dolu_adim = [ad for ad, g in adimlar if _serbest_metin(g)]
        ozet["kar_tanesi"] = {"adim": len(adimlar), "dolu": len(dolu_adim)}
        for i, (ad, govde) in enumerate(adimlar):
            metin = _serbest_metin(govde)
            if i == 0 and metin:
                kelime = len(re.findall(r"\w+", metin))
                if kelime > 25:
                    bulgular.append(bulgu("uyari", "oz-uzun", f"kar-tanesi.md: tek cümlelik öz {kelime} kelime (en fazla 25 önerilir)"))
            if i == 1 and metin:
                cumle = len([c for c in re.split(r"[.!?…]+", metin) if c.strip()])
                if cumle < 4:
                    bulgular.append(bulgu("uyari", "ozet-kisa", f"kar-tanesi.md: tek paragraflık özet {cumle} cümle "
                                          "(kurulum, üç dönüm ve son için beş cümle önerilir)"))
        bos_sonra_dolu = [ad for j, (ad, g) in enumerate(adimlar[:-1]) if not _serbest_metin(g)
                          and any(_serbest_metin(g2) for _, g2 in adimlar[j + 1:])]
        for ad in bos_sonra_dolu[:3]:
            bulgular.append(bulgu("uyari", "atlanan-adim", f"kar-tanesi.md: '{ad}' boş ama sonraki adımlar dolu"))
    sahneler = sahneleri_oku(proje)
    ozet["sahne"] = len(sahneler)
    onceki = 0
    for s in sahneler:
        yer = f"sahneler.md satır {s['satir']}"
        if s["bolum"] is None:
            bulgular.append(bulgu("hata", "sahne-bolumsuz", f"{yer}: 'Bölüm' sütunu sayı değil"))
        else:
            if s["bolum"] < onceki:
                bulgular.append(bulgu("uyari", "sahne-sirasi", f"{yer}: {s['bolum']}. bölüm sahnesi {onceki}. bölüm "
                                      "sahnesinden sonra listelenmiş (geri dönüş sahnesiyse sorun yok)"))
            onceki = max(onceki, s["bolum"])
        if s["durum"] == "çıkarıldı":
            continue
        eksik = [ad for ad, anahtar in (("amaç", "amac"), ("çatışma", "catisma"), ("sonuç", "sonuc")) if _bos(s[anahtar])]
        if eksik and s["durum"] != "fikir":
            bulgular.append(bulgu("uyari", "sahne-eksik", f"{yer} ('{s['sahne']}'): {', '.join(eksik)} boş"))
        d = s["deger"].strip()
        # İşaretlerin önüne isteğe bağlı bir duygu adı yazılabilir: "güven + → korku −"
        m = re.fullmatch(r"[^+−\-→>]*?\s*([+−-])\s*(?:→|->)\s*[^+−\-→>]*?\s*([+−-])", d)
        if d and not m:
            bulgular.append(bulgu("uyari", "deger-bicimi", f"{yer}: 'Değer' sütunu '+ → −' ya da 'güven + → korku −' "
                                  f"biçiminde olmalı, '{s['deger']}' yazılmış"))
        elif m and m.group(1).replace("−", "-") == m.group(2).replace("−", "-"):
            bulgular.append(bulgu("uyari", "duz-sahne", f"{yer} ('{s['sahne']}'): değer değişmiyor ({s['deger']}); "
                                  "sahne bir şeyi değiştirmiyorsa birleştirmeyi ya da çıkarmayı düşünün"))
        if s["durum"] and s["durum"] not in DURUMLAR:
            bulgular.append(bulgu("uyari", "durum-bilinmeyen", f"{yer}: bilinmeyen durum '{s['durum']}' "
                                  f"(geçerli: {', '.join(sorted(DURUMLAR))})"))
    bakis = Counter(s["bakis"] for s in sahneler if s["bakis"] and not _bos(s["bakis"]))
    ozet["bakis_acisi"] = dict(bakis)
    if bolum_sayisi_gercek and sahneler:
        plansiz = sorted({b.no for b in yazilan} - {s["bolum"] for s in sahneler if s["bolum"]})
        if plansiz:
            bulgular.append(bulgu("bilgi", "sahnesiz-bolum", "sahne kartı olmayan yazılmış bölümler: "
                                  + ", ".join(map(str, plansiz[:20]))))
    if not ozet["yapilar"] and ozet["kar_tanesi"] is None and not sahneler:
        bulgular.append(bulgu("bilgi", "plan-yok", "henüz yapı, kar tanesi ya da sahne kartı yok; 'baslat' ya da 'sahneler' "
                              "komutuyla başlayın"))
    return {"ozet": ozet, "bulgular": bulgular}


def pano_metni(proje: Path) -> str:
    sahneler = sahneleri_oku(proje)
    if not sahneler:
        return "plan/sahneler.md yok ya da boş; 'sahneler' komutuyla şablonu oluşturun."
    s = []
    son = None
    for k in sahneler:
        if k["bolum"] != son:
            son = k["bolum"]
            s.append(f"\n━━ {son if son is not None else '?'}. bölüm ━━")
        durum = f"[{k['durum']}]" if k["durum"] else ""
        s.append(f"  ▸ {k['sahne'] or '(adsız)'} {durum}  · BA: {k['bakis'] or '?'} · {k['mekan'] or '?'} · {k['deger']}")
        if not _bos(k["amac"]):
            s.append(f"      amaç: {k['amac']} | çatışma: {k['catisma']} | sonuç: {k['sonuc']}")
    return "\n".join(s).strip()


def pano_html(proje: Path) -> str:
    e = html.escape
    sahneler = sahneleri_oku(proje)
    renkler = ["#f2b84b", "#4fd1c5", "#f687b3", "#90cdf4", "#9ae6b4", "#fbd38d", "#d6bcfa"]
    bakis_renk: dict[str, str] = {}
    sutunlar: dict[Any, list[str]] = {}
    for k in sahneler:
        renk = bakis_renk.setdefault(k["bakis"], renkler[len(bakis_renk) % len(renkler)])
        soluk = " soluk" if k["durum"] == "çıkarıldı" else ""
        kart = (f"<div class='kart{soluk}' style='border-top:6px solid {renk}'><b>{e(k['sahne'] or '(adsız)')}</b>"
                f"<small>{e(k['bakis'])} · {e(k['mekan'])}</small><p>{e(k['amac'])}</p>"
                f"<p class='c'>{e(k['catisma'])}</p><footer>{e(k['deger'])} <i>{e(k['durum'])}</i></footer></div>")
        sutunlar.setdefault(k["bolum"], []).append(kart)
    govde = "".join(f"<section><h2>{e(str(b))}. bölüm</h2>{''.join(k)}</section>" for b, k in sutunlar.items())
    lejant = "".join(f"<span style='background:{r}'>{e(b or '?')}</span>" for b, r in bakis_renk.items())
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><title>{e(kitap_proje.kitap_basligi(proje))} — Sahne Panosu</title>
<style>body{{font-family:system-ui,sans-serif;background:#6b4f33;margin:0;padding:20px;color:#222}}
h1{{color:#fff8e7}} .pano{{display:flex;gap:14px;overflow-x:auto;align-items:flex-start}}
section{{min-width:220px;max-width:240px}} h2{{color:#fff8e7;font-size:1em}}
.kart{{background:#fffdf5;border-radius:4px;padding:10px;margin-bottom:10px;box-shadow:2px 3px 6px rgba(0,0,0,.35)}}
.kart b{{display:block}} .kart small{{color:#666}} .kart p{{margin:6px 0;font-size:.9em}} .kart p.c{{color:#9b2c2c}}
.kart footer{{font-size:.8em;color:#444}} .soluk{{opacity:.45}}
.lejant span{{display:inline-block;padding:2px 8px;margin:0 6px 6px 0;border-radius:10px;font-size:.85em}}</style></head>
<body><h1>{e(kitap_proje.kitap_basligi(proje))} — sahne panosu</h1><div class="lejant">{lejant}</div>
<div class="pano">{govde or '<p>Henüz sahne kartı yok.</p>'}</div></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Kurgu planı: yapı yöntemleri, kar tanesi, sahne kartları ve pano.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    alt.add_parser("yontemler", help="kullanılabilir yapı yöntemlerini listele")
    p_b = alt.add_parser("baslat", help="seçilen yöntemin şablonunu plan/ klasörüne yaz")
    p_b.add_argument("--yontem", choices=tuple(YONTEMLER) + ("kar-tanesi",), required=True, help="yapı yöntemi")
    p_b.add_argument("--bolum-sayisi", type=int, help="planlanan bölüm sayısı (vuruşların bölümünü tahmin eder)")
    p_b.add_argument("--hedef-kelime", type=int, help="kitabın hedef kelime sayısı")
    p_s = alt.add_parser("sahneler", help="plan/sahneler.md sahne kartı şablonunu oluştur")
    p_d = alt.add_parser("denetle", help="yapı, kar tanesi ve sahne kartlarını denetle")
    p_d.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_p = alt.add_parser("pano", help="sahne kartlarını mantar pano görünümünde göster")
    p_p.add_argument("--html", type=Path, help="panoyu bu HTML dosyasına yaz")
    for p in (p_b, p_s, p_d, p_p):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "yontemler":
            for anahtar_, y in YONTEMLER.items():
                print(f"{anahtar_:<22} {y['ad']} ({len(y['vuruslar'])} vuruş): {y['aciklama']}")
            print(f"{'kar-tanesi':<22} Kar tanesi ({len(KAR_TANESI)} adım): tek cümleden başlayıp planı adım adım genişletir.")
        elif arg.komut == "baslat":
            print(f"Şablon yazıldı: {baslat(arg.proje, arg.yontem, arg.bolum_sayisi, arg.hedef_kelime)}")
        elif arg.komut == "sahneler":
            kitap_proje.proje_klasoru(arg.proje)
            print(f"Şablon yazıldı: {_dosya_yaz(arg.proje / 'plan' / 'sahneler.md', sahne_sablonu())}")
        elif arg.komut == "denetle":
            sonuc = denetle(arg.proje)
            if arg.json:
                print(json.dumps(sonuc, ensure_ascii=False, indent=2))
            else:
                o = sonuc["ozet"]
                for ad, y in o["yapilar"].items():
                    print(f"{ad}: {y['dolu']}/{y['vurus']} vuruş dolu")
                if o["kar_tanesi"]:
                    print(f"kar-tanesi.md: {o['kar_tanesi']['dolu']}/{o['kar_tanesi']['adim']} adım dolu")
                if o["sahne"]:
                    print(f"sahneler.md: {o['sahne']} sahne; bakış açısı dağılımı: "
                          + ", ".join(f"{b} {n}" for b, n in o["bakis_acisi"].items()))
                isaret = {"hata": "✗", "uyari": "!", "bilgi": "·"}
                for b in sonuc["bulgular"]:
                    print(f"{isaret[b['duzey']]} [{b['kimlik']}] {b['ileti']}")
                if not sonuc["bulgular"]:
                    print("Sorun bulunmadı.")
            return 1 if any(b["duzey"] == "hata" for b in sonuc["bulgular"]) else 0
        else:
            kitap_proje.proje_klasoru(arg.proje)
            print(pano_metni(arg.proje))
            if arg.html:
                arg.html.parent.mkdir(parents=True, exist_ok=True)
                arg.html.write_text(pano_html(arg.proje), encoding="utf-8")
                print(f"\nHTML pano yazıldı: {arg.html}")
    except (PlanHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
