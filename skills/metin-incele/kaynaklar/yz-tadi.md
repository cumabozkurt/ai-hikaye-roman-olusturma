# Yapay Zekâ Tadı: Türkçe Kurgu İçin Tanı ve Giderme Rehberi

"Yapay zekâ tadı", metnin dil bilgisi açısından doğru ama insan elinden çıkmamış gibi okunmasıdır: her paragrafta aynı ritim, soyut duygu adları, çeviri kokan yapılar, her şeyi açıklayan bir anlatıcı ve fragman gibi biten bölümler. Bu rehber Türkçeye özgü belirtileri, denetleyicinin (`ai_kalip_denetle.py`) kurallarını ve özgün önce/sonra örneklerini içerir.

## 1. Engelleyici kalıplar (görülünce düzeltilir)

| Kural kimliği | Belirti | Neden sorun |
|---|---|---|
| `degil-ama-donusu` | "Bu bir veda değildi, bir başlangıçtı." / "Korku değil, meraktı." | Yapay zekânın en tanıdık imzası; anlamı ters çevirip derinlik taklidi yapar. |
| `bir-yandan-diger-yandan` | "Bir yandan kaçmak istiyor, diğer yandan kalmak istiyordu." | İkilemi göstermek yerine adlandırır. |
| `olumsuzluk-dizisi` | "Ne bir ses vardı, ne bir ışık, ne de bir umut." | Üçlü olumsuzlama ritmi yapaydır. |
| `ses-karsitligi` | "Sesi alçaktı ama keskin." / "Fısıldadı ama her kelime yankılandı." | Klişe karakter sunumu. |
| `fragman-kapanis` | "Her şey değişecekti." / "Asıl hikâye şimdi başlıyordu." / "Henüz bilmiyordu ki…" | Bölüm sonunu olay yerine anlatıcı reklamıyla kapatır. |
| `tire-yogunlugu` | Anlatıda cümle ortasında sık uzun tire (—) | İngilizce yapay zekâ ritmi; Türkçede virgül, iki nokta ya da yeni cümle doğaldır. Satır başındaki konuşma çizgisi sayılmaz. |

## 2. Uyarı kalıpları (yoğunlaşınca düzeltilir)

- **Klişe yoğunluğu** (`klise-yogunlugu`): "derin bir nefes aldı", "kalbi küt küt atıyordu", "dudaklarında bir gülümseme belirdi", "tüyleri diken diken oldu", "zaman durmuş gibiydi", "boğazında bir düğüm". Bin kelimede dörtten fazlası yapay tat verir.
- **Benzetme yoğunluğu** (`benzetme-yogunlugu`) ve **"adeta/sanki" zinciri**: aynı paragrafta iki benzetme işaretinden fazlası.
- **Soyut dolgu** (`soyut-dolgu`): "bu durum", "söz konusu", "son derece", "kaçınılmaz olarak", "bir şekilde", "kelimenin tam anlamıyla".
- **Çeviri kalkı** (`ceviri-kalki`): "günün sonunda", "fark yarattı", "önemli bir rol oynadı", "hiçbir fikrim yok", "göz teması kurdu", "senin için orada olacağım".
- **Edilgen çeviri yapısı** (`edilgen-ceviri-yapisi`): "kapı Mehmet tarafından açıldı" → "Mehmet kapıyı açtı"; "-mekteydi" → "-iyordu".
- **Yığılmış sıfat** (`yigilmis-sifat`): "soğuk, karanlık, ürkütücü, sessiz oda".
- **Uzun paragraf** (`uzun-paragraf`): 180 kelimeyi aşan blok; Wattpad okurunun telefonda kaybolduğu yer.
- **Tırnakla vurgu** (`tirnakla-vurgu`): anlatıda kısa sözcüğü tırnağa alarak ironi yapmak ("o 'dostu'").
- **Kesik cümle dizisi** (`kesik-cumle-dizisi`): art arda altıdan çok dört kelimelik cümle; gerilim yerine telgraf etkisi.

## 3. Yapısal belirtiler (denetleyici göremez, göz görür)

1. **Her şeyi açıklayan anlatıcı**: "Bu, onun annesine duyduğu öfkenin bir yansımasıydı." → Okura bırak.
2. **Duygu adı koymak**: "Büyük bir hüzün hissetti." → Bedende ve eylemde göster.
3. **Kusursuz simetri**: Her paragraf üç cümle, her diyalog tek replik + tek tepki.
4. **Hep aynı açılış**: "Güneş ufukta yükselirken…", "Yağmur camlara vururken…".
5. **Herkes aynı konuşuyor**: Esnaf, profesör ve lise öğrencisi aynı ölçünlü Türkçeyle konuşur. Türkçede hitap (abi, hocam, efendim, kanka), şive izleri ve cümle uzunluğu karakteri ayırır.
6. **Ahlak dersiyle kapanış**: Sahne sonunda anlatıcının çıkardığı ders.
7. **Kültürel boşluk**: İstanbul'da geçen sahnede ne çay bardağı ne vapur ne ezan sesi var; her yer "bir şehir".

## 4. Özgün önce/sonra örnekleri

**Örnek A — duygu adı ve klişe**

> Önce: Ayşe derin bir nefes aldı. Kalbi küt küt atıyordu. İçini tarif edilemez bir korku kaplamıştı ama cesur olmak zorundaydı.

> Sonra: Ayşe anahtarı kilide iki kez sokamadı. Üçüncüsünde kapı açıldı; içeriden kızarmış soğan kokusu geldi. Annesi hiç soğan kızartmazdı.

**Örnek B — "değil… ama…" ve fragman kapanış**

> Önce: Bu bir tesadüf değildi, bir mesajdı. Ve Emre bilmiyordu ki o gece her şey değişecekti.

> Sonra: Kartın arkasında, Emre'nin on yıl önce yalnızca babasına söylediği lakap yazıyordu. Babası üç yıldır toprağın altındaydı.

**Örnek C — çeviri kalkı ve edilgen**

> Önce: Toplantı müdür tarafından başlatıldı. Günün sonunda, bu karar şirket için önemli bir rol oynayacaktı.

> Sonra: Müdür kimseyi beklemeden başladı. Kararı herkes o akşam, maaşlar yatmayınca anladı.

**Örnek D — herkes aynı konuşuyor**

> Önce: — Merhaba, nasılsınız? Size nasıl yardımcı olabilirim? dedi bakkal.

> Sonra: — Hoş geldin kızım, ekmek mi? Sıcak çıktı, al bir tane de yolda ye.

## 5. Giderme sırası (üç geçiş)

1. **Yapı geçişi**: fragman kapanışı, açıklayan anlatıcı, ahlak dersi, simetri. Önce bunlar; çünkü cümle düzeltmesi yapıyı kurtarmaz.
2. **Cümle geçişi**: engelleyici kalıplar, çeviri kalkları, edilgen yapılar, soyut dolgu.
3. **Ses geçişi**: klişeleri somut ayrıntıyla değiştir; karakter seslerini ayır; kültürel dokuyu (mekân, eşya, hitap) ekle.

Her geçişten sonra `ai_kalip_denetle.py --basarisiz engelleyici` ve `bozulma_denetle.py` yeniden çalıştırılır. Uyarıların sıfırlanması hedef değildir; her uyarıya "düzelt" ya da "bilinçli tercih" kararı verilir. Bilinçli tercihler kitabın `.yz-beyaz-liste` dosyasına satır satır yazılır.

## 6. Yapmayın

- Klişeyi başka bir klişeyle değiştirmek ("kalbi küt küt atıyordu" → "kalbi göğüs kafesini dövüyordu").
- Uzunluğu korumak için dolgu eklemek.
- Karakterin konuşma dilindeki bilinçli bozuklukları (diyalogdaki "gelicem", "napıyon") ölçünlü dile çevirmek.
- Plan dışı olay eklemek: yz tadı gidermek biçim işidir, kurguyu değiştirmez.
