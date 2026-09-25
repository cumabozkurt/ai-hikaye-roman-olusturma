#!/usr/bin/env python3
"""Uzaktan hata ayıklama (CDP) açık, ayrı profilli bir Chrome/Chromium/Edge başlatır.

Kullanım::

    cdp_chrome_baslat.py [--port 9222] [--profil ~/.hikaye-cdp-profil] [--tarayici YOL] [--kuru]

Güvenlik: Tarayıcı yalnızca 127.0.0.1 üzerinde dinler ve kişisel profilinizden AYRI bir
profil klasörü kullanır. Bu profilde oturum açtığınız siteler (ör. yayınevi paneli) yalnızca
bu profile aittir. İş bitince tarayıcıyı kapatın.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

ADAYLAR = {
    "Linux": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"],
    "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Chromium.app/Contents/MacOS/Chromium",
               "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
    "Windows": [r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
                r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"],
}


def tarayici_bul(istenen: str | None = None) -> str | None:
    if istenen:
        return istenen if Path(istenen).exists() or shutil.which(istenen) else None
    for aday in ADAYLAR.get(platform.system(), []):
        yol = os.path.expandvars(aday)
        if Path(yol).is_file():
            return yol
        bulunan = shutil.which(yol)
        if bulunan:
            return bulunan
    return None


def cdp_hazir_mi(port: int) -> dict | None:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as y:  # noqa: S310
            return json.loads(y.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def komut_olustur(tarayici: str, port: int, profil: Path) -> list[str]:
    return [tarayici, f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={profil}", "--no-first-run", "--no-default-browser-check", "about:blank"]


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--port", type=int, default=9222)
    ayr.add_argument("--profil", type=Path, default=Path.home() / ".hikaye-cdp-profil")
    ayr.add_argument("--tarayici")
    ayr.add_argument("--kuru", action="store_true", help="başlatmadan komutu göster")
    arg = ayr.parse_args(argv)
    surum = cdp_hazir_mi(arg.port)
    if surum:
        print(json.dumps({"tamam": True, "durum": "zaten_acik", "tarayici": surum.get("Browser"), "port": arg.port}, ensure_ascii=False))
        return 0
    tarayici = tarayici_bul(arg.tarayici)
    if not tarayici:
        print(json.dumps({"tamam": False, "hata": "Chrome, Chromium ya da Edge bulunamadı; --tarayici ile yolu verin"}, ensure_ascii=False))
        return 2
    komut = komut_olustur(tarayici, arg.port, arg.profil.expanduser())
    if arg.kuru:
        print(json.dumps({"tamam": True, "komut": komut}, ensure_ascii=False))
        return 0
    arg.profil.expanduser().mkdir(parents=True, exist_ok=True)
    secenek = {"creationflags": 0x00000008} if platform.system() == "Windows" else {"start_new_session": True}
    subprocess.Popen(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **secenek)  # noqa: S603
    for _ in range(30):
        time.sleep(0.5)
        surum = cdp_hazir_mi(arg.port)
        if surum:
            print(json.dumps({"tamam": True, "durum": "baslatildi", "tarayici": surum.get("Browser"), "port": arg.port,
                              "profil": str(arg.profil.expanduser())}, ensure_ascii=False))
            return 0
    print(json.dumps({"tamam": False, "hata": f"tarayıcı başladı ama {arg.port} portu yanıt vermiyor"}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
