# Tür Kartı: Osmanlı Dönemi Romanı

## Okur beklentisi

Okur, İstanbul'un konaklarından taşra kasabasına, saraydan çarşıya uzanan bir dünyanın içinde yaşamak ister. Dönem kokusu (dil, eşya, hitap, gündelik hayat) doğru olmalı; duygular ve çatışmalar bugünün okuruna yakın gelmelidir. Okur müze gezisi değil, o sokaklarda yürüyen insanların hikâyesini bekler.

## Temel mekanikler

- Dönemi daraltın: "Osmanlı" beş yüzyılı aşan bir dönemdir. Lale Devri (1718–1730), Tanzimat (1839 sonrası), II. Abdülhamid dönemi (1876–1909), II. Meşrutiyet (1908) ve Mütareke yılları (1918–1922) birbirinden çok farklıdır. `plan/genel-plan.md` içine `- Dönem: 1908–1912` gibi bir satır yazın; `donem_denetle.py` bu satırı okur.
- Takvim ve saat: Resmî yazışmada Rumi ve Hicri takvim, gündelik hayatta ezani (alaturka) saat kullanılır; güneş batınca saat on iki olur. Bir karakterin "saat dokuzda buluşalım" demesi dönem saatine göre düşünülmelidir.
- Ad ve hitap: Soyadı yoktur. Kişiler ad, baba adı, lakap, memleket ya da meslekle anılır (Kâtip Rıza Efendi, Hacı Ahmedoğlu, Kasap Mehmet). Hitaplar toplumsal konumu gösterir: Efendi (okumuş, memur, din adamı), Bey (asker ya da ileri gelen), Paşa (yüksek rütbe), Ağa, Hanım, Hanımefendi.
- Para ve ölçü: Kuruş, para, mecidiye, altın lira; ölçüde arşın, okka, dirhem, endaze. Fiyatlar araştırılmalıdır (`hikaye-arastirmaci`, kaynaklar `arastirma/` klasörüne).
- Toplumsal katmanlar: Konak ile mahalle, Müslüman ve gayrimüslim mahalleleri, lonca, vakıf, kadı, muhtar (1829 sonrası), zaptiye. Çok dilli ve çok dinli bir şehir hayatı doğru yansıtılmalıdır.
- Gerçek kişiler yan rolde, kurgu karakterler ön planda; gerçek bir kişiye söyletilen söz kaynağa dayanmalıdır.

## Düzyazı dokusu

- Dönem dili ölçülü: Osmanlıca sözcükler anlamı bağlamdan çıkacak biçimde serpiştirilir; her paragrafa bir sözlük yükü bindirilmez. Kitaba özgü terimler `kurgu/sozluk.md` dosyasına yazılır, yanlış yazımlar orada tanımlanır.
- Anlatı dili bugünün Türkçesidir; diyaloglar döneme göre biraz daha resmî ve hitaplıdır. "Tamam", "okey", "stres", "sorun değil" gibi yakın dönem ifadeleri diyaloğa girmez.
- Duyusal dönem ayrıntısı: gaz lambası, mangal, tandır, hamam buharı, kayık ve pazar kayığı, fayton, tulumbacılar, bekçinin sopası, ezan ve kilise çanı bir arada.
- Mekân ölçeği: Ulaşım yavaştır. İstanbul'dan Selanik'e, Bursa'ya ya da Konya'ya yolculuğun süresi ve aracı (vapur, tren hattının varlığı, at arabası) hesaba katılır.

## Sık kullanılan kalıplar

konak entrikası, mektupla ilerleyen aşk, ihbar ve sürgün, kayıp miras, gizli cemiyet, salgın ve karantina, yangın gecesi, çarşıda cinayet, Mütareke İstanbul'unda casusluk.

Kalıp kullanmak sorun değildir; okur onu bilir ve yeni bir yorum bekler.

## Kaçınılacaklar

- Dönemi tek renk göstermek: bütün Osmanlı'yı saray entrikası ya da yalnızca yoksulluk olarak çizmek.
- Anakronizm: soyadı, "Bay/Bayan" hitabı, radyo, Latin harfli gazete, metrik ölçüyle alışveriş. `donem_denetle.py --proje KITAP` her bölümden sonra çalıştırılır.
- Kadın karakterleri ya yalnızca kurban ya da bugünün değerleriyle konuşan kahramanlar olarak yazmak; dönemin sınırları içinde güç arayan kadınlar çok daha ilginçtir.
- Gerçek tarihî olayları kaynak göstermeden değiştirmek; kurgusal sapma bilinçliyse sonsözde belirtin.

## Bölüm sonu kancası seçenekleri

ele geçen mektup, mühürlü ferman, yangın çanı, kapıya dayanan zaptiye, yanlış kişiye verilen emanet, sürgün haberi.

## Tipik uzunluk

Basılı: 80–130 bin kelime; dizi uyarlamasına göz kırpan romanlarda 25–40 bölüm.

## Öz denetim soruları

Bölüm yazıldıktan sonra anlatı yazarı ve inceleme bu soruları yanıtlar; "hayır" yanıtı bir revizyon notudur.

1. Bu bölümdeki her eşya, kurum, hitap ve ifade seçilen yıllarda var mıydı (`donem_denetle.py` temiz mi)?
2. Karakterler dönemin toplumsal kurallarına göre mi davranıyor; kural çiğneniyorsa bedeli gösteriliyor mu?
3. Osmanlıca sözcükler anlamı bağlamdan çıkacak kadar az ve yerinde mi?
