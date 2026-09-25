# Değişiklik Günlüğü

Biçim [Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/) ilkelerine, sürümleme [Anlamsal Sürümleme](https://semver.org/lang/tr/) kurallarına uyar.

## [1.1.0] - 2026-09-25

İkinci inceleme turu: üç bağımsız göz (araç mühendisi, Türk editör, ilk kez kullanan) ve karşılaştırmalı araştırma. Ayrıntı: [docs/INCELEME-RAPORU.md](docs/INCELEME-RAPORU.md).

### Eklendi
- `e-kitap-derle` becerisi (20. beceri): Markdown bölümlerinden EPUB 3 ve tek dosyalık HTML okuma kopyası; kapak, künye, içindekiler, yeniden üretilebilir çıktı (`SOURCE_DATE_EPOCH`), bitmemiş işaret kapısı. W3C EPUBCheck 5.1.0 ile hatasız.
- `metin_analizi.py`: Ateşman okunabilirlik puanı, cümle uzunluğu ortalaması ve sapması, diyalog oranı, yakın tekrarlar, cümle başı tekrarları, duyu dağılımı, `[TK]`/`[DOLDUR]` işaretleri.
- Kitaba özgü `.yasak-kaliplar` dosyası (`ifade => öneri`); `ai_kalip_denetle.py` engelleyici `kitap-yasagi` bulgusu verir.
- `metin-incele` için okur paneli (`kaynaklar/okur-paneli.md`): altı Türk okur profiliyle bırakma noktası analizi.
- 12 tür kartına "Öz denetim soruları" ve Türkçe kelime sayısı notu.
- `evals/`: `claude plugin eval` biçiminde 23 değerlendirme vakası (her beceri için tetiklenme + sonuç, 3 olumsuz vaka).
- Ortak `dosya_oku.py`: UTF-8 BOM, Windows-1254 geri dönüşü, ikili dosya ve klasör reddi.
- README yeniden tasarlandı: afiş, rozetler, akış şeması, gerçek terminal çıktıları, önce/sonra örneği, karşılaştırma, SSS, yol haritası.

### Düzeltildi
- 357 bozuk girdi denemesinde 60 Python izi (traceback) → 0; bütün hata iletileri Türkçe (`HIKAYE_AYIKLA=1` ile ayrıntı).
- 122 komut satırı seçeneğinde eksik yardım metni tamamlandı; kapsama testi eklendi.
- Çalışma masası sunucusu DNS yeniden bağlama saldırısına karşı yalnızca yerel `Host` başlığını kabul ediyor.
- `turkce_uyum_denetle.py` var olmayan yolda sessizce geçiyordu; artık hata veriyor.
- `metin_olcum.py --hedef -5` eksi işaretini yutuyordu; `liste_tara.py` bozuk liste biçiminde çöküyordu.
- Örnek romanın ilk bölümünde saat kadranında olmayan "on dördün üstünde" ifadesi düzeltildi.

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
