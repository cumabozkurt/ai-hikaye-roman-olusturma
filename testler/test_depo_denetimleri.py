"""Depo bütünlüğü: paylaşılan kopyalar, bildirimler, statik denetim ve Türkçe uyum denetimi."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from conftest import KOK, calistir, modul_yukle

BETIKLER = KOK / "betikler"
AGENT_PLUGINS_ALANLARI = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license",
                          "keywords", "extensions"}


def test_paylasilan_kopyalar_esit() -> None:
    sonuc = calistir(BETIKLER / "paylasilanlari_esitle.py", "--denetle")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr


def test_bildirimler_guncel() -> None:
    sonuc = calistir(BETIKLER / "eklenti_dosyalari_uret.py", "--denetle")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr


def test_statik_denetim_temiz() -> None:
    sonuc = calistir(BETIKLER / "statik_denetim.py")
    assert sonuc.returncode == 0, sonuc.stdout + sonuc.stderr


def test_turkce_uyum_depoda_temiz() -> None:
    sonuc = calistir(BETIKLER / "turkce_uyum_denetle.py")
    assert sonuc.returncode == 0, sonuc.stdout
    assert "CJK: 0" in sonuc.stdout


def test_depoda_hic_cjk_karakteri_yok() -> None:
    desen = re.compile("[\u3000-\u303F\u3400-\u4DBF\u4E00-\u9FFF\uFF00-\uFFEF]")
    bulunan = []
    for p in KOK.rglob("*"):
        if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts and p.suffix not in {".png", ".jpg"}:
            try:
                if desen.search(p.read_text(encoding="utf-8")):
                    bulunan.append(p)
            except UnicodeDecodeError:
                continue
    assert not bulunan, bulunan


@pytest.mark.parametrize(("icerik", "kural"), [
    ("# Başlık\n\nBu metin \u4e2d\u6587 içeriyor.\n", "cjk"),
    ("# Kaynak ve Tesekkur\n\nBu depo icin yazıldı; Turkce degil.\n", "ascii-turkce"),
    ("# Not\n\nHerkez geldi, birşey olmadı.\n", "yazim"),
    ("# Not\n\nThis is the best tool for you.\n", "ingilizce"),
    ("# Not\n\nBozuk \ufffd karakter.\n", "kodlama"),
])
def test_turkce_uyum_hatalari_yakalar(tmp_path: Path, icerik: str, kural: str) -> None:
    dosya = tmp_path / "belge.md"
    dosya.write_text(icerik, encoding="utf-8")
    sonuc = calistir(BETIKLER / "turkce_uyum_denetle.py", "--json", dosya)
    veri = json.loads(sonuc.stdout)
    assert sonuc.returncode == 1 and kural in {b["kural"] for b in veri["bulgular"]}, veri


def test_turkce_uyum_kod_ve_tanimlayicilari_atlar(tmp_path: Path) -> None:
    dosya = tmp_path / "belge.md"
    dosya.write_text("# Kurulum\n\n`yazim-denetle` becerisi ve `turkce_kaliplar.py` modülü; bkz. [öykü](oyku-yaz/SKILL.md).\n\n"
                     "```bash\npython icin.py --degil\n```\n\nwattpad-bolum-planla becerisi çalışır.\n", encoding="utf-8")
    sonuc = calistir(BETIKLER / "turkce_uyum_denetle.py", dosya)
    assert sonuc.returncode == 0, sonuc.stdout


def test_turkce_uyum_python_dosyasinda_cjk(tmp_path: Path) -> None:
    dosya = tmp_path / "betik.py"
    dosya.write_text('ETIKET = "\u7b2c\u4e00\u7ae0"\n', encoding="utf-8")
    assert calistir(BETIKLER / "turkce_uyum_denetle.py", dosya).returncode == 1


def test_eklenti_bildirimleri_belirtime_uygun() -> None:
    kok = json.loads((KOK / "plugin.json").read_text(encoding="utf-8"))
    assert set(kok) <= AGENT_PLUGINS_ALANLARI, set(kok) - AGENT_PLUGINS_ALANLARI
    assert kok["name"] == "ai-hikaye-roman-olusturma"
    assert "com.openai" in kok["extensions"]
    claude = json.loads((KOK / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    pazar = json.loads((KOK / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert claude["name"] == pazar["name"] == pazar["plugins"][0]["name"] == "ai-hikaye-roman-olusturma"
    assert claude["version"] == kok["version"] == pazar["plugins"][0].get("version", kok["version"])
    codex_pazar = json.loads((KOK / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    girdi = codex_pazar["plugins"][0]
    assert girdi["policy"]["installation"] == "AVAILABLE" and girdi["policy"]["authentication"] == "ON_INSTALL"
    assert girdi["category"]
    assert not (KOK / "hooks").exists(), "kök hooks/ klasörü Claude ve Codex tarafından otomatik yüklenir; bilinçli olarak yok"


def test_zcode_eklenti_varliklari() -> None:
    klasor = KOK / "skills" / "hikaye-kurulum" / "varliklar" / "zcode"
    kancalar = json.loads((klasor / "hooks.json").read_text(encoding="utf-8"))
    metin = json.dumps(kancalar)
    assert "${ZCODE_PLUGIN_ROOT}" in metin and "--eklenti" in metin
    beceriler = {p.parent.name for p in (KOK / "skills").glob("*/SKILL.md")}
    komutlar = {p.stem for p in (klasor / "commands").glob("*.md")}
    assert beceriler == komutlar


def test_her_betik_icin_test_var() -> None:
    """Her Python betiğinin adı en az bir test dosyasında geçmeli (kapsam bekçisi)."""
    testler = "\n".join(p.read_text(encoding="utf-8") for p in (KOK / "testler").glob("test_*.py"))
    betikler = {p.name for p in (KOK / "paylasilan" / "betikler").glob("*.py")}
    betikler |= {p.name for p in (KOK / "skills").glob("*/betikler/*.py")}
    betikler |= {p.name for p in (KOK / "betikler").glob("*.py")}
    betikler.add("hikaye_kanca.py")
    kur_disi = {"kur.py", "hikaye_kanca.py"}  # sabit yol değişkenleriyle (KUR, KANCA) çağrılır
    eksik = sorted(b for b in betikler - kur_disi if b not in testler and b.removesuffix(".py") not in testler)
    assert not eksik, eksik


def test_kurulum_betikleri_var() -> None:
    sh = (BETIKLER / "kur.sh").read_text(encoding="utf-8")
    ps = (BETIKLER / "kur.ps1").read_text(encoding="utf-8")
    for yol in (".claude/skills", ".agents/skills", "opencode/skills"):
        assert yol in sh
    for yol in (".claude\\skills", ".agents\\skills", "opencode\\skills"):
        assert yol in ps


def test_kur_sh_gecici_eve_kurar(tmp_path: Path) -> None:
    import shutil
    import subprocess

    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("bash betiği Unix benzeri sistemlerde sınanır")
    sonuc = subprocess.run(["bash", str(BETIKLER / "kur.sh"), "claude"], capture_output=True, text=True,
                           env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}, timeout=60)
    assert sonuc.returncode == 0, sonuc.stderr
    kurulan = {p.name for p in (tmp_path / ".claude" / "skills").iterdir()}
    assert {"roman-yaz", "hikaye-kurulum", "yazim-denetle"} <= kurulan
    assert not list((tmp_path / ".claude" / "skills").rglob("__pycache__"))


def test_on_bilgi_ayristirici_uyumlu() -> None:
    kur = modul_yukle("kur.py")
    for skill in (KOK / "skills").glob("*/SKILL.md"):
        alanlar, govde = kur.on_bilgi(skill.read_text(encoding="utf-8"))
        assert alanlar["name"] == skill.parent.name and govde.strip()


def test_turkce_argparse_iletileri(tmp_path: Path) -> None:
    sonuc = calistir("wattpad_planla.py", "takvim")
    assert sonuc.returncode == 2
    assert "kullanım:" in sonuc.stderr and "hata: şu argümanlar zorunlu" in sonuc.stderr
    assert "usage:" not in sonuc.stderr and "error:" not in sonuc.stderr
    yardim = calistir("hikayectl.py", "--help")
    assert "seçenekler" in yardim.stdout and "show this help" not in yardim.stdout
    secim = calistir("kapak_olustur.py", "istem", "--baslik", "X", "--yazar", "Y", "--tur", "yok")
    assert "geçersiz seçim" in secim.stderr


def test_hata_iletilerinde_ingilizce_yok() -> None:
    """Betiklerin kullanıcıya dönük dizelerinde sık İngilizce hata sözcükleri bulunmamalı."""
    desen = re.compile(r"""(?:print|raise \w+|ekle|sorunlar\.append|hatalar\.append)\([^)]*["'][^"']*\b(?:error|warning|not found|failed|invalid|missing|please)\b""", re.I)
    bulunan = []
    for p in (KOK / "paylasilan" / "betikler").glob("*.py"):
        for no, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if desen.search(satir):
                bulunan.append(f"{p.name}:{no}")
    assert not bulunan, bulunan
