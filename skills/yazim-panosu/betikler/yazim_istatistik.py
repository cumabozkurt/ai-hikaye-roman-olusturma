#!/usr/bin/env python3
"""Yazım hedefleri ve istatistik panosu: günlük kelime, seri, bitiş tahmini, bölüm ilerlemesi.

Kullanım::

    yazim_istatistik.py hedef   --proje KITAP --toplam 80000 [--bitis 2027-03-01] [--gunluk 1000]
    yazim_istatistik.py kaydet  --proje KITAP            # bugünkü toplamı deftere yazar
    yazim_istatistik.py pano    --proje KITAP [--html pano.html] [--json]

Veriler ``KITAP/.hikaye/istatistik.json`` dosyasında tutulur. ``kaydet`` her
çağrıldığında bugünün son toplamını günceller; o gün yazılan kelime, bugünkü son
toplam ile önceki kayıtlı günün son toplamı arasındaki farktır (silme eksi sayılır).
Sayfa tahmini sayfa başına 250 kelime, okuma süresi dakikada 200 kelime varsayar.

Çıkış kodu: 0 başarılı, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitap_proje  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

SAYFA_BASINA = 250
DAKIKADA = 200
ASGARI_TAHMIN_GUNU = 3  # bitiş tahmini için son 7 günde gereken yazım günü
EN_UZAK_TAHMIN_GUNU = 3650
AYLAR = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim",
         "Kasım", "Aralık")


class IstatistikHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def tarih_coz(deger: str) -> dt.date:
    try:
        return dt.date.fromisoformat(deger.strip())
    except ValueError:
        raise IstatistikHatasi(f"geçersiz tarih: {deger!r} (beklenen biçim: 2027-03-01)") from None


def tr_tarih(gun: dt.date) -> str:
    return f"{gun.day} {AYLAR[gun.month - 1]} {gun.year}"


def sayi(n: float) -> str:
    """Türkçe binlik ayırıcı: 12.345"""
    return f"{int(round(n)):,}".replace(",", ".")


def _dosya(proje: Path) -> Path:
    return proje / ".hikaye" / "istatistik.json"


def defter_oku(proje: Path) -> dict[str, Any]:
    yol = _dosya(proje)
    bos: dict[str, Any] = {"sema_surumu": 1, "hedef": {}, "gunler": {}}
    if not yol.is_file():
        return bos
    try:
        veri = json.loads(yol.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as hata:
        raise IstatistikHatasi(f"istatistik defteri bozuk: {yol} ({hata.__class__.__name__}). "
                               "Dosyayı silerseniz yeni defter açılır.") from None
    if not isinstance(veri, dict):
        raise IstatistikHatasi(f"istatistik defteri bozuk: {yol} (kök nesne değil)")
    hedef = veri.get("hedef") if isinstance(veri.get("hedef"), dict) else {}
    gunler = {}
    for gun, kayit in (veri.get("gunler") or {}).items() if isinstance(veri.get("gunler"), dict) else []:
        try:
            dt.date.fromisoformat(gun)
            son = int(kayit["kelime"]) if isinstance(kayit, dict) else int(kayit)
            ilk = int(kayit.get("ilk", son)) if isinstance(kayit, dict) else son
            gunler[gun] = {"ilk": ilk, "kelime": son}
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return {"sema_surumu": 1, "hedef": hedef, "gunler": dict(sorted(gunler.items()))}


def defter_yaz(proje: Path, defter: dict[str, Any]) -> None:
    yol = _dosya(proje)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(".gecici")
    gecici.write_text(json.dumps(defter, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    os.replace(gecici, yol)


def hedef_ayarla(proje: Path, toplam: int | None, bitis: str | None, gunluk: int | None) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    defter = defter_oku(proje)
    hedef = defter["hedef"]
    if toplam is not None:
        if not 1000 <= toplam <= 2_000_000:
            raise IstatistikHatasi("--toplam 1.000 ile 2.000.000 kelime arasında olmalı")
        hedef["toplam_kelime"] = toplam
    if bitis is not None:
        hedef["bitis"] = tarih_coz(bitis).isoformat()
    if gunluk is not None:
        if not 50 <= gunluk <= 20000:
            raise IstatistikHatasi("--gunluk 50 ile 20.000 kelime arasında olmalı")
        hedef["gunluk_kelime"] = gunluk
    if not hedef:
        raise IstatistikHatasi("en az bir hedef verin: --toplam, --bitis ya da --gunluk")
    defter_yaz(proje, defter)
    return hedef


def kaydet(proje: Path, bugun: dt.date | None = None) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    bugun = bugun or dt.date.today()
    toplam = sum(b.kelime for b in kitap_proje.bolumler(proje))
    defter = defter_oku(proje)
    onceki = defter["gunler"].get(bugun.isoformat())
    defter["gunler"][bugun.isoformat()] = {"ilk": onceki["ilk"] if onceki else toplam, "kelime": toplam}
    defter["gunler"] = dict(sorted(defter["gunler"].items()))
    defter_yaz(proje, defter)
    return {"tarih": bugun.isoformat(), "toplam": toplam}


def gunluk_yazilan(gunler: dict[str, dict[str, int]]) -> dict[str, int]:
    """Her kayıtlı gün için o gün yazılan (net) kelime.

    Önceki kayıtlı günün son toplamına göre hesaplanır; ilk kayıtlı günde o günün ilk
    kaydı başlangıç noktasıdır (içe aktarılan eski metin 'bugün yazıldı' sayılmaz)."""
    sonuc: dict[str, int] = {}
    onceki: int | None = None
    for gun, kayit in sorted(gunler.items()):
        toplam = kayit["kelime"]
        sonuc[gun] = toplam - (kayit.get("ilk", toplam) if onceki is None else onceki)
        onceki = toplam
    return sonuc


def pano_verisi(proje: Path, bugun: dt.date | None = None) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    bugun = bugun or dt.date.today()
    defter = defter_oku(proje)
    hedef = defter["hedef"]
    bolum_listesi = []
    for b in kitap_proje.bolumler(proje):
        plan = kitap_proje.plan_hedefi(proje, b.no)
        bolum_listesi.append({"no": b.no, "baslik": b.baslik, "kelime": b.kelime, "hedef": plan,
                              "yuzde": round(100 * b.kelime / plan) if plan else None})
    toplam = sum(b["kelime"] for b in bolum_listesi)
    yazilan = gunluk_yazilan(defter["gunler"])
    if defter["gunler"] and max(defter["gunler"]) == bugun.isoformat():
        yazilan[bugun.isoformat()] = yazilan.get(bugun.isoformat(), 0) + toplam - defter["gunler"][bugun.isoformat()]["kelime"]
    elif defter["gunler"]:
        son = defter["gunler"][max(defter["gunler"])]["kelime"]
        yazilan[bugun.isoformat()] = toplam - son
    seri = 0
    gun = bugun
    if yazilan.get(gun.isoformat(), 0) <= 0:
        gun -= dt.timedelta(days=1)  # bugün henüz yazılmadıysa seri dünden sayılır
    while yazilan.get(gun.isoformat(), 0) > 0:
        seri += 1
        gun -= dt.timedelta(days=1)
    son_30 = [(bugun - dt.timedelta(days=i)) for i in range(29, -1, -1)]
    grafik = [{"tarih": g.isoformat(), "kelime": max(0, yazilan.get(g.isoformat(), 0))} for g in son_30]
    son_7 = sum(max(0, yazilan.get((bugun - dt.timedelta(days=i)).isoformat(), 0)) for i in range(7))
    hiz = son_7 / 7
    veri: dict[str, Any] = {
        "kitap": kitap_proje.kitap_basligi(proje), "bugun": bugun.isoformat(), "toplam_kelime": toplam,
        "bolum_sayisi": len(bolum_listesi), "sayfa_tahmini": round(toplam / SAYFA_BASINA),
        "okuma_dakikasi": round(toplam / DAKIKADA), "bugun_yazilan": yazilan.get(bugun.isoformat(), 0),
        "seri_gun": seri, "son_7_gun_ortalama": round(hiz), "grafik": grafik, "bolumler": bolum_listesi,
        "hedef": hedef, "kayitli_gun": len(defter["gunler"]),
    }
    hedef_toplam = hedef.get("toplam_kelime")
    if hedef_toplam:
        kalan = max(0, hedef_toplam - toplam)
        veri["ilerleme_yuzde"] = min(100, round(100 * toplam / hedef_toplam, 1))
        veri["kalan_kelime"] = kalan
        yazilan_gun = sum(1 for i in range(7) if yazilan.get((bugun - dt.timedelta(days=i)).isoformat(), 0) > 0)
        if hiz >= 1 and kalan > 0 and yazilan_gun >= ASGARI_TAHMIN_GUNU:
            gun_sayisi = -(-kalan // round(hiz))
            if gun_sayisi <= EN_UZAK_TAHMIN_GUNU:
                veri["tahmini_bitis"] = (bugun + dt.timedelta(days=gun_sayisi)).isoformat()
            else:
                veri["tahmini_bitis_uzak"] = True
        if hedef.get("bitis"):
            kalan_gun = (dt.date.fromisoformat(hedef["bitis"]) - bugun).days
            veri["kalan_gun"] = kalan_gun
            veri["gereken_gunluk"] = -(-kalan // kalan_gun) if kalan_gun > 0 else kalan
    if hedef.get("gunluk_kelime"):
        veri["gunluk_hedef_yuzde"] = round(100 * max(0, veri["bugun_yazilan"]) / hedef["gunluk_kelime"])
    return veri


def yuzde(deger: float) -> str:
    """Yüzdeyi Türkçe ondalık virgülle yazar: 1.5 -> '%1,5'."""
    return "%" + f"{deger:g}".replace(".", ",")


def cubuk(oran: float, genislik: int = 20) -> str:
    dolu = max(0, min(genislik, round(oran * genislik)))
    return "█" * dolu + "░" * (genislik - dolu)


def metin_panosu(v: dict[str, Any]) -> str:
    s = [f"📊 {v['kitap']} — yazım panosu ({tr_tarih(dt.date.fromisoformat(v['bugun']))})", ""]
    s.append(f"Toplam: {sayi(v['toplam_kelime'])} kelime · {v['bolum_sayisi']} bölüm · "
             f"~{sayi(v['sayfa_tahmini'])} sayfa · ~{sayi(v['okuma_dakikasi'])} dk okuma")
    if "ilerleme_yuzde" in v:
        s.append(f"Kitap hedefi: {cubuk(v['ilerleme_yuzde'] / 100)} {yuzde(v['ilerleme_yuzde'])} "
                 f"({sayi(v['toplam_kelime'])} / {sayi(v['hedef']['toplam_kelime'])}; kalan {sayi(v['kalan_kelime'])})")
    bugun = f"Bugün: {sayi(v['bugun_yazilan'])} kelime"
    if "gunluk_hedef_yuzde" in v:
        bugun += f" (günlük hedef {sayi(v['hedef']['gunluk_kelime'])}, tamamlanan {yuzde(v['gunluk_hedef_yuzde'])})"
    s.append(bugun + f" · seri: {v['seri_gun']} gün · son 7 gün ortalaması: {sayi(v['son_7_gun_ortalama'])}/gün")
    if "kalan_gun" in v:
        if v["kalan_gun"] > 0:
            s.append(f"Bitiş tarihine {v['kalan_gun']} gün var; yetişmek için günde {sayi(v['gereken_gunluk'])} kelime gerekiyor.")
        else:
            s.append("Bitiş tarihi geçti ya da bugün; hedef tarihi güncellemeyi düşünün.")
    if "tahmini_bitis" in v:
        s.append(f"Bu hızla tahmini bitiş: {tr_tarih(dt.date.fromisoformat(v['tahmini_bitis']))}")
    elif v.get("tahmini_bitis_uzak"):
        s.append("Bu hızla hedefe ulaşmak on yıldan uzun sürer; günlük hedefi gözden geçirin.")
    elif "kalan_kelime" in v and v["kalan_kelime"] > 0 and v["kayitli_gun"] > 0:
        s.append(f"Bitiş tahmini için son 7 günün en az {ASGARI_TAHMIN_GUNU} gününde yazım kaydı gerekir.")
    if v["kayitli_gun"] == 0:
        s.append("Henüz günlük kayıt yok: her yazım oturumunun sonunda 'kaydet' komutunu çalıştırın.")
    en_cok = max((g["kelime"] for g in v["grafik"]), default=0)
    if en_cok > 0:
        bloklar = "▁▂▃▄▅▆▇█"
        s.append("Son 30 gün: " + "".join("·" if g["kelime"] <= 0 else bloklar[min(7, round(7 * g["kelime"] / en_cok))]
                                          for g in v["grafik"]))
    if v["bolumler"]:
        s += ["", "Bölümler:"]
        for b in v["bolumler"]:
            if b["hedef"]:
                s.append(f"  {b['no']:>3}. {b['baslik'][:38]:<38} {sayi(b['kelime']):>7} / {sayi(b['hedef']):>6} "
                         f"{cubuk(b['kelime'] / b['hedef'], 10)} %{b['yuzde']}")
            else:
                s.append(f"  {b['no']:>3}. {b['baslik'][:38]:<38} {sayi(b['kelime']):>7}")
    return "\n".join(s)


def html_panosu(v: dict[str, Any]) -> str:
    e = html.escape
    en_cok = max((g["kelime"] for g in v["grafik"]), default=0) or 1
    cubuklar = []
    for i, g in enumerate(v["grafik"]):
        yukseklik = round(120 * g["kelime"] / en_cok)
        cubuklar.append(f'<rect x="{i * 20 + 4}" y="{130 - yukseklik}" width="14" height="{yukseklik}" rx="2">'
                        f'<title>{e(g["tarih"])}: {sayi(g["kelime"])} kelime</title></rect>')
    satirlar = []
    for b in v["bolumler"]:
        oran = min(1.0, b["kelime"] / b["hedef"]) if b["hedef"] else 0
        hedef = f"{sayi(b['hedef'])}" if b["hedef"] else "—"
        satirlar.append(f"<tr><td>{b['no']}</td><td>{e(b['baslik'])}</td><td>{sayi(b['kelime'])}</td><td>{hedef}</td>"
                        f"<td><div class='bar'><span style='width:{round(oran * 100)}%'></span></div></td></tr>")
    ilerleme = v.get("ilerleme_yuzde")
    kartlar = [("Toplam kelime", sayi(v["toplam_kelime"])), ("Bölüm", str(v["bolum_sayisi"])),
               ("Sayfa (tahmini)", sayi(v["sayfa_tahmini"])), ("Bugün", sayi(v["bugun_yazilan"])),
               ("Seri", f"{v['seri_gun']} gün"), ("7 gün ortalaması", sayi(v["son_7_gun_ortalama"]))]
    if ilerleme is not None:
        kartlar.insert(1, ("Kitap hedefi", yuzde(ilerleme)))
    if "tahmini_bitis" in v:
        kartlar.append(("Tahmini bitiş", tr_tarih(dt.date.fromisoformat(v["tahmini_bitis"]))))
    if "gereken_gunluk" in v and v.get("kalan_gun", 0) > 0:
        kartlar.append(("Gereken günlük", sayi(v["gereken_gunluk"])))
    kart_html = "".join(f"<div class='kart'><b>{e(d)}</b><small>{e(a)}</small></div>" for a, d in kartlar)
    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(v['kitap'])} — Yazım Panosu</title>
<style>
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#0b1526;color:#e8eef7;margin:0;padding:24px}}
h1{{font-weight:600;margin:0 0 4px}} .alt{{color:#9fb0c8;margin-bottom:20px}}
.kartlar{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:24px}}
.kart{{background:#13223a;border:1px solid #22385a;border-radius:10px;padding:14px}}
.kart b{{display:block;font-size:1.5em;color:#f2b84b}} .kart small{{color:#9fb0c8}}
svg rect{{fill:#f2b84b}} section{{background:#13223a;border-radius:10px;padding:16px;margin-bottom:20px}}
table{{border-collapse:collapse;width:100%}} td,th{{padding:6px 8px;border-bottom:1px solid #22385a;text-align:left}}
.bar{{background:#22385a;border-radius:6px;height:10px;width:160px}} .bar span{{display:block;height:10px;border-radius:6px;background:#4fd1c5}}
</style></head><body>
<h1>{e(v['kitap'])}</h1><div class="alt">Yazım panosu · {e(tr_tarih(dt.date.fromisoformat(v['bugun'])))}</div>
<div class="kartlar">{kart_html}</div>
<section><h2>Son 30 gün</h2><svg viewBox="0 0 604 134" width="100%" role="img" aria-label="Son 30 günde yazılan kelime">{''.join(cubuklar)}</svg></section>
<section><h2>Bölümler</h2><table><tr><th>#</th><th>Başlık</th><th>Kelime</th><th>Hedef</th><th>İlerleme</th></tr>{''.join(satirlar)}</table></section>
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Yazım hedefleri, günlük kayıt ve istatistik panosu.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_h = alt.add_parser("hedef", help="kitap, bitiş tarihi ya da günlük kelime hedefi koy")
    p_h.add_argument("--toplam", type=int, help="kitabın hedef toplam kelime sayısı")
    p_h.add_argument("--bitis", help="hedef bitiş tarihi (YYYY-AA-GG)")
    p_h.add_argument("--gunluk", type=int, help="günlük kelime hedefi")
    p_k = alt.add_parser("kaydet", help="bugünkü toplam kelimeyi deftere yaz")
    p_p = alt.add_parser("pano", help="istatistik panosunu göster")
    p_p.add_argument("--html", type=Path, help="panoyu bu HTML dosyasına da yaz")
    for p in (p_h, p_k, p_p):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
        p.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    for p in (p_k, p_p):
        p.add_argument("--bugun", help="bugünün tarihi yerine bu tarihi kullan (YYYY-AA-GG; deneme ve geçmiş kayıt için)")
    arg = ayr.parse_args(argv)
    try:
        bugun = tarih_coz(arg.bugun) if getattr(arg, "bugun", None) else None
        if arg.komut == "hedef":
            sonuc: Any = hedef_ayarla(arg.proje, arg.toplam, arg.bitis, arg.gunluk)
            metin = "Hedef kaydedildi: " + ", ".join(f"{k} = {v}" for k, v in sonuc.items())
        elif arg.komut == "kaydet":
            sonuc = kaydet(arg.proje, bugun)
            metin = f"{sonuc['tarih']} için toplam {sayi(sonuc['toplam'])} kelime kaydedildi."
        else:
            sonuc = pano_verisi(arg.proje, bugun)
            metin = metin_panosu(sonuc)
            if arg.html:
                arg.html.parent.mkdir(parents=True, exist_ok=True)
                arg.html.write_text(html_panosu(sonuc), encoding="utf-8", newline="\n")
                metin += f"\n\nHTML pano yazıldı: {arg.html}"
    except (IstatistikHatasi, kitap_proje.ProjeHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2) if arg.json else metin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
