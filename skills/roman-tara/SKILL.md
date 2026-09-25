---
name: roman-tara
description: "Türkiye roman pazarı ve Wattpad taraması: tür ve etiket eğilimleri, en çok okunan diziler, bölüm sayıları, okur profili ve yayın yolu (Wattpad, e-kitap, basılı, sesli kitap). Sonunda gerekçeli konu ve tür kararı önerir. Tetikleyiciler: /roman-tara, \"hangi tür tutuyor\", \"Wattpad'de ne okunuyor\", \"pazar araştırması\", \"ne yazsam\"."
license: MIT
compatibility: "Python 3.11+ ve internet erişimi (Wattpad herkese açık API). Mağaza listeleri için isteğe bağlı olarak tarayici-cdp."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "oh-story-claudecode/story-long-scan"}
---

# roman-tara: Roman Pazarı Taraması

Yazarın hangi türde, hangi okura, hangi yayın yoluyla yazacağına veriyle karar vermesine yardım edersin. Veri toplar, yorumlar, seçenekleri gerekçelendirirsin; kararı yazar verir.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Çıktı: çalışma alanında `pazar/roman-taramasi-GG-AA-YYYY.md`.

## Önce oku

- `kaynaklar/platformlar-turkiye.md` (Türkiye'deki platformlar, liste kaynakları, yayınevi yolu, telif).
- `kaynaklar/tur-kartlari/README.md`.
- `kaynaklar/tarama-yontemi.md` (veri kaynakları, sınırlar, rapor şablonu).

## Akış

1. **Soru:** Yazara sor: "Hangi türler aklınızda? Hedefiniz Wattpad'de okur toplamak mı, yayınevine dosya mı, e-kitap mı?" Belirsizse 3–4 tür seç.
2. **Wattpad verisi:** Her tür/etiket için:

```bash
python3 betikler/liste_tara.py --sorgu polisiye --sorgu gizem --adet 100 --cikti pazar/wattpad-polisiye.md
```

Wattpad Türkiye'de Temmuz 2024'ten beri erişime kapalıdır; Türkiye'deki bir ağdan betik bağlantı hatası verebilir. Bu durumda engeli aşmaya çalışma: mağaza listelerine (tarayici-cdp) ve web aramasına geç, Wattpad verisinin yurt dışındaki Türkçe okuru yansıttığını raporda belirt. Betik yalnızca herkese açık Wattpad arama API'sini düşük hızla kullanır, Türkçe öyküleri ayıklar, en çok okunanları, sık etiketleri, ortanca bölüm sayısını ve tamamlanma oranını çıkarır. Ağ yoksa ya da API yanıt vermiyorsa bunu açıkça söyle; veri uydurma.

3. **Kitap listeleri (isteğe bağlı):** Kitapyurdu, D&R, idefix, BKM Kitap, Amazon.com.tr çok satan listeleri otomatik erişimi engeller. Yazar isterse `/tarayici-cdp` ile yazarın kendi tarayıcısında sayfayı açıp okuyabilirsin; ya da yazardan listenin ekran görüntüsünü/metnini iste. Yayınevlerinin "yeni çıkanlar" ve ödül listeleri (ör. Sait Faik Hikâye Armağanı, Orhan Kemal Roman Armağanı) edebî eğilim için yardımcıdır.
4. **Yorum:** Her tür için `kaynaklar/tarama-yontemi.md` şablonu: talep işaretleri, rekabet yoğunluğu, okur profili, tipik uzunluk ve bölüm ritmi, farklılaşma alanı, risk.
5. **Karar önerisi:** En fazla üç seçenek, her biri: öncül fikri, hedef okur, yayın yolu, neden şimdi, en büyük risk. Yazar seçerse `/roman-yaz` yapı tartışmasına geç ve bulguları `kurgu/tur-konumu.md` için kullan.

## Dikkat

- Okunma sayısı kalite ölçüsü değildir; "görünürlük" diye yorumla.
- Tarama anındaki verilerdir; tarihi rapora yaz.
- Başka yazarların öykülerinden metin kopyalanmaz; yalnızca başlık, etiket ve sayısal veriler kullanılır.
- Yetişkin içerik (+18) oranı yüksek türlerde Wattpad içerik kurallarını hatırlat.
