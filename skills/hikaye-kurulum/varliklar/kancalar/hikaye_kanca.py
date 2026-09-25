#!/usr/bin/env python3
"""AI Hikaye & Roman Oluşturma — bütün ev sahipleri için tek kanca (hook) çekirdeği.

Kullanım: ``hikaye_kanca.py OLAY --ev claude|codex|zcode|opencode|antigravity``
Girdi JSON olarak stdin'den okunur; çıktı ev sahibinin beklediği biçimde verilir.

Olaylar:
  oturum-basla        bağlam, etkin kitap, eksikler (sıkıştırma sonrası devir notu dahil)
  yazi-oncesi         bölüm planı olmadan ya da önceki bölüm kaydedilmeden metin yazımını engeller
  yazi-sonrasi        yazılan bölümde bozulma / yapay zekâ kalıbı / uzunluk bulgularını bildirir
  kayit-oncesi        git commit öncesi takibe kaydedilmemiş bölümleri uyarır
  sikistirma-oncesi   .hikaye/devir-notu.md dosyasını yazar
  sikistirma-sonrasi  devir notunu bağlama geri verir
  oturum-sonu         .hikaye/oturum-gunlugu.md dosyasına bir satır ekler
  dur                 Codex/Antigravity Stop olayı
  cagri-oncesi        Antigravity PreInvocation (bağlam + bekleyen bulgular)

Kanca yalnızca ``.hikaye-kurulu`` işareti olan projelerde çalışır; başka her yerde
sessizce izin verir. Beklenmeyen bir hata akışı asla kilitlemez (izin verilir).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

BURASI = Path(__file__).resolve().parent
KANCA_ADI = "hikaye_kanca.py"
sys.path.insert(0, str(BURASI))
# Eklenti kökünden (ör. ZCode ${ZCODE_PLUGIN_ROOT}) çalıştırıldığında denetim modülleri becerinin betikler/ klasöründedir.
_BECERI_BETIKLERI = BURASI.parent.parent / "betikler"
if _BECERI_BETIKLERI.is_dir():
    sys.path.append(str(_BECERI_BETIKLERI))

METIN_DESENI = re.compile(r"(?:^|/)metin/bolum-(\d{1,4})[^/]*\.md$")
OYKU_DESENI = re.compile(r"(?:^|/)oyku/([^/]+)/metin\.md$")
ATLAMA_ISARETI = "<!-- denetim:atla -->"
YAMA_HEDEFI = re.compile(r"^\*\*\* (?:Add File|Update File|Move to):\s*(.+?)\s*$", re.M)
YONLENDIRME = re.compile(r"(?:^|[\s;&|])(?:\d?>>?|tee(?:\s+-a)?)\s*[\"']?([^\s\"'|;&<>]+\.md)")
KOPYALA = re.compile(r"(?:^|[\s;&|])(?:cp|mv|Copy-Item|Move-Item|Set-Content|Out-File)\b[^|;&]*?\s[\"']?([^\s\"'|;&<>]+\.md)[\"']?\s*(?:$|[|;&])")
GIT_COMMIT = re.compile(r"(?:^|[\s;&|])git\s+(?:-C\s+\S+\s+)?commit\b")


# ------------------------------------------------------------------ yardımcılar

def girdi_oku() -> dict[str, Any]:
    try:
        ham = sys.stdin.read()
        veri = json.loads(ham) if ham.strip() else {}
        return veri if isinstance(veri, dict) else {}
    except (ValueError, OSError):
        return {}


def yaz(deger: Any) -> None:
    if deger is None:
        return
    sys.stdout.write(json.dumps(deger, ensure_ascii=False) if not isinstance(deger, str) else deger)


def git(kok: Path, *arg: str) -> str:
    try:
        return subprocess.run(["git", *arg], cwd=kok, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def proje_koku(girdi: dict[str, Any]) -> Path:
    for ad in ("HIKAYE_PROJE_KOKU", "CLAUDE_PROJECT_DIR", "CODEX_PROJECT_DIR", "ZCODE_PROJECT_DIR"):
        deger = os.environ.get(ad)
        if deger and Path(deger).is_dir():
            return Path(deger).resolve()
    if BURASI.name == "kancalar" and BURASI.parent.name == ".hikaye":
        return BURASI.parent.parent
    for aday in girdi.get("workspacePaths") or []:
        if isinstance(aday, str) and Path(aday).is_dir():
            return Path(aday).resolve()
    cwd = Path(girdi["cwd"]) if isinstance(girdi.get("cwd"), str) and Path(girdi["cwd"]).is_dir() else Path.cwd()
    ust = git(cwd, "rev-parse", "--show-toplevel")
    return Path(ust).resolve() if ust else cwd.resolve()


def kitaplar(kok: Path) -> list[Path]:
    sonuc = []
    for aday in [kok, *sorted(p for p in kok.iterdir() if p.is_dir() and not p.name.startswith("."))] if kok.is_dir() else []:
        if (aday / "takip").is_dir() or ((aday / "plan").is_dir() and (aday / "metin").is_dir()):
            sonuc.append(aday)
    for alt in ("romanlar", "kitaplar"):
        if (kok / alt).is_dir():
            sonuc += [p for p in sorted((kok / alt).iterdir()) if p.is_dir() and ((p / "takip").is_dir() or (p / "plan").is_dir())]
    return sonuc


def aktif_kitap(kok: Path) -> Path | None:
    isaret = kok / ".aktif-kitap"
    if isaret.is_file():
        yol = (kok / isaret.read_text(encoding="utf-8").strip()).resolve()
        if yol.is_dir():
            return yol
    bulunan = kitaplar(kok)
    return bulunan[0] if len(bulunan) == 1 else None


def son_kayit(kitap: Path) -> int | None:
    yol = kitap / "takip" / "_takip-durumu.json"
    if not yol.is_file():
        return None
    try:
        return int(json.loads(yol.read_text(encoding="utf-8")).get("son_kaydedilen_bolum", 0))
    except (OSError, ValueError, TypeError):
        return None


def goreli(kok: Path, yol: Path) -> str:
    try:
        return yol.resolve().relative_to(kok).as_posix()
    except ValueError:
        return yol.as_posix()


def dizeler(deger: Any) -> list[str]:
    if isinstance(deger, str):
        return [deger]
    if isinstance(deger, dict):
        return [s for v in deger.values() for s in dizeler(v)]
    if isinstance(deger, list):
        return [s for v in deger for s in dizeler(v)]
    return []


def hedefler(girdi: dict[str, Any], kok: Path) -> list[Path]:
    arac = girdi.get("tool_input") or girdi.get("toolInput") or girdi.get("input") or {}
    cagri = girdi.get("toolCall")
    if isinstance(cagri, dict):
        arac = cagri.get("args") or arac
    ham: list[str] = []
    if isinstance(arac, dict):
        for anahtar in ("file_path", "filePath", "path", "TargetFile", "targetFile", "FilePath"):
            if isinstance(arac.get(anahtar), str):
                ham.append(arac[anahtar])
    for metin in dizeler(arac):
        ham += YAMA_HEDEFI.findall(metin)
        if "\n" not in metin[:400] or metin.lstrip().startswith(("cat", "tee", "cp", "mv", "printf", "echo")):
            ham += YONLENDIRME.findall(metin) + KOPYALA.findall(metin)
    taban = kok
    for anahtar in ("cwd", "workdir", "Cwd"):
        if isinstance(arac, dict) and isinstance(arac.get(anahtar), str) and Path(arac[anahtar]).is_dir():
            taban = Path(arac[anahtar])
    sonuc = []
    for h in dict.fromkeys(ham):
        yol = Path(h)
        sonuc.append((yol if yol.is_absolute() else taban / yol).resolve())
    return sonuc


def metin_hedefi(kok: Path, yol: Path) -> tuple[str, Path, int | str] | None:
    g = goreli(kok, yol)
    m = METIN_DESENI.search(g)
    if m:
        return "roman", yol.parent.parent, int(m.group(1))
    m = OYKU_DESENI.search(g)
    if m:
        return "oyku", yol.parent, m.group(1)
    return None


def plan_yolu(kitap: Path, n: int) -> Path | None:
    klasor = kitap / "plan"
    if not klasor.is_dir():
        return None
    for yol in sorted(klasor.glob("bolum-plani_*.md")):
        m = re.search(r"(\d{1,4})", yol.name[len("bolum-plani_"):])
        if m and int(m.group(1)) == n:
            return yol
    return None


def onceki_metin_var(kitap: Path, n: int) -> bool:
    return any(re.match(rf"bolum-0*{n}(?:[_\-.]|$)", p.name) for p in (kitap / "metin").glob("bolum-*.md"))


# ------------------------------------------------------------------ kurallar

def engel_nedeni(kok: Path, yol: Path) -> str | None:
    hedef = metin_hedefi(kok, yol)
    if hedef is None:
        return None
    tur, kitap, anahtar = hedef
    if tur == "oyku":
        if not (kitap / "sahne-plani.md").is_file():
            return f"Öykü metni yazılmadan önce sahne planı gerekir: {goreli(kok, kitap / 'sahne-plani.md')} dosyasını oluşturun (oyku-yaz becerisi)."
        return None
    n = int(anahtar)
    plan = plan_yolu(kitap, n)
    if plan is None:
        return (f"{n}. bölümün planı yok. Önce {goreli(kok, kitap / 'plan' / f'bolum-plani_{n:03d}.md')} dosyasını "
                "'Hedef uzunluk: ... kelime' satırıyla yazın (roman-yaz becerisi, bölüm planı adımı).")
    if not re.search(r"^\s*[-*]?\s*\**Hedef uzunluk\**\s*:\s*[\d.]+", plan.read_text(encoding="utf-8"), re.M | re.I):
        return f"{goreli(kok, plan)} içinde 'Hedef uzunluk: 2200 kelime' biçiminde bir satır yok; önce ekleyin."
    son = son_kayit(kitap)
    if son is not None and n > son + 1 and n > 1 and onceki_metin_var(kitap, n - 1):
        return (f"{n - 1}. bölüm yazılmış ama takibe kaydedilmemiş (son kayıt: {son}). Önce "
                f"'hikayectl.py bolum kaydet --proje {goreli(kok, kitap)} --bolum {n - 1} --girdi ...' çalıştırın.")
    return None


def yazi_sonrasi_notu(kok: Path, yol: Path) -> str | None:
    hedef = metin_hedefi(kok, yol)
    if hedef is None or not yol.is_file():
        return None
    metin = yol.read_text(encoding="utf-8")
    if ATLAMA_ISARETI in metin:
        return None
    notlar: list[str] = []
    try:
        import ai_kalip_denetle
        import bozulma_denetle
        import metin_olcum
    except ImportError:
        return None
    for b in bozulma_denetle.denetle_metin(metin, goreli(kok, yol)):
        if b.onem == "engelleyici":
            notlar.append(f"- {b.satir}. satır [{b.kural}] {b.oneri}")
    beyaz = ai_kalip_denetle.beyaz_liste_yukle(yol)
    for b in ai_kalip_denetle.denetle_metin(metin, goreli(kok, yol), beyaz)[:12]:
        if b.onem == "engelleyici":
            notlar.append(f"- {b.satir}. satır [{b.kural}] “{b.alinti}” → {b.oneri}")
    tur, kitap, anahtar = hedef
    if tur == "roman":
        plan = plan_yolu(kitap, int(anahtar))
        if plan is not None:
            try:
                d = metin_olcum.uzunluk_degerlendir(metin_olcum.kelime_say(metin), metin_olcum.plandan_hedef(plan.read_text(encoding="utf-8")))
                if d["durum"] in {"cok_kisa", "cok_uzun"}:
                    notlar.append(f"- Uzunluk {d['gercek']} kelime; hedef {d['hedef']} (sert sınırın dışında).")
            except metin_olcum.OlcumHatasi:
                pass
    if not notlar:
        return None
    return (f"[ai-hikaye denetimi] {goreli(kok, yol)} için bulgular:\n" + "\n".join(notlar)
            + "\nBu bulguları bir sonraki bölüme geçmeden düzeltin. Bilinçli bir tercihse satırı kitabın .yz-beyaz-liste dosyasına ekleyin.")


def oturum_mesajlari(kok: Path, ev: str, kaynak: str = "") -> list[str]:
    mesajlar: list[str] = []
    isaret = kok / ".hikaye-kurulu"
    try:
        bilgi = json.loads(isaret.read_text(encoding="utf-8"))
        if ev not in bilgi.get("ev_sahipleri", []):
            mesajlar.append(f"[hikaye-kurulum] Bu proje {ev} için kurulmamış; hikaye-kurulum becerisini yeniden çalıştırın.")
    except (OSError, ValueError):
        mesajlar.append("[hikaye-kurulum] .hikaye-kurulu okunamadı; hikaye-kurulum becerisini yeniden çalıştırın.")
    kitap = aktif_kitap(kok)
    if kitap is not None:
        son = son_kayit(kitap)
        baglam = kitap / "takip" / "baglam.md"
        satir = f"[hikaye bağlamı] Etkin kitap: {goreli(kok, kitap)}."
        if baglam.is_file():
            satir += f" Uzun yazıma devam etmeden önce {goreli(kok, baglam)} dosyasını okuyun."
        if son is not None:
            sonraki = son + 1
            satir += f" Son kaydedilen bölüm: {son}; sıradaki: {sonraki} (plan {'hazır' if plan_yolu(kitap, sonraki) else 'yok'})."
            kaydedilmemis = [int(m.group(1)) for p in (kitap / "metin").glob("bolum-*.md")
                             if (m := re.match(r"bolum-(\d+)", p.name)) and int(m.group(1)) > son]
            if kaydedilmemis:
                mesajlar.append(f"[süreklilik] Takibe kaydedilmemiş bölüm(ler): {', '.join(map(str, sorted(kaydedilmemis)))}. "
                                "Yeni bölüme geçmeden 'hikayectl.py bolum kaydet' çalıştırın.")
        mesajlar.insert(0, satir)
        if not (kitap / "kurgu" / "ton.md").is_file():
            mesajlar.append("[eksik] kurgu/ton.md yok; üslup kararı olmadan yazılan bölümler tutarsız olur.")
    elif kitaplar(kok):
        mesajlar.append("[hikaye bağlamı] Birden fazla kitap var; .aktif-kitap dosyasına çalışılan kitabın yolunu yazın ('hikaye' becerisi: kitap değiştir).")
    devir = kok / ".hikaye" / "devir-notu.md"
    if kaynak == "compact" and devir.is_file():
        mesajlar.append("[sıkıştırma sonrası] Devir notu:\n" + devir.read_text(encoding="utf-8")[:4000])
    return mesajlar


def devir_notu_yaz(kok: Path) -> str:
    kitap = aktif_kitap(kok)
    satirlar = ["# Devir Notu", "", f"- Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    if kitap is not None:
        satirlar.append(f"- Etkin kitap: {goreli(kok, kitap)}")
        son = son_kayit(kitap)
        if son is not None:
            satirlar.append(f"- Son kaydedilen bölüm: {son}; sıradaki: {son + 1}")
        baglam = kitap / "takip" / "baglam.md"
        if baglam.is_file():
            satirlar.append(f"- Önce oku: {goreli(kok, baglam)}")
    else:
        satirlar.append("- Etkin kitap bulunamadı")
    degisen = [s for s in git(kok, "status", "--porcelain").splitlines() if s.strip()]
    satirlar.append(f"- Git: {len(degisen)} değişmiş dosya")
    satirlar.append("- Kural: takip dosyalarını elle düzenleme; bölüm bitince hikayectl.py bolum kaydet.")
    icerik = "\n".join(satirlar) + "\n"
    hedef = kok / ".hikaye" / "devir-notu.md"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(icerik, encoding="utf-8", newline="\n")
    return icerik


def kayit_uyarisi(kok: Path, komut: str) -> str | None:
    if not GIT_COMMIT.search(komut):
        return None
    sahnelenen = git(kok, "diff", "--cached", "--name-only").splitlines()
    uyarilar = []
    for dosya in sahnelenen:
        m = METIN_DESENI.search(dosya)
        if not m:
            continue
        kitap = (kok / dosya).parent.parent
        son = son_kayit(kitap)
        if son is not None and int(m.group(1)) > son:
            uyarilar.append(f"{dosya} takibe kaydedilmeden commit ediliyor (son kayıt: {son}).")
    for dosya in sahnelenen:
        if "/takip/" in f"/{dosya}" and not dosya.endswith("_takip-durumu.json"):
            kitap = kok / dosya.split("/takip/")[0] if "/takip/" in dosya else kok
            durum = kitap / "takip" / "_takip-durumu.json"
            if durum.is_file() and durum.as_posix() not in {(kok / s).as_posix() for s in sahnelenen}:
                uyarilar.append(f"{dosya} değişmiş ama _takip-durumu.json değişmemiş: görünüm elle düzenlenmiş olabilir.")
                break
    return ("[ai-hikaye] " + " ".join(uyarilar)) if uyarilar else None


# ------------------------------------------------------------------ Antigravity bekleyen bulgular

def bekleyen_yolu(girdi: dict[str, Any]) -> Path | None:
    klasor = girdi.get("artifactDirectoryPath")
    if isinstance(klasor, str) and Path(klasor).is_dir():
        return Path(klasor) / "ai-hikaye-bekleyen.json"
    konusma = re.sub(r"[^A-Za-z0-9_-]", "", str(girdi.get("conversationId", "")))
    return Path(tempfile.gettempdir()) / f"ai-hikaye-{konusma}.json" if konusma else None


def bekleyen_oku(girdi: dict[str, Any]) -> dict[str, Any]:
    yol = bekleyen_yolu(girdi)
    try:
        veri = json.loads(yol.read_text(encoding="utf-8")) if yol else {}
        return {"bulgular": dict(veri.get("bulgular", {})), "dur_denemesi": int(veri.get("dur_denemesi", 0))}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"bulgular": {}, "dur_denemesi": 0}


def bekleyen_yaz(girdi: dict[str, Any], durum: dict[str, Any]) -> None:
    yol = bekleyen_yolu(girdi)
    if yol:
        yol.write_text(json.dumps(durum, ensure_ascii=False), encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ çıktı biçimleri

def baglam_ciktisi(ev: str, olay: str, metin: str) -> Any:
    if ev == "opencode":
        return {"not": metin}
    return {"hookSpecificOutput": {"hookEventName": olay, "additionalContext": metin[:9500]}}


def calistir(olay: str, ev: str, girdi: dict[str, Any]) -> tuple[Any, int]:
    kok = proje_koku(girdi)
    if not (kok / ".hikaye-kurulu").exists():
        if ev == "antigravity" and olay == "yazi-oncesi":
            return {"decision": "allow"}, 0
        if ev == "antigravity" and olay == "dur":
            return {"decision": "stop"}, 0
        if ev == "codex" and olay == "dur":
            return {}, 0
        return None, 0

    if olay in {"oturum-basla", "sikistirma-sonrasi"}:
        kaynak = "compact" if olay == "sikistirma-sonrasi" else str(girdi.get("source", ""))
        mesajlar = oturum_mesajlari(kok, ev, kaynak)
        return (baglam_ciktisi(ev, "SessionStart", "\n".join(mesajlar)) if mesajlar else None), 0

    if olay == "cagri-oncesi":  # Antigravity PreInvocation
        mesajlar = oturum_mesajlari(kok, ev) if girdi.get("invocationNum") == 0 else []
        notlar = [n for n in bekleyen_oku(girdi)["bulgular"].values() if n]
        mesajlar += notlar
        return ({"injectSteps": [{"ephemeralMessage": m} for m in mesajlar]} if mesajlar else {}), 0

    if olay == "yazi-oncesi":
        for yol in hedefler(girdi, kok):
            neden = engel_nedeni(kok, yol)
            if neden:
                if ev == "antigravity":
                    return {"decision": "deny", "reason": neden}, 0
                if ev == "opencode":
                    return {"engelle": True, "neden": neden}, 0
                return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                               "permissionDecisionReason": neden}}, 0
        komut = " ".join(dizeler((girdi.get("tool_input") or {}).get("command", ""))) if isinstance(girdi.get("tool_input"), dict) else ""
        if not komut and isinstance(girdi.get("toolCall"), dict):
            komut = " ".join(dizeler((girdi["toolCall"].get("args") or {}).get("CommandLine", "")))
        uyari = kayit_uyarisi(kok, komut) if komut else None
        if ev == "antigravity":
            return ({"decision": "allow", "reason": uyari} if uyari else {"decision": "allow"}), 0
        if uyari:
            return ({"not": uyari} if ev == "opencode" else {"systemMessage": uyari}), 0
        return None, 0

    if olay == "kayit-oncesi":
        komut = " ".join(dizeler((girdi.get("tool_input") or {}).get("command", ""))) if isinstance(girdi.get("tool_input"), dict) else ""
        uyari = kayit_uyarisi(kok, komut)
        return ({"systemMessage": uyari} if uyari else None), 0

    if olay == "yazi-sonrasi":
        notlar = {}
        for yol in hedefler(girdi, kok):
            notu = yazi_sonrasi_notu(kok, yol)
            notlar[str(yol)] = notu
        if ev == "antigravity":
            durum = bekleyen_oku(girdi)
            for anahtar, notu in notlar.items():
                if notu:
                    durum["bulgular"][anahtar] = notu
                else:
                    durum["bulgular"].pop(anahtar, None)
            durum["dur_denemesi"] = 0
            bekleyen_yaz(girdi, durum)
            return {}, 0
        birlesik = "\n\n".join(n for n in notlar.values() if n)
        return (baglam_ciktisi(ev, "PostToolUse", birlesik) if birlesik else None), 0

    if olay == "sikistirma-oncesi":
        icerik = devir_notu_yaz(kok)
        return (icerik if ev in {"claude", "codex", "zcode"} else {"not": icerik}), 0

    if olay == "oturum-sonu":
        kitap = aktif_kitap(kok)
        satir = f"- {datetime.now().strftime('%Y-%m-%d %H:%M')} · kitap: {goreli(kok, kitap) if kitap else '-'} · son kayıt: {son_kayit(kitap) if kitap else '-'}\n"
        gunluk = kok / ".hikaye" / "oturum-gunlugu.md"
        gunluk.parent.mkdir(parents=True, exist_ok=True)
        with gunluk.open("a", encoding="utf-8") as f:
            f.write(satir)
        return None, 0

    if olay == "dur":
        if ev == "antigravity":
            durum = bekleyen_oku(girdi)
            notlar = [n for n in durum["bulgular"].values() if n]
            sebep = str(girdi.get("terminationReason", ""))
            if notlar and girdi.get("fullyIdle") is not False and sebep in {"", "model_stop"} and durum["dur_denemesi"] < 1:
                durum["dur_denemesi"] += 1
                bekleyen_yaz(girdi, durum)
                return {"decision": "continue", "reason": "\n\n".join(notlar)}, 0
            return {"decision": "stop"}, 0
        return {}, 0
    return None, 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    olay = argv[0] if argv else ""
    ev = "claude"
    if "--ev" in argv:
        i = argv.index("--ev")
        ev = argv[i + 1] if i + 1 < len(argv) else ev
    girdi = girdi_oku()
    if "--eklenti" in argv and ev == "zcode":
        # Eklenti kancası, proje kancaları (kur.py --ev zcode) kuruluysa iki kez çalışmamak için susar.
        try:
            ayar = proje_koku(girdi) / ".zcode" / "config.json"
            if ayar.is_file() and KANCA_ADI in ayar.read_text(encoding="utf-8"):
                yaz(None)
                return 0
        except Exception:  # noqa: BLE001
            pass
    try:
        cikti, kod = calistir(olay, ev, girdi)
    except Exception as hata:  # noqa: BLE001 - kanca akışı asla kilitlememeli
        print(f"[ai-hikaye kanca] iç hata, izin verildi: {hata}", file=sys.stderr)
        cikti, kod = ({"decision": "allow"} if ev == "antigravity" and olay == "yazi-oncesi" else
                      {"decision": "stop"} if ev == "antigravity" and olay == "dur" else
                      {} if olay == "dur" else None), 0
    yaz(cikti)
    return kod


if __name__ == "__main__":
    sys.exit(main())
