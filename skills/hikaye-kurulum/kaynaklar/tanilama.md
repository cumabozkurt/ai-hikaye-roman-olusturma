# Tanılama ve Kaldırma

## Sık sorunlar

| Belirti | Neden | Çözüm |
|---|---|---|
| Kancalar hiç çalışmıyor | Oturum kurulumdan önce açıldı | Yeni oturum açın |
| Codex kancaları çalışmıyor | Proje kancaları güven onayı bekliyor | Codex'te `/hooks` ile inceleyip onaylayın |
| `python3: command not found` | Windows'ta Python `py` ile çağrılıyor | Kurulum betiği `python_komutu()` ile uygun komutu seçer; yine de sorun varsa Python 3.11+ kurup `kur.py`'yi yeniden çalıştırın |
| "eksik kanca dosyası" | `.hikaye/kancalar/` silinmiş | `kur.py --proje . --ev <ev>` ile yeniden kurun |
| OpenCode eklentisi yüklenmiyor | v1/v2 eklenti API'si farklı | `--opencode-surum 1` ya da `2` ile doğru sürümü zorlayın |
| ZCode'da ajanlar yok | ZCode özel ajan çalıştırmaz | Beceriler "Yedek: tek başına yürütüldü" ile ana oturumda çalışır; bu beklenen davranıştır |
| Antigravity kancası dosya bulamıyor | Kancalar `.agents/` klasöründen çalışır | Komutlar `../.hikaye/kancalar/…` kullanır; `.agents/hooks.json` elle taşındıysa yeniden kurun |
| "sembolik bağlantı üzerinden yazılmaz" | Hedef bir symlink | Bağlantıyı kaldırın ya da gerçek klasörde çalıştırın |

## Kanca elle test

```bash
echo '{"cwd": "'"$PWD"'"}' | python3 .hikaye/kancalar/hikaye_kanca.py oturum-basla --ev claude
```

Çıktı geçerli JSON olmalıdır.

## Kaldırma

1. `CLAUDE.md` / `AGENTS.md` içindeki `<!-- ai-hikaye:basla -->` … `<!-- ai-hikaye:bitir -->` bloğunu silin.
2. Ayar dosyalarından (`.claude/settings.local.json`, `.codex/hooks.json`, `.agents/hooks.json`, `.zcode/config.json`) `hikaye_kanca.py` içeren kayıtları silin.
3. `.opencode/plugins/ai-hikaye.ts`, bu paketin ajan dosyalarını ve `.agents/rules/ai-hikaye.md` dosyasını silin.
4. `.hikaye/kancalar/`, `.hikaye/kaynaklar/` ve `.hikaye-kurulu` dosyasını silin.

Kitap dosyalarınız (`metin/`, `plan/`, `kurgu/`, `takip/`) bu adımlardan etkilenmez.
