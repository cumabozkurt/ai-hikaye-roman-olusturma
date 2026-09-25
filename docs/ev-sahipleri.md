# Ev sahipleri: kurulum ayrıntıları ve sorun giderme

Günlük kullanım için README'deki [Kurulum](../README.md#kurulum) bölümü yeterlidir. Bu sayfa her ortamın ayrıntısını ve bilinen sınırlarını anlatır.

## Ortak adımlar

1. Becerileri kurun (eklenti, `npx skills` ya da `betikler/kur.sh`).
2. Yazım projesinin kökünde `/hikaye-kurulum` (Codex'te `$hikaye-kurulum`). Ajan önce `--kuru` ile ne yazılacağını gösterir, onayınızla kurar.
3. Yeni oturum açın. Denetim: `python3 betikler/kur.py --proje . --denetle` (beceri klasöründen).

Kurulum güvenlidir: `CLAUDE.md`/`AGENTS.md` içinde yalnızca `<!-- ai-hikaye:basla -->` … `<!-- ai-hikaye:bitir -->` bloğu değişir; JSON ayarlarda yalnızca `hikaye_kanca.py` içeren kayıtlar değişir; sembolik bağlantı üzerinden ve proje dışına yazılmaz; aynı komutu iki kez çalıştırmak bayt bayt aynı sonucu verir. Bozuk bir JSON ayar dosyası üzerine yazılmaz, hata bildirilir.

## Claude Code

- Eklenti: `/plugin marketplace add cumabozkurt/ai-hikaye-roman-olusturma` ve `/plugin install ai-hikaye-roman-olusturma@ai-hikaye-roman-olusturma`. Beceriler `/ai-hikaye-roman-olusturma:<beceri>` biçiminde çağrılır.
- `/hikaye-kurulum` şunları yazar: `CLAUDE.md` bloğu, `.claude/agents/*.md` (8 ajan), `.claude/rules/hikaye-yazim.md`, `.claude/settings.local.json` içinde `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SessionEnd` kancaları.
- Engelleme `PreToolUse` çıktısındaki `permissionDecision: "deny"` ile yapılır; gerekçe modele iletilir.

## OpenAI Codex

- Eklenti: `codex plugin marketplace add cumabozkurt/ai-hikaye-roman-olusturma`, ardından `codex plugin add ai-hikaye-roman-olusturma@ai-hikaye-roman-olusturma` ya da Codex içinde `/plugins`. Depo klonlandıysa `.agents/skills` bağlantısı becerileri doğrudan bulundurur (Windows'ta `git config core.symlinks true` gerekir).
- `$hikaye-kurulum` şunları yazar: `AGENTS.md` bloğu, `.codex/agents/*.toml` (salt okunur ajanlarda `sandbox_mode = "read-only"`), `.codex/hooks.json` (`SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SessionEnd`; Windows için `commandWindows`; bağlam kartı diske taşmasın diye `additionalContextLimit`).
- **Kancalar `/hooks` ile güven onayı verilene kadar sessizce atlanır**, plan kapısı dahil. İlk oturumda onay verin.

## OpenCode

- Beceriler `.opencode/skills`, `.claude/skills` ve `.agents/skills` klasörlerinden bulunur; `kur.sh opencode` kullanıcı klasörüne (`~/.config/opencode/skills`) kopyalar.
- `/hikaye-kurulum` OpenCode sürümünü algılar (`--opencode-surum 1|2` ile zorlanabilir): 2.x için `permissions` listeli ajanlar ve `{ id, setup }` biçiminde eklenti, 1.x için `tools` alanlı ajanlar ve 1.x eklenti API'si yazar. Ayrıca `.opencode/commands/*.md` eğik çizgi komutları üretir.
- Eklenti, yazma araçlarından önce çekirdeği çağırır; engel gerekirse aracı hata ile durdurur.

## Google Antigravity

- `/skills` menüsünden `hikaye-kurulum` seçin ve ev sahibi olarak Antigravity'yi belirtin. Kurulum `.agents/skills/` (gerçek klasörler), `.agents/agents/<ajan>/agent.md`, `.agents/rules/ai-hikaye.md` ve `.agents/hooks.json` içinde `ai-hikaye` grubunu yazar. Kullanıcının diğer beceri, ajan, kural ve kanca grupları korunur; `~/.gemini/` klasörüne yazılmaz.
- Kancalar Python gerektirir. CLI'da `agy -p` kullanırken çalışma alanını `--add-dir "$PWD"` ile ekleyin; aksi hâlde `.agents/` yüklenmez.

## ZCode

- Eklenti yönetiminde bu depoyu ekleyin; kök `marketplace.json` (`ai-hikaye-roman-olusturma-zcode`) ya da `.claude-plugin/marketplace.json` görünebilir, ikisi aynı paketi içerir.
- Eklenti kancaları `${ZCODE_PLUGIN_ROOT}` üzerinden çekirdeği çağırır. Projeye `/hikaye-kurulum` ile ZCode kancaları da kurulduysa eklenti kancası `--eklenti` bayrağıyla kendini susturur; kanca iki kez çalışmaz.
- ZCode özel ajan çalıştırmaz ve `PreCompact`/`SessionEnd` olayı sunmaz; ilgili adımlar ana oturumda yürütülür, bağlam `SessionStart` ile geri yüklenir.

## OpenClaw, Reasonix ve genel ajanlar

- Yalnızca beceriler: kurulum becerileri proje `skills/` klasörüne kopyalar ve `AGENTS.md` yazar. Ajan ve kanca kurulmaz; plan kapısı betik düzeyinde (`hikayectl.py bolum denetle`) uygulanır.
- Reasonix proje beceri köklerini (`.agents/skills`) tarar; `reasonix-plugin.json` ile eklenti olarak da kurulabilir.
- Web yapay zekâları: depo dosyalarını okuyabiliyorsa ilgili `skills/<ad>/SKILL.md` ve `kaynaklar/` dosyalarını okutun.

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| Beceriler görünmüyor | Yeni oturum açın; `npx skills` kurulumunda komutu yeniden çalıştırın; Codex/Windows'ta `core.symlinks` |
| Kancalar çalışmıyor | `.hikaye-kurulu` var mı? `kur.py --denetle` çıktısına bakın; Codex'te `/hooks` onayı |
| "Python bulunamadı" | Python 3.11+ kurun; Windows'ta `py -3` kullanılabilir |
| Plan kapısı yanlışlıkla engelliyor | Bölüm planı dosya adı `plan/bolum-plani_NNN.md` ve içinde `Hedef uzunluk: 2.200 kelime` satırı olmalı; önceki bölüm `hikayectl.py bolum kaydet` ile kaydedilmiş olmalı |
| `npx skills add` çok sayıda "… does not support global skill installation" satırı yazıyor | Zararsızdır: araç bulduğu bütün ajanlara kurmayı dener. Yalnızca kullandıklarınızı seçmek için `-a claude-code codex opencode` ekleyin |
| `claude plugin validate` "CLAUDE.md eklenti bağlamı olarak yüklenmez" uyarısı veriyor | Beklenen durumdur: depo kökündeki `CLAUDE.md` yalnızca geliştiriciler içindir; eklenti becerileri etkilenmez |
| Bir betik kısa bir Türkçe hata verip duruyor | Ayrıntılı Python izini görmek için komutu `HIKAYE_AYIKLA=1` ortam değişkeniyle yeniden çalıştırın ve hata bildirimine ekleyin |
| Türkçe karakterler bozuk görünüyor | Dosyayı UTF-8 olarak kaydedin. Betikler Windows-1254 dosyaları uyarıyla okur; Word belgelerini önce `.txt` ya da `.md` olarak dışa aktarın |
| Wattpad taraması bağlantı hatası veriyor | Wattpad Türkiye'de erişime kapalıdır; `--girdi` ile kayıtlı yanıt kullanın ya da mağaza listelerine `tarayici-cdp` ile bakın |

Ayrıntılı tanılama: [`skills/hikaye-kurulum/kaynaklar/tanilama.md`](../skills/hikaye-kurulum/kaynaklar/tanilama.md).
