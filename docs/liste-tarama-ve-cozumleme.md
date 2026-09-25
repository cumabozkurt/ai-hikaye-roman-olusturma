# Pazar taraması ve çözümleme

## Tarama (`roman-tara`, `oyku-tara`)

Amaç, "hangi tür, hangi okur, hangi açı?" sorusuna veriyle yaklaşmaktır.

1. **Wattpad herkese açık API'si** (`liste_tara.py`): tür ve etiket aramaları, en çok okunanlar, sık etiketler, ortanca bölüm sayısı, tamamlanma oranı, oy/okunma oranı. Wattpad'in dil alanı Türkçe öykülerde güvenilir olmadığından Türkçe süzgeci başlık, etiket ve tanıtımdaki Türkçe harf ve sözcüklerle yapılır; Azerice (ə) ayrılır. İstekler arasında 1 saniye beklenir, oturum ya da kişisel veri kullanılmaz.
   - **Erişim:** Wattpad Türkiye'de Temmuz 2024'ten beri erişime kapalıdır. Türkiye'deki bir ağdan betik bağlantı hatası verir; bu durumda `--girdi` ile kayıtlı bir yanıt kullanılabilir. Wattpad verisi bugün ağırlıkla yurt dışındaki Türkçe okuru yansıtır; rapor bunu belirtir.
2. **Kitap mağazaları** (Kitapyurdu, D&R, idefix, BKM Kitap, Amazon.com.tr): otomatik isteklere çoğunlukla kapalıdır (403) ya da içeriği JavaScript ile yükler. `tarayici-cdp` becerisi yazarın kendi, ayrı profilli tarayıcısıyla sayfayı açar ve yalnızca görünen metni okur.
3. **Web araması** son çaredir; bulunan her veri kaynağıyla yazılır, veri uydurulmaz.

Rapor sonunda gerekçeli bir tür ve konu önerisi yer alır; karar yazarındır.

## Çözümleme (`roman-cozumle`, `oyku-cozumle`)

Kaynak metin bir kez okunur; sonraki aşamalar diske yazılmış özetleri kullanır.

1. `bolum_dizini.py`: Türkçe bölüm başlıklarını ("BÖLÜM 1", "Bölüm Yedi: Kapı", "1. Bölüm", Önsöz, Epilog…) tanır, içindekiler bloğunu atar, satır aralıklarını, kelime sayılarını ve SHA-256 özetlerini yazar.
2. `cozumleme_calismasi.py plan`: ilk üç bölümden sonrası en çok üç bölümlük gruplara ayrılır; her grup için aralık özeti verilir.
3. `bolum-cikarici` ajanı her grubu okuyup şemaya uygun JSON üretir; `kaydet` şemayı doğrular (uzun alıntıyı telif nedeniyle reddeder) ve özetleri yazar. Kaynak metin plan alındıktan sonra değiştiyse kayıt reddedilir.
4. Aşamalar: yapı, karakter ve ilişkiler (`iliski_semasi.py` ile Mermaid şeması), duygu mekanizmaları, üslup profili, rapor.
5. `ilham_dizini.py`: çözümlenmiş kitapların duygu mekanizması kartlarını etiketle sorgulanabilir bir kütüphaneye dönüştürür. Kartlar soyuttur; özgün eserin adları, olay zinciri ve cümleleri yeni metne taşınmaz.

Çözümleme yalnızca yazarın okuma ve öğrenme amacıyla kullanabileceği metinlerle yapılmalıdır; çıktılar başkasına ait metni çoğaltmaz.
