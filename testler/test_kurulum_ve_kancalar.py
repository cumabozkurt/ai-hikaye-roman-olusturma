"""kur.py (bütün ev sahipleri, idempotentlik, kullanıcı dosyalarının korunması) ve kanca girdi/çıktısı."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import BECERILER, KANCA, ORNEK_ROMAN, calistir, json_cikti

KUR = BECERILER / "hikaye-kurulum" / "betikler" / "kur.py"
EVLER = ["claude", "codex", "opencode", "antigravity", "zcode", "openclaw", "reasonix", "genel"]


def _kur(proje: Path, *arg: str) -> dict:
    sonuc = calistir(KUR, "--proje", proje, *arg)
    veri = json_cikti(sonuc)
    assert sonuc.returncode == 0 and veri["tamam"], sonuc.stdout
    return veri


def _anlik(proje: Path) -> dict[str, bytes]:
    return {p.relative_to(proje).as_posix(): p.read_bytes() for p in sorted(proje.rglob("*"))
            if p.is_file() and ".hikaye-kurulu" not in p.name}


@pytest.mark.parametrize("ev", EVLER)
def test_her_ev_sahibi_icin_kurulum_idempotent(tmp_path: Path, ev: str) -> None:
    proje = tmp_path / "proje"
    proje.mkdir()
    ilk = _kur(proje, "--ev", ev, "--opencode-surum", "2")
    assert ilk["eylem_sayisi"] > 0
    once = _anlik(proje)
    ikinci = _kur(proje, "--ev", ev, "--opencode-surum", "2")
    assert ikinci["eylem_sayisi"] == 0, ikinci["eylemler"]
    assert _anlik(proje) == once
    denetim = json_cikti(calistir(KUR, "--proje", proje, "--denetle"))
    assert denetim["tamam"], denetim
    assert (proje / ".hikaye" / "kancalar" / "hikaye_kanca.py").is_file()


def test_kuru_calisma_hicbir_sey_yazmaz(tmp_path: Path) -> None:
    veri = _kur(tmp_path, "--ev", "hepsi", "--kuru", "--opencode-surum", "2")
    assert veri["kuru"] and veri["eylem_sayisi"] > 0
    assert list(tmp_path.iterdir()) == []


def test_kullanici_dosyalari_korunur(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# Benim kurallarım\n\nKısa yaz.\n", encoding="utf-8")
    ayar = tmp_path / ".claude" / "settings.local.json"
    ayar.parent.mkdir()
    ayar.write_text(json.dumps({"permissions": {"allow": ["Read"]},
                                "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "benim.sh"}]}]}}),
                    encoding="utf-8")
    (tmp_path / ".claude" / "agents").mkdir()
    (tmp_path / ".claude" / "agents" / "benim-ajanim.md").write_text("---\nname: benim-ajanim\n---\n", encoding="utf-8")
    _kur(tmp_path, "--ev", "claude")
    _kur(tmp_path, "--ev", "claude")
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.startswith("# Benim kurallarım") and claude.count("<!-- ai-hikaye:basla -->") == 1
    veri = json.loads(ayar.read_text(encoding="utf-8"))
    assert veri["permissions"] == {"allow": ["Read"]}
    komutlar = json.dumps(veri["hooks"]["PreToolUse"])
    assert "benim.sh" in komutlar and komutlar.count("hikaye_kanca.py") == 1
    assert (tmp_path / ".claude" / "agents" / "benim-ajanim.md").is_file()
    assert (tmp_path / ".claude" / "agents" / "anlati-yazari.md").is_file()


def test_bozuk_json_ayar_uzerine_yazilmaz(tmp_path: Path) -> None:
    ayar = tmp_path / ".codex" / "hooks.json"
    ayar.parent.mkdir()
    ayar.write_text("{bozuk", encoding="utf-8")
    sonuc = calistir(KUR, "--proje", tmp_path, "--ev", "codex")
    assert sonuc.returncode == 1 and "geçerli JSON değil" in sonuc.stdout
    assert ayar.read_text(encoding="utf-8") == "{bozuk"


def test_bilinmeyen_ev_sahibi_reddedilir(tmp_path: Path) -> None:
    assert calistir(KUR, "--proje", tmp_path, "--ev", "vscode").returncode == 2


def test_sembolik_baglanti_uzerinden_yazilmaz(tmp_path: Path) -> None:
    proje = tmp_path / "proje"
    (proje / ".zcode").mkdir(parents=True)
    dis = tmp_path / "dis"
    dis.mkdir()
    try:
        (proje / ".zcode" / "skills").symlink_to(dis, target_is_directory=True)
    except OSError:
        pytest.skip("bu sistemde sembolik bağlantı oluşturulamıyor")
    sonuc = calistir(KUR, "--proje", proje, "--ev", "zcode")
    assert sonuc.returncode == 1
    assert list(dis.iterdir()) == []


def test_codex_ajanlari_gecerli_toml(tmp_path: Path) -> None:
    import tomllib

    _kur(tmp_path, "--ev", "codex")
    for toml in (tmp_path / ".codex" / "agents").glob("*.toml"):
        veri = tomllib.loads(toml.read_text(encoding="utf-8"))
        assert veri["name"] == toml.stem and veri["developer_instructions"].strip()
        assert veri["sandbox_mode"] in {"read-only", "workspace-write"}
    kancalar = json.loads((tmp_path / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    assert {"SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "SessionEnd"} <= set(kancalar)
    assert all("commandWindows" in h for g in kancalar["PreToolUse"] for h in g["hooks"])
    assert kancalar["SessionStart"][0]["hooks"][0]["additionalContextLimit"] >= 3000
    assert kancalar["SessionEnd"][0]["hooks"][0]["timeout"] <= 3


def test_opencode_surum1_ve_surum2(tmp_path: Path) -> None:
    for surum in ("1", "2"):
        proje = tmp_path / surum
        proje.mkdir()
        _kur(proje, "--ev", "opencode", "--opencode-surum", surum)
        eklenti = (proje / ".opencode" / "plugins" / "ai-hikaye.ts").read_text(encoding="utf-8")
        ajan = (proje / ".opencode" / "agents" / "anlati-yazari.md").read_text(encoding="utf-8")
        if surum == "1":
            assert "tools:" in ajan and "permissions:" not in ajan
        else:
            assert "permissions:" in ajan
        assert "hikaye_kanca.py" in eklenti


# ------------------------------------------------------------------ kancalar

@pytest.fixture()
def kurulu(tmp_path: Path) -> Path:
    proje = tmp_path / "yazim"
    proje.mkdir()
    _kur(proje, "--ev", "claude,codex,zcode,antigravity")
    shutil.copytree(ORNEK_ROMAN, proje / "saatcinin-kizi")
    return proje


def _kanca(proje: Path, olay: str, ev: str, girdi: dict, *ek: str) -> str:
    sonuc = calistir(proje / ".hikaye" / "kancalar" / "hikaye_kanca.py", olay, "--ev", ev, *ek,
                     girdi=json.dumps(girdi, ensure_ascii=False))
    assert sonuc.returncode == 0, sonuc.stderr
    return sonuc.stdout


def test_oturum_basla_baglam_verir(kurulu: Path) -> None:
    cikti = json.loads(_kanca(kurulu, "oturum-basla", "claude", {"source": "startup", "cwd": str(kurulu)}))
    baglam = cikti["hookSpecificOutput"]["additionalContext"]
    assert cikti["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "saatcinin-kizi" in baglam or "Saatçinin" in baglam
    assert len(baglam) <= 10000


@pytest.mark.parametrize(("ev", "anahtar"), [("claude", "permissionDecision"), ("codex", "permissionDecision"),
                                             ("antigravity", "decision"), ("opencode", "engelle")])
def test_plansiz_bolum_yazimi_engellenir(kurulu: Path, ev: str, anahtar: str) -> None:
    hedef = kurulu / "saatcinin-kizi" / "metin" / "bolum-009_erken.md"
    girdi = ({"toolCall": {"args": {"TargetFile": str(hedef)}}} if ev == "antigravity"
             else {"tool_name": "Write", "tool_input": {"file_path": str(hedef), "content": "x"}, "cwd": str(kurulu)})
    cikti = json.loads(_kanca(kurulu, "yazi-oncesi", ev, girdi))
    metin = json.dumps(cikti, ensure_ascii=False)
    assert anahtar in metin and ("deny" in metin or cikti.get("engelle") is True)
    assert "plan" in metin.lower()


def test_planli_siradaki_bolume_izin_verilir(kurulu: Path) -> None:
    hedef = kurulu / "saatcinin-kizi" / "metin" / "bolum-003_zarf.md"
    cikti = _kanca(kurulu, "yazi-oncesi", "claude", {"tool_name": "Write", "tool_input": {"file_path": str(hedef)}})
    assert "deny" not in cikti


def test_kabuk_yonlendirmesi_de_yakalanir(kurulu: Path) -> None:
    komut = "cat > saatcinin-kizi/metin/bolum-010_x.md <<'SON'\nmetin\nSON"
    cikti = _kanca(kurulu, "yazi-oncesi", "claude", {"tool_name": "Bash", "tool_input": {"command": komut, "cwd": str(kurulu)}})
    assert "deny" in cikti


def test_yazi_sonrasi_bozulmayi_bildirir(kurulu: Path) -> None:
    hedef = kurulu / "saatcinin-kizi" / "metin" / "bolum-003_zarf.md"
    satir = "Defne zarfı açtı ve içinden eski bir fotoğraf çıktı, sararmış kenarlarıyla."
    hedef.write_text("# Bölüm 3\n\n" + "\n\n".join([satir] * 8) + "\n\nBir yapay zekâ olarak", encoding="utf-8")
    cikti = json.loads(_kanca(kurulu, "yazi-sonrasi", "claude", {"tool_name": "Write", "tool_input": {"file_path": str(hedef)}}))
    assert cikti["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert cikti["hookSpecificOutput"]["additionalContext"].strip()


def test_kurulu_olmayan_projede_sessiz(tmp_path: Path) -> None:
    sonuc = calistir(KANCA, "yazi-oncesi", "--ev", "claude", girdi=json.dumps({"cwd": str(tmp_path)}),
                     ortam={"HIKAYE_PROJE_KOKU": str(tmp_path)})
    assert sonuc.returncode == 0 and sonuc.stdout == ""
    sonuc = calistir(KANCA, "yazi-oncesi", "--ev", "antigravity", girdi="bozuk json", ortam={"HIKAYE_PROJE_KOKU": str(tmp_path)})
    assert json.loads(sonuc.stdout) == {"decision": "allow"}


def test_zcode_eklenti_kancasi_proje_kancasi_varken_susar(kurulu: Path) -> None:
    hedef = kurulu / "saatcinin-kizi" / "metin" / "bolum-009_erken.md"
    girdi = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(hedef)}})
    ortam = {"HIKAYE_PROJE_KOKU": str(kurulu)}
    sessiz = calistir(KANCA, "yazi-oncesi", "--ev", "zcode", "--eklenti", girdi=girdi, ortam=ortam)
    assert sessiz.stdout == ""
    (kurulu / ".zcode" / "config.json").unlink()
    etkin = calistir(KANCA, "yazi-oncesi", "--ev", "zcode", "--eklenti", girdi=girdi, ortam=ortam)
    assert "deny" in etkin.stdout


def test_sikistirma_ve_oturum_sonu_dosyalari(kurulu: Path) -> None:
    _kanca(kurulu, "sikistirma-oncesi", "claude", {"trigger": "auto"})
    assert (kurulu / ".hikaye" / "devir-notu.md").is_file()
    _kanca(kurulu, "oturum-sonu", "claude", {})
    assert "son kayıt: 2" in (kurulu / ".hikaye" / "oturum-gunlugu.md").read_text(encoding="utf-8")
    cikti = json.loads(_kanca(kurulu, "oturum-basla", "codex", {"source": "compact"}))
    assert cikti["hookSpecificOutput"]["additionalContext"]


def test_antigravity_dur_bekleyen_bulguda_bir_kez_devam_ettirir(kurulu: Path) -> None:
    hedef = kurulu / "saatcinin-kizi" / "metin" / "bolum-003_zarf.md"
    hedef.write_text("# Bölüm 3\n\nBir yapay zekâ olarak bu sahneyi yazamam.\n", encoding="utf-8")
    ortak = {"conversationId": "k1", "workspacePaths": [str(kurulu)]}
    _kanca(kurulu, "yazi-sonrasi", "antigravity", {**ortak, "toolCall": {"args": {"TargetFile": str(hedef)}}})
    ilk = json.loads(_kanca(kurulu, "dur", "antigravity", {**ortak, "fullyIdle": True}))
    ikinci = json.loads(_kanca(kurulu, "dur", "antigravity", {**ortak, "fullyIdle": True}))
    assert ilk["decision"] == "continue" and ikinci["decision"] == "stop"
