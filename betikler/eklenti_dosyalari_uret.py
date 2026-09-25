#!/usr/bin/env python3
"""Bütün eklenti/pazar yeri bildirimlerini ve ZCode eklenti varlıklarını tek kaynaktan üretir.

Kullanım::

    python betikler/eklenti_dosyalari_uret.py            # yaz
    python betikler/eklenti_dosyalari_uret.py --denetle  # güncel değilse çıkış kodu 1

Üretilenler: plugin.json (Agent Plugins 1.0.0 + extensions.com.openai), .codex-plugin/plugin.json
(eski Codex sürümleri için uyumluluk), .claude-plugin/plugin.json ve marketplace.json (Claude Code;
Codex de okur), .agents/plugins/marketplace.json (Codex depo pazar yeri), marketplace.json ve
.zcode-plugin/plugin.json (ZCode), reasonix-plugin.json, ZCode komutları ve eklenti kancaları.
Sürüm, ad ve açıklamalar yalnızca bu dosyada değiştirilir.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "paylasilan" / "betikler"))
try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

KOK = Path(__file__).resolve().parent.parent
BECERI_SAYISI = len(list((KOK / "skills").glob("*/SKILL.md")))
SURUM = "1.1.0"
AD = "ai-hikaye-roman-olusturma"
GORUNEN_AD = "AI Hikaye & Roman Oluşturma"
DEPO = "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma"
YAZAR = {"name": "Cuma Bozkurt", "url": "https://github.com/cumabozkurt"}
KISA = "Türkçe roman ve öykü yazımı için yapay zekâ becerileri: pazar taraması, çözümleme, yazım, süreklilik takibi, TDK denetimi, yapay zekâ tadı giderme, Wattpad ve yayınevi hazırlığı."
UZUN = (f"{BECERI_SAYISI} Türkçe beceri, 7 ajan ve kancalarla fikirden yayına roman ve öykü yazımı: Wattpad ve Türkiye kitap pazarı taraması, "
        "roman/öykü çözümleme, bölüm bölüm yazım, 100+ bölümlük süreklilik takibi, TDK yazım denetimi, yapay zekâ tadı giderme, "
        "kapak, Wattpad yayın takvimi, yayınevi dosyası, EPUB e-kitap, uyarlama sinopsisi ve sesli kitap hazırlığı.")
ANAHTARLAR = ["turkce", "roman-yazimi", "oyku", "wattpad", "yazarlik", "agent-skills", "claude-code", "codex", "opencode", "tdk", "epub"]
KANCA_YOLU = "skills/hikaye-kurulum/varliklar/kancalar/hikaye_kanca.py"
ZCODE_KLASORU = "skills/hikaye-kurulum/varliklar/zcode"


def beceriler() -> list[tuple[str, str]]:
    sonuc = []
    for skill in sorted((KOK / "skills").glob("*/SKILL.md")):
        on = skill.read_text(encoding="utf-8").split("---")[1]
        m = re.search(r'^description:\s*"(.*)"\s*$', on, re.M)
        aciklama = json.loads(f'"{m.group(1)}"') if m else ""
        sonuc.append((skill.parent.name, aciklama))
    return sonuc


def dosyalar() -> dict[str, Any]:
    arayuz = {
        "displayName": GORUNEN_AD,
        "shortDescription": KISA,
        "longDescription": UZUN,
        "developerName": YAZAR["name"],
        "category": "Productivity",
        "capabilities": ["Read", "Write"],
        "websiteURL": DEPO,
        "defaultPrompt": [
            "Polisiye bir roman yazmak istiyorum, nereden başlayalım?",
            "Bu bölümdeki yapay zekâ tadını gider.",
            "Romanımın 1-40. bölümlerinde tutarlılık hatası var mı?",
        ],
        "brandColor": "#B5651D",
    }
    uret: dict[str, Any] = {
        "plugin.json": {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": AD, "version": SURUM, "description": KISA, "author": YAZAR,
            "homepage": DEPO, "repository": DEPO, "license": "MIT", "keywords": ANAHTARLAR,
            "extensions": {"com.openai": {"interface": arayuz}},
        },
        ".codex-plugin/plugin.json": {
            "name": AD, "version": SURUM, "description": KISA, "author": YAZAR, "homepage": DEPO,
            "repository": DEPO, "license": "MIT", "keywords": ANAHTARLAR, "skills": "./skills/", "interface": arayuz,
        },
        ".claude-plugin/plugin.json": {
            "name": AD, "displayName": GORUNEN_AD, "version": SURUM, "description": KISA, "author": YAZAR,
            "homepage": DEPO, "repository": DEPO, "license": "MIT", "keywords": ANAHTARLAR,
        },
        ".claude-plugin/marketplace.json": {
            "name": AD, "owner": YAZAR,
            "metadata": {"description": f"{GORUNEN_AD}: {KISA}", "version": SURUM},
            "plugins": [{"name": AD, "source": "./", "description": KISA, "version": SURUM,
                         "category": "writing", "keywords": ANAHTARLAR, "homepage": DEPO, "license": "MIT"}],
        },
        ".agents/plugins/marketplace.json": {
            "name": AD, "interface": {"displayName": GORUNEN_AD},
            "plugins": [{"name": AD, "source": {"source": "local", "path": "./"},
                         "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Productivity"}],
        },
        "marketplace.json": {
            "name": f"{AD}-zcode", "description": f"{GORUNEN_AD} için ZCode eklenti pazar yeri", "version": 1,
            "plugins": [{"name": AD, "source": "./", "version": SURUM, "description": f"{BECERI_SAYISI} Türkçe yazım becerisi, komutlar ve ZCode yazım kancaları."}],
        },
        ".zcode-plugin/plugin.json": {
            "name": AD, "version": SURUM, "description": KISA, "skills": "skills",
            "commands": f"{ZCODE_KLASORU}/commands", "hooks": f"{ZCODE_KLASORU}/hooks.json",
        },
        "reasonix-plugin.json": {"name": AD, "version": SURUM, "description": KISA, "skills": "skills"},
    }

    def surec(olay: str) -> dict[str, Any]:
        return {"type": "process", "command": "python3",
                "args": [f"${{ZCODE_PLUGIN_ROOT}}/{KANCA_YOLU}", olay, "--ev", "zcode", "--eklenti"], "timeoutMs": 15000}

    uret[f"{ZCODE_KLASORU}/hooks.json"] = {"hooks": {
        "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [surec("oturum-basla")]}],
        "PreToolUse": [{"matcher": "Bash|Write|Edit|ApplyPatch", "hooks": [surec("yazi-oncesi")]}],
        "PostToolUse": [{"matcher": "Write|Edit|ApplyPatch", "hooks": [surec("yazi-sonrasi")]}],
    }}
    for ad, aciklama in beceriler():
        kisa = aciklama.split(" Tetikleyiciler:")[0]
        kisa = (kisa[:157] + "…") if len(kisa) > 160 else kisa
        uret[f"{ZCODE_KLASORU}/commands/{ad}.md"] = (
            f"---\ndescription: {json.dumps(kisa, ensure_ascii=False)}\nskills: {ad}\n---\n\n"
            f"`${ad}` becerisini çağır ve kullanıcının isteğine göre yürüt.\n\nKullanıcının isteği: $ARGUMENTS\n")
    return uret


def metin(deger: Any) -> str:
    return deger if isinstance(deger, str) else json.dumps(deger, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ayr.add_argument("--denetle", action="store_true")
    arg = ayr.parse_args(argv)
    uret = dosyalar()
    farkli = []
    for goreli, deger in uret.items():
        yol = KOK / goreli
        icerik = metin(deger)
        if yol.is_file() and yol.read_text(encoding="utf-8") == icerik:
            continue
        farkli.append(goreli)
        if not arg.denetle:
            yol.parent.mkdir(parents=True, exist_ok=True)
            yol.write_text(icerik, encoding="utf-8", newline="\n")
    komut_klasoru = KOK / ZCODE_KLASORU / "commands"
    fazla = [p for p in komut_klasoru.glob("*.md") if f"{ZCODE_KLASORU}/commands/{p.name}" not in uret] if komut_klasoru.is_dir() else []
    for p in fazla:
        farkli.append(str(p.relative_to(KOK)) + " (fazla)")
        if not arg.denetle:
            p.unlink()
    if arg.denetle:
        if farkli:
            print("Güncel olmayan eklenti dosyaları (python betikler/eklenti_dosyalari_uret.py çalıştırın):")
            print("\n".join(f"  - {f}" for f in farkli))
            return 1
        print("Eklenti dosyaları güncel.")
        return 0
    print(f"{len(farkli)} dosya güncellendi." if farkli else "Güncellenecek dosya yok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
