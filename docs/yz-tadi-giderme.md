# Yapay zekâ tadını gidermenin somut yolu

"Yapay zekâ tadı", okurun "bunu makine yazmış" hissine kapıldığı tekrar eden kalıplardır. Tek tek yanlış değildirler; yoğunlaştıklarında metin sahte ve boş okunur. Bu paket onları bir yazım denetleyicisi (lint) gibi ele alır: satır ve sütun numarasıyla gösterir, bir düzeltme yönü önerir, metni kendisi değiştirmez.

## Denetçi neyi yakalar?

| Kural | Örnek | Önem |
|---|---|---|
| `degil-ama-donusu` | "Bu sadece bir saat değildi, geçmişin kapısıydı." | engelleyici |
| `bir-yandan-diger-yandan` | "Bir yandan korkuyor, diğer yandan merak ediyordu." | engelleyici |
| `olumsuzluk-dizisi` | "Korku yoktu. Tereddüt yoktu. Geri dönüş yoktu." | engelleyici |
| `ses-karsitligi` | "Sesi alçaktı ama herkesi susturdu." | engelleyici |
| `fragman-kapanis` | "Hiçbir şey eskisi gibi olmayacaktı." | engelleyici |
| `klise-yogunlugu` | derin nefes, hızla çarpan kalp, duran zaman | uyarı |
| `benzetme-yogunlugu`, `adeta-sanki-zinciri` | "adeta… sanki… gibi" | uyarı |
| `soyut-dolgu` | "bu durum", "son derece", "kelimenin tam anlamıyla" | uyarı |
| `tire-yogunlugu` | anlatıda cümle içi uzun tire bolluğu | engelleyici |
| `ceviri-kalki`, `edilgen-ceviri-yapisi` | "günün sonunda", "tarafından yapılmakta olan" | uyarı |
| `kesik-cumle-dizisi`, `uzun-paragraf` | art arda altı kesik cümle, 180 kelimeyi aşan paragraf | uyarı |
| `tirnakla-vurgu`, `yigilmis-sifat` | tırnakla vurgulanan sözcük, üst üste yığılmış sıfatlar | uyarı |

Ayrıca `bozulma_denetle.py` zayıf modellerin sert sinyallerini yakalar: yarım kalan metin, döngüye giren paragraflar, "bir yapay zekâ olarak" türü cümleler, metne sızan çalışma notları.

## Nasıl düzeltilir?

1. **Söylemek yerine göstermek:** "Korkuyordu" yerine korkunun görünür izi: elin durması, bardağın masaya fazla sert konması.
2. **Olumsuzu değil olanı yazmak:** "Tereddüt yoktu" yerine yapılan hareket.
3. **Tek benzetme:** Bir cümlede en güçlü benzetmeyi bırakın.
4. **Bölümü müjdeyle değil eylemle bitirmek:** "Her şey değişecekti" yerine somut bir replik ya da nesne.
5. **Karaktere özgü tepki:** Genel beden klişesi yerine o karakterin alışkanlığı.

Bilinçli bir üslup tercihi olan ifadeleri kitap kökündeki `.yz-beyaz-liste` dosyasına satır satır yazabilirsiniz; denetçi onları atlar. Tersine, bu kitapta hiç görmek istemediğiniz ifadeleri `.yasak-kaliplar` dosyasına yazın (her satır `ifade` ya da `ifade => öneri`); denetçi onları engelleyici `kitap-yasagi` bulgusu olarak gösterir.

## Örnek

[`ornekler/yz-tadi-karsilastirma/`](../ornekler/yz-tadi-karsilastirma/README.md): aynı sahnenin iki hâli. Önceki hâlde 10 bulgu (6 engelleyici), sonraki hâlde 0 bulgu.

## Sınır

Denetçi bir yapay zekâ dedektörü değildir. Amaç okuma deneyimidir; bir tespit aracının puanını düşürmek değil. Son karar yazarın okumasıdır.
