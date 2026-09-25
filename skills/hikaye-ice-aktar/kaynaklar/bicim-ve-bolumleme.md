# Biçim ve Bölümleme

## Tanınan bölüm başlıkları

| Desen | Örnek |
|---|---|
| `^#{1,3}\s+` | `# Bölüm 1`, `## 12. Bölüm` |
| `^(BÖLÜM|Bölüm)\s+(\d+|[A-ZÇĞİÖŞÜ]+)` | `BÖLÜM BİR`, `Bölüm 7: Kapı` |
| `^\d+\.\s*$` ya da `^\d+\s*$` | `1.` |
| Wattpad dışa aktarımı | bölüm adı + boş satır + metin |

`***`, `* * *`, `⁂` sahne ayracıdır, bölüm sınırı değildir.

## Normalleştirme

- Satır sonları `\n`, dosya sonu tek satır sonu.
- BOM kaldırılır.
- Windows-1254 / ISO-8859-9 kodlamalı dosyalar UTF-8'e dönüştürülür (`ı`, `ğ`, `ş` bozulmuşsa kodlama yanlıştır).
- Metin gövdesine başka dokunulmaz: yazım ya da noktalama düzeltmesi içe aktarmanın parçası değildir; yazar isterse ayrıca `/yazim-denetle`.

## Adlandırma

`bolum-001_kisa-baslik.md`: üç haneli numara, alt çizgi, Türkçe karakterleri ASCII'ye çevrilmiş (`ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u`) küçük harfli kısa başlık. Başlık yoksa `bolum-001.md`.
