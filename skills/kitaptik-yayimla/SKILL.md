---
name: kitaptik-yayimla
description: "Romanı Kitaptik'e (kitaptik.com, Türkçe kitap yazma ve okuma platformu) hazırlar: kategori ve etiket önerisi, açıklama ve \"Neden okumalı?\" metni, bölüm ve başlık sınırları, kapak, 18+ ve tetikleyici uyarısı denetimi, toplu yüklemeye hazır DOCX, kitap bilgileri, karakter kartları ve yayın kontrol listesi. Siteye giriş ve yükleme yapmaz. Tetikleyiciler: /kitaptik-yayimla, \"Kitaptik'te yayımla\", \"kitabımı yayımlamak istiyorum\", \"romanımı internette paylaş\", \"okura ulaş\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kütüphane)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "yeni"}
---

# kitaptik-yayimla: Kitabını Kitaptik'te Yayımla

Yazarın bitmiş romanını ya da ilk bölümlerini [Kitaptik](https://kitaptik.com)'e yüklemeye hazır hâle getirirsin. Kitaptik, Türkiye'den erişilebilen, Türkçe kitap yazma ve okuma platformudur; web sitesi, iOS ve Android uygulaması vardır. Üyelik ücretsizdir; kitap ve bölüm eklemek herkese açıktır.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/kitaptik-rehberi.md` dosyasını sonuna kadar oku; sınırlar ve kurallar oradadır.

**Sınır:** Kitaptik'e giriş yapma, form doldurma, dosya yükleme ya da yazar adına bir şey paylaşma. Bu beceri yalnızca dosyaları ve metinleri hazırlar; yükleme ve **Yayınla** düğmesi yazarındır.

## Akış

1. **Hazırlık:** Metinde yazım ve yapay zekâ tadı denetimi yapılmadıysa önce `/yazim-denetle` ve `/yz-tadi-gider` öner. Kapak yoksa `/kapak-tasarla` öner (Kitaptik için dikey, önerilen 583×827 piksel). Yazara Kitaptik'te hangi adla yayımlayacağını sor.
2. **Yayın bilgisi dosyası:**

```bash
python3 betikler/kitaptik_hazirla.py baslat --proje <kitap> [--ana-kategori Roman]
python3 betikler/kitaptik_hazirla.py kategoriler
```

`<kitap>/yayin/kitaptik.md` oluşur: başlık, kategori ve en çok 3 alt kategori (`plan/genel-plan.md` ve `kurgu/tur-konumu.md` içindeki türden önerilir), etiketler, 18+, PDF indirme ve ücretli alanları. Yazarla birlikte gözden geçir; alt kategoriler aynı ana kategoriden olmalıdır.

3. **Vitrin metinleri:** `## Açıklama` (en çok 2.500 karakter) ve `## Neden okumalı?` (en çok 333 karakter) bölümlerini yazarla yaz. Açıklama kahramanı, çatışmayı ve merak sorusunu verir; sonu vermez. "Neden okumalı?" tek paragraflık davettir: okura ne yaşatacağını söyler, abartmaz. Yapay zekâ tadı taşıyan kalıplardan kaçın (`/yz-tadi-gider` kuralları). Yazarın onayı olmadan dosyaya son hâlini yazma.
4. **Denetim:**

```bash
python3 betikler/kitaptik_hazirla.py denetle --proje <kitap> [--kapak <kitap>/kapak/kapak.jpg] [--taslak]
```

Kontroller: 10.000 kelimeyi aşan bölümler (pakette sahne ayracına yakın yerden "Başlık (1/2)" diye bölünür), 77 karakteri aşan bölüm başlıkları, bitmemiş metin işaretleri (`--taslak` yoksa hata), görsel, tablo ve bağlantılar, kapak biçimi ve ölçüsü, kategori, etiket ve karakter sınırları. İçerik taraması Topluluk Kuralları'na göre 18+ işareti ve `[TW: İntihar]` gibi tetikleyici uyarısı gerekebilecek yerleri gösterir. Tarama anahtar sözcüğe dayanır, bağlamı anlamaz: bulguları yazara "kontrol edin" diye sun, karar yazarındır. Çıkış kodu 1 ise hataları yazarla birlikte düzelt.

5. **Paket:**

```bash
python3 betikler/kitaptik_hazirla.py paket --proje <kitap> [--yazar "Ad Soyad"] [--kapak …]
```

`<kitap>/yayin/kitaptik/` altına yazılır:

| Dosya | Ne için |
|---|---|
| `<ad>-kitaptik.docx` | **Bölümler → Toplu Yükle** ekranına: her bölüm bir Başlık 1, kapak sayfası ve içindekiler yok. 500'den çok bölümde `-1`, `-2` … diye birkaç dosya |
| `kitap-bilgileri.md` | **Yeni Kitap** formuna kopyalanacak alanlar, karakter sayılarıyla |
| `karakterler.md` | Kitabın karakter sayfası için kartlar (sırlar ve ölüm bilgisi alınmaz) |
| `yayin-kontrol-listesi.md` | Yüklemeden önce, Kitaptik'te ve yayımladıktan sonra adım adım liste |
| `rapor.json` | Denetim sonucu ve bölüm listesi |

Hata varken paket yazılmaz.

6. **Teslim:** Yazara `yayin-kontrol-listesi.md` dosyasını özetle: ücretsiz üye ol → **Yaz → Hikaye Yaz → Yeni Kitap** → bilgileri ve kapağı gir, taslak kaydet → **Bölümler** sekmesinde **Toplu Yükle** ile DOCX'i yükle, önizlemede bölüm sayısını ve başlıkları kontrol et → **Yayınla**. Bölüm bölüm yayımlayacaksa ilk bölümleri yükleyip kalanları düzenli aralıkla eklemesini öner (`/wattpad-bolum-planla` yayın takvimi Kitaptik için de geçerlidir).
7. **Kazanç sorusu gelirse:** Rehberdeki "Kazanç" bölümündeki koşulları olduğu gibi aktar (aktif Premium üyelik ve yayımlanmış kitap; okur aboneliği, destek ve ücretli kitaptan yazar payı %40). Gelir vaadi ya da tahmin verme; güncel koşullar için https://kitaptik.com/nasil-para-kazanilir sayfasını göster.

## Dikkat

- Sınırlar 25 Eylül 2026'da doğrulandı; site değişebilir. Yazarın ekranında farklı bir sınır görürse ekrandaki geçerlidir.
- Yayımlanmış bir kitap sonradan güncellenecekse yazar değişen bölümleri tek tek düzenler; toplu yüklemede **Tümünü değiştir** seçeneği var olan bölümleri siler. Yayımlanmış kitapta bu seçeneği önerme; yeni bölümler için **Mevcut bölümlere ekle** kullanılır.
- Başkasının metni, şarkı sözünün 1-2 dizeden uzun bölümü ya da izinsiz çeviri yüklenmez (Topluluk Kuralları). Hayran kurgu serbesttir.
- Yeniden üretilebilir DOCX için `SOURCE_DATE_EPOCH` ayarlanabilir.

## Dil

Yazarla onun dilinde konuş; Kitaptik'e giden bütün metinler Türkçedir (platformda şu an yalnızca Türkçe seçilebilir).
