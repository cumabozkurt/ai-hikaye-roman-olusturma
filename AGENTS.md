# AGENTS.md: depo geliştirme rehberi

Bu dosya, **AI Hikaye & Roman Oluşturma** deposunu geliştiren kodlama ajanları içindir. Kullanıcının yazım projesine kurulan yönlendirme metni değildir; o metin `skills/hikaye-kurulum/varliklar/sablonlar/` altındaki şablondan `kur.py` tarafından üretilir.

## Depo nedir?

Türkçe roman ve öykü yazımı için 19 beceri (`skills/<ad>/SKILL.md` + `kaynaklar/`, `betikler/`, `varliklar/`), 7 ajan şablonu, tek Python kanca çekirdeği ve 8 ev sahibi için uyarlama katmanı. Ürün, Markdown ile yazılmış yazım yöntemi ve iş akışı sözleşmesidir; betikler belirlenimci denetim ve kayıt araçlarıdır.

## Değişiklikten önce bilinmesi gerekenler

- Paylaşılan dosyaların tek kaynağı `paylasilan/`; değiştirince `python3 betikler/paylasilanlari_esitle.py`.
- Eklenti bildirimleri ve ZCode varlıkları üretilir: `python3 betikler/eklenti_dosyalari_uret.py`. `plugin.json`, `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/`, `.zcode-plugin/`, `marketplace.json`, `reasonix-plugin.json` dosyalarını elle düzenlemeyin.
- Kök klasörde `hooks/` klasörü **bilinçli olarak yoktur**: Claude Code ve Codex eklenti kökündeki `hooks/hooks.json` dosyasını kendiliğinden yükler; kancalar projeye `hikaye-kurulum` ile kurulur.
- `.agents/skills` → `../skills` göreli sembolik bağlantısı Codex ve OpenCode keşfi içindir; kaldırmayın.
- Ön bilgi tek satırlıdır: `description` çift tırnaklı dize, `metadata` tek satır JSON (OpenClaw ve basit ayrıştırıcılar buna güvenir).
- Beceriler birbirinin dosyasına başvurmaz (istisna: `tarayici-cdp` temel bileşen olarak anılabilir).
- Kullanıcıya dönük her metin Türkiye Türkçesidir.

## Doğrulama

```bash
python3 -m pytest
python3 betikler/statik_denetim.py
python3 betikler/turkce_uyum_denetle.py
```

Ayrıntılı kurallar: [CONTRIBUTING.md](CONTRIBUTING.md). Mimari: [docs/mimari.md](docs/mimari.md). Kararlar: [docs/mimari-kararlar.md](docs/mimari-kararlar.md).
