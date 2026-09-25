# E-Kitap Rehberi

## Biçimler

| Biçim | Ne için | Not |
|---|---|---|
| EPUB 3 | Google Play Kitaplar, Apple Books, Kobo, Kindle (KDP EPUB kabul eder), yerli e-kitap mağazaları | Yeniden akan metin; okur yazı boyutunu değiştirebilir. |
| HTML okuma kopyası | Beta okurlar, editöre hızlı önizleme, telefonda okuma | Tek dosya; e-posta ekiyle gönderilebilir, gece modu vardır. |
| PDF / Word | Yayınevi dosyası | Bu beceri üretmez; `/yayinevi-dosyasi` kullanın. |

## Teslim listesi

- [ ] Kitap adı ve yazar adı künyede, kapakta ve mağaza formunda birebir aynı.
- [ ] Kapak: dikey, en az 1600×2560 piksel, JPG ya da PNG; küçük boyutta (telefondaki mağaza listesinde) ad okunuyor.
- [ ] Bitmemiş metin işareti yok (`metin_analizi.py` ve derleme uyarısı temiz).
- [ ] Bölüm başlıkları tutarlı biçimde (`# 1. Bölüm — Başlık`).
- [ ] Sahne geçişleri `* * *` ile işaretli; boş satır tek başına sahne geçişi sayılmaz.
- [ ] Diyaloglar konuşma çizgisiyle (—) başlıyor; her replik ayrı paragraf.
- [ ] EPUBCheck hatasız ya da hatalar yazara bildirildi.
- [ ] ISBN: Türkiye'de ISBN, Kültür ve Turizm Bakanlığı Kütüphaneler ve Yayımlar Genel Müdürlüğü bünyesindeki Türkiye ISBN Ajansı üzerinden alınır; basılı kitap ve e-kitap için ayrı numara gerekir. Mağazaların bir kısmı kendi kimlik numarasıyla ISBN'siz yayına da izin verir; yazara güncel koşulları mağazadan doğrulamasını söyleyin.
- [ ] Telif sayfası (isteğe bağlı): "© Yıl Ad Soyad. Bütün hakları saklıdır." ve varsa yayıncı bilgisi.

## Beta okur kopyası

HTML kopyası, beta okurlara gönderilecek en pratik biçimdir. Gönderirken okurlara 3–5 somut soru ekleyin (ör. "Hangi bölümde okumayı bıraktınız?", "Katilin kim olduğunu ilk ne zaman tahmin ettiniz?"). `metin-incele` becerisinin okur paneli (`kaynaklar/okur-paneli.md`) soruları seçmek için kullanılabilir.

## Sınırlar

Derleyici bilinçli olarak küçük bir Markdown alt kümesini destekler. Tablo, görsel, dipnot ve iç bağlantı gereken kitaplar için pandoc (`pandoc metin/*.md -o kitap.epub --metadata lang=tr`) daha uygundur.
