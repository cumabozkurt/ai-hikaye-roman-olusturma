# Değişiklik Günlüğü

Biçim [Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/) ilkelerine, sürümleme [Anlamsal Sürümleme](https://semver.org/lang/tr/) kurallarına uyar.

## [1.0.0] - 2026-09-25

İlk sürüm: oh-story-claudecode v0.7.11 (commit 401019ea) temel alınarak Türkiye Türkçesi için baştan yazıldı.

### Eklendi

- 13 üst kaynak becerisinin Türkçe karşılıkları: `hikaye`, `hikaye-kurulum`, `roman-tara`, `oyku-tara`, `roman-cozumle`, `oyku-cozumle`, `roman-yaz`, `oyku-yaz`, `yz-tadi-gider`, `metin-incele`, `hikaye-ice-aktar`, `kapak-tasarla`, `tarayici-cdp`.
- 6 yeni beceri: `yazim-denetle` (TDK), `sureklilik-denetle`, `wattpad-bolum-planla`, `yayinevi-dosyasi`, `uyarlama-sinopsis`, `sesli-kitap-hazirla`.
- 7 Türkçe ajan ve tek Python kanca çekirdeği (Claude Code, Codex, OpenCode 1.x/2.x, Antigravity, ZCode).
- Türkçe yapay zekâ kalıp denetçisi, bozulma denetçisi, TDK yazım denetçisi, noktalama düzeltici, süreklilik denetçisi.
- Takip durumu (`_takip-durumu.json`) ve türetilmiş görünümler; yazar gerçeği / okur bilgisi ayrımı; atomik bölüm kaydı.
- 12 Türkçe tür kartı; Türkiye yayın ve okur platformları rehberi.
- Wattpad herkese açık API taraması (Türkçe süzgeçli) ve CDP tabanlı mağaza okuma.
- Agent Plugins 1.0.0 bildirimi, Claude Code ve Codex pazar yerleri, ZCode ve Reasonix bildirimleri; tek kaynaktan üretici.
- `kur.sh` / `kur.ps1` kullanıcı düzeyi kurulum betikleri.
- Statik denetim, Türkçe uyum denetimi (CJK ve Türkçe karakter hataları), argparse iletilerinin Türkçeleştirilmesi.
- Bütün Python betikleri için pytest testleri; Python 3.11–3.14 CI matrisi.
- Özgün örnekler: "Saatçinin Kızı" (roman), "Son Vapur" (öykü), yapay zekâ tadı karşılaştırması.
- Ayrıntılı inceleme raporu: `docs/INCELEME-RAPORU.md`.
