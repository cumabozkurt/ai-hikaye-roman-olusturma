---
name: hikaye-kurulum
description: "Yazım projesine ajanları, kancaları (yazım sonrası yapay zekâ tadı uyarısı, bölüm kaydı hatırlatması, oturum devri), proje kurallarını ve ortak kaynakları kurar ya da günceller. Claude Code, Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix ve genel ajanları destekler. Tetikleyiciler: /hikaye-kurulum, \"projeyi kur\", \"kancaları kur\", \"ajanları güncelle\", \"kurulumu denetle\"."
license: MIT
compatibility: "Python 3.11+. Kancalar için ev sahibinin kanca desteği gerekir (Claude Code, Codex, OpenCode, Antigravity, ZCode)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "oh-story-claudecode/story-setup"}
---

# hikaye-kurulum: Proje Kurulumu

Yazım projesini (yazarın kitap klasörü ya da çalışma alanı) diğer becerilerin tam gücüyle çalışacağı hâle getirirsin. Bütün işi tek bir deterministik betik yapar; sen doğru ev sahibini seçer, çalıştırır ve sonucu yazara açıklarsın.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}/betikler/kur.py`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## 1. Ev sahibini belirle

Hangi ajan ortamında çalıştığını bil (bilmiyorsan yazara sor). Yazar birden fazla araç kullanıyorsa hepsini birlikte kurabilirsin.

| Ev sahibi | `--ev` | Kurulanlar |
|---|---|---|
| Claude Code | `claude` | `.claude/agents/*.md`, `.claude/settings.local.json` kancaları, `CLAUDE.md` bloğu |
| OpenAI Codex | `codex` | `.codex/agents/*.toml`, `.codex/hooks.json` (Windows için `commandWindows`), `AGENTS.md` bloğu |
| OpenCode | `opencode` | `.opencode/agents/*.md`, `.opencode/plugins/ai-hikaye.ts` (v1/v2 otomatik), `AGENTS.md` bloğu |
| Google Antigravity | `antigravity` | `.agents/skills/`, `.agents/agents/*/agent.md`, `.agents/rules/ai-hikaye.md`, `.agents/hooks.json` |
| ZCode | `zcode` | `.zcode/config.json` süreç kancaları, `.zcode/commands/`, `AGENTS.md` bloğu (özel ajan yok) |
| OpenClaw / Reasonix / genel | `openclaw`, `reasonix`, `genel` | becerilerin kopyası ve `AGENTS.md` yönlendirmesi |

Her kurulumda ortak olarak `.hikaye/kancalar/` (kanca çekirdeği ve denetim modülleri), `.hikaye/kaynaklar/` (yapay zekâ tadı, TDK rehberi, tür kartları, takip protokolü vb.), `.hikaye-kurulu` işareti ve `.gitignore` bloğu yazılır.

## 2. Önce kuru çalıştır

```bash
python3 betikler/kur.py --proje . --ev claude --kuru
```

Çıktıdaki dosya listesini yazara kısaca göster. Mevcut dosyalar korunur:

- `CLAUDE.md` / `AGENTS.md`: yalnızca `<!-- ai-hikaye:basla -->` … `<!-- ai-hikaye:bitir -->` bloğu değişir.
- JSON ayarlar: yalnızca `hikaye_kanca.py` içeren kayıtlarımız değiştirilir; yazarın kendi kancaları ve diğer alanlar kalır.
- Yalnızca bu paketin bilinen adlı ajan ve beceri dosyaları güncellenir.
- Sembolik bağlantı üzerinden yazılmaz.

## 3. Kur

```bash
python3 betikler/kur.py --proje . --ev claude          # tek ev sahibi
python3 betikler/kur.py --proje . --ev claude,codex    # birden fazla
python3 betikler/kur.py --proje . --ev hepsi           # hepsi
```

OpenCode için sürüm `opencode --version` ile otomatik seçilir; zorlamak için `--opencode-surum 1` ya da `2`.

Aynı komutu yeniden çalıştırmak güvenlidir (sonuç bayt bayt aynı); beceri güncellemelerinden sonra bu yolla yenile.

## 4. Denetle

```bash
python3 betikler/kur.py --proje . --denetle
```

JSON rapordaki `sorunlar` boş olmalı. Sorun varsa `kaynaklar/tanilama.md` dosyasına bak.

## 5. Yazara bildir

```
✅ Kurulum tamam (Claude Code + Codex)
• 8 ajan: hikaye-mimari, anlati-yazari, tutarlilik-denetcisi, karakter-tasarimcisi, hikaye-arastirmaci, proje-kasifi, bolum-cikarici, bolum-hakemi
• Kancalar: oturum başında bağlam kartı, yazımdan önce plan ve kayıt kapısı, yazımdan sonra yapay zekâ tadı ve bozulma uyarısı, sıkıştırmadan önce devir notu
• Kaynaklar: .hikaye/kaynaklar/
Kancaların devreye girmesi için yeni bir oturum açın. Codex'te ilk açılışta /hooks ile kancalara güven onayı verin.
```

## Kancalar ne yapar?

| Olay | Davranış |
|---|---|
| Oturum başı / sıkıştırma sonrası | Aktif kitabın bağlam kartını (`takip/baglam.md`, en çok 10.000 karakter) ve varsa devir notunu oturuma ekler |
| Yazmadan önce | Bölüm planı ya da plandaki `Hedef uzunluk` satırı yoksa, önceki bölüm takibe kaydedilmemişse ya da öykünün sahne planı yoksa metin yazımını gerekçesiyle durdurur; `git commit` sırasında kaydedilmemiş bölümleri ve elle düzenlenmiş `takip/` görünümlerini uyarır |
| Yazdıktan sonra | Bölüm ya da öykü metninde engelleyici bozulma ve yapay zekâ kalıplarını bildirir |
| Sıkıştırma öncesi / oturum sonu / durma | `.hikaye/devir-notu.md` ve oturum günlüğü yazar |

Kancalar `.hikaye-kurulu` yoksa hiçbir şey yapmaz ve kendi hatalarında akışı asla kilitlemez (izin verir). Kanca istemeyen yazar ilgili ayar dosyasından `hikaye_kanca.py` kayıtlarını silebilir.

## Kaldırma

`kaynaklar/tanilama.md` içindeki "Kaldırma" bölümü.
