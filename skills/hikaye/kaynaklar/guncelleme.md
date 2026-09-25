# Güncelleme

| Kurulum yolu | Güncelleme |
|---|---|
| Claude Code eklentisi | `/plugin marketplace update ai-hikaye-roman-olusturma`, ardından `/plugin update ai-hikaye-roman-olusturma@ai-hikaye-roman-olusturma` |
| npx skills | `npx skills add cumabozkurt/ai-hikaye-roman-olusturma -y -g` (yeniden çalıştırmak günceller) |
| Codex eklentisi | `codex plugin marketplace upgrade ai-hikaye-roman-olusturma` |
| Git klonu | `git pull` ardından `bash betikler/kur.sh` (Windows: `powershell -File betikler/kur.ps1`) |

Beceriler güncellendikten sonra her yazım projesinde `/hikaye-kurulum` komutunu yeniden çalıştırın: kancalar, ajanlar ve `.hikaye/kaynaklar/` yenilenir; sizin dosyalarınıza (metin, plan, takip) dokunulmaz. Ardından yeni bir oturum açın.
