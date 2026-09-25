# Okur Paneli

Editör puanı "metin iyi mi?" sorusunu yanıtlar; okur paneli "kim, nerede okumayı bırakır?" sorusunu. Panel, metni farklı okur tiplerinin gözünden ayrı ayrı okumak ve her okurun **bıraktığı yeri** bulmak içindir. Okurlar gerçek kişiler değil, Türkiye'deki yaygın okur alışkanlıklarından türetilmiş örnek profillerdir.

## Kullanım

1. Metnin türüne ve yayın yoluna göre panelden **3 okur** seç (varsayılan: türün tutkunu + Wattpad okuru + yayınevi ilk okuru).
2. Her okur için metni baştan oku ve şunları yaz:
   - **Bırakma noktası:** okur hangi paragrafta telefonu bırakır ya da sayfayı çevirmez? Yoksa "sonuna kadar okur".
   - **Tutan an:** okuru en çok içine çeken cümle (alıntı).
   - **Soru:** okurun bölüm bitince aklında kalan merak sorusu. Soru yoksa kanca zayıftır.
   - **Tek cümlelik yorum:** okurun kendi ağzından, doğal Türkçeyle.
3. Panel sonuçlarını editör puanından **ayrı** bir tablo olarak ver; puanı değiştirmek için kullanma, öncelik listesine gerekçe olarak ekle.
4. Bir okur tipinin hep aynı yerde bıraktığı görülürse (ör. iki okur da 4. paragrafta), o bölüm öncelikli düzeltme listesinin ilk sırasına girer.

## Okurlar

### 1. Wattpad okuru (16–22 yaş, telefondan, gece)
- Bekler: ilk 3 paragrafta bir soru ya da çatışma, kısa paragraflar, bol diyalog, bölüm sonunda "bir bölüm daha" isteği.
- Bırakır: uzun betimleme bloklarında, geçmiş özetiyle açılan bölümlerde, 180 kelimeyi aşan paragraflarda.
- Sorar: "Bu ikisi ne zaman karşılaşacak?", "Kim o?"

### 2. Türün tutkunu (polisiye, fantastik ya da romantik; yılda 30+ kitap)
- Bekler: türün sözleşmesine saygı (tür kartı), ama bildiği kalıbın yeni bir yorumu.
- Bırakır: ipucunu okurdan saklayan hilelerde, "kolay çözülen" düğümlerde, türün klişesi hiç yorumlanmadan kullanıldığında.
- Sorar: "Bunu daha önce nerede okudum?", "Yazar bana karşı dürüst mü?"

### 3. Yayınevi ilk okuru (dosya okuru, günde onlarca dosya)
- Bekler: ilk sayfada özgün bir ses, temiz yazım, net bir öncül; üst yazıdaki vaadin metinde karşılığı.
- Bırakır: ilk sayfada yazım hatası yığınında, yapay zekâ kalıplarında, ilk 5 sayfada hiçbir şey olmadığında.
- Sorar: "Bu kitabın rafı ve okuru belli mi?", "Yazar bir sonraki kitabı da yazabilir mi?"

### 4. Edebiyat dergisi okuru (öykü okuru, dil duyarlılığı yüksek)
- Bekler: kelime seçiminde özen, alt metin, açık uçlu ama tatmin eden son, gereksiz açıklama yok.
- Bırakır: duyguyu adlandıran cümlelerde ("çok üzgündü"), özet sonlarda, ders veren kapanışlarda.
- Sorar: "Bu öykü neyi söylemeden söylüyor?"

### 5. Sesli kitap dinleyicisi (yolda, kulaklıkla)
- Bekler: kim konuşuyor hemen anlaşılsın, cümleler nefeste okunabilsin, sahne geçişleri sesle fark edilsin.
- Bırakır: uzun iç içe cümlelerde, konuşanın belli olmadığı diyalog dizilerinde, yalnızca görsel anlaşılan öğelerde (mesaj ekranı, tablo).
- Sorar: "Şu an kim konuşuyor?"

### 6. Gönülsüz okur (az kitap okuyan, dizi izleyen)
- Bekler: dizi hızında tempo, somut sahne, anlaşılır dil.
- Bırakır: soyut düşünce paragraflarında, çok sayıda karakterin aynı anda tanıtıldığı sahnelerde.
- Sorar: "Bu bir diziye uyarlansa ilk sahne ne olurdu?"

## Nesnel ölçümle birlikte okuma

`betikler/metin_analizi.py` çıktısı panelin sezgisini sayıyla destekler:

| Ölçüm | Hangi okur için önemli |
|---|---|
| Ateşman okunabilirlik 50'nin altı | Wattpad okuru, gönülsüz okur, sesli kitap dinleyicisi |
| Ortalama cümle 22 kelimeden uzun | Sesli kitap dinleyicisi, Wattpad okuru |
| Diyalog oranı %10'un altı (roman bölümü) | Wattpad okuru, gönülsüz okur |
| Yakın tekrarlar | Edebiyat dergisi okuru, yayınevi ilk okuru |
| Yalnızca görsel duyu | Edebiyat dergisi okuru |

Bu eşikler kural değil, bakılacak yeri gösteren işaretlerdir; kitabın bilinçli üslubu (`kurgu/ton.md`) her zaman önce gelir.

## Rapor biçimi

```
### Okur paneli
| Okur | Bırakma noktası | Tutan an | Aklında kalan soru |
|---|---|---|---|
| Wattpad okuru | Sonuna kadar | “Çünkü bu adam dün gece öldürüldü.” | Fotoğraftaki adam kim? |
| Yayınevi ilk okuru | 3. paragraf (tekrar eden “saat”) | … | … |
```
