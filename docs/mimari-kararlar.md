# Mimari kararlar

Her karar: sorun, karar, değerlendirilen alternatifler ve sonuçlar.

## MK-1: Betikler yalnızca Python standart kütüphanesiyle

- **Sorun:** Üst kaynak hem Node.js hem Python betikleri kullanıyordu; yazarların bilgisayarında iki çalışma zamanı ve npm bağımlılıkları gerekiyordu.
- **Karar:** Bütün denetim, kayıt, kurulum ve kanca betikleri Python 3.11+ standart kütüphanesiyle yazıldı. Yalnızca kapak kırpma isteğe bağlı olarak Pillow kullanır.
- **Alternatifler:** Node.js'e geçmek (Claude Code zaten Node ile gelir) cazipti, fakat Codex, Antigravity ve OpenClaw kullanıcılarında Node güvencesi yok; Python çoğu sistemde hazır.
- **Sonuç:** Tek çalışma zamanı, tek test aracı (pytest). OpenCode eklentisi TypeScript kalır ama yalnızca Python çekirdeğini çağırır.

## MK-2: Tek kanca çekirdeği

- **Sorun:** Sekiz ev sahibi farklı kanca biçimleri bekler; mantığı her birine ayrı yazmak sapmaya yol açar.
- **Karar:** `hikaye_kanca.py OLAY --ev EV` bütün mantığı taşır; ev sahibine özgü dosyalar yalnızca çağırır ve çıktıyı o ortamın biçimine çevirir.
- **Sonuç:** Kanca davranışı tek yerde test edilir (`testler/test_kurulum_ve_kancalar.py`).

## MK-3: Klasör ve dosya adları ASCII, içerik Türkçe

- **Sorun:** Türkçe karakterli dosya adları Windows, git ve bulut eşitlemede kodlama sorunları çıkarır; beceri adları Agent Skills belirtimine göre küçük harf, rakam ve tire olmalıdır.
- **Karar:** Beceri, klasör, dosya ve JSON anahtarları ASCII (`oyku-yaz`, `bolum-plani_001.md`, `son_kaydedilen_bolum`); bütün içerik, ileti ve belgeler doğru Türkçe karakterlerle.
- **Sonuç:** Türkçe uyum denetimi tire/alt çizgili tanımlayıcıları ve kod bloklarını atlar, düzyazıyı denetler.

## MK-4: Paylaşılan dosyalar kopyalanır, bağlanmaz

- **Sorun:** Beceriler `npx skills` ile tek tek kurulabilir; başka becerinin klasörüne göreli yol verilemez. Sembolik bağlantılar Windows'ta güvenilmez.
- **Karar:** Tek doğru kaynak `paylasilan/`; `paylasilanlari_esitle.py` içe aktarma bağımlılıklarını da çözerek kopyalar, CI eşitliği denetler.

## MK-5: Kök `hooks/` klasörü yok

- **Sorun:** Claude Code ve Codex eklenti kökündeki `hooks/hooks.json` dosyasını kendiliğinden yükler. Eklenti yüklü her projede kanca çalışması, yazım projesi olmayan depolarda gereksiz süreç ve kafa karışıklığı demektir.
- **Karar:** Kancalar yalnızca `hikaye-kurulum` ile, yazarın onayıyla projeye kurulur ve `.hikaye-kurulu` işareti olmayan projede hiçbir şey yapmaz. ZCode eklenti kancaları `varliklar/zcode/hooks.json` altında tutulur ve proje kancası varsa susar.

## MK-6: Wattpad API + yazarın tarayıcısı; mağaza kazıyıcısı yok

- **Sorun:** Üst kaynak Çin platformları için kazıyıcılar içeriyordu. Türkiye'deki kitap mağazaları otomatik isteklere 403 döner; Wattpad Türkiye'de erişime kapalıdır.
- **Karar:** Yalnızca herkese açık Wattpad arama API'si (düşük hız, kişisel veri yok) ve yazarın kendi tarayıcısıyla görünen metni okuyan CDP istemcisi. Erişim engelini aşma yöntemi önerilmez.

## MK-7: Wattpad planlayıcı adını korur, kapsamı genişler

- **Sorun:** Wattpad Türkiye'de erişime kapalı; ancak yazarların alışkanlıkları ve yurt dışındaki Türkçe okur kitlesi hâlâ Wattpad ölçülerine göre şekilleniyor.
- **Karar:** `wattpad-bolum-planla` adı korunur (bilinirlik), açıklaması "Wattpad ve benzeri bölümlü çevrim içi yayın" olarak genişletildi; erişim durumu belgelerde ve beceride açıkça yazılır.
