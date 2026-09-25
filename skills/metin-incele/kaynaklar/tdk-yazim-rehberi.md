# TDK Yazım ve Noktalama Rehberi (Kurgu İçin Özet)

Bu özet, Türk Dil Kurumu Yazım Kılavuzu'nun kurgu metinlerinde en sık karşılaşılan kurallarını içerir. Kesin kural ve güncel sözcük yazımı için: https://sozluk.gov.tr ve https://tdk.gov.tr/icerik/yazim-kurallari/ . Denetleyici: `yazim_denetle.py` (yazım), `noktalama_duzelt.py` (mekanik noktalama).

## 1. Ayrı yazılanlar

- **Bağlaç "de/da"** ayrı yazılır ve ünlü uyumuna uyar, ünsüz benzeşmesine girmez: "Ben *de* geldim", "Kitap *da* güzeldi". Bulunma eki "-de/-da/-te/-ta" bitişiktir: "evde", "sokakta". Sınama: sözcüğü çıkarınca anlam bozulmuyorsa bağlaçtır.
- **Bağlaç "ki"** ayrı yazılır: "Dedi *ki*…", "Öyle yorgundu *ki*…". Kalıplaşmış istisnalar bitişik: *belki, çünkü, sanki, oysaki, hâlbuki, mademki, meğerki, illaki*. İlgi eki "-ki" bitişiktir: "evdeki", "yarınki", "seninki".
- **Soru eki "mı/mi/mu/mü"** ayrı, kendinden sonraki eklerle bitişik yazılır: "Geliyor *musun*?", "Sen *mi* aradın?", "Yorgun *muydu*?".
- **"bir şey, her şey, hiçbir şey, şu an, her gün, bir gün, ya da, her biri, hiç kimse"** ayrı; **"hiçbir, birçok, birkaç, herhangi, bugün"** bitişik.

## 2. Kesme işareti

- Özel adlara gelen çekim ekleri kesmeyle ayrılır: *İstanbul'da, Ayşe'nin, Türkiye'ye, Wattpad'de*.
- Yapım ekinden önce kesme yoktur: *İstanbullu, Türkçe, Ankaralı*.
- Kurum, kuruluş, kurul ve iş yeri adlarına gelen ekler kesmeyle **ayrılmaz**: *Türk Dil Kurumunun, Kuzguncuk Saatçisine*.
- Kısaltmalar okunuşa göre ek alır: *TDK'nin, TBMM'de*.
- Sayılar: *3'üncü, 1987'de, 14.03'te*.

## 3. Büyük harf

- Cümle büyük harfle başlar. Konuşma çizgisinden sonraki replik de büyük harfle başlar.
- Replikten sonra gelen "dedi, diye sordu" küçük harfle devam eder: "— Geliyor musun? diye sordu."
- Hitap ve unvanlar ada bağlıysa büyük: *Ayşe Hanım, Nuri Usta, Doktor Selim*.
- Yön adları, özel ada dönüşmedikçe küçük: *kuzeye gitti*, ama *Kuzey Irak*.

## 4. Düzeltme işareti (şapka)

Anlam ayırt eden yerlerde kullanılır: *hâlâ* (henüz) / *hala* (babanın kız kardeşi); *kâr* / *kar*; *âlem* / *alem*. İnce "l" ve "k" belirten yerlerde: *dükkân, rüzgâr, hikâye, kâğıt, yâr*.

## 5. Diyalog biçimi

Türk yayıncılığında iki biçim yaygındır; kitap boyunca biri seçilir:

1. **Konuşma çizgisi (önerilen)**: Her replik yeni satırda "— " ile başlar. Anlatıcı eki replikten sonra virgülle ya da soru/ünlem işaretiyle bağlanır:

   ```
   — Yarın gelir misin? diye sordu Defne.
   — Gelirim, dedi Kerem. Ama erken değil.
   ```

2. **Tırnak**: “…” dizgi tırnağı; Wattpad'de düz tırnak da görülür. Tırnaklı diyalogda da her konuşan yeni paragraf açar.

Konuşma çizgisi uzun çizgidir (—); kısa çizgi (-) ya da en çizgisi (–) değildir. `noktalama_duzelt.py` satır başındaki "-" işaretini "— " olarak düzeltir.

## 6. Noktalama

- Virgül, nokta, iki nokta, noktalı virgül, soru ve ünlemden **önce boşluk olmaz**, **sonra boşluk olur**.
- Üç nokta (...) tamamlanmamış cümle ve duraksama için kullanılır; iki ya da dört nokta yanlıştır. Aşırı kullanımı yapay tat verir.
- Ünlem ve soru işareti yan yana: *Ne?!* kabul edilir, ama "!!!" çoğaltması kurguda özensiz görünür.
- Sıralı cümleler virgülle, bağlı cümleler noktalı virgülle ayrılabilir; uzun tire cümle içi ara söz için seyrek kullanılır.
- Sayılar: bine kadar olanlar ve cümle başındakiler yazıyla; saat ve tarih rakamla: *saat 03.14'te*, *14 Mart 1987*.

## 7. Sık yapılan yanlışlar

| Yanlış | Doğru | | Yanlış | Doğru |
|---|---|---|---|---|
| herkez | herkes | | yanlız | yalnız |
| yalnış | yanlış | | birşey | bir şey |
| herşey | her şey | | hiç bir | hiçbir |
| bir çok | birçok | | bir kaç | birkaç |
| tabi ki | tabii ki | | yada | ya da |
| malesef | maalesef | | orjinal | orijinal |
| şuan | şu an | | laboratuar | laboratuvar |
| makina | makine | | yinede | yine de |
| traş | tıraş | | kolleksiyon | koleksiyon |
| eşşek | eşek | | yapmışdı | yapmıştı |

## 8. Konuşma dili

Diyalogda bilinçli konuşma dili serbesttir ("gelicem", "napıyon", "bi dakka"); anlatıda ise ölçünlü dil beklenir. `yazim_denetle.py` bu yüzden gayriresmî biçimleri yalnızca anlatıda uyarı olarak raporlar.
