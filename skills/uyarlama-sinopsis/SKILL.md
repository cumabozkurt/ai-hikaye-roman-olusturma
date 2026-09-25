---
name: uyarlama-sinopsis
description: "Romanı dizi, film ya da dijital platform uyarlaması için sunuma hazırlar: tek cümlelik öncül (logline), bir ve üç sayfalık sinopsis, karakter kartları, sezon ve bölüm dökümü, ton ve referans önerisi, pazar notu. Türkiye dizi sektörünün (haftalık uzun bölüm, dijital platform kısa sezon) biçimlerine uyar. Tetikleyiciler: /uyarlama-sinopsis, \"dizi olur mu\", \"yapımcıya sunum\", \"logline yaz\", \"sezon planı\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca kelime ölçümü için)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "yeni"}
---

# uyarlama-sinopsis: Uyarlama Sunum Dosyası

Romanı bir yapımcının ya da platform içerik ekibinin 10 dakikada kavrayacağı bir sunuma dönüştürürsün. Kaynak kitabın planı, takip kayıtları ve karakter dosyaları senin ham maddendir.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/uyarlama-bicimleri.md` ve `kaynaklar/platformlar-turkiye.md` (§7) dosyalarını oku.

## Akış

1. **Biçim seç:** Yazara sor: haftalık televizyon dizisi, dijital platform dizisi, sinema filmi ya da kısa dikey dizi mi? Bilmiyorsa kitabın yapısına göre öner (çok karakterli aile dramı → haftalık dizi; 8–10 bölümlük gerilim → dijital platform; tek olaylı → film).
2. **Kaynakları oku:** `plan/genel-plan.md`, `kurgu/`, `takip/baglam.md` ve gerekirse bölüm özetleri. Kitap `/roman-cozumle` ile çözümlendiyse `cozumleme-raporu.md`.
3. **Üret** (`<kitap>/uyarlama/` altında, her biri ayrı dosya):
   - `logline.md`: 25–40 kelime; kahraman + istek + engel + risk.
   - `sinopsis-1-sayfa.md` (400–600 kelime) ve `sinopsis-3-sayfa.md` (1.200–1.800 kelime), sonu dâhil.
   - `karakterler.md`: ana kadro için kart (yaş, arzu, yara, sır, dönüşüm, oyuncu tipi yerine rol tanımı).
   - `sezon-plani.md`: biçime göre bölüm dökümü (her bölüm: başlık, A/B hikâyesi, bölüm sonu kancası). Kitapta olmayan yan hikâyeler "uyarlama önerisi" olarak işaretlenir.
   - `ton-ve-pazar.md`: ton, görsel dünya, mekânlar, hedef izleyici, benzer yapımlar (yalnızca ad), neden şimdi, yapım ölçeği notu.
4. **Ölç:** `python3 betikler/metin_olcum.py <kitap>/uyarlama/*.md` ile uzunlukları kontrol et.
5. **Rapor:** dosya listesi ve yazarın doldurması gerekenler (hak durumu, iletişim).

## Dikkat

- Uyarlama hakları yayınevi sözleşmesinde başkasına verilmiş olabilir; sunuma başlamadan yazara sor.
- Sunumu yapımcıya göndermeden önce eserin tarihli kanıtını (kayıt, noter) önermek iyi uygulamadır.
- Gerçek oyuncu adlarıyla "şu oynasın" önerisi yazmayı yazar açıkça istemedikçe yapma.
