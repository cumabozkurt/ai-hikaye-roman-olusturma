#!/usr/bin/env python3
"""hikaye-kurulum: yazım projesine kancaları, ajanları, kuralları ve kaynakları kurar.

Kullanım::

    kur.py --proje . --ev claude,codex            # kur ya da güncelle
    kur.py --proje . --ev hepsi --kuru            # yalnızca ne yapılacağını göster
    kur.py --proje . --denetle                    # kurulumu denetle (hiçbir şey yazmaz)

Ev sahipleri: claude, codex, opencode, antigravity, zcode, openclaw, reasonix, genel (hepsi).

Güvenlik ilkeleri:
  * Kullanıcının dosyaları korunur: CLAUDE.md/AGENTS.md işaretli blokla, JSON ayarlar
    yalnızca bizim kayıtlarımız değiştirilerek birleştirilir; bilinmeyen alanlar kalır.
  * Yalnızca bilinen adlı beceri/ajan dosyaları değiştirilir; kullanıcının diğerleri kalır.
  * Sembolik bağlantı üzerinden yazılmaz; hedef kaynağın içindeyse durulur.
  * Aynı komut iki kez çalıştırıldığında sonuç bayt bayt aynıdır (idempotent).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # argparse iletilerini ve hata iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
    from turkce_argparse import hata_iletisi
except ImportError:  # pragma: no cover
    hata_iletisi = str

SURUM = "1.1.0"
AJAN_SURUMU = 1
BETIKLER = Path(__file__).resolve().parent
BECERI_KOKU = BETIKLER.parent
BECERILER_KLASORU = BECERI_KOKU.parent
VARLIK = BECERI_KOKU / "varliklar"
EV_SAHIPLERI = ("claude", "codex", "opencode", "antigravity", "zcode", "openclaw", "reasonix", "genel")
EV_ADLARI = {
    "claude": "Claude Code", "codex": "OpenAI Codex", "opencode": "OpenCode", "antigravity": "Google Antigravity",
    "zcode": "ZCode", "openclaw": "OpenClaw", "reasonix": "Reasonix", "genel": "genel ajan / web yapay zekâsı",
}
CAGIRMA = {
    "claude": "`/roman-yaz` gibi eğik çizgi komutuyla (eklentiyle kurulduysa `/ai-hikaye-roman-olusturma:roman-yaz`) ya da doğal dille",
    "codex": "`$roman-yaz` ya da `/skills` menüsüyle",
    "opencode": "`/roman-yaz` komutuyla ya da doğal dille (skill aracı)",
    "antigravity": "`/skills` menüsünden seçerek ya da beceri adını doğal dille anarak",
    "zcode": "`$roman-yaz` ya da `/roman-yaz` komutuyla",
    "openclaw": "`/skill roman-yaz` ya da doğal dille",
    "reasonix": "beceri adını doğal dille anarak",
    "genel": "ilgili `skills/<ad>/SKILL.md` dosyasını okuyup adımları izleyerek",
}
KANCA_MODULLERI = ("turkce_kaliplar.py", "ai_kalip_denetle.py", "bozulma_denetle.py", "metin_olcum.py", "turkce_argparse.py", "dosya_oku.py")
BLOK_BASLA = "<!-- ai-hikaye:basla -->"
BLOK_BITIR = "<!-- ai-hikaye:bitir -->"
GITIGNORE_BLOK = ("# ai-hikaye:basla", ".hikaye/calisma/", ".hikaye/devir-notu.md", ".hikaye/oturum-gunlugu.md", "# ai-hikaye:bitir")
KANCA_KIMLIGI = "hikaye_kanca.py"
ANTIGRAVITY_ARACLARI = {
    "Read": ["view_file"], "Glob": ["find_by_name"], "Grep": ["grep_search"], "Write": ["write_to_file"],
    "Edit": ["replace_file_content", "multi_replace_file_content"], "Bash": ["run_command"],
}


class KurulumHatasi(RuntimeError):
    pass


# ------------------------------------------------------------------ dosya işlemleri

class Yazici:
    def __init__(self, proje: Path, kuru: bool) -> None:
        self.proje = proje
        self.kuru = kuru
        self.eylemler: list[str] = []

    def _guvenli(self, hedef: Path) -> None:
        for ata in [hedef, *hedef.parents]:
            if ata == self.proje.parent:
                break
            if ata.is_symlink() and ata != self.proje:
                raise KurulumHatasi(f"sembolik bağlantı üzerinden yazılmaz: {ata}")
        try:
            hedef.resolve().relative_to(self.proje.resolve())
        except ValueError as hata:
            raise KurulumHatasi(f"proje dışına yazılmaz: {hedef}") from hata

    def yaz(self, hedef: Path, icerik: str, calistirilabilir: bool = False) -> None:
        self._guvenli(hedef)
        eski = hedef.read_text(encoding="utf-8") if hedef.is_file() else None
        if eski == icerik:
            return
        self.eylemler.append(("güncelle " if eski is not None else "oluştur ") + hedef.relative_to(self.proje).as_posix())
        if self.kuru:
            return
        hedef.parent.mkdir(parents=True, exist_ok=True)
        fd, gecici = tempfile.mkstemp(dir=hedef.parent, prefix=".kur-", text=True)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(icerik)
        if calistirilabilir:
            os.chmod(gecici, 0o755)
        os.replace(gecici, hedef)

    def kopyala(self, kaynak: Path, hedef: Path) -> None:
        if kaynak.suffix in {".png", ".jpg", ".ico"}:
            self._guvenli(hedef)
            if not hedef.exists() or hedef.read_bytes() != kaynak.read_bytes():
                self.eylemler.append("kopyala " + hedef.relative_to(self.proje).as_posix())
                if not self.kuru:
                    hedef.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(kaynak, hedef)
            return
        self.yaz(hedef, kaynak.read_text(encoding="utf-8"), calistirilabilir=os.access(kaynak, os.X_OK))

    def klasor_esitle(self, kaynak: Path, hedef: Path) -> None:
        """Kaynak klasörü hedefe aynalar (hedefte fazladan olan dosyalar silinir)."""
        if hedef.resolve() == kaynak.resolve():
            return
        try:
            hedef.resolve().relative_to(kaynak.resolve())
            raise KurulumHatasi(f"hedef kaynağın içinde: {hedef}")
        except ValueError:
            pass
        beklenen = set()
        for dosya in sorted(kaynak.rglob("*")):
            if dosya.is_file() and "__pycache__" not in dosya.parts:
                goreli = dosya.relative_to(kaynak)
                beklenen.add(goreli)
                self.kopyala(dosya, hedef / goreli)
        if hedef.is_dir():
            for dosya in sorted(hedef.rglob("*"), reverse=True):
                if dosya.is_file() and dosya.relative_to(hedef) not in beklenen and "__pycache__" not in dosya.parts:
                    self.eylemler.append("sil " + dosya.relative_to(self.proje).as_posix())
                    if not self.kuru:
                        dosya.unlink()


def blok_birlestir(eski: str | None, blok: str) -> str:
    yeni_blok = f"{BLOK_BASLA}\n{blok.rstrip()}\n{BLOK_BITIR}\n"
    if not eski:
        return yeni_blok
    if BLOK_BASLA in eski and BLOK_BITIR in eski:
        bas = eski.index(BLOK_BASLA)
        son = eski.index(BLOK_BITIR) + len(BLOK_BITIR)
        return eski[:bas] + yeni_blok.rstrip("\n") + eski[son:]
    return eski.rstrip("\n") + "\n\n" + yeni_blok


def json_oku(yol: Path) -> dict[str, Any]:
    if not yol.is_file():
        return {}
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except ValueError as hata:
        raise KurulumHatasi(f"{yol} geçerli JSON değil; elle düzeltin ya da yedekleyip silin: {hata_iletisi(hata)}") from hata
    if not isinstance(veri, dict):
        raise KurulumHatasi(f"{yol} bir JSON nesnesi değil")
    return veri


def json_metni(veri: Any) -> str:
    return json.dumps(veri, ensure_ascii=False, indent=2) + "\n"


def bizim_mi(kayit: Any) -> bool:
    return KANCA_KIMLIGI in json.dumps(kayit, ensure_ascii=False)


def kancalari_birlestir(mevcut: dict[str, Any], bizim: dict[str, list[Any]]) -> dict[str, Any]:
    """{"hooks": {Olay: [grup, ...]}} biçimindeki ayarlarda yalnızca bizim grupları değiştirir."""
    sonuc = dict(mevcut)
    kancalar = dict(sonuc.get("hooks") or {})
    for olay in list(kancalar):
        gruplar = [g for g in kancalar[olay] if not bizim_mi(g)]
        if gruplar:
            kancalar[olay] = gruplar
        else:
            kancalar.pop(olay)
    for olay, gruplar in bizim.items():
        kancalar[olay] = list(kancalar.get(olay, [])) + gruplar
    sonuc["hooks"] = kancalar
    return sonuc


# ------------------------------------------------------------------ yardımcılar

def python_komutu() -> str:
    for aday in ("python3", "python"):
        if shutil.which(aday):
            return aday
    return "py -3" if shutil.which("py") else "python3"


PAKET_KIMLIGI = '"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma"'


def beceri_klasorleri() -> list[Path]:
    """Yalnızca bu pakete ait becerileri döndürür.

    ``npx skills`` ya da elle kurulumda becerilerimiz başka becerilerle aynı klasörde durabilir
    (ör. ``~/.agents/skills``); kullanıcının diğer becerileri projeye kopyalanmamalıdır.
    """
    return sorted(p for p in BECERILER_KLASORU.iterdir()
                  if (p / "SKILL.md").is_file() and PAKET_KIMLIGI in (p / "SKILL.md").read_text(encoding="utf-8"))


def on_bilgi(metin: str) -> tuple[dict[str, str], str]:
    if not metin.startswith("---\n"):
        return {}, metin
    son = metin.index("\n---\n", 4)
    alanlar: dict[str, str] = {}
    for satir in metin[4:son].splitlines():
        if ":" in satir and not satir.startswith(" "):
            anahtar, deger = satir.split(":", 1)
            alanlar[anahtar.strip()] = deger.strip()
    return alanlar, metin[son + 5:]


def ajanlar() -> list[tuple[str, dict[str, str], str]]:
    sonuc = []
    for yol in sorted((VARLIK / "ajanlar").glob("*.md")):
        alanlar, govde = on_bilgi(yol.read_text(encoding="utf-8"))
        sonuc.append((yol.stem, alanlar, govde))
    return sonuc


def arac_listesi(deger: str) -> list[str]:
    return [a.strip() for a in deger.strip("[]").split(",") if a.strip()]


def toml_dizesi(metin: str) -> str:
    return '"""\n' + metin.replace("\\", "\\\\").replace('"""', '\\"\\"\\"').rstrip() + '\n"""'


def opencode_surumu(istenen: str) -> int:
    if istenen in {"1", "2"}:
        return int(istenen)
    try:
        cikti = subprocess.run(["opencode", "--version"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"(\d+)\.\d+\.\d+", cikti)
        if m:
            return 1 if int(m.group(1)) < 2 else 2
    except (OSError, subprocess.SubprocessError):
        pass
    return 2


def codex_komutu(olay: str) -> tuple[str, str]:
    sh = ('ROOT="${CODEX_PROJECT_DIR:-$PWD}"; while [ ! -f "$ROOT/.hikaye/kancalar/hikaye_kanca.py" ]; do '
          'P="$(dirname "$ROOT")"; [ "$P" != "$ROOT" ] || exit 0; ROOT="$P"; done; '
          'PY=python3; command -v python3 >/dev/null 2>&1 || PY=python; '
          f'exec "$PY" "$ROOT/.hikaye/kancalar/hikaye_kanca.py" {olay} --ev codex')
    ps = ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$r=$env:CODEX_PROJECT_DIR; if (-not $r) { $r=(Get-Location).Path }; '
          "while ($true) { $k=Join-Path $r '.hikaye\\kancalar\\hikaye_kanca.py'; if (Test-Path -LiteralPath $k -PathType Leaf) { "
          f"$input | python $k {olay} --ev codex; exit $LASTEXITCODE }}; $p=Split-Path -Parent $r; if (-not $p -or $p -eq $r) {{ exit 0 }}; $r=$p }}\"")
    return sh, ps


# ------------------------------------------------------------------ ev sahibi kurulumları

def ortak_kur(y: Yazici, ev_listesi: list[str]) -> None:
    kancalar = y.proje / ".hikaye" / "kancalar"
    y.kopyala(VARLIK / "kancalar" / "hikaye_kanca.py", kancalar / "hikaye_kanca.py")
    for modul in KANCA_MODULLERI:
        y.kopyala(BETIKLER / modul, kancalar / modul)
    y.klasor_esitle(BECERI_KOKU / "kaynaklar", y.proje / ".hikaye" / "kaynaklar")
    gitignore = y.proje / ".gitignore"
    eski = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    if GITIGNORE_BLOK[0] not in eski:
        y.yaz(gitignore, (eski.rstrip("\n") + "\n\n" if eski.strip() else "") + "\n".join(GITIGNORE_BLOK) + "\n")
    isaret = y.proje / ".hikaye-kurulu"
    onceki = json_oku(isaret) if isaret.is_file() else {}
    evler = sorted(set(onceki.get("ev_sahipleri", [])) | set(ev_listesi), key=EV_SAHIPLERI.index)
    bilgi = {"surum": SURUM, "ajan_surumu": AJAN_SURUMU, "ev_sahipleri": evler, "kaynaklar": ".hikaye/kaynaklar",
             "kancalar": ".hikaye/kancalar", "kurulum_zamani": onceki.get("kurulum_zamani") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    y.yaz(isaret, json_metni(bilgi))


def yonlendirme_metni(ev: str) -> str:
    sablon = (VARLIK / "sablonlar" / "yonlendirme.md.sablon").read_text(encoding="utf-8")
    ajan_notu = ("hikaye-mimari, anlati-yazari, tutarlilik-denetcisi, karakter-tasarimcisi, hikaye-arastirmaci, proje-kasifi, bolum-cikarici. "
                 "Ajan kullanılamıyorsa (dosya yok, çalışma zamanı özel ajan desteklemiyor) görevi ana oturumda yürüt ve 'Yedek: tek başına yürütüldü' diye bildir.")
    if ev in {"zcode", "openclaw", "reasonix", "genel"}:
        ajan_notu = "bu ortamda özel ajan kurulmaz; bütün uzman görevleri ana oturumda yürütülür."
    return sablon.replace("{{EV_ADI}}", EV_ADLARI[ev]).replace("{{CAGIRMA}}", CAGIRMA[ev]).replace("{{AJANLAR}}", ajan_notu)


def claude_kur(y: Yazici, py: str) -> None:
    hedef = y.proje / "CLAUDE.md"
    y.yaz(hedef, blok_birlestir(hedef.read_text(encoding="utf-8") if hedef.is_file() else None, yonlendirme_metni("claude")))
    for ad, _, _ in ajanlar():
        y.kopyala(VARLIK / "ajanlar" / f"{ad}.md", y.proje / ".claude" / "agents" / f"{ad}.md")
    y.kopyala(VARLIK / "sablonlar" / "kural-claude.md", y.proje / ".claude" / "rules" / "hikaye-yazim.md")
    komut = lambda olay: f'{py} "$CLAUDE_PROJECT_DIR/.hikaye/kancalar/hikaye_kanca.py" {olay} --ev claude'  # noqa: E731
    grup = lambda olay, zaman=15, eslesme=None: {**({"matcher": eslesme} if eslesme else {}),  # noqa: E731
                                                "hooks": [{"type": "command", "command": komut(olay), "timeout": zaman}]}
    bizim = {
        "SessionStart": [grup("oturum-basla", 10, "startup|resume|clear|compact")],
        "PreToolUse": [grup("yazi-oncesi", 15, "Write|Edit|MultiEdit|Bash")],
        "PostToolUse": [grup("yazi-sonrasi", 20, "Write|Edit|MultiEdit")],
        "PreCompact": [grup("sikistirma-oncesi", 10, "manual|auto")],
        "SessionEnd": [grup("oturum-sonu", 5)],
    }
    ayar = y.proje / ".claude" / "settings.local.json"
    y.yaz(ayar, json_metni(kancalari_birlestir(json_oku(ayar), bizim)))


def codex_kur(y: Yazici) -> None:
    hedef = y.proje / "AGENTS.md"
    y.yaz(hedef, blok_birlestir(hedef.read_text(encoding="utf-8") if hedef.is_file() else None, yonlendirme_metni("codex")))
    for ad, alanlar, govde in ajanlar():
        salt_okunur = "Write" not in arac_listesi(alanlar.get("tools", ""))
        toml = "\n".join([
            f'name = "{ad}"',
            f"description = {json.dumps(alanlar.get('description', ''), ensure_ascii=False)}",
            f'nickname_candidates = ["{ad.replace("-", " ").title()}"]',
            f'sandbox_mode = "{"read-only" if salt_okunur else "workspace-write"}"',
            f"developer_instructions = {toml_dizesi(govde)}",
            "",
        ])
        y.yaz(y.proje / ".codex" / "agents" / f"{ad}.toml", toml)
    def grup(olay: str, eslesme: str | None, zaman: int, mesaj: str | None, baglam_siniri: int | None = None) -> dict[str, Any]:
        sh, ps = codex_komutu(olay)
        kanca: dict[str, Any] = {"type": "command", "command": sh, "commandWindows": ps, "timeout": zaman}
        if mesaj:
            kanca["statusMessage"] = mesaj
        if baglam_siniri:
            # Codex varsayılanı ≈2.500 belirteç; bağlam kartı (en çok 10.000 karakter) diske taşmasın.
            kanca["additionalContextLimit"] = baglam_siniri
        return {**({"matcher": eslesme} if eslesme else {}), "hooks": [kanca]}
    bizim = {
        "SessionStart": [grup("oturum-basla", "startup|resume|clear|compact", 10, "Hikâye bağlamı yükleniyor", 4000)],
        "PreToolUse": [grup("yazi-oncesi", "Bash|apply_patch|Edit|Write", 15, "Bölüm planı denetleniyor")],
        "PostToolUse": [grup("yazi-sonrasi", "apply_patch|Edit|Write", 20, "Bölüm metni denetleniyor", 3000)],
        "PreCompact": [grup("sikistirma-oncesi", "manual|auto", 10, "Devir notu yazılıyor")],
        "SessionEnd": [grup("oturum-sonu", None, 3, None)],  # Codex SessionEnd en çok 3 sn
    }
    ayar = y.proje / ".codex" / "hooks.json"
    y.yaz(ayar, json_metni(kancalari_birlestir(json_oku(ayar), bizim)))


def opencode_kur(y: Yazici, surum: int) -> None:
    hedef = y.proje / "AGENTS.md"
    y.yaz(hedef, blok_birlestir(hedef.read_text(encoding="utf-8") if hedef.is_file() else None, yonlendirme_metni("opencode")))
    for ad, alanlar, govde in ajanlar():
        araclar = arac_listesi(alanlar.get("tools", ""))
        yol = y.proje / ".opencode" / "agents" / f"{ad}.md"
        model = None
        if yol.is_file():
            m = re.search(r"^model:\s*(.+)$", yol.read_text(encoding="utf-8"), re.M)
            model = m.group(1).strip() if m else None
        izinler = ['  - action: "*"', '    resource: "*"', "    effect: deny"]
        eslem = {"Read": "read", "Glob": "glob", "Grep": "grep", "Write": "edit", "Edit": "edit", "Bash": "bash",
                 "WebSearch": "websearch", "WebFetch": "webfetch"}
        for eylem in dict.fromkeys(eslem[a] for a in araclar if a in eslem):
            izinler += [f"  - action: {eylem}", '    resource: "*"', "    effect: allow"]
        on = ["---", f"description: {json.dumps(alanlar.get('description', ''), ensure_ascii=False)}", "mode: subagent",
              *([f"model: {model}"] if model else []), "permissions:", *izinler, "---", ""]
        if surum == 1:  # 1.x "permissions" listesini tanımaz; "tools" ve "permission" kullanır
            araclar_v1 = {"write": "Write" in araclar, "edit": "Edit" in araclar, "bash": "Bash" in araclar}
            on = ["---", f"description: {json.dumps(alanlar.get('description', ''), ensure_ascii=False)}", "mode: subagent",
                  *([f"model: {model}"] if model else []), "tools:", *(f"  {k}: {'true' if v else 'false'}" for k, v in araclar_v1.items()), "---", ""]
        y.yaz(yol, "\n".join(on) + govde.lstrip("\n"))
    eklenti = "ai-hikaye-v1.ts" if surum == 1 else "ai-hikaye-v2.ts"
    y.kopyala(VARLIK / "opencode" / eklenti, y.proje / ".opencode" / "plugins" / "ai-hikaye.ts")
    for beceri in beceri_klasorleri():
        alanlar, _ = on_bilgi((beceri / "SKILL.md").read_text(encoding="utf-8"))
        aciklama = alanlar.get("description", "").strip('"')[:160]
        y.yaz(y.proje / ".opencode" / "commands" / f"{beceri.name}.md",
              f"---\ndescription: {json.dumps(aciklama, ensure_ascii=False)}\n---\n\n"
              f"`{beceri.name}` becerisini yükle ve yönergelerine göre çalış.\n\nKullanıcının isteği: $ARGUMENTS\n")


def becerileri_kopyala(y: Yazici, hedef_klasor: Path) -> None:
    if hedef_klasor.is_symlink():
        raise KurulumHatasi(f"{hedef_klasor} bir sembolik bağlantı; içine kopyalamak bağlantı hedefini değiştirir. "
                            "Bağlantıyı kaldırıp yeniden deneyin ya da bu ev sahibi için kurulumu atlayın.")
    for beceri in beceri_klasorleri():
        y.klasor_esitle(beceri, hedef_klasor / beceri.name)


def antigravity_kur(y: Yazici, py: str) -> None:
    becerileri_kopyala(y, y.proje / ".agents" / "skills")
    for ad, alanlar, govde in ajanlar():
        araclar = [t for a in arac_listesi(alanlar.get("tools", "")) for t in ANTIGRAVITY_ARACLARI.get(a, [])]
        aciklama = alanlar.get("description", "")
        on = ["---", f"name: {ad}", "description: |", f"  {aciklama}", "tools:", *(f"  - {a}" for a in dict.fromkeys(araclar)),
              "mainAgent: false", "subagent: true", "---", ""]
        not_ = (f"\n---\n\nAntigravity notu: bu ajanı `invoke_subagent` ile `TypeName: \"{ad}\"` vererek çağırın. "
                "Çalışma zamanı özel ajan sunmuyorsa görevi ana oturumda yürütün ve bunu bildirin.\n")
        y.yaz(y.proje / ".agents" / "agents" / ad / "agent.md", "\n".join(on) + govde.lstrip("\n").rstrip() + "\n" + not_)
    kural = "---\ntrigger: always_on\n---\n\n" + yonlendirme_metni("antigravity")
    if len(kural) > 12000:
        raise KurulumHatasi("Antigravity kuralı 12.000 karakter sınırını aşıyor")
    y.yaz(y.proje / ".agents" / "rules" / "ai-hikaye.md", kural)
    komut = lambda olay: f"{py} ../.hikaye/kancalar/hikaye_kanca.py {olay} --ev antigravity"  # noqa: E731
    eslesme = "run_command|write_to_file|replace_file_content|multi_replace_file_content"
    grup = {
        "PreToolUse": [{"matcher": eslesme, "hooks": [{"type": "command", "command": komut("yazi-oncesi"), "timeout": 15}]}],
        "PostToolUse": [{"matcher": eslesme, "hooks": [{"type": "command", "command": komut("yazi-sonrasi"), "timeout": 20}]}],
        "PreInvocation": [{"type": "command", "command": komut("cagri-oncesi"), "timeout": 15}],
        "Stop": [{"type": "command", "command": komut("dur"), "timeout": 10}],
    }
    ayar = y.proje / ".agents" / "hooks.json"
    mevcut = json_oku(ayar)
    mevcut["ai-hikaye"] = grup
    y.yaz(ayar, json_metni(mevcut))


def zcode_kur(y: Yazici, py: str) -> None:
    becerileri_kopyala(y, y.proje / ".zcode" / "skills")
    hedef = y.proje / "AGENTS.md"
    y.yaz(hedef, blok_birlestir(hedef.read_text(encoding="utf-8") if hedef.is_file() else None, yonlendirme_metni("zcode")))
    for beceri in beceri_klasorleri():
        alanlar, _ = on_bilgi((beceri / "SKILL.md").read_text(encoding="utf-8"))
        y.yaz(y.proje / ".zcode" / "commands" / f"{beceri.name}.md",
              f"---\ndescription: {json.dumps(alanlar.get('description', '').strip(chr(34))[:160], ensure_ascii=False)}\nskills: {beceri.name}\n---\n\n"
              f"`${beceri.name}` becerisini çağır ve kullanıcının isteğine göre yürüt.\n\nKullanıcının isteği: $ARGUMENTS\n")
    parcalar = py.split()
    def surec(olay: str) -> dict[str, Any]:
        return {"type": "process", "command": parcalar[0],
                "args": [*parcalar[1:], "${ZCODE_PROJECT_DIR}/.hikaye/kancalar/hikaye_kanca.py", olay, "--ev", "zcode"], "timeoutMs": 15000}
    ayar = y.proje / ".zcode" / "config.json"
    mevcut = json_oku(ayar)
    kancalar = dict(mevcut.get("hooks") or {})
    olaylar = dict(kancalar.get("events") or {})
    for olay in list(olaylar):
        kalan = [g for g in olaylar[olay] if not bizim_mi(g)]
        if kalan:
            olaylar[olay] = kalan
        else:
            olaylar.pop(olay)
    for olay, eslesme, ad in (("SessionStart", "startup|resume|clear|compact", "oturum-basla"),
                              ("PreToolUse", "Bash|Write|Edit|ApplyPatch", "yazi-oncesi"),
                              ("PostToolUse", "Write|Edit|ApplyPatch", "yazi-sonrasi")):
        olaylar[olay] = list(olaylar.get(olay, [])) + [{"matcher": eslesme, "hooks": [surec(ad)]}]
    kancalar.update({"enabled": True, "timeoutMs": max(int(kancalar.get("timeoutMs", 0) or 0), 15000), "events": olaylar})
    mevcut["hooks"] = kancalar
    y.yaz(ayar, json_metni(mevcut))


def yalniz_beceri_kur(y: Yazici, ev: str) -> None:
    becerileri_kopyala(y, y.proje / "skills")
    hedef = y.proje / "AGENTS.md"
    y.yaz(hedef, blok_birlestir(hedef.read_text(encoding="utf-8") if hedef.is_file() else None, yonlendirme_metni(ev)))
    if ev == "reasonix":
        baglanti = y.proje / ".agents" / "skills"
        if not baglanti.exists() and not y.kuru:
            try:
                baglanti.parent.mkdir(parents=True, exist_ok=True)
                baglanti.symlink_to(Path("..") / "skills", target_is_directory=True)
                y.eylemler.append("bağlantı .agents/skills -> ../skills")
            except OSError:
                y.eylemler.append("uyarı: .agents/skills bağlantısı kurulamadı (Windows'ta geliştirici modu gerekir); reasonix-plugin.json ile kurun")


# ------------------------------------------------------------------ denetim

def denetle(proje: Path) -> dict[str, Any]:
    sorunlar: list[str] = []
    notlar: list[str] = []
    isaret = proje / ".hikaye-kurulu"
    if not isaret.is_file():
        return {"tamam": False, "sorunlar": ["kurulum yok: .hikaye-kurulu bulunamadı"], "notlar": []}
    bilgi = json_oku(isaret)
    if bilgi.get("ajan_surumu") != AJAN_SURUMU:
        sorunlar.append(f"ajan sürümü farklı (proje {bilgi.get('ajan_surumu')}, paket {AJAN_SURUMU}); yeniden kurun")
    for dosya in ("hikaye_kanca.py", *KANCA_MODULLERI):
        if not (proje / ".hikaye" / "kancalar" / dosya).is_file():
            sorunlar.append(f"eksik kanca dosyası: .hikaye/kancalar/{dosya}")
    evler = bilgi.get("ev_sahipleri", [])
    ajan_adlari = [a for a, _, _ in ajanlar()]
    if "claude" in evler:
        ayar = proje / ".claude" / "settings.local.json"
        if not ayar.is_file() or not bizim_mi(json_oku(ayar).get("hooks", {})):
            sorunlar.append("Claude kancaları .claude/settings.local.json içinde kayıtlı değil")
        sorunlar += [f"eksik Claude ajanı: {a}" for a in ajan_adlari if not (proje / ".claude" / "agents" / f"{a}.md").is_file()]
    if "codex" in evler:
        ayar = proje / ".codex" / "hooks.json"
        if not ayar.is_file() or not bizim_mi(json_oku(ayar)):
            sorunlar.append("Codex kancaları .codex/hooks.json içinde kayıtlı değil")
        sorunlar += [f"eksik Codex ajanı: {a}" for a in ajan_adlari if not (proje / ".codex" / "agents" / f"{a}.toml").is_file()]
        notlar.append("Codex kancaları ilk kullanımda /hooks ile güven onayı ister.")
    if "opencode" in evler and not (proje / ".opencode" / "plugins" / "ai-hikaye.ts").is_file():
        sorunlar.append("OpenCode eklentisi yok: .opencode/plugins/ai-hikaye.ts")
    if "antigravity" in evler and not (proje / ".agents" / "rules" / "ai-hikaye.md").is_file():
        sorunlar.append("Antigravity kuralı yok: .agents/rules/ai-hikaye.md")
    if "zcode" in evler and not bizim_mi(json_oku(proje / ".zcode" / "config.json")):
        sorunlar.append("ZCode kancaları .zcode/config.json içinde kayıtlı değil")
    if not shutil.which("python3") and not shutil.which("python"):
        sorunlar.append("Python 3 bulunamadı; kancalar çalışmaz (Python 3.11+ kurun)")
    elif sys.version_info < (3, 11):
        notlar.append("Python 3.11 ya da üstü önerilir")
    if "opencode" in evler or "antigravity" in evler:
        notlar.append("Kurulumdan sonra yeni bir oturum açın ki beceri, ajan ve kancalar yeniden taransın.")
    return {"tamam": not sorunlar, "ev_sahipleri": evler, "surum": bilgi.get("surum"), "sorunlar": sorunlar, "notlar": notlar}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--proje", type=Path, default=Path.cwd())
    ayr.add_argument("--ev", default="claude", help="virgülle ayrılmış liste ya da 'hepsi'")
    ayr.add_argument("--kuru", action="store_true", help="yazmadan yapılacakları listele")
    ayr.add_argument("--denetle", action="store_true", help="yalnızca kurulumu denetle")
    ayr.add_argument("--opencode-surum", default="otomatik", choices=["otomatik", "1", "2"])
    arg = ayr.parse_args(argv)
    proje = arg.proje.resolve()
    if not proje.is_dir():
        print(json.dumps({"tamam": False, "hata": f"proje klasörü yok: {proje}"}, ensure_ascii=False))
        return 2
    if arg.denetle:
        sonuc = denetle(proje)
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
        return 0 if sonuc["tamam"] else 1
    evler = list(EV_SAHIPLERI) if arg.ev.strip() == "hepsi" else [e.strip() for e in arg.ev.split(",") if e.strip()]
    bilinmeyen = [e for e in evler if e not in EV_SAHIPLERI]
    if bilinmeyen or not evler:
        print(json.dumps({"tamam": False, "hata": f"bilinmeyen ev sahibi: {', '.join(bilinmeyen) or '(boş)'}",
                          "gecerli": list(EV_SAHIPLERI)}, ensure_ascii=False))
        return 2
    y = Yazici(proje, arg.kuru)
    py = python_komutu()
    try:
        ortak_kur(y, evler)
        for ev in evler:
            if ev == "claude":
                claude_kur(y, py)
            elif ev == "codex":
                codex_kur(y)
            elif ev == "opencode":
                opencode_kur(y, opencode_surumu(arg.opencode_surum))
            elif ev == "antigravity":
                antigravity_kur(y, py)
            elif ev == "zcode":
                zcode_kur(y, py)
            else:
                yalniz_beceri_kur(y, ev)
    except KurulumHatasi as hata:
        print(json.dumps({"tamam": False, "hata": str(hata), "yapilanlar": y.eylemler}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"tamam": True, "kuru": arg.kuru, "ev_sahipleri": evler, "eylem_sayisi": len(y.eylemler),
                      "eylemler": y.eylemler,
                      "sonraki_adim": "Yeni bir oturum açın; Codex kullanıyorsanız /hooks ile kancalara güven onayı verin."},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
