---
name: roman-planla
description: "Romanı yazmaya başlamadan önce yapı kurar ve planı denetler: üç perde, kahramanın yolculuğu, serim-düğüm-çözüm, yedi nokta ya da kar tanesi yöntemiyle iskelet; sahne kartları (bakış açısı, mekân, amaç, çatışma, sonuç, değer değişimi) ve mantar pano; vuruşların doğru bölüme düşüp düşmediğini ölçen denetim; özet katmanları ve \"nerede kaldım\" raporu. Tetikleyiciler: /roman-planla, \"romanımı planla\", \"kar tanesi yöntemi\", \"sahne kartı\", \"üç perde\", \"olay örgüsü iskeleti\", \"nerede kalmıştım\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kitaplık). Proje yapısı: kaynaklar/proje-yapisi.md."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "yeni"}
---

# roman-planla: Yapı, Sahne Kartları ve Plan Denetimi

Yazarla birlikte romanın iskeletini kurar, sonra bu iskeletin ölçülebilir kurallara uyup uymadığını betikle denetlersin. **Plan yazarındır**: yöntemi sen seçmezsin, seçenekleri anlatıp yazara seçtirirsin; boş alanları yazarın cevaplarıyla doldurursun.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. `<kitap>` kitap klasörüdür (`plan/genel-plan.md` dosyasını içeren klasör).

## 1. Yöntem seç

```bash
python3 betikler/kurgu_plani.py yontemler
```

| Yöntem | Ne zaman |
|---|---|
| `uc-perde` | Gerilim, polisiye, romantik: 9 vuruş, yüzdelik konumlarıyla |
| `kahramanin-yolculugu` | Fantastik, macera, büyüme hikâyesi: 12 durak |
| `serim-dugum-cozum` | Klasik Türk romanı ve kısa roman: 6 aşama |
| `yedi-nokta` | Olay örgüsünü sondan başa kurmak isteyenler |
| `kar-tanesi` | Planı tek cümleden sahne listesine büyütmek isteyenler: 10 adım |

Tür kartı (`kaynaklar/tur-kartlari/`) yöntem önerir: polisiyede ipucu dağılımı, tarihî romanda dönem takvimi gibi.

## 2. Şablonu oluştur ve doldur

```bash
python3 betikler/kurgu_plani.py baslat --proje <kitap> --yontem uc-perde --bolum-sayisi 40 --hedef-kelime 90000
python3 betikler/kurgu_plani.py baslat --proje <kitap> --yontem kar-tanesi
```

Şablon `plan/yapi-<yontem>.md` (kar tanesi için `plan/kar-tanesi.md`) olarak yazılır; var olan dosyanın üzerine asla yazılmaz. Her vuruşun altındaki `- Bölüm:` ve `- Olay:` satırlarını yazarla birlikte doldur. Kar tanesinde adımları sırayla büyüt: 1. adım en fazla 25 kelimelik tek cümle, 2. adım en az dört cümlelik paragraf.

## 3. Sahne kartları

```bash
python3 betikler/kurgu_plani.py sahneler --proje <kitap>      # plan/sahneler.md tablosu
python3 betikler/kurgu_plani.py pano --proje <kitap>          # metin panosu
python3 betikler/kurgu_plani.py pano --proje <kitap> --html pano.html   # bakış açısına göre renkli kartlar
```

Her sahne satırı: `Bölüm`, `Sahne`, `Bakış açısı`, `Mekân`, `Amaç`, `Çatışma`, `Sonuç`, `Değer` (`+ → −` ya da `güven + → korku −`), `Durum` (`fikir`, `planlandı`, `taslak`, `yazıldı`, `revize`, `tamam`, `çıkarıldı`). Amaç–çatışma–sonuç üçlüsü olmayan sahne, sahne değil geçiştir.

## 4. Denetle

```bash
python3 betikler/kurgu_plani.py denetle --proje <kitap>
```

Yakaladıkları: boş vuruşlar, sırası bozuk vuruşlar, beklenen yüzdelik konumdan uzak düşen vuruşlar (ör. ilk dönüm noktası kitabın %25'i yerine %60'ında), bölüm sayısını aşan vuruşlar, kar tanesinde atlanan adımlar ve uzun 1. adım, amacı/çatışması/sonucu boş sahneler, değer değişimi olmayan düz sahneler, sahnesi olmayan bölümler. Uyarıları yazara göster; yapıyı bilerek bozmak yazarın hakkıdır, betik yalnızca haber verir.

## 5. Bölüm planlarına indir

`plan/genel-plan.md` henüz yoksa önce onu yaz: `/roman-yaz` kurulum akışında `hikaye-mimari` ajanı yapı iskeletini ve sahne kartlarını girdi olarak kullanıp tür, okur sözleşmesi, ciltler ve bölüm sayısını genel plana yazar.

Yapı ve sahneler oturunca her bölüm için `plan/bolum-plani_NNN.md` dosyasını `kaynaklar/bolum-plani-sablonu.md` ile yaz (ya da `/roman-yaz` akışına geç). Uzun romanda hepsini birden değil, önümüzdeki 3–5 bölümü ayrıntılı yaz.

## 6. Nerede kaldım? Özet katmanları

```bash
python3 betikler/proje_durumu.py durum --proje <kitap>        # sıradaki adım ve uyarılar
python3 betikler/proje_durumu.py ozet --proje <kitap> --cikti <kitap>/takip/ozet-katmanlari.md
```

`durum`: yarım kalan çalışma klasörü, yazılmış ama takibe kaydedilmemiş bölüm, planı eksik sıradaki bölüm, süresi geçen ipuçları, eski anlık görüntü gibi durumları bulur ve tek bir sıradaki adım önerir. Kesintiden sonra oturuma bununla başla.

`ozet`: kitap (tek cümlelik öz), cilt/perde (genel plandaki `**Ad** (1–20)` aralıkları ya da `--grup` büyüklüğünde parçalar) ve bölüm (takip kayıtlarındaki `Sonuç` satırları) katmanlarını tek dosyada toplar; eski ciltleri sıkıştırıp `--sinir` baytı aşmaz. 100 bölümlük romanda bütün metni okumadan bütün hikâyeyi hatırlamak için bağlama bunu koy.
