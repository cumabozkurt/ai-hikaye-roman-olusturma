# Yapay zekâyla yazılan romanı 100+ bölüm boyunca tutarlı tutmak

Uzun romanda en sık üç hata görülür: karakterlerin henüz öğrenmedikleri şeyi "bilmesi", ekilen ipuçlarının unutulması ve ölen ya da şehir dışındaki karakterin sahneye girmesi. Üçü de aynı kökten gelir: sohbet hafızası kitabı taşıyamaz.

## Çözüm: tek durum dosyası, türetilmiş görünümler

- `takip/_takip-durumu.json` bütün kalıcı durumu tutar: karakterlerin konumu, yaşam durumu, bildikleri; ipuçları ve çözüm planları; olaylar; bölüm kayıtları; uzunluk kayıtları.
- Her bölümden sonra model yalnızca küçük bir **işlem** hazırlar (bu bölümde ne değişti?). `hikayectl.py bolum kaydet` işlemi doğrular ve tek seferde, atomik olarak işler.
- `baglam.md` (bağlam kartı) bir sonraki bölüm için gereken tek dosyadır: güncel konum, kalıcı kısıtlar, açık ipuçları, sonraki bölüm sözleri, süreklilik riskleri. Boyutu sınırlıdır ve metin istemine olduğu gibi kopyalanmaz.

## Yazar gerçeği ve okur bilgisi

Olaylar iki çizelgede tutulur: `zaman-cizelgesi/yazar-gercegi.md` (olan her şey) ve `okur-bilgisi.md` (okurun metinde gördükleri). Açığa çıkmamış bir olay okur bilgisine geçmez; `sureklilik_denetle.py`, gizli olayın anahtar kelimesi plan izin vermeden metinde geçerse `gizli-olay-sizintisi` hatası verir.

## Kapılar

- Bölüm planı yoksa metin yazılamaz (kanca).
- Önceki bölüm takibe kaydedilmeden sonraki bölüm yazılamaz (kanca ve `bolum denetle`).
- Eski bir durum üzerinden hazırlanmış işlem reddedilir (`beklenen_revizyon`).
- Türetilmiş görünüm elle değiştirilirse `takip_kaydet.py denetle` yakalar.

## Süreklilik denetimi

`sureklilik_denetle.py --proje <kitap> --bolum N` şunları arar: öldüğü kayıtlı karakterin sahnede eylem yapması (tam ad ya da çakışmayan ilk ad), planlanan çözüm bölümü geçmiş açık ipucu, gizli bilgi sızıntısı, birbirine çok benzeyen karakter adları ve bir harf kayan ad yazımları (Elif → Elıf).

Örnek: [`ornekler/roman/saatcinin-kizi/`](../ornekler/roman/saatcinin-kizi/). Takip dosyaları `islem-ornekleri/` altındaki üç işlemden bayt bayt yeniden üretilir; testler bunu doğrular.
