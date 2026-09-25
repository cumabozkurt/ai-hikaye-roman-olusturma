# İş Akışı: Revizyon (Aşama 7)

Yazılmış ve kaydedilmiş bölümleri düzeltirken kullanılır.

## Kapsam belirle

- **Yerel düzeltme** (yazım, cümle, üslup): takip değişmez. Metni düzelt, `yazim_denetle.py` ve `ai_kalip_denetle.py` çalıştır, bitti.
- **Olay değişikliği** (bir karakter artık başka şey biliyor, bir olay farklı gelişiyor): takip de düzeltilmelidir.
- **Yapısal değişiklik** (bölüm silme, birleştirme, sıra değiştirme): önce `hikaye-mimari` ile planı güncelle, etkilenen bütün bölümleri listele, yazara onaylat.

## Olay değişikliğinde takip

1. `takip_kaydet.py goster --proje <kitap>` ile güncel revizyonu al.
2. `kip: "revizyon"` ve `bolum: N` içeren bir işlem hazırla; yalnızca değişen kayıtları gönder, bağlamı eksiksiz yeniden gönder.
3. `python3 betikler/takip_kaydet.py uygula --proje <kitap> --girdi revizyon.json`
4. Sonraki bölümleri `sureklilik_denetle.py --proje <kitap>` ile tara; etkilenen bölümleri yazara listele.

## Kurallar

- Revizyon bir karakteri emekliye ayıramaz; bu yalnızca yeni bölüm eklerken yapılır.
- Revizyondan sonra plan ile metin çelişiyorsa plan da güncellenir (`plan_gorunumu.py --gecmis` eski kapsamı gösterir).
- Yazarın kendi yazdığı bölümlerde üslubu koru; yalnızca istenen sorunu düzelt.
- Değişiklik özetini yazara "önce / sonra" biçiminde göster.
