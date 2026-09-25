# Değişiklik Günlüğü

Biçim [Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/) ilkelerine, sürümleme [Anlamsal Sürümleme](https://semver.org/lang/tr/) kurallarına uyar.

## [2.1.0] - 2026-09-25

Yazılan kitabın okura ulaşması için yeni son adım: **Kitaptik'te yayımla**. [Kitaptik](https://kitaptik.com), Türkiye'den erişilebilen, Türkçe kitap yazma ve okuma platformudur (web, iOS, Android). Yeni beceri kitabı Kitaptik'in yazar ekranına hazırlar; siteye giriş yapmaz, dosya yüklemez. Rehber: [docs/KITAPTIK-ILE-YAYIMLAMA.md](docs/KITAPTIK-ILE-YAYIMLAMA.md). İnceleme: [docs/INCELEME-RAPORU.md](docs/INCELEME-RAPORU.md) (Dördüncü Tur).

### Eklendi
- **Yeni beceri** `kitaptik-yayimla` (toplam 25) ve `kitaptik_hazirla.py` (yalnızca standart kütüphane):
  - `baslat`: `yayin/kitaptik.md` yayın bilgisi dosyası; kitabın türünden Kitaptik ana ve alt kategorisi ile etiket önerisi, plandaki tek cümlelik özden açıklama taslağı.
  - `denetle`: Kitaptik'in yazar ekranı sınırları (bölüm başına 10.000 kelime, bölüm başlığı 77 karakter, açıklama 2.500, "Neden okumalı?" 333, en çok 3 alt kategori, etiket kuralları, kapak biçimi, boyutu, ölçüsü ve hareketliliği); bitmemiş metin işaretleri, görsel, tablo ve bağlantılar; Topluluk Kuralları'na göre 18+ işareti ve `[TW: İntihar]` uyarısı gerekebilecek yerler için anahtar sözcük taraması.
  - `paket`: **Toplu Yükle** ekranına hazır DOCX (her bölüm bir Başlık 1, uzun bölümler sahne ayracına yakın yerden "(1/2)" diye bölünür, 500'den çok bölümde birden çok dosya), kitap bilgileri formu, karakter kartları (sırlar alınmaz), yayın kontrol listesi ve `rapor.json`. Hata varken dosya yazılmaz; aynı girdi aynı DOCX'i verir.
  - `kategoriler`: Kitaptik'in 10 ana kategorisi ve alt kategorileri.
- `docs/KITAPTIK-ILE-YAYIMLAMA.md`: adım adım yayımlama rehberi, doğrulanmış özellikler ve sınırlar, kazanç koşulları (vaatsiz).
- `testler/test_kitaptik.py` (32 test) ve `testler/araclar/kitaptik_docx_oku.js`: üretilen DOCX açık kaynak mammoth kitaplığıyla, Kitaptik'in "her Başlık 1 yeni bölüm" kuralına göre okunur; bölüm başlıkları ve kelime sayıları raporla karşılaştırılır. CI çıktı doğrulama işinde atlanmadan çalışır.
- Kitaptik değerlendirme vakası (toplam 28).

### Değişti
- İş akışı Kitaptik'le bitiyor: `hikaye`, `roman-yaz`, `e-kitap-derle`, `wattpad-bolum-planla`, `metin-incele` ve kurulum yönlendirme tablosu yayın adımında `/kitaptik-yayimla`yı öneriyor; `proje_durumu.py` planlanan bölümler bitince Kitaptik paketini hatırlatıyor.
- `platformlar-turkiye.md`: Kitaptik satırı; Wattpad'in Türkiye'deki erişim engeli notu yurt içi seçeneği gösteriyor.
- Örnek roman Kitaptik'te yayımlanacak biçimde güncellendi (tür, yayın biçimi, karakter rolleri).
- `e_kitap_derle.py` ve `belge_yazicilar.py` paylaşılan betiklere taşındı (e-kitap-derle ve kitaptik-yayimla aynı kodu kullanır).
- Eklenti açıklamaları ajan sayısını dosyalardan sayıyor (8).

## [2.0.0] - 2026-09-25

En büyük güncelleme: dokuz açık kaynak roman yazım projesi uçtan uca incelendi ve Türkçe roman yazan birinin başka bir araca ihtiyaç duymaması için eksik yetenekler bağımsız olarak, testleriyle birlikte yazıldı. Karşılaştırma ve lisanslar: [docs/OZELLIK-KARSILASTIRMA.md](docs/OZELLIK-KARSILASTIRMA.md). İnceleme: [docs/INCELEME-RAPORU.md](docs/INCELEME-RAPORU.md) (Üçüncü Tur).

### Eklendi
- **4 yeni beceri** (toplam 24): `roman-planla`, `kurgu-ansiklopedisi`, `bolum-dongusu`, `yazim-panosu`.
- **8. ajan** `bolum-hakemi`: revizyon döngüsü için salt okunur hakem; plan maddelerini `tamam` / `eksik` / `doğrulanmalı` olarak işaretler (ajan sürümü 2).
- `kurgu_plani.py`: üç perde, kahramanın yolculuğu, serim-düğüm-çözüm, yedi nokta ve kar tanesi şablonları; vuruşların beklenen konuma, sıraya ve bölüm sayısına göre denetimi; sahne kartları (bakış açısı, amaç, çatışma, sonuç, değer değişimi, durum), metin ve HTML mantar pano.
- `kurgu_ansiklopedisi.py`: karakter (mülakat soruları dahil), mekân, nesne, grup ve dünya kayıtları; sözlük ve zaman çizelgesi; kayıt doğrulama, metinle tutarlılık (yanlış yazım, cümle başında dahil ad kayması, erken görünüş, ölümden sonra görünüş, doğmadan önceki olay), bölümlere dağılım (HTML ısı haritası), Mermaid/DOT ilişki grafiği ve bayt sınırlı bölüm bağlam paketi.
- `ipucu_defteri.py`: ipuçlarının son anıldığı bölüm, süresi geçen, unutulan, plan dışı ve tek bölümde yığılan çözümler; ASCII şerit.
- `proje_durumu.py`: "nerede kaldım" raporu (yarım bölüm, kaydedilmemiş bölüm, eksik plan, süresi geçen ipucu, eski anlık görüntü, süren döngü, kayıttan sonra değişen bölüm) ve kitap → cilt → bölüm özet katmanları.
- `bilgi_ara.py`: Türkçe ek budamalı, düzeltme işaretine duyarsız BM25 proje araması.
- `revizyon_dongusu.py`: yaz → eleştir → düzelt döngüsü; mekanik puan (yapay zekâ kalıbı, ritim, tekrar, plan uzunluğu, ses izi) ve hakem puanı, hedef, plato ve en fazla tur ile durma; revizyon talimatı; bölüme yazmak için `--yazar-onayladi` ve otomatik anlık görüntü.
- `turnuva.py`: aynı bölümün taslaklarını ikili karşılaştırıp Elo ile sıralayan turnuva.
- `ses_izi.py`: cümle uzunluğu, diyalog oranı, zarf-fiil sıklığı, sözcük çeşitliliği gibi ölçülerle üslup profili ve sapma raporu.
- `anlik_goruntu.py`: içerik adresli anlık görüntüler, `son~N` kısayolu, satır ve kelime düzeyinde fark, önce güvenlik kopyası alan geri yükleme, temizlik ve bütünlük denetimi.
- `yazim_istatistik.py`: kitap, bitiş tarihi ve günlük hedef; günlük kayıt, seri, 7 günlük hız, bitiş tahmini, bölüm ilerlemesi; metin ve HTML pano.
- `donem_denetle.py`: Osmanlı ve erken Cumhuriyet için dönem uyumsuzluğu denetimi (soyadı, Bay/Bayan, Latin harfleri, radyo, fes gibi); kitaba özgü `.donem-istisnalari`.
- `belge_ice_aktar.py`: DOCX, ODT, EPUB, TXT ve Markdown taslaklarını Türkçe bölüm başlıklarını ("Birinci Bölüm", "BÖLÜM BİR", "3. bölüm: …") tanıyarak böler; italik ve kalın korunur; kelime sayısı %1'den fazla tutmazsa hiçbir dosya yazmaz; DOCTYPE/ENTITY içeren XML ve aşırı büyük arşiv parçaları reddedilir.
- `e-kitap-derle`: DOCX, ODT, A5 baskı HTML'i, PDF (Chrome/Chromium/Edge ile), TXT ve Markdown çıktıları; varsayılan `hepsi`.
- Tür kartları: **Osmanlı dönemi** ve **erken Cumhuriyet** (toplam 14).
- Çalışma masası: Genel, Kurgu, Sahneler, İpuçları, Döngü ve Sürümler sekmeleri; `#sekme=` bağlantıları; Yenile düğmesi; Türkçe sayı ve tarih biçimi; bir bölüm okunamazsa panel çökmez.
- Örnek roman: yapı iskeleti, sahne kartları, mekân ve nesne kayıtları, sözlük ve zaman çizelgesi; bütün 2.0 denetimlerinden temiz geçer.
- 4 yeni değerlendirme vakası (toplam 27), uçtan uca roman senaryosu testi, CI'da EPUBCheck ve LibreOffice ile atlanmayan çıktı doğrulama işi.
- README yeniden tasarlandı: tanıtım, "Neden bu proje?", tipik araç türleriyle ve dokuz projeyle karşılaştırma, çalışma masası görüntüleri, Esinlenilen Projeler.

### Düzeltildi
- Alan satırı ayrıştırıcıları boş bir `- Alan:` satırında bir sonraki satırı değer sanıyordu (10 betik).
- `sureklilik_denetle.py` satır numaralarını 2 satır kaydırıyordu; ölü karakterin fotoğraf ya da anı cümlesinden sonraki anılması yanlış uyarı veriyordu.
- Takip durumundaki ipuçları sözlük biçimindeyken bazı araçlar liste bekliyordu.
- Örnek romanda Kerem ile Tahsin arasındaki akrabalık metinde ve takip dosyalarında çelişiyordu (ağabey / kardeş); yaşlarla uyumlu olarak amca–yeğen yapıldı.
- Çalışma masası `--port` yardımında yanlış varsayılan (9222) yazıyordu.
- Windows'ta CRLF satır sonlu dosyalar özetleri platforma göre değiştiriyordu: ortak okuyucu satır sonlarını LF'ye çeviriyor, betikler her platformda LF yazıyor.
- macOS'ta başsız Chrome PDF'yi yazdıktan sonra kapanmayabiliyordu: tamamlanan PDF izlenip süreç kapatılıyor, toplam süre 90 saniyeyle sınırlı.
- Dönem denetimi "radyoaktif", "radyolog" gibi sözcüklerde yanlış uyarı veriyordu.
- İstatistik, çok az yazım gününden anlamsız bitiş tarihleri tahmin ediyordu; artık son 7 günde en az 3 yazım günü gerekiyor.

## [1.1.0] - 2026-09-25

İkinci inceleme turu: üç bağımsız göz (araç mühendisi, Türk editör, ilk kez kullanan) ve karşılaştırmalı araştırma. Ayrıntı: [docs/INCELEME-RAPORU.md](docs/INCELEME-RAPORU.md).

### Eklendi
- `e-kitap-derle` becerisi (20. beceri): Markdown bölümlerinden EPUB 3 ve tek dosyalık HTML okuma kopyası; kapak, künye, içindekiler, yeniden üretilebilir çıktı (`SOURCE_DATE_EPOCH`), bitmemiş işaret kapısı. W3C EPUBCheck 5.1.0 ile hatasız.
- `metin_analizi.py`: Ateşman okunabilirlik puanı, cümle uzunluğu ortalaması ve sapması, diyalog oranı, yakın tekrarlar, cümle başı tekrarları, duyu dağılımı, `[TK]`/`[DOLDUR]` işaretleri.
- Kitaba özgü `.yasak-kaliplar` dosyası (`ifade => öneri`); `ai_kalip_denetle.py` engelleyici `kitap-yasagi` bulgusu verir.
- `metin-incele` için okur paneli (`kaynaklar/okur-paneli.md`): altı Türk okur profiliyle bırakma noktası analizi.
- 12 tür kartına "Öz denetim soruları" ve Türkçe kelime sayısı notu.
- `evals/`: `claude plugin eval` biçiminde 23 değerlendirme vakası (her beceri için tetiklenme + sonuç, 3 olumsuz vaka).
- Ortak `dosya_oku.py`: UTF-8 BOM, Windows-1254 geri dönüşü, ikili dosya ve klasör reddi.
- README yeniden tasarlandı: afiş, rozetler, akış şeması, gerçek terminal çıktıları, önce/sonra örneği, karşılaştırma, SSS, yol haritası.

### Düzeltildi
- 357 bozuk girdi denemesinde 60 Python izi (traceback) → 0; bütün hata iletileri Türkçe (`HIKAYE_AYIKLA=1` ile ayrıntı).
- 122 komut satırı seçeneğinde eksik yardım metni tamamlandı; kapsama testi eklendi.
- Çalışma masası sunucusu DNS yeniden bağlama saldırısına karşı yalnızca yerel `Host` başlığını kabul ediyor.
- `turkce_uyum_denetle.py` var olmayan yolda sessizce geçiyordu; artık hata veriyor.
- `metin_olcum.py --hedef -5` eksi işaretini yutuyordu; `liste_tara.py` bozuk liste biçiminde çöküyordu.
- Örnek romanın ilk bölümünde saat kadranında olmayan "on dördün üstünde" ifadesi düzeltildi.

## [1.0.0] - 2026-09-25

İlk sürüm: oh-story-claudecode v0.7.11 (commit 401019ea) temel alınarak Türkiye Türkçesi için baştan yazıldı.

### Eklendi

- 13 üst kaynak becerisinin Türkçe karşılıkları: `hikaye`, `hikaye-kurulum`, `roman-tara`, `oyku-tara`, `roman-cozumle`, `oyku-cozumle`, `roman-yaz`, `oyku-yaz`, `yz-tadi-gider`, `metin-incele`, `hikaye-ice-aktar`, `kapak-tasarla`, `tarayici-cdp`.
- 6 yeni beceri: `yazim-denetle` (TDK), `sureklilik-denetle`, `wattpad-bolum-planla`, `yayinevi-dosyasi`, `uyarlama-sinopsis`, `sesli-kitap-hazirla`.
- 7 Türkçe ajan ve tek Python kanca çekirdeği (Claude Code, Codex, OpenCode 1.x/2.x, Antigravity, ZCode).
- Türkçe yapay zekâ kalıp denetçisi, bozulma denetçisi, TDK yazım denetçisi, noktalama düzeltici, süreklilik denetçisi.
- Takip durumu (`_takip-durumu.json`) ve türetilmiş görünümler; yazar gerçeği / okur bilgisi ayrımı; atomik bölüm kaydı.
- 12 Türkçe tür kartı; Türkiye yayın ve okur platformları rehberi.
- Wattpad herkese açık API taraması (Türkçe süzgeçli) ve CDP tabanlı mağaza okuma.
- Agent Plugins 1.0.0 bildirimi, Claude Code ve Codex pazar yerleri, ZCode ve Reasonix bildirimleri; tek kaynaktan üretici.
- `kur.sh` / `kur.ps1` kullanıcı düzeyi kurulum betikleri.
- Statik denetim, Türkçe uyum denetimi (CJK ve Türkçe karakter hataları), argparse iletilerinin Türkçeleştirilmesi.
- Bütün Python betikleri için pytest testleri; Python 3.11–3.14 CI matrisi.
- Özgün örnekler: "Saatçinin Kızı" (roman), "Son Vapur" (öykü), yapay zekâ tadı karşılaştırması.
- Ayrıntılı inceleme raporu: `docs/INCELEME-RAPORU.md`.
