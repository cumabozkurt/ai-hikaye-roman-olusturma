---
name: hikaye
description: "Hikâye ve roman yazımının giriş noktası: isteği doğru beceriye yönlendirir, yazım projesinin durumunu özetler, birden fazla kitap arasında geçiş yapar, yazar hafızasını yönetir ve yerel çalışma masası panelini açar. Tetikleyiciler: /hikaye, \"hikâye yazmak istiyorum\", \"nereden başlasam\", \"kitaplarım\", \"projenin durumu ne\", \"çalışma masasını aç\", \"bunu hatırla\"."
license: MIT
compatibility: "Python 3.11+ (çalışma masası için tarayıcı). Claude Code, Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.1.0", "ust-kaynak": "oh-story-claudecode/story"}
---

# hikaye: Giriş ve Yönlendirme

Yazarın ilk durağısın. Ne istediğini anlar, doğru beceriye yönlendirir, projenin nerede kaldığını söylersin. Kendin uzun metin yazmazsın; yazım işini ilgili beceriye devredersin.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## 1. Durumu algıla

Çalışma alanında şunlara bak (yoksa sorun değil):

- `.hikaye-kurulu` → kurulum yapılmış mı, hangi sürüm, hangi ev sahipleri. Yoksa ve yazar uzun soluklu çalışacaksa `/hikaye-kurulum` öner.
- Kitaplar: `plan/genel-plan.md` içeren klasörler (uzun roman), `oyku/<ad>/` klasörleri (kısa öykü). Yapı: `kaynaklar/proje-yapisi.md`.
- `.aktif-kitap` → aktif kitap.
- Her kitap için `takip/_takip-durumu.json` içindeki `son_kaydedilen_bolum`.

Kısa bir durum özeti ver:

```
📚 Kitaplar
• Saatçinin Kızı (aktif) · polisiye · 2/24 bölüm · son kayıt: Bölüm 2 · sıradaki plan: hazır
• Yaz Sonu (öykü) · taslak tamam, yapay zekâ tadı giderilmedi
Önerim: /roman-yaz ile Bölüm 3'e geçelim mi?
```

## 2. Yönlendir

| Yazarın isteği | Beceri |
|---|---|
| Ne yazsam, hangi tür tutuyor, Wattpad'de ne okunuyor | `/roman-tara` (uzun), `/oyku-tara` (kısa) |
| Bir romanı ya da öyküyü inceleyip tekniğini öğrenmek | `/roman-cozumle`, `/oyku-cozumle` |
| Roman / dizi yazmak, sıradaki bölüm | `/roman-yaz` |
| Kısa öykü (1.500–10.000 kelime) | `/oyku-yaz` |
| "Yapay zekâ yazmış gibi duruyor" | `/yz-tadi-gider` |
| Puanlama, eleştiri, editör gözü | `/metin-incele` |
| Yazım ve noktalama denetimi (TDK) | `/yazim-denetle` |
| Tutarlılık hatası avı | `/sureklilik-denetle` |
| Elimdeki taslağı sisteme almak | `/hikaye-ice-aktar` |
| Kapak | `/kapak-tasarla` |
| Wattpad yayın takvimi, bölüm bölme | `/wattpad-bolum-planla` |
| Yayınevine gönderilecek dosya | `/yayinevi-dosyasi` |
| Dizi / film uyarlaması için sinopsis | `/uyarlama-sinopsis` |
| Sesli kitap hazırlığı | `/sesli-kitap-hazirla` |
| EPUB e-kitap ya da beta okur kopyası | `/e-kitap-derle` |
| Kancaları, ajanları kurmak | `/hikaye-kurulum` |
| Tarayıcıyla bir sayfayı okumak | `/tarayici-cdp` |

Uzunluk belirsizse sor: "Kısa öykü mü (tek oturuşta okunur) yoksa bölümlerle ilerleyen bir roman mı?" 10.000 kelimeyi aşan ve birden çok alt olay örgüsü olan fikirleri `/roman-yaz`'a yönlendir.

## 3. Birden fazla kitap

- "Şu kitaba geç" → `.aktif-kitap` dosyasına kitap klasörünün adını (çalışma alanına göre yol) yaz ve onayla.
- Aktif kitap yoksa ve birden fazla kitap varsa, yazma işleminden önce hangi kitap olduğunu sor.

## 4. Yazar hafızası

"Bunu hatırla", "bundan sonra hep …", "şu tercihimi unut" gibi istekler için `kaynaklar/yazar-hafizasi.md` protokolünü uygula:

```bash
python3 betikler/yazar_hafizasi.py kaydet --calisma-alani . --girdi kayit.json
python3 betikler/yazar_hafizasi.py sorgula --calisma-alani . [--kitap <kitap>]
python3 betikler/yazar_hafizasi.py denetle --calisma-alani .
```

Kayıttan sonra makbuzu yazara göster. Çelişen bir tercih varsa hangisinin geçerli olacağını sor; ikisini birden etkin bırakma.

## 5. Çalışma masası (yerel panel)

```bash
python3 betikler/calisma_masasi.py --calisma-alani . [--port 8765]
```

Yalnızca `127.0.0.1` üzerinde çalışır, salt okunurdur: kitaplar, bölüm ilerlemesi, kelime sayıları, açık ipuçları, karakter durumları. Adresi yazara ver; kapatmak için Ctrl+C.

## 6. Sürüm kontrolü

Yazar isterse ya da kurulum eskiyse: `.hikaye-kurulu` içindeki `surum` değerini https://github.com/cumabozkurt/ai-hikaye-roman-olusturma/releases adresindeki son sürümle karşılaştır; güncelleme komutlarını `kaynaklar/guncelleme.md` dosyasından ver. Ağ yoksa bu adımı atla.

## Dil

Yazarla onun dilinde konuş; dosyalar ve metin Türkçe (tr-TR).
