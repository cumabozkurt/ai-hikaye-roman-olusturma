#!/usr/bin/env python3
"""Yaz → eleştir → düzelt döngüsü: ölçülebilir puanlama, tur kaydı, plato tespiti, yazar onayı.

Döngüyü model yürütür ama kararı yazar verir: araç ``metin/`` klasörüne yalnızca
``kabul --yazar-onayladi`` ile ve önce anlık görüntü alarak yazar.

Puan iki kaynaktan gelir:

* Mekanik puan (0–10, araç ölçer): yapay zekâ kalıpları, cümle ritmi, yakın
  tekrarlar, plan hedefine göre uzunluk ve (varsa) kitabın ses izine benzerlik.
  Bitmemiş metin işaretleri ([TK] vb.) bir kapıdır: varken hedefe ulaşılmış sayılmaz.
* Hakem puanı (1–10, model ya da insan editör doldurur): ``rubrik`` komutunun
  verdiği altı ölçüt ve bölüm planındaki maddelerin tek tek "tamam / eksik /
  dogrulanmali" değerlendirmesi. "eksik" ya da "dogrulanmali" madde varken hedefe
  ulaşılmış sayılmaz.

Toplam = 0,4 × mekanik + 0,6 × hakem (hakem yoksa yalnızca mekanik).

Kullanım::

    revizyon_dongusu.py olc    --dosya taslak.md [--proje KITAP --bolum 7]
    revizyon_dongusu.py rubrik --proje KITAP --bolum 7
    revizyon_dongusu.py kaydet --proje KITAP --bolum 7 --dosya taslak.md [--hakem hakem.json] [--hedef 8] [--en-fazla-tur 4]
    revizyon_dongusu.py brief  --proje KITAP --bolum 7
    revizyon_dongusu.py durum  --proje KITAP --bolum 7 [--json]
    revizyon_dongusu.py kabul  --proje KITAP --bolum 7 --tur 3 --yazar-onayladi

Karar değerleri: devam, dur-hedef, dur-plato (son iki turda 0,2 puandan az
ilerleme), dur-tur-siniri.

Çıkış kodu: 0 başarılı, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_kalip_denetle  # noqa: E402
import anlik_goruntu  # noqa: E402
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402
import metin_analizi  # noqa: E402
import metin_olcum  # noqa: E402
import ses_izi  # noqa: E402
import turkce_kaliplar as tk  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

OLCUTLER = {
    "plan_sadakati": "Bölüm planındaki olaylar, seçim ve kanca gerçekleşiyor mu?",
    "gerilim": "Okur sayfayı çevirmek istiyor mu? Sahnelerde amaç ve engel var mı?",
    "karakter": "Karakterler kendileri gibi mi davranıyor, sesleri ayrışıyor mu?",
    "somutluk": "Soyut duygu adlandırma yerine somut ayrıntı ve duyular mı var?",
    "diyalog": "Diyalog doğal mı, alt metin taşıyor mu, bilgi dökmüyor mu?",
    "dil": "Türkçe akıcı ve doğru mu (TDK yazımı, doğal söz dizimi, çeviri kokusu yok)?",
}
DUZEY_CAPALARI = ("1–3: yeniden yazılmalı; 4–5: belirgin sorunlar; 6–7: yayımlanabilir taslak; "
                  "8–9: güçlü, küçük rötuş; 10: örnek gösterilecek düzeyde")
PLAN_ALANLARI = ("Ana olay", "Kahramanın amacı / kritik seçimi", "Açılış kancası", "Doyum anı",
                 "Bölüm sonu kancası", "Duygu hedefi")
DURUMLAR = ("tamam", "eksik", "dogrulanmali")
MEKANIK_AGIRLIK = 0.4
PLATO_ESIGI = 0.2


class DonguHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe hata."""


def _sinirla(x: float) -> float:
    return round(max(0.0, min(10.0, x)), 2)


def mekanik_olc(metin: str, proje: Path | None = None, bolum: int | None = None) -> dict[str, Any]:
    analiz = metin_analizi.analiz_et(metin)
    n = analiz["kelime"]
    if n == 0:
        raise DonguHatasi("taslak boş ya da ölçülecek kelime yok")
    hayali = (proje / "metin" / "_taslak.md") if proje else Path("_taslak.md")
    beyaz = ai_kalip_denetle.beyaz_liste_yukle(hayali) if proje else []
    yasak = ai_kalip_denetle.yasak_liste_yukle(hayali) if proje else []
    bulgular = ai_kalip_denetle.denetle_metin(metin, "taslak", beyaz, yasak)
    eng = sum(1 for b in bulgular if b.onem == ai_kalip_denetle.ENGELLEYICI)
    uyari = len(bulgular) - eng
    yogunluk = (2.5 * eng + uyari) / max(n, 600) * 1000  # çok kısa metinde tek bulgu puanı sıfırlamasın
    puanlar: dict[str, float] = {"yz_kaliplari": _sinirla(10 - 1.25 * yogunluk)}
    cu = analiz["cumle_uzunlugu"]
    cv = cu["sapma"] / cu["ortalama"] if cu["ortalama"] else 0
    puanlar["ritim"] = _sinirla(10 * min(1.0, cv / 0.5) - max(0.0, (cu["ortalama"] - 24) / 2))
    tekrar = sum(1 for y in analiz["yankilar"] if y["sayi"] >= 3) + len(analiz["cumle_basi"])
    puanlar["tekrar"] = _sinirla(10 - 1.5 * tekrar / max(n, 1000) * 1000)
    hedef = kitap_proje.plan_hedefi(proje, bolum) if proje and bolum else None
    olcum_kelime = metin_olcum.kelime_say(metin)
    if hedef:
        oran = olcum_kelime / hedef
        ic, sert = metin_olcum.IC_BANT, metin_olcum.SERT_BANT
        if ic[0] <= oran <= ic[1]:
            puanlar["uzunluk"] = 10.0
        elif sert[0] <= oran < ic[0]:
            puanlar["uzunluk"] = _sinirla(4 + 6 * (oran - sert[0]) / (ic[0] - sert[0]))
        elif ic[1] < oran <= sert[1]:
            puanlar["uzunluk"] = _sinirla(4 + 6 * (sert[1] - oran) / (sert[1] - ic[1]))
        else:
            puanlar["uzunluk"] = 0.0
    profil_yolu = proje / "kurgu" / "ses-izi.json" if proje else None
    ses = None
    if profil_yolu and profil_yolu.is_file():
        try:
            ses = ses_izi.karsilastir(dosya_oku.json_nesne_oku(profil_yolu), metin)
            puanlar["ses"] = _sinirla(ses["benzerlik"] / 10)
        except (ses_izi.SesHatasi, dosya_oku.DosyaHatasi):
            ses = None
    toplam = round(sum(puanlar.values()) / len(puanlar), 2)
    return {
        "kelime": olcum_kelime, "hedef_kelime": hedef, "puanlar": puanlar, "mekanik": toplam,
        "bitmemis_isaret": len(analiz["isaretler"]),
        "yz_bulgulari": [{"satir": b.satir, "kural": b.kural, "alinti": b.alinti, "oneri": b.oneri, "onem": b.onem}
                         for b in bulgular[:30]],
        "uyarilar": analiz["uyarilar"],
        "ses_sapmalari": [ses_izi.sapma_cumlesi(x) for x in (ses or {}).get("sapmalar", [])[:5]],
    }


def plan_maddeleri(proje: Path, bolum: int) -> list[str]:
    yol = kitap_proje.plan_dosyasi(proje, bolum)
    if yol is None:
        raise DonguHatasi(f"{bolum}. bölümün planı yok: plan/bolum-plani_{bolum:03d}.md")
    metin = dosya_oku.metin_oku(yol, uyar=False)
    maddeler = []
    for alan in PLAN_ALANLARI:
        m = re.search(rf"^[ \t]*[-*][ \t]+\**{re.escape(alan)}\**[ \t]*:[ \t]*(.+)$", metin, re.M | re.I)
        if m and m.group(1).strip() and "[doldurulacak]" not in m.group(1):
            maddeler.append(f"{alan}: {m.group(1).strip()}")
    tablo = re.search(r"^##\s+Olay Akışı\s*$(.*?)(?=^##\s|\Z)", metin, re.M | re.S)
    if tablo:
        satirlar = [s for s in tablo.group(1).splitlines() if s.strip().startswith("|")]
        if len(satirlar) >= 3:
            basliklar = [tk.tr_kucuk(h.strip()) for h in satirlar[0].strip("|").split("|")]
            i = basliklar.index("olay") if "olay" in basliklar else None
            for s in satirlar[2:]:
                hucre = [h.strip() for h in s.strip("|").split("|")]
                if i is not None and i < len(hucre) and hucre[i]:
                    maddeler.append(f"Olay: {hucre[i]}")
    gizli = re.search(r"^[ \t]*[-*][ \t]+\**Bu bölümde açığa çıkmayacaklar\**[ \t]*:[ \t]*(.+)$", metin, re.M | re.I)
    if gizli:
        for parca in re.split(r"[;]", gizli.group(1)):
            if parca.strip().strip("."):
                maddeler.append(f"Açığa çıkmamalı: {parca.strip().strip('.')}")
    return maddeler


def rubrik_metni(proje: Path, bolum: int) -> str:
    maddeler = plan_maddeleri(proje, bolum)
    sablon = {"olcutler": {k: 0 for k in OLCUTLER},
              "plan_maddeleri": [{"madde": m, "durum": "tamam | eksik | dogrulanmali", "kanit": "metinden kısa alıntı"}
                                 for m in maddeler],
              "guclu": ["..."], "zayif": ["..."], "oneriler": ["..."]}
    s = [f"# Hakem yönergesi — {bolum}. bölüm", "",
         "Taslağı bir Türk yayınevi editörü gözüyle baştan sona okuyun. Puanları cömert değil, dürüst verin.",
         f"Ölçek: {DUZEY_CAPALARI}.", "", "## Ölçütler", ""]
    s += [f"- **{k}**: {v}" for k, v in OLCUTLER.items()]
    s += ["", "## Plan maddeleri", "",
          "Her maddeyi ayrı değerlendirin. Hazırlık ya da ima 'tamam' sayılmaz; metinde gerçekleşmediyse 'eksik', "
          "emin değilseniz 'dogrulanmali' yazın ve kanıt olarak kısa bir alıntı verin.", ""]
    s += [f"{i}. {m}" for i, m in enumerate(maddeler, 1)] or ["(planda değerlendirilecek madde bulunamadı)"]
    s += ["", "## Yanıt biçimi (yalnızca JSON)", "", "```json", json.dumps(sablon, ensure_ascii=False, indent=2), "```"]
    return "\n".join(s)


def hakem_dogrula(veri: dict[str, Any]) -> dict[str, Any]:
    olcutler = veri.get("olcutler")
    if not isinstance(olcutler, dict):
        raise DonguHatasi("hakem dosyasında 'olcutler' nesnesi yok")
    eksik = [k for k in OLCUTLER if k not in olcutler]
    if eksik:
        raise DonguHatasi(f"hakem dosyasında eksik ölçüt: {', '.join(eksik)}")
    for k in OLCUTLER:
        v = olcutler[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 1 <= v <= 10:
            raise DonguHatasi(f"'{k}' puanı 1 ile 10 arasında bir sayı olmalı, {v!r} verilmiş")
    maddeler = veri.get("plan_maddeleri", [])
    if not isinstance(maddeler, list):
        raise DonguHatasi("'plan_maddeleri' bir liste olmalı")
    for i, m in enumerate(maddeler, 1):
        if not isinstance(m, dict) or m.get("durum") not in DURUMLAR:
            raise DonguHatasi(f"{i}. plan maddesinin 'durum' değeri tamam, eksik ya da dogrulanmali olmalı")
    for alan in ("guclu", "zayif", "oneriler"):
        if alan in veri and not (isinstance(veri[alan], list) and all(isinstance(x, str) for x in veri[alan])):
            raise DonguHatasi(f"'{alan}' metin listesi olmalı")
    return {"olcutler": {k: float(olcutler[k]) for k in OLCUTLER}, "plan_maddeleri": maddeler,
            "guclu": veri.get("guclu", []), "zayif": veri.get("zayif", []), "oneriler": veri.get("oneriler", []),
            "hakem": round(sum(float(olcutler[k]) for k in OLCUTLER) / len(OLCUTLER), 2)}


def _klasor(proje: Path, bolum: int) -> Path:
    if not 1 <= bolum <= 9999:
        raise DonguHatasi("--bolum 1 ile 9999 arasında olmalı")
    return proje / ".hikaye" / "dongu" / f"bolum-{bolum:03d}"


def turlar(proje: Path, bolum: int) -> list[dict[str, Any]]:
    yol = _klasor(proje, bolum) / "dongu.json"
    if not yol.is_file():
        return []
    veri = dosya_oku.json_nesne_oku(yol)
    liste = veri.get("turlar")
    if not isinstance(liste, list):
        raise DonguHatasi(f"döngü kaydı bozuk: {yol}")
    return liste


def karar_ver(liste: list[dict[str, Any]], hedef: float, en_fazla: int) -> str:
    son = liste[-1]
    kapilar = son["bitmemis_isaret"] > 0 or son.get("acik_plan_maddesi", 0) > 0
    if son["toplam"] >= hedef and not kapilar:
        return "dur-hedef"
    if len(liste) >= en_fazla:
        return "dur-tur-siniri"
    if len(liste) >= 3:
        onceki_en_iyi = max(t["toplam"] for t in liste[:-2])
        if max(t["toplam"] for t in liste[-2:]) - onceki_en_iyi < PLATO_ESIGI:
            return "dur-plato"
    return "devam"


def kaydet(proje: Path, bolum: int, dosya: Path, hakem: Path | None, not_: str, hedef: float,
           en_fazla: int) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    if not 1 <= en_fazla <= 20:
        raise DonguHatasi("--en-fazla-tur 1 ile 20 arasında olmalı")
    if not 1 <= hedef <= 10:
        raise DonguHatasi("--hedef 1 ile 10 arasında olmalı")
    metin = dosya_oku.metin_oku(dosya)
    olcum = mekanik_olc(metin, proje, bolum)
    hakem_verisi = hakem_dogrula(dosya_oku.json_nesne_oku(hakem)) if hakem else None
    liste = turlar(proje, bolum)
    no = len(liste) + 1
    klasor = _klasor(proje, bolum)
    klasor.mkdir(parents=True, exist_ok=True)
    kopya = klasor / f"tur-{no:02d}.md"
    kopya.write_text(metin, encoding="utf-8")
    toplam = olcum["mekanik"]
    if hakem_verisi:
        toplam = round(MEKANIK_AGIRLIK * olcum["mekanik"] + (1 - MEKANIK_AGIRLIK) * hakem_verisi["hakem"], 2)
    acik = sum(1 for m in (hakem_verisi or {}).get("plan_maddeleri", []) if m["durum"] != "tamam")
    kayit = {"tur": no, "zaman": dt.datetime.now().replace(microsecond=0).isoformat(), "dosya": kopya.name,
             "ozet": hashlib.sha256(metin.encode("utf-8")).hexdigest(), "not": not_.strip(), "kelime": olcum["kelime"],
             "puanlar": olcum["puanlar"], "mekanik": olcum["mekanik"], "hakem": hakem_verisi,
             "toplam": toplam, "bitmemis_isaret": olcum["bitmemis_isaret"], "acik_plan_maddesi": acik,
             "yz_bulgulari": olcum["yz_bulgulari"][:15], "uyarilar": olcum["uyarilar"],
             "ses_sapmalari": olcum["ses_sapmalari"]}
    if liste and kayit["ozet"] == liste[-1]["ozet"] and (hakem_verisi or {}) == (liste[-1].get("hakem") or {}):
        kopya.unlink()
        raise DonguHatasi("bu taslak bir önceki turla aynı; değişiklik yapmadan yeni tur açılmaz")
    liste.append(kayit)
    en_iyi = max(liste, key=lambda t: (t["toplam"], -t["tur"]))
    kayit["karar"] = karar_ver(liste, hedef, en_fazla)
    kayit["en_iyi_tur"] = en_iyi["tur"]
    yol = klasor / "dongu.json"
    gecici = yol.with_suffix(".gecici")
    gecici.write_text(json.dumps({"sema_surumu": 1, "bolum": bolum, "hedef": hedef, "en_fazla_tur": en_fazla,
                                  "turlar": liste}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(gecici, yol)
    return kayit


def brief(proje: Path, bolum: int) -> str:
    liste = turlar(proje, bolum)
    if not liste:
        raise DonguHatasi(f"{bolum}. bölüm için kayıtlı tur yok; önce 'kaydet'")
    en_iyi = max(liste, key=lambda t: (t["toplam"], -t["tur"]))
    son = liste[-1]
    s = [f"# Revizyon talimatı — {bolum}. bölüm, {len(liste) + 1}. tur", "",
         f"Temel metin: **{en_iyi['tur']}. tur** (`.hikaye/dongu/bolum-{bolum:03d}/{en_iyi['dosya']}`, toplam "
         f"{tk.tr_ondalik(en_iyi['toplam'], 2)}). Son tur: {son['tur']} ({tk.tr_ondalik(son['toplam'], 2)}).",
         "Yalnızca aşağıdaki sorunları düzeltin; iyi çalışan sahneleri yeniden yazmayın. Olay örgüsünü planın dışına taşımayın.", ""]
    zayif_olcut = sorted(en_iyi["puanlar"].items(), key=lambda x: x[1])[:3]
    s += ["## Mekanik ölçümde en zayıf alanlar", ""]
    aciklama = {"yz_kaliplari": "yapay zekâ kalıpları", "ritim": "cümle ritmi", "tekrar": "yakın tekrarlar",
                "uzunluk": "plan hedefine göre uzunluk", "ses": "kitabın ses izine benzerlik"}
    s += [f"- {aciklama.get(k, k)}: {tk.tr_ondalik(v, 1)}/10" for k, v in zayif_olcut]
    if en_iyi.get("hedef_kelime") or en_iyi["puanlar"].get("uzunluk", 10) < 10:
        hedef = kitap_proje.plan_hedefi(proje, bolum)
        if hedef:
            fark = en_iyi["kelime"] - hedef
            s.append(f"- Uzunluk: {en_iyi['kelime']} kelime, hedef {hedef}; "
                     + (f"yaklaşık {fark} kelime kısaltın." if fark > 0 else f"yaklaşık {-fark} kelime genişletin (sahne ekleyerek, dolgu yapmadan)."))
    h = en_iyi.get("hakem")
    if h:
        s += ["", "## Hakem değerlendirmesi", ""]
        s += [f"- {k}: {tk.tr_ondalik(v, 0)}/10 — {OLCUTLER[k]}" for k, v in sorted(h["olcutler"].items(), key=lambda x: x[1])[:3]]
        acik = [m for m in h["plan_maddeleri"] if m["durum"] != "tamam"]
        if acik:
            s += ["", "### Gerçekleşmemiş ya da doğrulanması gereken plan maddeleri", ""]
            s += [f"- [{m['durum']}] {m.get('madde', '')}" + (f" — {m['kanit']}" if m.get("kanit") else "") for m in acik]
        if h.get("zayif"):
            s += ["", "### Zayıf yönler", ""] + [f"- {x}" for x in h["zayif"][:6]]
        if h.get("oneriler"):
            s += ["", "### Öneriler", ""] + [f"- {x}" for x in h["oneriler"][:6]]
        if h.get("guclu"):
            s += ["", "### Korunacak güçlü yönler", ""] + [f"- {x}" for x in h["guclu"][:5]]
    if en_iyi["yz_bulgulari"]:
        s += ["", "## Düzeltilecek kalıplar (satır: alıntı → öneri)", ""]
        s += [f"- {b['satir']}: “{b['alinti']}” → {b['oneri']}" for b in en_iyi["yz_bulgulari"][:12]]
    if en_iyi["uyarilar"]:
        s += ["", "## Anlatım ölçümleri", ""] + [f"- {u}" for u in en_iyi["uyarilar"][:8]]
    if en_iyi.get("ses_sapmalari"):
        s += ["", "## Ses izinden sapmalar", ""] + [f"- {u}" for u in en_iyi["ses_sapmalari"]]
    if en_iyi["bitmemis_isaret"]:
        s += ["", f"- {en_iyi['bitmemis_isaret']} bitmemiş metin işaretini ([TK] vb.) doldurun."]
    return "\n".join(s) + "\n"


def kabul(proje: Path, bolum: int, tur: int) -> dict[str, Any]:
    liste = turlar(proje, bolum)
    kayit = next((t for t in liste if t.get("tur") == tur), None)
    if kayit is None:
        raise DonguHatasi(f"{bolum}. bölümde {tur}. tur yok")
    kaynak = _klasor(proje, bolum) / kayit["dosya"]
    if not kaynak.is_file() or hashlib.sha256(kaynak.read_bytes()).hexdigest() != kayit["ozet"]:
        raise DonguHatasi(f"tur dosyası eksik ya da değiştirilmiş: {kaynak}")
    mevcut = [b for b in kitap_proje.bolumler(proje) if b.no == bolum]
    hedef = mevcut[0].yol if mevcut else proje / "metin" / f"bolum-{bolum:03d}.md"
    goruntu = anlik_goruntu.anlik_al(proje, f"{bolum}. bölüm, {tur}. tur kabulü öncesi", degismediyse_atla=True)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(kaynak, hedef)
    return {"hedef": hedef.as_posix(), "tur": tur, "anlik_goruntu": goruntu["kimlik"] if goruntu else None}


def durum_metni(proje: Path, bolum: int) -> str:
    liste = turlar(proje, bolum)
    if not liste:
        return f"{bolum}. bölüm için henüz tur yok."
    s = [f"{bolum}. bölüm döngüsü:", " Tur  Mekanik  Hakem  Toplam  Kelime  Karar"]
    for t in liste:
        hakem = tk.tr_ondalik(t["hakem"]["hakem"], 2) if t.get("hakem") else "  —  "
        s.append(f" {t['tur']:>3}  {tk.tr_ondalik(t['mekanik'], 2):>7}  {hakem:>5}  {tk.tr_ondalik(t['toplam'], 2):>6}  "
                 f"{t['kelime']:>6}  {t.get('karar', '')}")
    en_iyi = max(liste, key=lambda t: (t["toplam"], -t["tur"]))
    s.append(f"En iyi tur: {en_iyi['tur']}. Kabul için: revizyon_dongusu.py kabul --proje ... --bolum {bolum} "
             f"--tur {en_iyi['tur']} --yazar-onayladi")
    return "\n".join(s)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="Yaz → eleştir → düzelt döngüsü: puanlama, tur kaydı ve yazar onayı.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_o = alt.add_parser("olc", help="bir taslağın mekanik puanını ölç")
    p_o.add_argument("--dosya", type=Path, required=True, help="taslak dosyası")
    p_o.add_argument("--proje", type=Path, help="kitap klasörü (plan hedefi, listeler ve ses izi için)")
    p_o.add_argument("--bolum", type=int, help="bölüm numarası (plan hedefi için)")
    p_o.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_r = alt.add_parser("rubrik", help="hakem yönergesini ve JSON şablonunu yazdır")
    p_k = alt.add_parser("kaydet", help="bir taslağı yeni tur olarak kaydet ve karar ver")
    p_k.add_argument("--dosya", type=Path, required=True, help="taslak dosyası")
    p_k.add_argument("--hakem", type=Path, help="hakem değerlendirmesi (rubrik biçiminde JSON)")
    p_k.add_argument("--not", dest="not_", default="", help="bu tur için kısa not")
    p_k.add_argument("--hedef", type=float, default=8.0, help="durma puanı (varsayılan 8)")
    p_k.add_argument("--en-fazla-tur", type=int, default=4, help="en fazla tur sayısı (varsayılan 4)")
    p_k.add_argument("--json", action="store_true", help="tur kaydını JSON olarak yaz")
    p_b = alt.add_parser("brief", help="sonraki tur için revizyon talimatı üret")
    p_d = alt.add_parser("durum", help="turları ve kararları göster")
    p_d.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_a = alt.add_parser("kabul", help="seçilen turu bölüm dosyasına yaz (yazar onayı gerekir)")
    p_a.add_argument("--tur", type=int, required=True, help="kabul edilecek tur")
    p_a.add_argument("--yazar-onayladi", action="store_true", help="yazar bu turu okudu ve onayladı")
    for p in (p_r, p_k, p_b, p_d, p_a):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
        p.add_argument("--bolum", type=int, required=True, help="bölüm numarası")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "olc":
            if arg.bolum is not None and arg.proje is None:
                raise DonguHatasi("--bolum yalnızca --proje ile kullanılır")
            if arg.proje:
                kitap_proje.proje_klasoru(arg.proje)
            sonuc = mekanik_olc(dosya_oku.metin_oku(arg.dosya), arg.proje, arg.bolum)
            if arg.json:
                print(json.dumps(sonuc, ensure_ascii=False, indent=2))
            else:
                print(f"Mekanik puan: {tk.tr_ondalik(sonuc['mekanik'], 2)}/10 ({sonuc['kelime']} kelime)")
                for k, v in sonuc["puanlar"].items():
                    print(f"  {k:<13} {tk.tr_ondalik(v, 1):>5}")
                if sonuc["bitmemis_isaret"]:
                    print(f"  ! {sonuc['bitmemis_isaret']} bitmemiş metin işareti var (kapı)")
        elif arg.komut == "rubrik":
            kitap_proje.proje_klasoru(arg.proje)
            print(rubrik_metni(arg.proje, arg.bolum))
        elif arg.komut == "kaydet":
            k = kaydet(arg.proje, arg.bolum, arg.dosya, arg.hakem, arg.not_, arg.hedef, arg.en_fazla_tur)
            if arg.json:
                print(json.dumps(k, ensure_ascii=False, indent=2))
                return 0
            hakem = f", hakem {tk.tr_ondalik(k['hakem']['hakem'], 2)}" if k["hakem"] else " (hakemsiz)"
            print(f"{k['tur']}. tur kaydedildi: toplam {tk.tr_ondalik(k['toplam'], 2)} "
                  f"(mekanik {tk.tr_ondalik(k['mekanik'], 2)}{hakem}). En iyi tur: {k['en_iyi_tur']}. Karar: {k['karar']}")
            if k["acik_plan_maddesi"]:
                print(f"  ! {k['acik_plan_maddesi']} plan maddesi tamamlanmadı ya da doğrulanmalı")
        elif arg.komut == "brief":
            print(brief(arg.proje, arg.bolum), end="")
        elif arg.komut == "durum":
            if arg.json:
                print(json.dumps(turlar(arg.proje, arg.bolum), ensure_ascii=False, indent=2))
            else:
                print(durum_metni(arg.proje, arg.bolum))
        else:
            if not arg.yazar_onayladi:
                raise DonguHatasi("bölüm dosyasına yazmak için yazarın onayı gerekir: --yazar-onayladi "
                                  "(önce 'durum' ve tur dosyasını yazara gösterin)")
            s = kabul(arg.proje, arg.bolum, arg.tur)
            print(f"{s['tur']}. tur {s['hedef']} dosyasına yazıldı."
                  + (f" Önceki hâl {s['anlik_goruntu']} anlık görüntüsünde." if s["anlik_goruntu"] else ""))
    except (DonguHatasi, kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi, anlik_goruntu.AnlikHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
