---
name: sesli-kitap-hazirla
description: "Roman ya da öyküyü sesli kitaba hazırlar: seslendirme için temizlenmiş metin, bölüm başına süre tahmini, özel ad ve yabancı sözcükler için telaffuz sözlüğü, karakter ses kartları, seslendirmen ya da metin okuma (TTS) notları ve Storytel/Audible teslim kontrol listesi. Tetikleyiciler: /sesli-kitap-hazirla, \"sesli kitap yapmak istiyorum\", \"seslendirme metni\", \"telaffuz listesi\"."
license: MIT
compatibility: "Python 3.11+."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.0.0", "ust-kaynak": "yeni"}
---

# sesli-kitap-hazirla: Sesli Kitap Hazırlığı

Kitabı bir seslendirmenin ya da metin okuma motorunun hatasız okuyacağı hâle getirirsin. Anlatıyı değiştirmezsin; seslendirme katmanı hazırlarsın.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/sesli-kitap-rehberi.md` dosyasını oku.

## Akış

1. **Hazırla:**

```bash
python3 betikler/sesli_kitap_hazirla.py --proje <kitap> [--hiz 150]
python3 betikler/sesli_kitap_hazirla.py --dosya oyku/<ad>/metin.md
```

`<kitap>/sesli-kitap/` altında `seslendirme/*.txt`, `sure.md`, `telaffuz.md` oluşur.

2. **Telaffuz sözlüğü:** `telaffuz.md` adaylarını gözden geçir; gerçekten özel ad olanları tut (cümle başındaki sıradan sözcükleri sil), her biri için okunuşu hece ve vurguyla yaz (`Kuzguncuk — kuz-gun-cuk`). Sayıları nasıl okunacağına göre yaz: `03.14` → "üçü on dört geçe"; `1987` → "bin dokuz yüz seksen yedi". Yazara belirsizleri sor.
3. **Karakter ses kartları:** Her ana karakter için yaş, bölge/ağız, konuşma temposu, ses rengi ve tipik ifadesi (`kaynaklar/sesli-kitap-rehberi.md` şablonu). Takip kayıtları ve `kurgu/karakterler/` kaynak alınır.
4. **Seslendirme notları:** Uzun cümleleri, okurken nefesi zorlayan yapıları ve yalnızca görsel olarak anlaşılan öğeleri (mesaj ekranı, tablo, dipnot) işaretle; yazara sesli karşılık öner. Metni yazar onaylamadan değiştirme.
5. **Rapor:** toplam süre, dosyalar, telaffuz sözlüğünde doldurulacaklar, teslim kontrol listesi.
