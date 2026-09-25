# Tarama Yöntemi

## Veri kaynakları

| Kaynak | Erişim | Ne verir |
|---|---|---|
| Wattpad arama API'si (`liste_tara.py`) | otomatik, herkese açık | okunma, oy, bölüm sayısı, etiketler, tamamlanma |
| Wattpad Türkiye etiket sayfaları | tarayıcı | güncel öne çıkanlar, "Wattys" kazananları |
| Kitapyurdu / D&R / idefix / BKM / Amazon.com.tr çok satanlar | tarayıcı (`/tarayici-cdp`) ya da yazarın ilettiği liste | basılı pazarda tür payı |
| Yayınevlerinin katalogları ve dosya kabul sayfaları | tarayıcı | hangi yayınevi hangi türü basıyor |
| Storytel / Audible Türkiye | tarayıcı | sesli kitapta öne çıkan türler |

Otomatik erişimi engelleyen sitelerde engeli aşmaya çalışma; tarayıcı yolunu ya da yazarın kendi verisini kullan.

## Tür değerlendirme şablonu

```markdown
### <Tür>
- Talep işaretleri: (ortanca okunma, en çok okunan dilimdeki okunma, etiket sıklığı)
- Rekabet: (öykü sayısı, tamamlanma oranı düşükse "bitirmek bile fark yaratır")
- Okur profili: (yaş, beklenti; tur-kartlari'ndan)
- Uzunluk ve ritim: (ortanca bölüm sayısı, önerilen bölüm uzunluğu)
- Farklılaşma alanı: (etiketlerde eksik kalan kombinasyonlar)
- Risk: (aşırı doygun kalıp, içerik kuralları, uyarlama/telif)
```

## Rapor şablonu

```markdown
# Roman Pazarı Taraması (GG.AA.YYYY)
## Özet (3 madde)
## Türler
## Karar önerileri (en çok 3)
## Yöntem ve sınırlar
```
