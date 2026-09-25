# Kitaptik ile Yayımlama

Bu paketle yazdığınız romanı ya da öyküyü okura ulaştırmanın en kısa yolu: **[Kitaptik](https://kitaptik.com)**. Kitaptik, Türkiye'den erişilebilen, Türkçe kitap yazma ve okuma platformudur; web sitesi, iOS ve Android uygulaması vardır. Üyelik ücretsizdir, kitap ve bölüm eklemek için seviye ya da onay beklemezsiniz.

`/kitaptik-yayimla` becerisi kitabınızı Kitaptik'in yazar ekranına hazırlar. **Siteye giriş yapmaz, form doldurmaz, dosya yüklemez**; yükleme ve **Yayınla** düğmesi sizin elinizdedir.

> Bu sayfadaki bilgiler 25 Eylül 2026'da kitaptik.com'un herkese açık sayfalarından ve yazar ekranındaki sınırlardan doğrulandı. Platform değişebilir; karar vermeden önce bağlantısı verilen sayfayı açın. Bu sayfada okunma sayısı, kazanç tahmini ya da okur yorumu yoktur ve olmayacaktır: sonuç kitabınıza ve emeğinize bağlıdır.

## İçindekiler

- [Neden Kitaptik?](#neden-kitaptik)
- [Beş adımda yayın](#beş-adımda-yayın)
- [Paket neler üretir?](#paket-neler-üretir)
- [Denetim neye bakar?](#denetim-neye-bakar)
- [Sınırlar](#sınırlar)
- [Topluluk Kuralları'ndan yazarı ilgilendirenler](#topluluk-kurallarından-yazarı-ilgilendirenler)
- [Haklarınız](#haklarınız)
- [Kazanç koşulları](#kazanç-koşulları)
- [Sık sorulanlar](#sık-sorulanlar)

## Neden Kitaptik?

Kitaptik'te doğrulanan ve yazar için işe yarayan özellikler:

| Yazar için | Okur için |
|---|---|
| Ücretsiz üyelik; kitap ve bölüm eklemek herkese açık | Çevrim içi okuma: temalar, kaldığı yerden devam |
| Zengin metin düzenleyici; Word'den tek bölüm ya da **Toplu Yükle** | Ücretsiz PDF indirme (yazar kapatabilir) |
| Taslak olarak saklama, bölümleri tek düğmeyle yayımlama | Uygulamada çevrim dışı okuma |
| Karakter ve tanıtım sayfaları, ortak yazar | Sesli okuma ve hızlı okuma modları |
| Kitap istatistik sayfası: görüntülenme, okunma, indirme, beğeni, kütüphane ve liste sayıları | Paragraf paragraf yorum, beğeni, 1-5 yıldız puan |
| Kategori ve liste sıralamaları (popüler, çok beğenilen, çok yorumlanan, en yüksek puanlı, yükselen yıldızlar, yeni bölüm eklenenler) | Kütüphane (Okunacak / Okunuyor / Okundu) ve okuma listeleri |
| Takipçilere yeni bölüm bildirimi | Alıntı kartları, yazar takibi |
| Aktif Premium üyelikle okur aboneliği, destek ve ücretli kitaptan yazar payı %40 | Web, iOS ve Android |

Kaynak sayfalar: [Nasıl Yazar Olunur](https://kitaptik.com/nasil-yazar-olunur) · [Kullanım Kılavuzu](https://kitaptik.com/yardim-merkezi/kullanim-kilavuzu) · [Sık Sorulan Sorular](https://kitaptik.com/yardim-merkezi/sss) · [Tanıtım](https://kitaptik.com/tanitim) · [Mobil Uygulamalar](https://kitaptik.com/mobil-uygulamalar) · [Nasıl Para Kazanılır](https://kitaptik.com/nasil-para-kazanilir)

Wattpad'e Türkiye'den Temmuz 2024'ten beri mahkeme kararıyla erişilemiyor ([platformlar](../paylasilan/kaynaklar/platformlar-turkiye.md)). Bölüm bölüm yayın, düzenli takvim ve ilk bölüm kancası gibi bu paketteki Wattpad ölçüleri Kitaptik'te de geçerlidir.

## Beş adımda yayın

Kitap klasörünüzde (ör. `saatcinin-kizi/`) ajanınıza "Kitabımı Kitaptik'te yayımlamak istiyorum" demeniz yeterli. Beceri şu adımları sizinle yürütür; betikleri doğrudan da çalıştırabilirsiniz:

```bash
# 1. Yayın bilgisi dosyası: kategori, alt kategori, etiket önerisi ve açıklama taslağı
python3 skills/kitaptik-yayimla/betikler/kitaptik_hazirla.py baslat --proje saatcinin-kizi

# 2. yayin/kitaptik.md dosyasında "Açıklama" ve "Neden okumalı?" bölümlerini ajanla birlikte yazın

# 3. Denetim: sınırlar, kapak, bitmemiş metin, 18+ ve tetikleyici uyarısı sinyalleri
python3 skills/kitaptik-yayimla/betikler/kitaptik_hazirla.py denetle --proje saatcinin-kizi

# 4. Paket: toplu yükleme DOCX'i, kitap bilgileri, karakter kartları, kontrol listesi
python3 skills/kitaptik-yayimla/betikler/kitaptik_hazirla.py paket --proje saatcinin-kizi --yazar "Ad Soyad"
```

**5. Kitaptik'te (elle, kendi hesabınızla):**

1. Ücretsiz üye olun ve e-postanızı doğrulayın.
2. **Yaz → Hikaye Yaz → Yeni Kitap**: `kitap-bilgileri.md` içindeki alanları kopyalayın, kapağı yükleyin, taslak olarak kaydedin.
3. **Bölümler** sekmesinde **Toplu Yükle**: `<ad>-kitaptik.docx` dosyasını seçin. Önizlemede bölüm sayısını, başlıkları ve kelime sayılarını kontrol edip **İçe Aktar**.
4. **Yayınla**: taslak bölümler okura açılır.
5. Kitap bittiyse **Kitap Tamamlandı** anahtarını açın; karakter kartlarını kitabın karakter sayfasına ekleyin.

Bölüm bölüm yayımlamak isterseniz ilk bölümleri yükleyip kalanları düzenli aralıklarla ekleyin; `/wattpad-bolum-planla` becerisinin yayın takvimi bunun için de kullanılabilir.

## Paket neler üretir?

`<kitap>/yayin/kitaptik/` klasörüne:

| Dosya | İçerik |
|---|---|
| `<ad>-kitaptik.docx` | Toplu yükleme için: her bölüm bir Başlık 1, kapak sayfası ve içindekiler yok; ara başlıklar kalın, alıntılar italik, sahne ayracı `* * *`. 10.000 kelimeyi aşan bölümler sahne ayracına yakın yerden "Başlık (1/2)" diye bölünür, 77 karakteri aşan başlıklar kısaltılır. 500'den çok bölümde `-1`, `-2` … diye birkaç dosya |
| `kitap-bilgileri.md` | Yeni Kitap formunun alanları, karakter sayılarıyla |
| `karakterler.md` | Karakter kartları: ad, soyad, rol (Ana karakter, Yardımcı, Düşman, Anlatıcı, Diğer) ve kısa tanıtım. Sırlar, yaralar ve ölüm bilgisi spoiler olmasın diye alınmaz |
| `yayin-kontrol-listesi.md` | Yüklemeden önce, Kitaptik'te ve yayımladıktan sonra yapılacaklar |
| `rapor.json` | Denetim sonucu ve bölüm listesi (başlık, kelime, kaynak dosya) |

Denetimde hata varsa hiçbir dosya yazılmaz. Üretilen DOCX, web uygulamalarında Word dosyalarını okumak için yaygın kullanılan açık kaynak [mammoth](https://github.com/mwilliamson/mammoth.js) kitaplığıyla ve LibreOffice ile test edilir: Kitaptik'in "her Başlık 1 yeni bölüm" kuralıyla okunduğunda bölüm başlıkları ve kelime sayıları rapordakiyle birebir aynı çıkar.

## Denetim neye bakar?

| Düzey | Örnek |
|---|---|
| **Hata** (paket yazılmaz) | Bitmemiş metin işareti (`[TK]`, `TODO`; `--taslak` ile uyarıya düşer), geçersiz kategori ya da başka ana kategoriden alt kategori, 3'ten çok alt kategori, 2.500 karakteri aşan açıklama, ücretli kitapta 10 TL'den düşük fiyat, hareketli ya da 100×100'den küçük kapak, desteklenmeyen kapak biçimi (SVG gibi), 1.200'den çok bölüm |
| **Uyarı** | Bölünecek uzun bölüm, kısaltılacak başlık, görsel ve tablo (içe aktarmada düşer), bölüm içi bağlantı, 40 karakteri aşan ya da çok sayıda etiket, düşük çözünürlüklü, yatay ya da oranı farklı kapak, yetişkin içerik sinyali varken 18+ işaretsiz kitap, intihar geçen bölümde tetikleyici uyarısı yok |
| **Bilgi** | Kapak yok, "Neden okumalı?" boş, alt kategori ya da etiket yok, çoklu DOCX |

İçerik taraması anahtar sözcüklere dayanır ve bağlamı anlamaz: "kontrol edin" demektir, hüküm değildir. 18+ işaretleme kararı sizindir.

## Sınırlar

| Alan | Sınır |
|---|---|
| Word dosyası | Yalnızca `.docx` (eski `.doc` değil), en çok 20 MB; görseller alınmaz |
| Toplu yükleme | Her Başlık 1 yeni bölüm; tek seferde en çok 500 bölüm, sonraki dosyalar **Mevcut bölümlere ekle** ile. **Tümünü değiştir** var olan bölümleri siler |
| Bölüm | En çok 10.000 kelime; başlık en çok 77 karakter |
| Kitap | En çok 1.200 bölüm; başlık en az 2 karakter |
| Açıklama / Neden okumalı? / Telif notu | 2.500 / 333 / 1.000 karakter |
| Kategori | Zorunlu; en çok 3 alt kategori, hepsi aynı ana kategoriden |
| Etiket | Virgül, `#` ya da `;` ile ayrılır; etiket başına en çok 40 karakter, en çok 30 etiket |
| Dil | Şu an yalnızca Türkçe |
| Kapak | JPEG, PNG, WebP, HEIC, AVIF; hareketsiz; en çok 20 MB; en az 100×100, önerilen 583×827 piksel (dikey) |

Ana kategoriler: Roman, Öykü, Şiir, Deneme, Mektup, Sözler (Aforizma), Kişisel Gelişim, Spiritüel (Dini), Dünya Klasikleri, Diğer ([kategoriler](https://kitaptik.com/kategoriler)). Alt kategori listesi: `kitaptik_hazirla.py kategoriler`.

## Topluluk Kuralları'ndan yazarı ilgilendirenler

Tam metin: [kitaptik.com/sayfa/topluluk-kurallari](https://kitaptik.com/sayfa/topluluk-kurallari)

- **18+ işareti zorunlu:** açık cinsellik, aşırı şiddet, yoğun küfür, madde kullanımı teması. Yanlış işaretlenen kitap kaldırılabilir.
- **Kesin yasak:** çocukların cinselleştirilmesi, cinsel saldırının yüceltilmesi, ensest ve hayvanlarla cinsellik, gerçek kişilerin cinselleştirilmesi.
- **İntihar ve kendine zarar:** teşvik eden, yücelten ya da yöntem anlatan içerik yasak; konuyu işleyen bölümün başına `[TW: İntihar]` gibi uyarı.
- **Kapak:** çıplaklık ve aşırı kan yok; başkasının çizimi izinsiz kullanılmaz.
- **Etkileşim:** kitapla ilgisiz etiket yığmak, "oy karşılığı oy" ve sahte okunma yasak.
- **Bağlantı:** bölümlerde reklam ya da başka siteye yönlendirme yok; kendi sosyal medya hesabınızı ya da basılı kitabınızı tanıtmak serbest.
- **Telif:** hayran kurgu serbest; kopya ve izinsiz çeviri yasak; şarkı sözünden en çok 1-2 dize.

Kurallarda yapay zekâ yardımıyla yazılmış metinler için ayrı bir madde yok (25 Eylül 2026). Metnin sahibi ve sorumlusu yine yazardır: bu paket yazımı destekler, yayımlanan her cümlenin kararı sizindir.

## Haklarınız

[Kullanım Şartları](https://kitaptik.com/sayfa/kullanim-sartlari)'na göre içeriğin sahipliği yazarda kalır. Kitaptik, hikâyeleri üçüncü tarafların üretken yapay zekâ modellerini eğitmek için satmayacağını taahhüt eder; site içi öneri ve yazım denetimi araçları için içerikleri analiz etme ve kapak, özet ya da bölümleri tanıtımda kullanma hakkını saklı tutar.

## Kazanç koşulları

Kaynak: [Nasıl Para Kazanılır](https://kitaptik.com/nasil-para-kazanilir) (25 Eylül 2026). Koşullar değişebilir; güncelini sayfadan okuyun.

- **Şart:** aktif Premium üyelik ve en az bir yayımlanmış kitap.
- **Kanallar:** okur aboneliği (yazarın belirlediği paketler ve abonelere özel içerik), kitaba ya da bölüme destek, ücretli kitap (fiyat en az 10 TL; yayımlanmış bölüm sayısında site ayarı olan bir alt sınır vardır).
- **Yazar payı:** %40. Reklam gelirinden yazar payı yoktur.
- **Ödeme:** en az 1.000 TL birikince IBAN'a TL olarak, moderatör onayıyla. Vergi yükümlülüğü yazara aittir.

Okur bulmanın ve kazancın garantisi yoktur. Kitaptik'in [yazarlık rehberi](https://kitaptik.com/nasil-yazar-olunur) düzenli yayının okurun kitabı takip etmesine yardım ettiğini, okunan, yorumlanan, beğenilen ve kitaplığa eklenen kitapların platformda daha çok öne çıktığını söylüyor. Bu paketin payına düşen, kitabı o okura hazır hâle getirmek.

## Sık sorulanlar

**Beceri kitabımı benim yerime yükler mi?** Hayır. Hesabınıza giriş yapmaz, şifre istemez, siteyle bağlantı kurmaz. Dosyaları hazırlar; yüklemeyi siz yaparsınız.

**Bölümlerim Wattpad için 2.000 kelimeye bölünmüştü, sorun olur mu?** Olmaz. Kitaptik'in sınırı bölüm başına 10.000 kelimedir; kısa bölümler olduğu gibi yüklenir.

**Kitabım bitmedi, yine de yayımlayabilir miyim?** Evet. İlk bölümleri yayımlayıp yeni bölümleri sonradan **Mevcut bölümlere ekle** ile ya da tek tek ekleyebilirsiniz. Bitmemiş metin işaretleri kalan bölümleri `--taslak` olmadan pakete almayın.

**Aynı kitabı yayınevine de gönderebilir miyim?** İçeriğin sahipliği sizde kalır. Ancak bazı yayınevleri ve yarışmalar çevrim içi yayımlanmış metni "yayımlanmış" sayar; göndermeden önce şartnameyi okuyun (`/yayinevi-dosyasi`).

**Kapak yok, ne yapayım?** `/kapak-tasarla` becerisi Kitaptik için dikey kapak önerir (583×827 piksel). Kapaksız da yayımlayabilirsiniz ama kapak okurun ilk gördüğü şeydir.
