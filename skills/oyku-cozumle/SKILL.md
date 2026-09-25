---
name: oyku-cozumle
description: "Bir kısa öyküyü çözümler: açılış kancası, paragraf paragraf merak ve duygu eğrisi, dönüm noktasının hazırlanışı, karakter tasarımı, ilişkiler, son paragrafın etkisi ve yeniden kullanılabilir teknikler. Tetikleyiciler: /oyku-cozumle, \"bu öyküyü çözümle\", \"neden etkileyici\", \"tekniğini çıkar\"."
license: MIT
compatibility: "Python 3.11+. Kaynak metin yazarın yasal olarak eriştiği bir kopya olmalıdır."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.0.0", "ust-kaynak": "oh-story-claudecode/story-short-analyze"}
---

# oyku-cozumle: Kısa Öykü Çözümleme

Bir kısa öyküyü, yazarın kendi öyküsünde kullanabileceği tekniklere ayırırsın. Hedef: "Bu öykü okuru nasıl, hangi cümlelerle yakaladı ve nereye götürdü?"

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Çıktı: `cozumleme-kutuphanesi/oyku/<ad>/cozumleme.md` (yazar başka bir yer isterse orası; örn. `oyku/<kendi-oykusu>/ornek/<ad>.md`).

## Sınırlar

- Alıntılar kısa (en çok 2 cümle, bölüm başına); metnin tamamı çıktıya kopyalanmaz.
- Yalnızca soyut teknik aktarılır; olay, ad ve imza imgeler yeni öyküye taşınmaz.
- Metinde olmayanı uydurma.

## Akış

1. **Ölç:** `python3 betikler/metin_olcum.py <dosya>` (kelime sayısı). Paragrafları numarala (P1, P2 …).
2. **Açılış (`kaynaklar/cozumleme-olcutleri.md` §1):** ilk üç cümlede karakter, durum ve tuhaflık/eksiklik; okurun ilk sorusu.
3. **Paragraf haritası (§2):** her paragraf için tek satır: işlev (merak / bilgi / duygu / hazırlık / dönüm / yankı), gerilim 1–5, okurun o anki sorusu. Tablo hâlinde.
4. **Dönüm noktası (§3):** nerede, hangi hazırlık ipuçlarıyla (paragraf numaraları), okurun yanlış beklentisi neydi.
5. **Karakter (§4):** istek, korku, sır; nasıl tanıtıldı (eylem / diyalog / başkasının gözü); ilişkiler ve güç dengesi.
6. **Son (§5):** son paragrafın türü (görüntü, cümle, sessizlik, dönüş) ve bıraktığı duygu.
7. **Dil (§6):** anlatıcı, zaman, cümle ritmi, diyalog oranı, benzetme sıklığı; yapay zekâ tadı taşıyan kalıplar var mı.
8. **Teknik kartları:** yeniden kullanılabilir 3–5 teknik; her biri "Teknik — Nasıl çalışıyor — Kendi öykünde nasıl uygularsın (farklı bir örnekle)".

## Rapor

`kaynaklar/cozumleme-olcutleri.md` sonundaki şablonu kullan. Yazara özet olarak: tek cümlelik öncül, hedef duygu, dönüm, en güçlü 3 teknik.

## Akış bağlantıları

Öğrenilen tekniklerle yazmak için `/oyku-yaz`; tür ve yayın yeri için `/oyku-tara`.
