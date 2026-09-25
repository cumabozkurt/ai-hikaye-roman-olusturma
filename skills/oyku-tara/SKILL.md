---
name: oyku-tara
description: "Kısa öykü için yayın yeri ve eğilim taraması: Wattpad'deki kısa öyküler ve tek bölümlükler, edebiyat dergileri, öykü yarışmaları ve antolojiler; tür, uzunluk ve teslim koşullarına göre öneri. Tetikleyiciler: /oyku-tara, \"öykümü nereye göndereyim\", \"öykü yarışmaları\", \"kısa öykü eğilimleri\"."
license: MIT
compatibility: "Python 3.11+ ve internet erişimi (Wattpad herkese açık API)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "oh-story-claudecode/story-short-scan"}
---

# oyku-tara: Kısa Öykü Taraması

Kısa öyküsü için yazara uygun yayın yerini ve güncel eğilimi bulursun.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/platformlar-turkiye.md` (§6 Öykü yayın yolları) ve `kaynaklar/tur-kartlari/kisa-oyku.md` dosyalarını oku.

## Akış

1. **Öyküyü tanı:** tür, uzunluk (kelime), hedef (okur toplamak / ödül / dergide yayımlanmak / antoloji).
2. **Wattpad eğilimi:**

```bash
python3 betikler/liste_tara.py --sorgu "kısa hikaye" --sorgu kısahikaye --sorgu "<tür>" --adet 80
```

Ortanca bölüm sayısı 1–3 olan sonuçlar tek bölümlük öykülerin görünürlüğünü gösterir.

3. **Dergiler ve yarışmalar:** Güncel çağrılar sık değişir; yazarın izniyle web araması yap ya da `/tarayici-cdp` ile resmî sayfaları aç. Her aday için: son başvuru tarihi, kelime/sayfa sınırı, konu kısıtı, dosya biçimi, rumuz/anonimlik kuralı, daha önce yayımlanmamış olma şartı, ödül. Tarihi geçmiş çağrıyı önermeden önce doğrula; doğrulayamadıysan "doğrulanmadı" yaz.
4. **Eşleştirme:** Öykünün uzunluğu ve türüyle uyumlu en fazla 5 yer, her biri için uygunluk gerekçesi ve hazırlık listesi (uzunluk ayarı, rumuz, biyografi, dosya adı).
5. **Rapor:** `pazar/oyku-taramasi-GG-AA-YYYY.md`.

## Dikkat

- Aynı öyküyü aynı anda birden fazla yarışmaya göndermek çoğu şartnamede yasaktır; şartnameyi yazara hatırlat.
- Wattpad'de yayımlanan öykü birçok yarışmada "yayımlanmış" sayılır.
- Veri uydurma; çağrı bilgisi doğrulanamıyorsa belirt.

Yazmaya geçmek için `/oyku-yaz`.
