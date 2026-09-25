---
name: e-kitap-derle
description: "Roman ya da öykü bölümlerini EPUB 3 e-kitaba, yayınevine gönderilecek DOCX ve ODT dosyasına (A4, TNR 12, 1,5 aralık, sayfa numarası), A5 baskıya hazır HTML ve PDF'ye, HTML okuma kopyasına, TXT ve tek Markdown'a derler; bitmemiş metin işaretlerini yakalar, teslim listesi verir. Pandoc gerekmez. Tetikleyiciler: /e-kitap-derle, \"EPUB yap\", \"Word dosyası\", \"PDF hazırla\", \"okuma kopyası\", \"beta okurlara gönder\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kütüphane)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "yeni"}
---

# e-kitap-derle: EPUB, DOCX, ODT, PDF ve Okuma Kopyası

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
python3 betikler/e_kitap_derle.py --proje <kitap> --yazar "Ad Soyad" --bicim docx pdf
python3 betikler/e_kitap_derle.py --dosya oyku/<ad>/metin.md --baslik "Öykü Adı" --yazar "Ad Soyad" --bicim html
```

| `--bicim` | Çıktı | Ne için |
|---|---|---|
| `epub` | `<ad>.epub` (EPUB 3, EPUBCheck uyumlu) | Google Play Kitaplar, Kobo, Apple Books, Kindle (Send to Kindle EPUB kabul eder) |
| `html` | `<ad>.html` | Beta okur, tarayıcıda okuma |
| `docx` | `<ad>.docx` | Yayınevi ve editör: A4, Times New Roman 12, 1,5 satır aralığı, 2,5 cm kenar, iki yana yaslı ve girintili paragraflar, her bölüm yeni sayfada, kapak sayfasında yaklaşık kelime sayısı, üst bilgide "Soyad / Kitap adı", altta sayfa numarası, dil tr-TR |
| `odt` | `<ad>.odt` | Aynı gönderim biçimi, LibreOffice için |
| `yazdir` | `<ad>-baski.html` | A5 baskıya hazır sayfa (tarayıcıdan "PDF olarak kaydet") |
| `pdf` | `<ad>.pdf` | `yazdir` çıktısının yüklü Chrome/Chromium/Edge ile PDF'si; tarayıcı yoksa hata verir, `yazdir` kullan |
| `txt`, `md` | `<ad>.txt`, `<ad>-tam.md` | Düz metin, tek dosya Markdown |
| `hepsi` (varsayılan) | epub, html, docx, odt, yazdir | |

Çıktılar varsayılan olarak `<kitap>/yayin/` klasörüne yazılır (`--cikti` ile değişir). Bölüm sırası dosya adındaki numaradır (`bolum-001_…`); bölüm başlığı dosyadaki ilk `#` başlığıdır. Yayınevine gönderim kuralları için `/yayinevi-dosyasi` becerisine bak; her yayınevinin kendi şartı önce gelir. Kitabı Kitaptik'te (kitaptik.com) okura açmak için `/kitaptik-yayimla` kullan: oradaki toplu yükleme DOCX'i bu gönderim DOCX'inden farklıdır (kapak sayfası yok, her bölüm bir Başlık 1).

4. **Bitmemiş işaretler:** Betik `[TK]`, `[DOLDUR]`, `⟦…⟧`, `TODO` bulursa çıkış kodu 1 ile durur ve satırları listeler. Yazar yalnızca beta okuma kopyası istiyorsa `--taslak` ile derle ve raporda "taslak" olarak belirt.
5. **Doğrulama:** Mümkünse W3C EPUBCheck ile doğrula (`java -jar epubcheck.jar <dosya>.epub`); yoksa HTML kopyasını tarayıcıda açıp içindekiler bağlantılarını ve Türkçe karakterleri kontrol et. DOCX/ODT dosyasını Word ya da LibreOffice'te açıp ilk sayfayı, üst bilgiyi ve sayfa numaralarını göz ile denetle.
6. **Rapor:** üretilen dosyalar ve boyutları, bölüm sayısı, uyarılar, `kaynaklar/e-kitap-rehberi.md` içindeki teslim listesinden eksik kalanlar (ISBN, kapak ölçüsü, künye bilgileri).

## Dikkat

- Yeniden üretilebilir çıktı için `SOURCE_DATE_EPOCH` ortam değişkenini ayarla; aynı girdi aynı EPUB'u verir.
- Desteklenen Markdown alt kümesi dışındaki öğeler (tablo, görsel, dipnot) düz metin olarak geçer; kitapta bunlar varsa yazarı uyar ve gerekirse pandoc öner.
- Yazarın izni olmadan metni e-kitap mağazasına yükleme ya da paylaşma; bu beceri yalnızca dosyayı hazırlar.

## Dil

Yazarla onun dilinde konuş; e-kitap üst verisi `tr` dil koduyla, künye ve içindekiler Türkçe üretilir.
