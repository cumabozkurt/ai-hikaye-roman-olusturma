#!/usr/bin/env python3
"""Depo için statik denetim: beceri biçimi, bağlantılar, eşitlik, sürüm tutarlılığı.

Kullanım::

    python betikler/statik_denetim.py [--json]

Denetimler (Agent Skills belirtimi, Claude Code ve Codex belgelerine göre):
  * Her ``skills/<ad>/SKILL.md``: YAML ön bilgisi; ``name`` klasör adıyla aynı, küçük harf-rakam-tire,
    en çok 64 karakter; ``description`` boş değil, en çok 500 karakter (Codex önerisi; belirtim sınırı 1024);
    yalnızca izinli alanlar; ``metadata`` dize→dize eşlemi ve ``surum`` eklenti sürümüyle aynı;
    SKILL.md 500 satırdan kısa.
  * SKILL.md içinde anılan ``kaynaklar/…``, ``betikler/…``, ``varliklar/…`` yolları var.
  * Bütün Markdown dosyalarındaki göreli bağlantılar çözülüyor.
  * Ajan dosyalarında ``name`` (dosya adıyla aynı), ``description`` ve ``tools`` var.
  * Bütün JSON dosyaları ayrıştırılıyor; bütün Python dosyaları derleniyor.
  * Paylaşılan kopyalar eşit (``paylasilanlari_esitle.py --denetle``) ve bildirimler güncel
    (``eklenti_dosyalari_uret.py --denetle``).
  * Sürüm tek: üretici, kur.py, SKILL.md metadata ve CHANGELOG ilk sürüm başlığı.
  * ``.agents/skills`` → ``../skills`` sembolik bağlantısı.
Çıkış: 0 temiz, 1 hata var.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paylasilan" / "betikler"))
try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KOK = Path(__file__).resolve().parent.parent
ATLANAN = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}
IZINLI_ALANLAR = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
AD_DESENI = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
YOL_DESENI = re.compile(r"`((?:kaynaklar|betikler|varliklar)/[^`\s]+)`")
BAGLANTI = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def dosyalar(desen: str) -> list[Path]:
    """Deseni kök altında arar; ``.agents/skills`` bağlantısı üzerinden gelen kopyaları atlar."""
    adaylar = KOK.glob(desen) if "/" in desen else KOK.rglob(desen)
    return sorted(p for p in adaylar
                  if not (set(p.relative_to(KOK).parts) & ATLANAN) and not p.relative_to(KOK).as_posix().startswith(".agents/skills/"))


def on_bilgi(metin: str) -> dict[str, str] | None:
    if not metin.startswith("---\n") or "\n---\n" not in metin[4:]:
        return None
    govde = metin[4:metin.index("\n---\n", 4)]
    alanlar: dict[str, str] = {}
    for satir in govde.splitlines():
        if satir and not satir.startswith((" ", "\t", "#")) and ":" in satir:
            a, d = satir.split(":", 1)
            alanlar[a.strip()] = d.strip()
    return alanlar


def yaml_dizesi(deger: str) -> str:
    if deger.startswith('"'):
        return json.loads(deger)
    return deger


def surum_bul() -> str:
    m = re.search(r'^SURUM = "([^"]+)"', (KOK / "betikler" / "eklenti_dosyalari_uret.py").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


def beceri_denetle(hatalar: list[str], surum: str) -> None:
    for skill in dosyalar("skills/*/SKILL.md"):
        klasor = skill.parent
        goreli = skill.relative_to(KOK).as_posix()
        metin = skill.read_text(encoding="utf-8")
        alanlar = on_bilgi(metin)
        if alanlar is None:
            hatalar.append(f"{goreli}: YAML ön bilgisi yok")
            continue
        ad = alanlar.get("name", "")
        if ad != klasor.name:
            hatalar.append(f"{goreli}: name ({ad!r}) klasör adıyla ({klasor.name!r}) aynı olmalı")
        if not AD_DESENI.match(ad) or len(ad) > 64:
            hatalar.append(f"{goreli}: name küçük harf, rakam ve tireden oluşmalı, en çok 64 karakter")
        fazla = set(alanlar) - IZINLI_ALANLAR
        if fazla:
            hatalar.append(f"{goreli}: izinsiz ön bilgi alanları: {', '.join(sorted(fazla))}")
        try:
            aciklama = yaml_dizesi(alanlar.get("description", ""))
        except ValueError:
            hatalar.append(f"{goreli}: description geçerli bir çift tırnaklı dize değil")
            aciklama = ""
        if not aciklama.strip():
            hatalar.append(f"{goreli}: description boş")
        elif len(aciklama) > 500:
            hatalar.append(f"{goreli}: description {len(aciklama)} karakter (en çok 500)")
        try:
            meta = json.loads(alanlar.get("metadata", "{}"))
            if not isinstance(meta, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in meta.items()):
                raise ValueError
            if meta.get("surum") != surum:
                hatalar.append(f"{goreli}: metadata.surum {meta.get('surum')!r}, eklenti sürümü {surum!r}")
        except ValueError:
            hatalar.append(f"{goreli}: metadata dize→dize eşlemi olmalı")
        satir_sayisi = metin.count("\n") + 1
        if satir_sayisi >= 500:
            hatalar.append(f"{goreli}: {satir_sayisi} satır (500'den kısa olmalı; ayrıntıyı kaynaklar/ altına taşıyın)")
        for yol in YOL_DESENI.findall(metin):
            if any(c in yol for c in "<>*{}…") or "NNN" in yol:
                continue
            if not (klasor / yol.rstrip("/")).exists():
                hatalar.append(f"{goreli}: anılan yol yok: {yol}")


def ajan_denetle(hatalar: list[str]) -> None:
    for ajan in dosyalar("skills/hikaye-kurulum/varliklar/ajanlar/*.md"):
        alanlar = on_bilgi(ajan.read_text(encoding="utf-8")) or {}
        goreli = ajan.relative_to(KOK).as_posix()
        if alanlar.get("name") != ajan.stem:
            hatalar.append(f"{goreli}: name dosya adıyla aynı olmalı")
        for alan in ("description", "tools"):
            if not alanlar.get(alan):
                hatalar.append(f"{goreli}: {alan} alanı yok")


def baglanti_denetle(hatalar: list[str]) -> None:
    for md in dosyalar("*.md"):
        metin = md.read_text(encoding="utf-8")
        metin = re.sub(r"```.*?```", "", metin, flags=re.S)
        metin = re.sub(r"`[^`\n]*`", "", metin)
        for hedef in BAGLANTI.findall(metin):
            if re.match(r"^[a-z]+:", hedef) or hedef.startswith("#"):
                continue
            yol = hedef.split("#", 1)[0]
            if yol and not (md.parent / yol).exists():
                hatalar.append(f"{md.relative_to(KOK).as_posix()}: kırık bağlantı: {hedef}")


def bicim_denetle(hatalar: list[str]) -> None:
    for js in dosyalar("*.json"):
        try:
            json.loads(js.read_text(encoding="utf-8"))
        except ValueError as hata:
            hatalar.append(f"{js.relative_to(KOK).as_posix()}: geçersiz JSON: {hata}")
    for py in dosyalar("*.py"):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")
        except SyntaxError as hata:
            hatalar.append(f"{py.relative_to(KOK).as_posix()}: sözdizimi hatası: {hata}")


def surum_denetle(hatalar: list[str], surum: str) -> None:
    kur = (KOK / "skills" / "hikaye-kurulum" / "betikler" / "kur.py").read_text(encoding="utf-8")
    m = re.search(r'^SURUM = "([^"]+)"', kur, re.M)
    if not m or m.group(1) != surum:
        hatalar.append(f"kur.py SURUM {m.group(1) if m else None!r}, eklenti sürümü {surum!r}")
    degisiklik = KOK / "CHANGELOG.md"
    if degisiklik.is_file():
        m = re.search(r"^## \[?(\d+\.\d+\.\d+)", degisiklik.read_text(encoding="utf-8"), re.M)
        if not m or m.group(1) != surum:
            hatalar.append(f"CHANGELOG.md ilk sürüm başlığı {m.group(1) if m else None!r}, eklenti sürümü {surum!r}")
    else:
        hatalar.append("CHANGELOG.md yok")


def yardimci_denetle(hatalar: list[str]) -> None:
    for betik in ("paylasilanlari_esitle.py", "eklenti_dosyalari_uret.py"):
        sonuc = subprocess.run([sys.executable, str(KOK / "betikler" / betik), "--denetle"], capture_output=True, text=True, encoding="utf-8")
        if sonuc.returncode != 0:
            hatalar.append(f"{betik} --denetle başarısız: {(sonuc.stdout + sonuc.stderr).strip()[:500]}")
    bag = KOK / ".agents" / "skills"
    # Windows'ta core.symlinks kapalıysa git bağlantıyı hedef yolunu içeren düz dosya olarak açar.
    duz_dosya = bag.is_file() and bag.read_text(encoding="utf-8").strip() == "../skills"
    if not duz_dosya and (not bag.is_symlink() or Path(os.readlink(bag)).as_posix() != "../skills"):
        hatalar.append(".agents/skills, ../skills klasörüne göreli sembolik bağlantı olmalı")


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    hatalar: list[str] = []
    surum = surum_bul()
    beceri_denetle(hatalar, surum)
    ajan_denetle(hatalar)
    baglanti_denetle(hatalar)
    bicim_denetle(hatalar)
    surum_denetle(hatalar, surum)
    yardimci_denetle(hatalar)
    if arg.json:
        print(json.dumps({"tamam": not hatalar, "hatalar": hatalar}, ensure_ascii=False, indent=2))
    else:
        for h in hatalar:
            print("✗ " + h)
        print(f"Statik denetim: {len(hatalar)} hata ({len(dosyalar('skills/*/SKILL.md'))} beceri).")
    return 0 if not hatalar else 1


if __name__ == "__main__":
    sys.exit(main())
