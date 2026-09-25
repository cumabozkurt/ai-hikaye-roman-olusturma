---
name: yayinevi-dosyasi
description: "Türkiye'deki yayınevlerine roman ya da öykü dosyası hazırlar: künye, örnek bölümler (yaklaşık 30 sayfa), tam metin, bir sayfalık sinopsis, üst yazı, yazar biyografisi, yazım denetimi ve Word çıktısı; yayınevi seçimi, gönderim ve sözleşme öncesi kontrol listesi. Tetikleyiciler: /yayinevi-dosyasi, \"yayınevine göndereceğim\", \"sinopsis yaz\", \"üst yazı\", \"dosya hazırla\"."
license: MIT
compatibility: "Python 3.11+. Word çıktısı için isteğe bağlı pandoc."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "yeni"}
---

# yayinevi-dosyasi: Yayınevi Dosyası

Yazarın kitabını bir editörün masasına profesyonel bir dosya olarak koyarsın. Metni değiştirmezsin; paketler, şablonları doldurur, eksikleri gösterirsin.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/dosya-hazirligi.md` ve `kaynaklar/platformlar-turkiye.md` (§4–5) dosyalarını oku.

## Akış

1. **Hazırlık kontrolü:** Kitap bitti mi? (Türkiye'de ilk roman dosyaları çoğunlukla tamamlanmış metinle değerlendirilir.) Yazım denetimi yapıldı mı (`/yazim-denetle`)? Yapay zekâ tadı giderildi mi (`/yz-tadi-gider`)? Eksikse önce onları öner.
2. **Paket:**

```bash
python3 betikler/dosya_paketi.py --proje <kitap> --yazar "Ad Soyad" --tam [--docx] [--kelime-siniri 9000]
```

`<kitap>/yayinevi/GG-AA-YYYY/` altında künye, örnek bölümler, tam metin, şablonlar ve yazım denetimi özeti oluşur.

3. **Sinopsis:** `sinopsis.md` şablonunu kitabın planından ve takip kayıtlarından yararlanarak doldur: 400–600 kelime, sonu açıkça yazılmış. Yazara onaylat.
4. **Üst yazı ve biyografi:** Yazarın bilgileriyle doldur; abartılı övgü ("başyapıt", "çok satacak") kullanma.
5. **Yayınevi seçimi:** Yazarın türüne uygun yayınevlerini ve güncel dosya kabul koşullarını (e-posta, form, biçim, yanıt süresi) yazarla birlikte araştır; sayfa JavaScript ile çiziliyorsa `/tarayici-cdp`. Doğrulayamadığın koşulu "doğrulanmadı" diye işaretle.
6. **Biçim:** `kaynaklar/dosya-hazirligi.md` §Biçim (yayınevinin kendi kuralı önceliklidir).
7. **Rapor:** paket klasörü, yazım hatası sayısı, doldurulacak alanlar, gönderim kontrol listesi.

## Dikkat

- Aynı anda birden çok yayınevine gönderim yaygındır ama üst yazıda belirtmek nezakettir; yayınevinin kuralı "tek başvuru" ise uyulur.
- Sözleşme teklifinde telif oranı, baskı adedi, haklar (e-kitap, sesli kitap, çeviri, uyarlama) ve süre maddelerini yazara hatırlat; hukuki danışmanlık verme, bir uzmana ya da meslek birliğine yönlendir.
- Yapay zekâ desteği kullanıldıysa yayınevinin politikasını yazara sor ve dürüst beyanı öner.
