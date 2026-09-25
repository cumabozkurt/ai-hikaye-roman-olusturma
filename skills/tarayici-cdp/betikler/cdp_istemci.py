#!/usr/bin/env python3
"""Yerel CDP tarayıcısıyla sayfa açma ve metin okuma (yalnızca standart kütüphane).

Kullanım::

    cdp_istemci.py sekmeler                         # açık sekmeler
    cdp_istemci.py ac  --adres https://…            # yeni sekmede aç, sekme kimliğini yaz
    cdp_istemci.py metin --sekme KIMLIK [--bekle 3] [--azami 20000]
    cdp_istemci.py oku --adres https://… [--bekle 3]   # aç + metni al + sekmeyi kapat
    cdp_istemci.py kapat --sekme KIMLIK

Yalnızca 127.0.0.1 adresindeki tarayıcıya bağlanır. Sayfa metni ``document.body.innerText``
ile okunur; form doldurma, tıklama, çerez ya da parola okuma işlemi YOKTUR.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.parse
import urllib.request
from typing import Any

try:  # argparse iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
except ImportError:  # pragma: no cover
    pass


class CdpHatasi(RuntimeError):
    pass


def http_json(port: int, yol: str, yontem: str = "GET") -> Any:
    istek = urllib.request.Request(f"http://127.0.0.1:{port}{yol}", method=yontem)
    try:
        with urllib.request.urlopen(istek, timeout=5) as y:  # noqa: S310 - yalnızca localhost
            govde = y.read().decode("utf-8")
    except OSError as hata:
        raise CdpHatasi(f"127.0.0.1:{port} yanıt vermiyor; önce cdp_chrome_baslat.py çalıştırın ({hata})") from hata
    try:
        return json.loads(govde)
    except ValueError:
        return govde


class WebSoketi:
    """CDP için yeterli, en küçük RFC 6455 istemcisi (metin çerçeveleri, maskeli gönderim)."""

    def __init__(self, adres: str, zaman_asimi: float = 15) -> None:
        u = urllib.parse.urlparse(adres)
        if u.hostname not in ("127.0.0.1", "localhost"):
            raise CdpHatasi("yalnızca yerel tarayıcıya bağlanılır")
        self.soket = socket.create_connection((u.hostname, u.port or 80), timeout=zaman_asimi)
        anahtar = base64.b64encode(os.urandom(16)).decode()
        istek = (f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                 f"Sec-WebSocket-Key: {anahtar}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.soket.sendall(istek.encode())
        yanit = b""
        while b"\r\n\r\n" not in yanit:
            parca = self.soket.recv(4096)
            if not parca:
                raise CdpHatasi("web soketi el sıkışması başarısız")
            yanit += parca
        if b" 101 " not in yanit.split(b"\r\n", 1)[0]:
            raise CdpHatasi("web soketi el sıkışması reddedildi")
        self.tampon = yanit.split(b"\r\n\r\n", 1)[1]
        self.sayac = 0

    def _oku(self, n: int) -> bytes:
        while len(self.tampon) < n:
            parca = self.soket.recv(65536)
            if not parca:
                raise CdpHatasi("bağlantı kapandı")
            self.tampon += parca
        veri, self.tampon = self.tampon[:n], self.tampon[n:]
        return veri

    def gonder(self, metin: str) -> None:
        yuk = metin.encode("utf-8")
        baslik = bytearray([0x81])
        if len(yuk) < 126:
            baslik.append(0x80 | len(yuk))
        elif len(yuk) < 65536:
            baslik += bytes([0x80 | 126]) + struct.pack(">H", len(yuk))
        else:
            baslik += bytes([0x80 | 127]) + struct.pack(">Q", len(yuk))
        maske = os.urandom(4)
        self.soket.sendall(bytes(baslik) + maske + bytes(b ^ maske[i % 4] for i, b in enumerate(yuk)))

    def al(self) -> str:
        parcalar = b""
        while True:
            b1, b2 = self._oku(2)
            uzunluk = b2 & 0x7F
            if uzunluk == 126:
                uzunluk = struct.unpack(">H", self._oku(2))[0]
            elif uzunluk == 127:
                uzunluk = struct.unpack(">Q", self._oku(8))[0]
            maske = self._oku(4) if b2 & 0x80 else None
            yuk = self._oku(uzunluk)
            if maske:
                yuk = bytes(b ^ maske[i % 4] for i, b in enumerate(yuk))
            kod = b1 & 0x0F
            if kod == 0x8:
                raise CdpHatasi("tarayıcı bağlantıyı kapattı")
            if kod in (0x9, 0xA):
                continue
            parcalar += yuk
            if b1 & 0x80:
                return parcalar.decode("utf-8")

    def cagir(self, yontem: str, parametre: dict[str, Any] | None = None) -> dict[str, Any]:
        self.sayac += 1
        kimlik = self.sayac
        self.gonder(json.dumps({"id": kimlik, "method": yontem, "params": parametre or {}}))
        while True:
            mesaj = json.loads(self.al())
            if mesaj.get("id") == kimlik:
                if "error" in mesaj:
                    raise CdpHatasi(f"{yontem}: {mesaj['error'].get('message')}")
                return mesaj.get("result", {})

    def kapat(self) -> None:
        try:
            self.soket.close()
        except OSError:
            pass


def sekmeler(port: int) -> list[dict[str, Any]]:
    return [{"kimlik": s["id"], "baslik": s.get("title", ""), "adres": s.get("url", "")}
            for s in http_json(port, "/json/list") if s.get("type") == "page"]


def ac(port: int, adres: str) -> dict[str, Any]:
    if urllib.parse.urlparse(adres).scheme not in ("http", "https"):
        raise CdpHatasi("yalnızca http/https adresleri açılır")
    s = http_json(port, "/json/new?" + urllib.parse.quote(adres, safe=":/?&=%#"), yontem="PUT")
    return {"kimlik": s["id"], "adres": s.get("url", adres)}


def metin(port: int, sekme: str, bekle: float, azami: int) -> dict[str, Any]:
    hedef = next((s for s in http_json(port, "/json/list") if s.get("id") == sekme), None)
    if not hedef:
        raise CdpHatasi(f"sekme bulunamadı: {sekme}")
    time.sleep(max(0.0, bekle))
    ws = WebSoketi(hedef["webSocketDebuggerUrl"])
    try:
        sonuc = ws.cagir("Runtime.evaluate", {"expression": "JSON.stringify({b: document.title, m: document.body ? document.body.innerText : ''})",
                                               "returnByValue": True})
    finally:
        ws.kapat()
    veri = json.loads(sonuc.get("result", {}).get("value") or "{}")
    govde = veri.get("m", "")
    return {"baslik": veri.get("b", ""), "adres": hedef.get("url"), "uzunluk": len(govde),
            "kesildi": len(govde) > azami, "metin": govde[:azami]}


def kapat(port: int, sekme: str) -> dict[str, Any]:
    http_json(port, f"/json/close/{urllib.parse.quote(sekme)}")
    return {"kapatildi": sekme}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--port", type=int, default=9222)
    alt = ayr.add_subparsers(dest="komut", required=True)
    alt.add_parser("sekmeler")
    for ad in ("ac", "oku"):
        p = alt.add_parser(ad)
        p.add_argument("--adres", required=True)
        if ad == "oku":
            p.add_argument("--bekle", type=float, default=3)
            p.add_argument("--azami", type=int, default=20000)
    p = alt.add_parser("metin")
    p.add_argument("--sekme", required=True)
    p.add_argument("--bekle", type=float, default=0)
    p.add_argument("--azami", type=int, default=20000)
    alt.add_parser("kapat").add_argument("--sekme", required=True)
    arg = ayr.parse_args(argv)
    try:
        if arg.komut == "sekmeler":
            sonuc: Any = sekmeler(arg.port)
        elif arg.komut == "ac":
            sonuc = ac(arg.port, arg.adres)
        elif arg.komut == "metin":
            sonuc = metin(arg.port, arg.sekme, arg.bekle, arg.azami)
        elif arg.komut == "kapat":
            sonuc = kapat(arg.port, arg.sekme)
        else:
            s = ac(arg.port, arg.adres)
            try:
                sonuc = metin(arg.port, s["kimlik"], arg.bekle, arg.azami)
            finally:
                kapat(arg.port, s["kimlik"])
    except (CdpHatasi, KeyError, ValueError, OSError) as hata:
        print(json.dumps({"tamam": False, "hata": str(hata)}, ensure_ascii=False))
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
