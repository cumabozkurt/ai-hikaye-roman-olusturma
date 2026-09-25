# Yazar Hafızası Protokolü

Yazar hafızası, yazarın **açıkça söylediği** kalıcı tercihleri saklar: üslup, hikâye tasarımı, çalışma biçimi, teslim biçimi ve birlikte çalışma. Hikâye olguları (karakterin göz rengi, olay sırası) buraya değil, kitabın `kurgu/` ve `takip/` dosyalarına yazılır.

## İki düzey

| Depo | Yer | Kimlik | İçerik |
|---|---|---|---|
| Proje | `{çalışma alanı}/.hikaye/yazar-hafizasi/` | `AP001…` | genel, tür ve iş akışı tercihleri |
| Kitap | `{kitap}/.hikaye/yazar-hafizasi/` | `KP001…` | yalnızca o kitaba ait tercihler |

Her depoda `durum.json` (yetkili), `profil.md` (üretilen görünüm) ve `gunluk.md` bulunur.

## Ne kaydedilir, ne kaydedilmez

- **Kaydedilir**: "Bundan sonra diyaloglarda argo kullanma", "Bu kitapta bölümler 2.000 kelimeyi geçmesin", "Bana önce plan göster, sonra yaz".
- **Kaydedilmez**: tek seferlik istekler ("bu bölümü biraz kısalt"), modelin kendi çıkarımları (yazar bir şeyi üç kez düzeltti diye kural yazılmaz), hikâye olguları.
- Kapsamı belirsizse sorulur: "Bunu yalnızca bu kitap için mi, bütün kitapların için mi hatırlayayım?"
- Var olan bir tercihle çelişiyorsa sessizce üzerine yazılmaz: `degistir` eylemiyle eskisi `yerine_gecti` olur ya da `celisir` alanıyla karar yazara bırakılır.

## Komutlar

```bash
python3 yazar_hafizasi.py baslat  --calisma-alani . --kitap KITAP
python3 yazar_hafizasi.py kaydet  --calisma-alani . --kitap KITAP --girdi hafiza.json
python3 yazar_hafizasi.py sorgula --calisma-alani . --kitap KITAP --is-akisi bolum-taslagi
python3 yazar_hafizasi.py denetle --calisma-alani . --kitap KITAP
```

`sorgula` en fazla 2 KB tercih döndürür (önem → kitaba özgülük → yenilik sırasıyla). Görev birleşimleri: `bolum-taslagi` (üslup + hikâye tasarımı), `yz-tadi-gider` (üslup), `kurgu-plan` (hikâye tasarımı + süreç + birlikte çalışma), `inceleme` (teslim + birlikte çalışma + üslup).

## Makbuz

Araç `"tamam": true` ve **"Yazar Hafızası Makbuzu"** satırı döndürmeden "hatırladım" denmez. Yazara önce tek cümleyle ne hatırlandığı söylenir, makbuz en sona konur:

> Tamam, bu kitapta diyalogları tırnakla değil konuşma çizgisiyle yazacağım.
> Yazar Hafızası Makbuzu: eklendi KP003: Diyaloglar konuşma çizgisiyle yazılır

## Önceliklendirme

Anlık istek > kitabın üslup dosyası (`kurgu/ton.md`) > yazar hafızası > genel kaynaklar. Hafıza düşük öncelikli bir eğilimdir; tutarlılığı, ritmi ya da hedef uzunluğu bozacaksa uygulanmaz.
