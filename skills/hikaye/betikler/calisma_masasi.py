#!/usr/bin/env python3
"""Çalışma masası: yazım projesinin salt okunur yerel paneli.

Kullanım::

    calisma_masasi.py --calisma-alani . [--port 8765] [--json]

Yalnızca 127.0.0.1 adresine bağlanır, dosya yazmaz. ``--json`` paneli açmadan
durum özetini yazdırır (testler ve betik kullanımı için).
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metin_olcum  # noqa: E402

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass

VARLIK = Path(__file__).resolve().parent.parent / "varliklar" / "calisma-masasi.html"
ATLANAN = {".git", "node_modules", ".hikaye", "__pycache__", ".venv", "cozumleme-kutuphanesi"}


def _json(yol: Path) -> dict[str, Any]:
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
        return veri if isinstance(veri, dict) else {}
    except (OSError, ValueError):
        return {}


def kitaplari_bul(kok: Path, derinlik: int = 3) -> list[Path]:
    bulunan: list[Path] = []

    def gez(klasor: Path, kalan: int) -> None:
        if (klasor / "plan" / "genel-plan.md").is_file():
            bulunan.append(klasor)
            return
        if kalan == 0:
            return
        try:
            altlar = sorted(p for p in klasor.iterdir() if p.is_dir() and not p.is_symlink())
        except OSError:
            return
        for alt in altlar:
            if alt.name not in ATLANAN and not alt.name.startswith("."):
                gez(alt, kalan - 1)

    gez(kok, derinlik)
    return bulunan


def kitap_ozeti(kok: Path, kitap: Path) -> dict[str, Any]:
    durum = _json(kitap / "takip" / "_takip-durumu.json")
    bolumler = []
    toplam = 0
    for dosya in sorted((kitap / "metin").glob("bolum-*.md")):
        try:
            sayi = metin_olcum.kelime_say(dosya.read_text(encoding="utf-8"))
        except OSError:
            continue
        toplam += sayi
        bolumler.append({"dosya": dosya.name, "kelime": sayi})
    planlar = sorted(p.name for p in (kitap / "plan").glob("bolum-plani_*.md"))
    ipuclari = [
        {"id": k, "ozet": v.get("ozet", ""), "durum": v.get("durum", "")}
        for k, v in sorted((durum.get("ipuclari") or {}).items())
        if isinstance(v, dict) and v.get("durum") == "ekili"
    ]
    karakterler = []
    for ad, kayit in sorted((durum.get("karakterler") or {}).items()):
        if isinstance(kayit, dict):
            karakterler.append({"ad": ad, "yasam": kayit.get("yasam_durumu", ""), "konum": kayit.get("konum", "")})
    return {
        "ad": durum.get("kitap_adi") or kitap.name,
        "yol": str(kitap.relative_to(kok)) if kitap != kok else ".",
        "son_kaydedilen_bolum": durum.get("son_kaydedilen_bolum", 0),
        "revizyon": durum.get("durum_revizyonu"),
        "bolum_sayisi": len(bolumler),
        "plan_sayisi": len(planlar),
        "toplam_kelime": toplam,
        "bolumler": bolumler,
        "acik_ipuclari": ipuclari,
        "karakterler": karakterler,
    }


def durum_ozeti(kok: Path) -> dict[str, Any]:
    kok = kok.resolve()
    aktif = (kok / ".aktif-kitap").read_text(encoding="utf-8").strip() if (kok / ".aktif-kitap").is_file() else ""
    kurulum = _json(kok / ".hikaye-kurulu")
    kitaplar = [kitap_ozeti(kok, k) for k in kitaplari_bul(kok)]
    for k in kitaplar:
        k["aktif"] = bool(aktif) and k["yol"] == aktif
    oykuler = sorted(p.name for p in (kok / "oyku").glob("*") if p.is_dir()) if (kok / "oyku").is_dir() else []
    return {"calisma_alani": str(kok), "kurulum": kurulum, "aktif_kitap": aktif, "kitaplar": kitaplar, "oykuler": oykuler}


def sayfa(ozet: dict[str, Any]) -> str:
    sablon = VARLIK.read_text(encoding="utf-8") if VARLIK.is_file() else "<pre>{{VERI}}</pre>"
    veri = json.dumps(ozet, ensure_ascii=False).replace("</", "<\\/")
    return sablon.replace("{{BASLIK}}", html.escape(Path(ozet["calisma_alani"]).name)).replace("{{VERI}}", veri)


def sunucu_olustur(kok: Path, port: int) -> ThreadingHTTPServer:
    class Isleyici(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            # DNS yeniden bağlama (rebinding) saldırılarına karşı yalnızca yerel Host başlığı kabul edilir.
            konak = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
            if konak not in {"127.0.0.1", "localhost"}:
                self.send_error(403, "Forbidden", "Yalnızca yerel erişime izin verilir.")
                return
            if self.path in ("/", "/index.html"):
                govde, tur = sayfa(durum_ozeti(kok)).encode("utf-8"), "text/html; charset=utf-8"
            elif self.path == "/api/durum":
                govde, tur = json.dumps(durum_ozeti(kok), ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", tur)
            self.send_header("Content-Length", str(len(govde)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(govde)

        def log_message(self, *args: Any) -> None:
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Isleyici)


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--calisma-alani", type=Path, default=Path.cwd())
    ayr.add_argument("--port", type=int, default=8765)
    ayr.add_argument("--json", action="store_true")
    arg = ayr.parse_args(argv)
    if not arg.calisma_alani.is_dir():
        print(f"Çalışma alanı bulunamadı: {arg.calisma_alani}", file=sys.stderr)
        return 2
    if arg.json:
        print(json.dumps(durum_ozeti(arg.calisma_alani), ensure_ascii=False, indent=2))
        return 0
    try:
        sunucu = sunucu_olustur(arg.calisma_alani, arg.port)
    except OSError as hata:
        print(f"Port {arg.port} açılamadı ({hata}); --port ile başka bir port deneyin.", file=sys.stderr)
        return 2
    print(f"Çalışma masası: http://127.0.0.1:{sunucu.server_address[1]}/  (kapatmak için Ctrl+C)")
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nÇalışma masası kapatıldı.")
    finally:
        sunucu.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
