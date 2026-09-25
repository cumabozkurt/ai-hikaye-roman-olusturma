---
name: e-kitap-derle
description: "Roman ya da öykü bölümlerini EPUB 3 e-kitaba ve tek dosyalık HTML okuma kopyasına derler: kapak, künye, içindekiler, sahne ayraçları, diyalog biçimi; bitmemiş metin işaretlerini ([TK], [DOLDUR]) yakalar ve Google Play Kitaplar, Kindle, Apple Books ve beta okur paylaşımı için teslim listesi verir. Pandoc gerekmez. Tetikleyiciler: /e-kitap-derle, \"EPUB yap\", \"e-kitap hazırla\", \"okuma kopyası\", \"beta okurlara gönder\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kütüphane)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.1.0", "ust-kaynak": "yeni"}
---

# e-kitap-derle: EPUB ve Okuma Kopyası

Bitmiş ya da beta okura gidecek metni okunabilir bir e-kitaba dönüştürürsün. Metni değiştirmezsin; derler, denetler ve teslim için eksikleri gösterirsin.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/e-kitap-rehberi.md` dosyasını sonuna kadar oku.

## Akış

1. **Hazırlık:** Kitap adı, yazar adı (künyede görünecek biçimiyle) ve varsa kapak görseli (`/kapak-tasarla` çıktısı, `.jpg` ya da `.png`, en az 1600×2560 piksel önerilir) yazardan alınır. Bölümlerde yazım ve yapay zekâ tadı denetimi yapılmadıysa önce `/yazim-denetle` ve `/yz-tadi-gider` öner; yazar istemezse devam et.
2. **Ön okuma ölçümü (isteğe bağlı ama önerilir):**

```bash
python3 betikler/metin_analizi.py <kitap>/metin/*.md
```

Bitmemiş metin işareti ya da çok yakın tekrarlar varsa yazara listele.

3. **Derle:**

```bash
python3 betikler/e_kitap_derle.py --proje <kitap> --yazar "Ad Soyad" [--kapak <kitap>/kapak/kapak.jpg]
python3 betikler/e_kitap_derle.py --dosya oyku/<ad>/metin.md --baslik "Öykü Adı" --yazar "Ad Soyad" --bicim html
```

Çıktılar varsayılan olarak `<kitap>/yayin/<kitap-adi>.epub` ve `.html` olur. Bölüm sırası dosya adındaki numaradır (`bolum-001_…`); bölüm başlığı dosyadaki ilk `#` başlığıdır.

4. **Bitmemiş işaretler:** Betik `[TK]`, `[DOLDUR]`, `⟦…⟧`, `TODO` bulursa çıkış kodu 1 ile durur ve satırları listeler. Yazar yalnızca beta okuma kopyası istiyorsa `--taslak` ile derle ve raporda "taslak" olarak belirt.
5. **Doğrulama:** Mümkünse W3C EPUBCheck ile doğrula (`java -jar epubcheck.jar <dosya>.epub`); yoksa HTML kopyasını tarayıcıda açıp içindekiler bağlantılarını ve Türkçe karakterleri kontrol et.
6. **Rapor:** üretilen dosyalar ve boyutları, bölüm sayısı, uyarılar, `kaynaklar/e-kitap-rehberi.md` içindeki teslim listesinden eksik kalanlar (ISBN, kapak ölçüsü, künye bilgileri).

## Dikkat

- Yeniden üretilebilir çıktı için `SOURCE_DATE_EPOCH` ortam değişkenini ayarla; aynı girdi aynı EPUB'u verir.
- Desteklenen Markdown alt kümesi dışındaki öğeler (tablo, görsel, dipnot) düz metin olarak geçer; kitapta bunlar varsa yazarı uyar ve gerekirse pandoc öner.
- Yazarın izni olmadan metni e-kitap mağazasına yükleme ya da paylaşma; bu beceri yalnızca dosyayı hazırlar.

## Dil

Yazarla onun dilinde konuş; e-kitap üst verisi `tr` dil koduyla, künye ve içindekiler Türkçe üretilir.
