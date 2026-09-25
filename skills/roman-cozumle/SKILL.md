---
name: roman-cozumle
description: "Bir romanı ya da Wattpad dizisini yapısal olarak çözümler: bölüm dizini, ilk üç bölümün derin incelemesi, bölüm özetleri, olay örgüsü, tempo, duygu mekanizmaları, karakterler, ilişki şeması (Mermaid) ve üslup profili. Sonuçlar kitaplar arası ilham kütüphanesine eklenir. Tetikleyiciler: /roman-cozumle, \"bu romanı çözümle\", \"yapısını çıkar\", \"neden bu kadar okunuyor\", \"ilham kütüphanesi\"."
license: MIT
compatibility: "Python 3.11+. Kaynak metin yazarın yasal olarak eriştiği bir kopya olmalıdır."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.1.0", "ust-kaynak": "oh-story-claudecode/story-long-analyze"}
---

# roman-cozumle: Roman Çözümleme

Sen bir kurgu yapısı çözümleyicisisin. Bir romanın **neden işlediğini** çıkarır, yazarın kendi kitabında kullanabileceği soyut mekanizmalara dönüştürürsün.

**Temel ilke:** Bölüm sınırları bir kez, mekanik olarak çıkarılır. Kaynak metin ardışık gruplar hâlinde bir kez okunur; o okumada hem bölüm bilgisi hem bölümler arası gözlem üretilir. Sonraki aşamalar diske yazılmış sonuçları kullanır, metni yeniden okumaz.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Çıktı klasörü: `cozumleme-kutuphanesi/<kitap-adi>/` (yapı: `kaynaklar/cikti-sablonlari.md`).

## Çözümleme sınırları

1. Yalnızca okunan metne ve var olan sonuçlara dayan; bilinmeyeni "metinde belirtilmemiş" diye yaz.
2. Kesin bilgiler bölüm numarası ve kısa konum ipucuyla (5–15 kelime) desteklenir; çıkarımlar kanıt gücüyle işaretlenir.
3. Olayların gerçek sırası, metinde açıklanma sırası, okurun bildiği ve karakterin bildiği ayrı tutulur.
4. **Telif:** Yalnızca soyut mekanizma aktarılır. Özgün adlar, dünyaya özgü unsurlar, olay zinciri, imza sahneleri ve cümleler yeni metne taşınmaz. Alıntılar bölüm başına en çok iki kısa cümledir. Kaynak metin paylaşılmaz, depoya eklenmez.
5. Alanları doldurmak için olgu uydurma.

Yazara yazılan her şey (durup soru sorma, ilerleme, raporlar) `kaynaklar/yazara-anlatim.md` biçimindedir.

## Aşama 0: Hazırlık ve dizin

Kitap adı, kaynak ve yazılı izin/erişim durumu yoksa sor. Metni `cozumleme-kutuphanesi/<kitap>/kaynak/metin.txt` olarak kaydet (UTF-8; Windows-1254 otomatik çözülür). Klasör zaten varsa önce salt okunur incele:

```bash
python3 betikler/mevcut_varliklari_incele.py --kok cozumleme-kutuphanesi/<kitap> --kisa
```

`dogrudan_kullan` → çözümleme hazır; metni okumadan kullan. `devam_et` → eksikleri tamamla. Var olan özetlerin üzerine yazılmaz.

```bash
python3 betikler/bolum_dizini.py --kaynak cozumleme-kutuphanesi/<kitap>/kaynak/metin.txt --cikti cozumleme-kutuphanesi/<kitap>/bolum-dizini.csv
python3 betikler/cozumleme_calismasi.py asama --kok cozumleme-kutuphanesi/<kitap> --asama 0
```

Dizin hata verirse (numara atlaması, başlık yok) kaynağı düzeltmeden devam etme.

## Aşama 1: İlk üç bölüm

İlk üç bölümü dizindeki satır aralıklarıyla oku ve `bolumler/ilk-uc-bolum.md` (açılış, kanca, okur sözleşmesi, karakter tanıtımı, bilgi dağıtımı, bölüm sonları) ile `hizli-bakis.md` yaz. Yazar tek seferde her şeyi istemediyse burada dur ve devam edip etmeyeceğini sor.

## Aşama 2: Bölüm grupları

```bash
python3 betikler/cozumleme_calismasi.py plan --kok cozumleme-kutuphanesi/<kitap>
```

Her grup en çok 3 bölüm ve 12.000 kelimedir. Her grup için `bolum-cikarici` ajanına dizindeki satır aralıklarını ver (ajan yoksa ana oturumda). Çıktı `bolum_dizini.py` içindeki `GRUP_SEMASI` biçiminde JSON'dur (her bölüm için 10–30 olay noktası). Kaydet:

```bash
python3 betikler/cozumleme_calismasi.py kaydet --kok cozumleme-kutuphanesi/<kitap> --girdi grup-4-6.json --aralik-ozeti <plan çıktısındaki değer>
```

Doğrulama hatasında grubu düzelt ya da daha küçük gruba böl. Bütün gruplar bitince `asama --asama 2`.

## Aşama 3: Olay örgüsü, tempo, duygu mekanizmaları

Yalnızca özetlerden ve önbellekten çalış. `olay-orgusu/hikaye-hatti.md` (ana ve yan hatlar, neden-sonuç), `olay-orgusu/tempo.md` (her bölüm için olay ilerlemesi 1–5, okur duygusu ve şiddeti 1–5, anlatım yoğunluğu 1–3) ve `olay-orgusu/duygu-mekanizmalari.md` (en güçlü en az üç mekanizma için `## DM-001: Başlık` kartları; `Etiketler:` ve `Mekanizma:` satırları zorunlu). Sonra `asama --asama 3`.

## Aşama 4: Karakterler, dünya, ilişkiler

`karakterler/<ad>.md`, `dunya/<konu>.md`, `karakterler/iliskiler.md` (`| Kimden | Kime | İlişki | Bölüm | Not |` tablosu). Şema:

```bash
python3 betikler/iliski_semasi.py --kok cozumleme-kutuphanesi/<kitap>
python3 betikler/cozumleme_calismasi.py asama --kok cozumleme-kutuphanesi/<kitap> --asama 4
```

## Aşama 5: Rapor

`cozumleme-raporu.md` ve `ozet.md` (`kaynaklar/cikti-sablonlari.md`): ne çözümlendi, temel bulgular, okurun peşinden gittiği soru, hikâyenin nasıl ilerlediği, karakterler, okur ile karakter arasındaki bilgi farkı, tempo, temel mekanizmalar, alınabilecek teknikler, **alınmaması gerekenler**. Sonra `asama --asama 5`.

## Aşama 6: Üslup profili

`kaynaklar/uslup-profili.md` yöntemiyle, dizinden seçilen 4–6 bölümün belirli bölümlerini okuyarak `uslup.md` yaz; `asama --asama 6`. Bu profil yazarın kendi kitabında `kurgu/ton.md` için esin kaynağı olabilir, kopyalanmaz.

## İlham kütüphanesi (isteğe bağlı)

"İlham kütüphanesi", "kitaplar arası mekanizma" istenirse `kaynaklar/ilham-kutuphanesi.md`:

```bash
python3 betikler/ilham_dizini.py olustur --kutuphane cozumleme-kutuphanesi
python3 betikler/ilham_dizini.py sorgula --kutuphane cozumleme-kutuphanesi --etiket intikam --etiket aile
```

## Durum

```bash
python3 betikler/cozumleme_calismasi.py durum --kok cozumleme-kutuphanesi/<kitap>
```

## Akış bağlantıları

Çözümleme bitince: `/roman-yaz` (kitabın okur sözleşmesine esin), `/roman-tara` (pazar yönü), `/hikaye-ice-aktar` değil (o yazarın kendi taslağı içindir).
