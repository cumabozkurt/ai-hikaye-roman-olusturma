#!/usr/bin/env python3
"""Roman çözümleme çalışmasının durum yöneticisi.

Kullanım::

    cozumleme_calismasi.py plan   --kok cozumleme-kutuphanesi/kitap
    cozumleme_calismasi.py kaydet --kok … --girdi grup-4-6.json --aralik-ozeti SHA
    cozumleme_calismasi.py durum  --kok …
    cozumleme_calismasi.py asama  --kok … --asama 3

İlke: kaynak metin bir kez, ardışık bölüm grupları hâlinde okunur; sonraki aşamalar
diske yazılmış özetleri kullanır ve metni yeniden okumaz. ``plan`` yalnızca okur;
``kaydet`` grubu ``bolum_dizini.GRUP_SEMASI`` ile doğrulayıp önce önbelleğe, sonra
bölüm özetlerine, en son ``_ilerleme.json`` dosyasına yazar. Var olan özetlerin
üzerine yazılmaz (yeniden çözümlemek için özeti silin).

Çıkış: 0 tamam, 1 doğrulama hatası, 2 hatalı girdi.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bolum_dizini as bd  # noqa: E402

try:  # argparse iletilerini ve hata iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
    from turkce_argparse import hata_iletisi
except ImportError:  # pragma: no cover
    hata_iletisi = str

EN_COK_GRUP_KELIME = 12000
ASAMALAR = {
    "0": ("Bölüm dizini", ["bolum-dizini.csv"]),
    "1": ("İlk üç bölüm derin çözümleme", ["bolumler/ilk-uc-bolum.md", "hizli-bakis.md"]),
    "2": ("Bölüm özetleri", []),
    "3": ("Olay örgüsü ve tempo", ["olay-orgusu/hikaye-hatti.md", "olay-orgusu/tempo.md", "olay-orgusu/duygu-mekanizmalari.md"]),
    "4": ("Karakterler, dünya, ilişkiler", ["karakterler/iliskiler.md"]),
    "5": ("Çözümleme raporu", ["cozumleme-raporu.md", "ozet.md"]),
    "6": ("Üslup profili", ["uslup.md"]),
}


class CalismaHatasi(ValueError):
    pass


def ilerleme_yolu(kok: Path) -> Path:
    return kok / "_ilerleme.json"


def ilerleme_oku(kok: Path) -> dict[str, Any]:
    yol = ilerleme_yolu(kok)
    if not yol.is_file():
        return {"sema_surumu": 1, "asamalar": {}, "gruplar": {}}
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except ValueError as hata:
        raise CalismaHatasi(f"_ilerleme.json bozuk: {hata}") from hata
    veri.setdefault("asamalar", {})
    veri.setdefault("gruplar", {})
    return veri


def ilerleme_yaz(kok: Path, veri: dict[str, Any]) -> None:
    bd.atomik_yaz(ilerleme_yolu(kok), (json.dumps(veri, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def dizin(kok: Path) -> list[dict[str, str]]:
    yol = kok / "bolum-dizini.csv"
    if not yol.is_file():
        raise CalismaHatasi("bolum-dizini.csv yok; önce bolum_dizini.py çalıştırın")
    return [s for s in bd.dizin_oku(yol) if s["tur"] == "bolum"]


def ozet_yolu(kok: Path, n: int) -> Path:
    return kok / "bolumler" / f"bolum-{n:03d}_ozet.md"


def aralik_ozeti(satirlar: list[dict[str, str]], ilk: int, son: int) -> str:
    parca = "".join(s["bolum_sha256"] for s in satirlar if ilk <= int(s["bolum"]) <= son)
    return hashlib.sha256(f"{ilk}-{son}:{parca}".encode()).hexdigest()


def plan(kok: Path) -> dict[str, Any]:
    satirlar = dizin(kok)
    eksik = [int(s["bolum"]) for s in satirlar if int(s["bolum"]) > 3 and not ozet_yolu(kok, int(s["bolum"])).is_file()]
    kelime = {int(s["bolum"]): int(s["kelime"]) for s in satirlar}
    gruplar: list[dict[str, Any]] = []
    mevcut: list[int] = []
    for n in eksik:
        ardisik = not mevcut or n == mevcut[-1] + 1
        sigar = sum(kelime[m] for m in mevcut) + kelime[n] <= EN_COK_GRUP_KELIME
        if mevcut and (not ardisik or len(mevcut) >= bd.EN_COK_GRUP or not sigar):
            gruplar.append(mevcut)
            mevcut = []
        mevcut.append(n)
    if mevcut:
        gruplar.append(mevcut)
    return {
        "ilk_uc_bolum_hazir": (kok / "bolumler" / "ilk-uc-bolum.md").is_file(),
        "gruplar": [{"kimlik": f"GRUP-{g[0]}-{g[-1]}", "ilk": g[0], "son": g[-1],
                     "kelime": sum(kelime[m] for m in g),
                     "satirlar": [f"{s['baslangic_satiri']}-{s['bitis_satiri']}" for s in satirlar if g[0] <= int(s["bolum"]) <= g[-1]],
                     "aralik_ozeti": aralik_ozeti(satirlar, g[0], g[-1])} for g in gruplar],
    }


def ozet_metni(b: dict[str, Any]) -> str:
    satir = [f"# Bölüm {b['bolum']} Özeti", "", b["ozet"].strip(), "", "## Olay noktaları", ""]
    satir += [f"{i}. {x}" for i, x in enumerate(b.get("olay_noktalari", []), start=1)]
    duygu = b.get("duygu") or {}
    kanca = b.get("kanca") or {}
    satir += ["", "## Duygu ve kanca", "", f"- Gerilim: {duygu.get('gerilim')}/10 · {duygu.get('baskin_duygu', '')}",
              f"- Açılış: {kanca.get('acilis', '')}", f"- Kapanış: {kanca.get('kapanis', '')}"]
    if b.get("karakter_degisimleri"):
        satir += ["", "## Karakter değişimleri", ""] + [f"- {d.get('karakter')}: {d.get('degisim')}" for d in b["karakter_degisimleri"]]
    if b.get("ipuclari"):
        satir += ["", "## İpuçları", ""] + [f"- ({i.get('islem')}) {i.get('ipucu')}" for i in b["ipuclari"]]
    return "\n".join(satir) + "\n"


def kaydet(kok: Path, girdi: Path, beklenen_ozet: str | None) -> dict[str, Any]:
    try:
        veri = json.loads(girdi.read_text(encoding="utf-8"))
    except (OSError, ValueError) as hata:
        raise CalismaHatasi(f"girdi okunamadı: {hata_iletisi(hata)}") from hata
    sorunlar = bd.grup_dogrula(veri)
    if sorunlar:
        return {"tamam": False, "sorunlar": sorunlar}
    ilk, son = veri["grup"]["ilk"], veri["grup"]["son"]
    satirlar = dizin(kok)
    gercek = aralik_ozeti(satirlar, ilk, son)
    if beklenen_ozet and beklenen_ozet != gercek:
        return {"tamam": False, "sorunlar": ["kaynak metin plan alındıktan sonra değişmiş (aralık özeti uyuşmuyor); planı yeniden alın"]}
    onbellek = kok / "_onbellek" / f"grup-{ilk}-{son}.json"
    bd.atomik_yaz(onbellek, (json.dumps(veri, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    yazilan, atlanan = [], []
    for b in veri["bolumler"]:
        yol = ozet_yolu(kok, b["bolum"])
        if yol.is_file():
            atlanan.append(str(yol.relative_to(kok)))
            continue
        bd.atomik_yaz(yol, ozet_metni(b).encode("utf-8"))
        yazilan.append(str(yol.relative_to(kok)))
    ilerleme = ilerleme_oku(kok)
    ilerleme["gruplar"][f"GRUP-{ilk}-{son}"] = {"aralik_ozeti": gercek, "durum": "tamam"}
    ilerleme_yaz(kok, ilerleme)
    return {"tamam": True, "onbellek": str(onbellek.relative_to(kok)), "yazilan": yazilan, "atlanan": atlanan}


def asama_isaretle(kok: Path, asama: str) -> dict[str, Any]:
    ad, gerekenler = ASAMALAR[asama]
    eksik = [g for g in gerekenler if not (kok / g).is_file()]
    if asama == "2":
        satirlar = dizin(kok)
        eksik += [str(ozet_yolu(kok, int(s["bolum"])).relative_to(kok)) for s in satirlar
                  if int(s["bolum"]) > 3 and not ozet_yolu(kok, int(s["bolum"])).is_file()]
    if asama == "4":
        karakter_var = any(p.name != "iliskiler.md" for p in (kok / "karakterler").glob("*.md"))
        dunya_var = any((kok / "dunya").glob("*.md"))
        if not (karakter_var and dunya_var):
            eksik.append("karakterler/*.md ve dunya/*.md (en az birer dosya)")
    if eksik:
        return {"tamam": False, "asama": asama, "ad": ad, "eksik": eksik}
    ilerleme = ilerleme_oku(kok)
    ilerleme["asamalar"][asama] = {"ad": ad, "durum": "tamam"}
    ilerleme_yaz(kok, ilerleme)
    return {"tamam": True, "asama": asama, "ad": ad}


def durum(kok: Path) -> dict[str, Any]:
    ilerleme = ilerleme_oku(kok)
    try:
        p = plan(kok)
        bekleyen = [g["kimlik"] for g in p["gruplar"]]
    except CalismaHatasi:
        bekleyen = ["bolum-dizini.csv yok"]
    asamalar = {k: ("tamam" if k in ilerleme["asamalar"] else "bekliyor") for k in ASAMALAR}
    tamam = all(v == "tamam" for v in asamalar.values())
    return {"asamalar": asamalar, "bekleyen_gruplar": bekleyen, "son_durum": "tamamlandı" if tamam else "sürüyor"}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ayr.add_subparsers(dest="komut", required=True)
    for ad in ("plan", "kaydet", "durum", "asama"):
        p = alt.add_parser(ad)
        p.add_argument("--kok", required=True, type=Path)
        if ad == "kaydet":
            p.add_argument("--girdi", required=True, type=Path)
            p.add_argument("--aralik-ozeti")
        if ad == "asama":
            p.add_argument("--asama", required=True, choices=list(ASAMALAR))
    arg = ayr.parse_args(argv)
    if not arg.kok.is_dir():
        print(json.dumps({"tamam": False, "hata": f"klasör yok: {arg.kok}"}, ensure_ascii=False))
        return 2
    try:
        if arg.komut == "plan":
            sonuc = plan(arg.kok)
        elif arg.komut == "kaydet":
            sonuc = kaydet(arg.kok, arg.girdi, arg.aralik_ozeti)
        elif arg.komut == "asama":
            sonuc = asama_isaretle(arg.kok, arg.asama)
        else:
            sonuc = durum(arg.kok)
    except CalismaHatasi as hata:
        print(json.dumps({"tamam": False, "hata": str(hata)}, ensure_ascii=False))
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 1 if sonuc.get("tamam") is False else 0


if __name__ == "__main__":
    sys.exit(main())
