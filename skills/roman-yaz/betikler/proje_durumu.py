#!/usr/bin/env python3
"""Proje durumu ve özet katmanları: "Nerede kaldım, sırada ne var?" ve uzun roman belleği.

Kullanım::

    proje_durumu.py durum --proje KITAP [--json]
    proje_durumu.py ozet  --proje KITAP [--grup 10] [--sinir 16000] [--cikti ozet.md]

``durum``: planlar, yazılmış ve takibe kaydedilmiş bölümler, yarım kalmış çalışma
klasörleri, süresi geçen ipuçları, son anlık görüntünün yaşı ve döngü kayıtlarına
bakarak kaldığınız yeri ve sıradaki adımı söyler (kesintiden sonra devam etmek için).

``ozet``: üç katmanlı bellek üretir. Kitap katmanı (tek cümlelik öz ve genel plan),
cilt/perde katmanı (bölüm aralıkları: genel plandaki "(1–20)" gibi aralıklar ya da
``--grup`` büyüklüğünde parçalar) ve bölüm katmanı (takip kayıtlarındaki "Sonuç"
satırları). Eski ciltler sıkıştırılır (her bölümün ilk cümlesi), son cilt tam kalır;
toplam boyut ``--sinir`` baytı aşmaz. Bütün romanı okumadan bütün romanı hatırlamak içindir.

Çıkış kodu: 0 başarılı, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

def _takip(proje: Path) -> dict[str, Any]:
    return kitap_proje.takip_durumu(proje)


def _son_kayitli(durum: dict[str, Any]) -> int:
    for anahtar in ("son_kaydedilen_bolum", "son_bolum"):
        deger = durum.get(anahtar)
        if isinstance(deger, int) and not isinstance(deger, bool):
            return deger
    return 0


def durum_raporu(proje: Path, bugun: dt.date | None = None) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    bugun = bugun or dt.date.today()
    takip = _takip(proje)
    son = _son_kayitli(takip)
    yazilan = {b.no: b for b in kitap_proje.bolumler(proje)}
    plan_klasoru = proje / "plan"
    planli = sorted(int(m.group(1)) for y in (plan_klasoru.iterdir() if plan_klasoru.is_dir() else [])
                    if (m := kitap_proje.PLAN_DOSYASI.match(y.name)))
    calisma = proje / ".hikaye" / "calisma"
    yarim = sorted(int(m.group(1)) for y in (calisma.iterdir() if calisma.is_dir() else [])
                   if y.is_dir() and (m := re.match(r"bolum-(\d+)$", y.name)))
    uyarilar: list[str] = []
    adimlar: list[str] = []
    sonraki = son + 1
    if not (plan_klasoru / "genel-plan.md").is_file():
        iskelet = sorted(y.name for y in plan_klasoru.glob("yapi-*.md")) + \
            (["kar-tanesi.md"] if (plan_klasoru / "kar-tanesi.md").is_file() else [])
        if iskelet:
            adimlar.append(f"Yapı iskeleti hazır ({', '.join(iskelet)}); şimdi '/roman-yaz' kurulum akışıyla "
                           "plan/genel-plan.md dosyasını yazın (iskelet bu planın girdisidir).")
        else:
            adimlar.append("Genel plan yok: '/roman-planla' ile yapı iskeletini kurun, ardından '/roman-yaz' "
                           "kurulum akışıyla plan/genel-plan.md dosyasını yazın.")
    kaydedilmemis = sorted(n for n in yazilan if n > son)
    for n in yarim:
        adimlar.append(f"{n}. bölüm yarım kalmış (.hikaye/calisma/bolum-{n:03d} var): taslağı tamamlayıp "
                       f"'hikayectl.py bolum kaydet --proje ... --bolum {n}' ile kaydedin.")
    if kaydedilmemis and not yarim:
        n = kaydedilmemis[0]
        adimlar.append(f"{n}. bölüm yazılmış ama takibe kaydedilmemiş: 'hikayectl.py bolum denetle' ve 'bolum kaydet' çalıştırın.")
    if not adimlar:
        if sonraki not in planli:
            adimlar.append(f"{sonraki}. bölümün planı yok: plan/bolum-plani_{sonraki:03d}.md yazın (bölüm planı şablonu).")
            if son >= 1 and not (proje / "yayin" / "kitaptik" / "rapor.json").is_file():
                adimlar.append("Planlanan bölümlerin hepsi yazıldı. Kitap bittiyse ya da ilk bölümleri okura açmak "
                               "istiyorsanız '/kitaptik-yayimla' ile Kitaptik (kitaptik.com) yayın paketini hazırlayın.")
        else:
            adimlar.append(f"{sonraki}. bölümü yazın: önce 'kurgu_ansiklopedisi.py baglam --bolum {sonraki}' ile bağlam paketini alın.")
    kayitlar = takip.get("uzunluk_kayitlari")
    degisen = []
    if isinstance(kayitlar, dict):
        for n, b in sorted(yazilan.items()):
            kayit = kayitlar.get(str(n))
            if n > son or not isinstance(kayit, dict) or not isinstance(kayit.get("govde_sha256"), str):
                continue
            try:
                taze = kitap_proje.metin_olcum.govde_ozeti(dosya_oku.metin_oku(b.yol))
            except dosya_oku.DosyaHatasi:
                continue
            if taze != kayit["govde_sha256"]:
                degisen.append(n)
    if degisen:
        sirali = [f"{n}." for n in degisen]
        liste = sirali[0] if len(sirali) == 1 else ", ".join(sirali[:-1]) + " ve " + sirali[-1]
        uyarilar.append(f"{liste} bölüm takibe kaydedildikten sonra değişmiş: takip bilgisi eski kalmış olabilir; "
                        "'sureklilik_denetle.py' çalıştırın, olgu değiştiyse bölümü yeniden kaydedin.")
    for i in kitap_proje.acik_ipuclari(proje, takip):
        hedef = i.get("planlanan_cozum_bolumu")
        if isinstance(hedef, int) and hedef < sonraki:
            uyarilar.append(f"İpucu {i.get('id', '?')} ({i.get('ozet', '')}) {hedef}. bölümde çözülecekti, hâlâ açık.")
    kayit_klasoru = proje / ".hikaye" / "anliklar" / "kayitlar"
    anliklar = sorted(kayit_klasoru.glob("*.json")) if kayit_klasoru.is_dir() else []
    if yazilan and not anliklar:
        uyarilar.append("Hiç anlık görüntü yok: 'anlik_goruntu.py al --proje ...' ile sürüm alın.")
    elif anliklar:
        m = re.match(r"(\d{8})", anliklar[-1].name)
        if m:
            yas = (bugun - dt.datetime.strptime(m.group(1), "%Y%m%d").date()).days
            if yas >= 7:
                uyarilar.append(f"Son anlık görüntü {yas} gün önce alınmış; yeni bir sürüm alın.")
    dongu = proje / ".hikaye" / "dongu" / f"bolum-{sonraki:03d}" / "dongu.json"
    dongu_durumu = None
    if dongu.is_file():
        try:
            turlar = dosya_oku.json_nesne_oku(dongu).get("turlar", [])
            if isinstance(turlar, list) and turlar and isinstance(turlar[-1], dict):
                dongu_durumu = {"tur": len(turlar), "karar": turlar[-1].get("karar")}
                adimlar.insert(0, f"{sonraki}. bölümün revizyon döngüsü sürüyor ({len(turlar)} tur, karar: "
                                  f"{turlar[-1].get('karar')}): 'revizyon_dongusu.py durum' ile devam edin.")
        except dosya_oku.DosyaHatasi:
            pass
    return {
        "kitap": kitap_proje.kitap_basligi(proje), "son_kaydedilen_bolum": son, "yazilan_bolum": len(yazilan),
        "planli_bolum": len(planli), "toplam_kelime": sum(b.kelime for b in yazilan.values()),
        "yarim_kalan": yarim, "kaydedilmemis": kaydedilmemis, "sonraki_bolum": sonraki,
        "adimlar": adimlar, "uyarilar": uyarilar, "degisen_bolumler": degisen, "dongu": dongu_durumu, "anlik_goruntu": len(anliklar),
    }


def durum_metni(d: dict[str, Any]) -> str:
    s = [f"📍 {d['kitap']}: {d['yazilan_bolum']} bölüm yazıldı, {d['son_kaydedilen_bolum']} bölüm takibe kaydedildi, "
         f"{d['planli_bolum']} bölüm planı var; toplam {format(d['toplam_kelime'], ',').replace(',', '.')} kelime.",
         "", "Sıradaki adım:"]
    s += [f"  {i}. {a}" for i, a in enumerate(d["adimlar"], 1)]
    if d["uyarilar"]:
        s += ["", "Dikkat:"] + [f"  - {u}" for u in d["uyarilar"]]
    return "\n".join(s)


def bolum_ozetleri(proje: Path) -> dict[int, str]:
    sonuc: dict[int, str] = {}
    klasor = proje / "takip" / "bolum-kayitlari"
    if klasor.is_dir():
        for yol in sorted(klasor.glob("bolum-*.md")):
            m = re.match(r"bolum-(\d+)\.md$", yol.name)
            if not m:
                continue
            satir = re.search(r"^[ \t]*-[ \t]*Sonuç[ \t]*:[ \t]*(.+)$", dosya_oku.metin_oku(yol, uyar=False), re.M)
            if satir:
                sonuc[int(m.group(1))] = satir.group(1).strip()
    baglam = _takip(proje).get("baglam", {})
    for kayit in baglam.get("son_bolumler", []) if isinstance(baglam, dict) else []:
        if isinstance(kayit, dict) and isinstance(kayit.get("bolum"), int) and kayit.get("ozet"):
            sonuc.setdefault(kayit["bolum"], str(kayit["ozet"]))
    return dict(sorted(sonuc.items()))


def ciltler(proje: Path, son_bolum: int, grup: int) -> list[tuple[str, int, int]]:
    yol = proje / "plan" / "genel-plan.md"
    bulunan: list[tuple[str, int, int]] = []
    if yol.is_file():
        for m in re.finditer(r"\*\*(.+?)\*\*\s*\((\d+)\s*[–-]\s*(\d+)\)", dosya_oku.metin_oku(yol, uyar=False)):
            bas, bit = int(m.group(2)), int(m.group(3))
            if 1 <= bas <= bit:
                bulunan.append((m.group(1).strip(), bas, bit))
    if bulunan:
        return sorted(bulunan, key=lambda x: x[1])
    return [(f"{i // grup + 1}. kısım", i + 1, i + grup) for i in range(0, max(son_bolum, 1), grup)]


def _oz(proje: Path) -> str:
    kar = proje / "plan" / "kar-tanesi.md"
    if kar.is_file():
        m = re.search(r"^##\s*1\.[^\n]*\n(.*?)(?=^##\s|\Z)", dosya_oku.metin_oku(kar, uyar=False), re.M | re.S)
        if m:
            metin = " ".join(s.strip() for s in m.group(1).splitlines() if s.strip() and not s.lstrip().startswith(">"))
            if metin:
                return metin
    genel = proje / "plan" / "genel-plan.md"
    if genel.is_file():
        m = re.search(r"^[ \t]*[-*][ \t]+\**(?:Tek cümlelik öz|Tek cümlelik özet|Öz)\**[ \t]*:[ \t]*(.+)$", dosya_oku.metin_oku(genel, uyar=False),
                      re.M | re.I)
        if m:
            return m.group(1).strip()
    return ""


def ilk_cumle(metin: str) -> str:
    m = re.match(r"(.+?[.!?…])(?:\s|$)", metin)
    return m.group(1) if m else metin


def ozet_katmanlari(proje: Path, grup: int = 10, sinir: int = 16000) -> str:
    kitap_proje.proje_klasoru(proje)
    ozetler = bolum_ozetleri(proje)
    son = max(ozetler, default=0)
    parcalar = [f"# Özet katmanları — {kitap_proje.kitap_basligi(proje)}", ""]
    oz = _oz(proje)
    parcalar += ["## Kitap", "", oz or "(tek cümlelik öz yazılmamış: plan/kar-tanesi.md 1. adım)", ""]
    if not ozetler:
        return "\n".join(parcalar + ["Henüz takibe kaydedilmiş bölüm özeti yok."]) + "\n"
    gruplar = [(ad, bas, bit) for ad, bas, bit in ciltler(proje, son, grup) if any(bas <= n <= bit for n in ozetler)]
    kapsanan = {n for _, bas, bit in gruplar for n in ozetler if bas <= n <= bit}
    if set(ozetler) - kapsanan:
        eksik = sorted(set(ozetler) - kapsanan)
        gruplar.append(("Diğer bölümler", eksik[0], eksik[-1]))
    for sikistir in (1, 2, 3):
        govde = []
        for i, (ad, bas, bit) in enumerate(gruplar):
            eski = i < len(gruplar) - 1
            govde += [f"## {ad} ({bas}–{bit})", ""]
            for n in (n for n in ozetler if bas <= n <= bit):
                metin = ozetler[n]
                if eski and sikistir >= 2:
                    metin = ilk_cumle(metin)
                govde.append(f"- {n}: {metin}")
            if eski and sikistir >= 3:
                govde = govde[:-sum(1 for n in ozetler if bas <= n <= bit)] + [
                    f"- {bas}–{bit}: " + " ".join(ilk_cumle(ozetler[n]) for n in ozetler if bas <= n <= bit)[:600]]
            govde.append("")
        belge = "\n".join(parcalar + govde)
        if len(belge.encode("utf-8")) <= sinir:
            return belge
    kes = belge.encode("utf-8")[:sinir].decode("utf-8", errors="ignore")
    return kes.rsplit("\n", 1)[0] + "\n\n(Sınır nedeniyle kesildi.)\n"


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Proje durumu (sıradaki adım) ve özet katmanları (uzun roman belleği).")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_d = alt.add_parser("durum", help="nerede kaldığınızı ve sıradaki adımı göster")
    p_d.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_o = alt.add_parser("ozet", help="kitap, cilt ve bölüm katmanlı özet belleği üret")
    p_o.add_argument("--grup", type=int, default=10, help="genel planda aralık yoksa kaç bölümde bir kısım (varsayılan 10)")
    p_o.add_argument("--sinir", type=int, default=16000, help="en büyük boyut (bayt, varsayılan 16000)")
    p_o.add_argument("--cikti", type=Path, help="bu dosyaya yaz (varsayılan: standart çıktı)")
    for p in (p_d, p_o):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "durum":
            d = durum_raporu(arg.proje)
            print(json.dumps(d, ensure_ascii=False, indent=2) if arg.json else durum_metni(d))
        else:
            if not 1 <= arg.grup <= 500:
                raise kitap_proje.ProjeHatasi("--grup 1 ile 500 arasında olmalı")
            if arg.sinir < 1000:
                raise kitap_proje.ProjeHatasi("--sinir en az 1000 bayt olmalı")
            belge = ozet_katmanlari(arg.proje, arg.grup, arg.sinir)
            if arg.cikti:
                arg.cikti.parent.mkdir(parents=True, exist_ok=True)
                arg.cikti.write_text(belge, encoding="utf-8", newline="\n")
                print(f"Özet katmanları yazıldı: {arg.cikti} ({len(belge.encode('utf-8'))} bayt)")
            else:
                print(belge, end="")
    except (kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
