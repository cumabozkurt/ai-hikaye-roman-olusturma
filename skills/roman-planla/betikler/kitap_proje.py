"""Kitap projesi klasörünü okuyan ortak yardımcılar (bölümler, planlar, başlık).

Yeni araçların hepsi bölüm dosyalarını aynı kuralla bulur: ``metin/bolum-NNN_baslik.md``
(NNN 1–4 hane). Aynı numaralı iki bölüm dosyası kullanıcı hatasıdır ve Türkçe iletiyle
bildirilir.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dosya_oku  # noqa: E402
import metin_olcum  # noqa: E402

BOLUM_DOSYASI = re.compile(r"^bolum-(\d{1,4})(?:[_-][^/\\]*)?\.md$", re.I)
PLAN_DOSYASI = re.compile(r"^bolum-plani_(\d{1,4})\.md$", re.I)
BASLIK = re.compile(r"^#\s+(.+?)\s*$", re.M)


class ProjeHatasi(ValueError):
    """Kullanıcıya gösterilecek Türkçe proje hatası."""


@dataclass
class Bolum:
    no: int
    yol: Path
    _metin: str | None = field(default=None, repr=False)

    @property
    def metin(self) -> str:
        if self._metin is None:
            self._metin = metin_olcum.satir_sonlarini_duzelt(dosya_oku.metin_oku(self.yol, uyar=False))
        return self._metin

    @property
    def govde(self) -> str:
        return metin_olcum.gorunur_govde(self.metin)

    @property
    def satir_govdesi(self) -> str:
        """Satır numaraları dosyayla aynı kalacak biçimde ön bilgi, yorum ve başlıkları boşaltır."""
        return satir_koruyan_govde(self.metin)

    @property
    def kelime(self) -> int:
        return metin_olcum.kelime_say(self.metin)

    @property
    def baslik(self) -> str:
        m = BASLIK.search(self.metin)
        if m:
            return m.group(1).strip()
        ad = self.yol.stem.split("_", 1)
        return ad[1].replace("-", " ").capitalize() if len(ad) == 2 else f"{self.no}. Bölüm"


def satir_koruyan_govde(metin: str) -> str:
    bosalt = lambda m: re.sub(r"[^\n]", " ", m.group(0))  # noqa: E731
    metin = metin_olcum.ON_BILGI.sub(bosalt, metin, count=1)
    metin = metin_olcum.HTML_YORUM.sub(bosalt, metin)
    return "\n".join("" if s.lstrip().startswith("#") else s for s in metin.split("\n"))


def proje_klasoru(proje: Path) -> Path:
    if not proje.exists():
        raise ProjeHatasi(f"proje klasörü bulunamadı: {proje}")
    if not proje.is_dir():
        raise ProjeHatasi(f"proje klasörü bekleniyordu, dosya verildi: {proje}")
    return proje


def bolumler(proje: Path, zorunlu: bool = False) -> list[Bolum]:
    """Bölümleri numara sırasıyla döndürür. ``zorunlu`` ise hiç bölüm yokken hata verir."""
    klasor = proje_klasoru(proje) / "metin"
    bulunan: dict[int, Path] = {}
    if klasor.is_dir():
        for yol in sorted(klasor.iterdir()):
            m = BOLUM_DOSYASI.match(yol.name)
            if not m or not yol.is_file():
                continue
            no = int(m.group(1))
            if no in bulunan:
                raise ProjeHatasi(f"{no}. bölüm için iki dosya var: {bulunan[no].name} ve {yol.name}")
            bulunan[no] = yol
    if zorunlu and not bulunan:
        raise ProjeHatasi(f"{klasor} içinde bolum-NNN_*.md biçiminde bölüm dosyası yok")
    return [Bolum(no, yol) for no, yol in sorted(bulunan.items())]


def plan_dosyasi(proje: Path, no: int) -> Path | None:
    klasor = proje / "plan"
    if not klasor.is_dir():
        return None
    for yol in sorted(klasor.iterdir()):
        m = PLAN_DOSYASI.match(yol.name)
        if m and int(m.group(1)) == no and yol.is_file():
            return yol
    return None


def plan_hedefi(proje: Path, no: int) -> int | None:
    """Bölüm planındaki hedef uzunluk; plan ya da satır yoksa None."""
    yol = plan_dosyasi(proje, no)
    if yol is None:
        return None
    try:
        return metin_olcum.plandan_hedef(dosya_oku.metin_oku(yol, uyar=False))
    except (ValueError, dosya_oku.DosyaHatasi):
        return None


def kitap_basligi(proje: Path) -> str:
    plan = proje / "plan" / "genel-plan.md"
    if plan.is_file():
        try:
            m = re.search(r"^#\s+(.+?)\s*(?:[—–-]\s*Genel Plan)?\s*$", dosya_oku.metin_oku(plan, uyar=False), re.M)
        except dosya_oku.DosyaHatasi:
            m = None
        if m:
            return m.group(1).strip()
    return proje.resolve().name.replace("-", " ").title()


ACIK_IPUCU_DURUMLARI = {"ekili", "süresi geçti"}


def takip_durumu(proje: Path) -> dict:
    """``takip/_takip-durumu.json`` içeriği; dosya yoksa ya da bozuksa boş sözlük."""
    yol = proje / "takip" / "_takip-durumu.json"
    if not yol.is_file():
        return {}
    try:
        return dosya_oku.json_nesne_oku(yol)
    except dosya_oku.DosyaHatasi:
        return {}


def acik_ipuclari(proje: Path, durum: dict | None = None) -> list[dict]:
    """Takip kaydındaki açık (ekili ya da süresi geçmiş) ipuçları, numara sırasıyla.

    ``ipuclari`` alanı takip_kaydet.py'de ``{"F001": {...}}`` sözlüğüdür; eski ya da elle
    yazılmış kayıtlar için liste biçimi de kabul edilir.
    """
    durum = takip_durumu(proje) if durum is None else durum
    ham = durum.get("ipuclari", {})
    ogeler = list(ham.values()) if isinstance(ham, dict) else ham if isinstance(ham, list) else []
    acik = [dict(i) for i in ogeler if isinstance(i, dict) and str(i.get("durum", "ekili")) in ACIK_IPUCU_DURUMLARI]
    return sorted(acik, key=lambda i: str(i.get("id", "")))
