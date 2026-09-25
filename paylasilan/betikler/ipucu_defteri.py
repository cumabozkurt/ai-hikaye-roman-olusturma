#!/usr/bin/env python3
"""İpucu defteri: ekilen ipuçlarının (foreshadowing) ne zaman ekildiğini, en son nerede anıldığını
ve ne zaman ödeneceğini tek tabloda gösterir; unutulan ve yığılan ipuçlarını uyarır.

Kullanım::

    ipucu_defteri.py rapor --proje KITAP [--unutma 8] [--toplam-bolum N] [--json]
    ipucu_defteri.py serit --proje KITAP

Veri kaynağı ``takip/_takip-durumu.json`` içindeki ``ipuclari`` kaydıdır (takip_kaydet.py
yazar). "Son anılma", ipucu özetindeki anlamlı sözcüklerin (5 harflik Türkçe gövde) aynı
paragrafta birlikte geçtiği son bölümdür; kesin değil, yazara hatırlatma amaçlıdır.

Uyarılar:

* ``suresi-gecti``: planlanan çözüm bölümü yazılan son bölümden önce, ipucu hâlâ açık.
* ``unutuldu``: açık ve ``--unutma`` bölümdür metinde anılmıyor (önemi yüksekse hata sayılır).
* ``plan-disi``: planlanan çözüm, kitabın planlanan bölüm sayısından sonra.
* ``yigilma``: aynı bölüme 3'ten fazla çözüm planlanmış.
* ``cozumsuz``: önemi yüksek ve çözüm bölümü planlanmamış.

Çıkış kodu: 0 hata yok, 1 hata düzeyinde bulgu var, 2 kullanım ya da dosya hatası.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bilgi_ara  # noqa: E402
import dosya_oku  # noqa: E402
import kitap_proje  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

YIGILMA_ESIGI = 3


GENEL_SOZCUKLER = {"bütün", "tüm", "hiçbi", "herke", "kadar", "sonra", "önce", "daha", "olan", "oldu", "olmuş", "şimdi",
                   "yine", "hâlâ", "artık", "bölüm", "gerçe"}


def anahtar_govdeler(ozet: str) -> set[str]:
    return {t for t in bilgi_ara.terimlere_ayir(ozet) if len(t) >= 4 and not t.isdigit() and t not in GENEL_SOZCUKLER}


def _eslesir(anahtar: str, terimler: set[str]) -> bool:
    """5 harflik gövde, kısa kökleri kaçırır ("saatler"→"saatl", "saat"→"saat"); 4+ harflik ortak önek yeter."""
    if anahtar in terimler:
        return True
    return any(len(t) >= 4 and (anahtar.startswith(t) or t.startswith(anahtar)) for t in terimler)


def son_anilma(govdeler: set[str], bolumler: list[kitap_proje.Bolum]) -> int | None:
    if not govdeler:
        return None
    gerekli = 1 if len(govdeler) == 1 else 2
    for b in reversed(bolumler):
        for paragraf in re.split(r"\n\s*\n", b.govde):
            terimler = set(bilgi_ara.terimlere_ayir(paragraf))
            if sum(1 for g in govdeler if _eslesir(g, terimler)) >= gerekli:
                return b.no
    return None


def planlanan_bolum_sayisi(proje: Path) -> int | None:
    genel = proje / "plan" / "genel-plan.md"
    if not genel.is_file():
        return None
    metin = dosya_oku.metin_oku(genel, uyar=False)
    m = re.search(r"^[ \t]*[-*][ \t]+\**(?:Bölüm sayısı|Toplam bölüm|Planlanan bölüm)\**[ \t]*:[ \t]*\**[ \t]*(\d{1,4})", metin, re.M | re.I)
    if m:
        return int(m.group(1))
    araliklar = [int(b) for _, b in re.findall(r"\((\d+)\s*[–-]\s*(\d+)\)", metin)]
    return max(araliklar) if araliklar else None


def rapor(proje: Path, unutma: int = 8, toplam_bolum: int | None = None) -> dict[str, Any]:
    kitap_proje.proje_klasoru(proje)
    durum = kitap_proje.takip_durumu(proje)
    ham = durum.get("ipuclari", {})
    ipuclari = [dict(v) for v in (ham.values() if isinstance(ham, dict) else ham if isinstance(ham, list) else [])
                if isinstance(v, dict)]
    ipuclari.sort(key=lambda i: str(i.get("id", "")))
    bolumler = kitap_proje.bolumler(proje)
    son_yazilan = max([b.no for b in bolumler] + [durum.get("son_kaydedilen_bolum", 0)
                                                  if isinstance(durum.get("son_kaydedilen_bolum"), int) else 0])
    toplam = toplam_bolum or planlanan_bolum_sayisi(proje)
    bulgular: list[dict[str, Any]] = []
    satirlar = []
    for ip in ipuclari:
        kimlik = str(ip.get("id", "?"))
        acik = str(ip.get("durum", "ekili")) in kitap_proje.ACIK_IPUCU_DURUMLARI
        plan = ip.get("planlanan_cozum_bolumu") if isinstance(ip.get("planlanan_cozum_bolumu"), int) else None
        ekildi = ip.get("ekildigi_bolum") if isinstance(ip.get("ekildigi_bolum"), int) else None
        anilma = son_anilma(anahtar_govdeler(str(ip.get("ozet", ""))), bolumler) if acik else None
        satir = {"id": kimlik, "ozet": str(ip.get("ozet", "")), "onem": str(ip.get("onem", "orta")),
                 "durum": str(ip.get("durum", "ekili")), "ekildigi_bolum": ekildi, "planlanan_cozum_bolumu": plan,
                 "son_anilma": anilma, "kalan": (plan - son_yazilan) if (acik and plan) else None}
        satirlar.append(satir)
        if not acik:
            continue
        if plan is not None and plan <= son_yazilan:
            bulgular.append({"duzey": "hata", "kural": "suresi-gecti", "id": kimlik,
                             "mesaj": f"{kimlik} {plan}. bölümde çözülecekti; {son_yazilan}. bölüm yazıldı, hâlâ açık."})
        referans = anilma or ekildi or 0
        if son_yazilan - referans >= unutma:
            yuksek = satir["onem"] == "yüksek"
            bulgular.append({"duzey": "hata" if yuksek else "uyari", "kural": "unutuldu", "id": kimlik,
                             "mesaj": f"{kimlik} ({satir['ozet'][:60]}) {son_yazilan - referans} bölümdür anılmıyor; "
                                      "okur unutmadan bir hatırlatma sahnesi düşünün."})
        if plan is not None and toplam and plan > toplam:
            bulgular.append({"duzey": "uyari", "kural": "plan-disi", "id": kimlik,
                             "mesaj": f"{kimlik} {plan}. bölüme planlanmış ama kitap {toplam} bölüm olarak planlı."})
        if plan is None and satir["onem"] == "yüksek":
            bulgular.append({"duzey": "uyari", "kural": "cozumsuz", "id": kimlik,
                             "mesaj": f"{kimlik} önemi yüksek ama çözüm bölümü planlanmamış."})
    yuk = Counter(s["planlanan_cozum_bolumu"] for s in satirlar
                  if s["planlanan_cozum_bolumu"] and s["durum"] in kitap_proje.ACIK_IPUCU_DURUMLARI)
    for bolum, adet in sorted(yuk.items()):
        if adet > YIGILMA_ESIGI:
            bulgular.append({"duzey": "uyari", "kural": "yigilma", "id": "",
                             "mesaj": f"{bolum}. bölüme {adet} ipucu çözümü yığılmış; bazılarını öne ya da arkaya dağıtın."})
    return {"son_yazilan_bolum": son_yazilan, "planlanan_bolum": toplam, "ipuclari": satirlar, "bulgular": bulgular,
            "ozet": {"toplam": len(satirlar), "acik": sum(1 for s in satirlar if s["durum"] in kitap_proje.ACIK_IPUCU_DURUMLARI),
                     "hata": sum(1 for b in bulgular if b["duzey"] == "hata"),
                     "uyari": sum(1 for b in bulgular if b["duzey"] == "uyari")}}


def rapor_metni(r: dict[str, Any]) -> str:
    o = r["ozet"]
    s = [f"İpucu defteri: {o['toplam']} ipucu, {o['acik']} açık · yazılan son bölüm {r['son_yazilan_bolum']}"
         + (f" / planlanan {r['planlanan_bolum']}" if r["planlanan_bolum"] else ""), ""]
    if not r["ipuclari"]:
        return "\n".join(s + ["Takip kaydında ipucu yok. Bölüm kaydında 'ipuclari' alanıyla ekleyin."])
    s.append(f"{'No':<5} {'Önem':<7} {'Durum':<13} {'Ekildi':>6} {'Son anılma':>10} {'Çözüm':>6} {'Kalan':>6}  Özet")
    for i in r["ipuclari"]:
        tire = lambda v: "—" if v is None else str(v)  # noqa: E731
        s.append(f"{i['id']:<5} {i['onem']:<7} {i['durum']:<13} {tire(i['ekildigi_bolum']):>6} {tire(i['son_anilma']):>10} "
                 f"{tire(i['planlanan_cozum_bolumu']):>6} {tire(i['kalan']):>6}  {i['ozet'][:70]}")
    if r["bulgular"]:
        s += ["", "Bulgular:"] + [f"  [{b['duzey']}] {b['mesaj']}" for b in r["bulgular"]]
    else:
        s += ["", "Sorun yok."]
    return "\n".join(s)


def serit(r: dict[str, Any], genislik: int = 60) -> str:
    """Her ipucu için bölüm ekseninde ekilme (●), son anılma (◆) ve planlanan çözüm (○) şeridi."""
    uclar = [v for i in r["ipuclari"] for v in (i["ekildigi_bolum"], i["planlanan_cozum_bolumu"], i["son_anilma"]) if v]
    son = max(uclar + [r["son_yazilan_bolum"], r["planlanan_bolum"] or 0, 1])
    olcek = min(1.0, genislik / son)
    konum = lambda b: min(genislik - 1, int((b - 1) * olcek))  # noqa: E731
    s = [f"Bölüm ekseni 1–{son}  (● ekildi, ◆ son anılma, ○ planlanan çözüm, │ yazılan son bölüm)"]
    for i in r["ipuclari"]:
        cizgi = [" "] * genislik
        bas, bit = i["ekildigi_bolum"], i["planlanan_cozum_bolumu"]
        if bas:
            for k in range(konum(bas), konum(bit) if bit and bit >= bas else konum(bas) + 1):
                cizgi[k] = "─"
        if r["son_yazilan_bolum"]:
            cizgi[konum(r["son_yazilan_bolum"])] = "│"
        if bit:
            cizgi[konum(bit)] = "○"
        if i["son_anilma"]:
            cizgi[konum(i["son_anilma"])] = "◆"
        if bas:
            cizgi[konum(bas)] = "●"
        s.append(f"{i['id']:<5} {''.join(cizgi)} {i['durum']}")
    return "\n".join(s)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description="İpucu defteri: ekilen ipuçlarını, son anılmalarını ve çözüm planını izler.")
    alt = ayr.add_subparsers(dest="komut", required=True)
    p_r = alt.add_parser("rapor", help="ipucu tablosu ve uyarılar")
    p_r.add_argument("--unutma", type=int, default=8, help="kaç bölüm anılmayan açık ipucu unutulmuş sayılır (varsayılan 8)")
    p_r.add_argument("--toplam-bolum", type=int, help="kitabın planlanan bölüm sayısı (varsayılan: genel plandan)")
    p_r.add_argument("--json", action="store_true", help="çıktıyı JSON olarak yaz")
    p_s = alt.add_parser("serit", help="bölüm ekseninde ipucu şeridi")
    for p in (p_r, p_s):
        p.add_argument("--proje", type=Path, required=True, help="kitap klasörü")
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "rapor":
            if not 1 <= arg.unutma <= 500:
                raise kitap_proje.ProjeHatasi("--unutma 1 ile 500 arasında olmalı")
            if arg.toplam_bolum is not None and not 1 <= arg.toplam_bolum <= 9999:
                raise kitap_proje.ProjeHatasi("--toplam-bolum 1 ile 9999 arasında olmalı")
            r = rapor(arg.proje, arg.unutma, arg.toplam_bolum)
            print(json.dumps(r, ensure_ascii=False, indent=2) if arg.json else rapor_metni(r))
            return 1 if r["ozet"]["hata"] else 0
        print(serit(rapor(arg.proje)))
    except (kitap_proje.ProjeHatasi, dosya_oku.DosyaHatasi) as hata:
        print(f"hata: {hata}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
