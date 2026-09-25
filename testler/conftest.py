"""Ortak test yardımcıları: betik çalıştırma, modül yükleme ve örnek projeyi geçici klasöre kopyalama."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

KOK = Path(__file__).resolve().parent.parent
PAYLASILAN = KOK / "paylasilan" / "betikler"
BECERILER = KOK / "skills"
ORNEK_ROMAN = KOK / "ornekler" / "roman" / "saatcinin-kizi"
ORNEK_ISLEMLER = KOK / "ornekler" / "roman" / "islem-ornekleri"
ORNEK_OYKU = KOK / "ornekler" / "oyku" / "son-vapur"
KANCA = BECERILER / "hikaye-kurulum" / "varliklar" / "kancalar" / "hikaye_kanca.py"


def betik_yolu(ad: str) -> Path:
    """Betik adını (ör. ``takip_kaydet.py``) paylaşılan klasörde, yoksa becerilerde, en son depo betiklerinde bulur."""
    aday = PAYLASILAN / ad
    if aday.is_file():
        return aday
    bulunan = sorted(BECERILER.glob(f"*/betikler/{ad}")) or sorted((KOK / "betikler").glob(ad))
    if not bulunan:
        raise FileNotFoundError(ad)
    return bulunan[0]


def calistir(ad: str | Path, *arg: Any, girdi: str | None = None, cwd: Path | None = None,
             ortam: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    yol = ad if isinstance(ad, Path) else betik_yolu(ad)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", **(ortam or {})}
    for gereksiz in ("CLAUDE_PROJECT_DIR", "CODEX_PROJECT_DIR", "ZCODE_PROJECT_DIR", "HIKAYE_PROJE_KOKU"):
        if not ortam or gereksiz not in ortam:
            env.pop(gereksiz, None)
    return subprocess.run([sys.executable, str(yol), *map(str, arg)], input=girdi, capture_output=True,
                          text=True, encoding="utf-8", cwd=cwd, env=env, timeout=120)


def json_cikti(sonuc: subprocess.CompletedProcess[str]) -> Any:
    try:
        return json.loads(sonuc.stdout)
    except ValueError as hata:  # pragma: no cover - teşhis için
        raise AssertionError(f"JSON değil:\nSTDOUT={sonuc.stdout}\nSTDERR={sonuc.stderr}") from hata


def modul_yukle(ad: str) -> ModuleType:
    yol = betik_yolu(ad)
    if str(yol.parent) not in sys.path:
        sys.path.insert(0, str(yol.parent))
    spec = importlib.util.spec_from_file_location(yol.stem, yol)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    sys.modules[yol.stem] = modul
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture()
def roman(tmp_path: Path) -> Path:
    """Örnek romanı (Saatçinin Kızı) kurulu bir çalışma alanına kopyalar; kitap yolunu döndürür."""
    alan = tmp_path / "alan"
    kitap = alan / "saatcinin-kizi"
    shutil.copytree(ORNEK_ROMAN, kitap)
    (alan / ".hikaye-kurulu").write_text('{"surum": "1.0.0"}\n', encoding="utf-8")
    return kitap


@pytest.fixture()
def oyku(tmp_path: Path) -> Path:
    hedef = tmp_path / "oyku" / "son-vapur"
    shutil.copytree(ORNEK_OYKU, hedef)
    return hedef
