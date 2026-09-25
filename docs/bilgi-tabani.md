# Bilgi tabanı

Her becerinin `kaynaklar/` klasörü yalnızca gerektiğinde okunur; bağlamı boşuna doldurmaz. Birden çok becerinin kullandığı kaynakların tek doğru kaynağı `paylasilan/kaynaklar/` klasörüdür.

## Ortak kaynaklar (`paylasilan/kaynaklar/`)

| Dosya | Konu |
|---|---|
| `proje-yapisi.md` | Kitap, öykü ve çalışma alanı klasör yapısı |
| `bolum-plani-sablonu.md` | Bölüm planı (sahne planı) sözleşmesi; `Hedef uzunluk` zorunlu |
| `takip-protokolu.md` | Takip işlemi JSON biçimi, ipucu ve olay yaşam döngüsü |
| `tdk-yazim-rehberi.md` | TDK Yazım Kılavuzu'na göre sık yanlışlar, bağlaç ve ek yazımı, noktalama, diyalog dizgisi |
| `yz-tadi.md` | Türkçe yapay zekâ kalıpları ve düzeltme yönleri |
| `uslup-karari.md` | Kitabın üslup dosyası (`kurgu/ton.md`) nasıl kurulur |
| `yazar-hafizasi.md` | Kanıta dayalı yazar tercihleri ve kayıt kuralları |
| `platformlar-turkiye.md` | Türkiye'de çevrim içi yayın, kitap satış listeleri, e-kitap ve sesli kitap, yayınevi, sözleşme ve telif, dergi ve yarışma, uyarlama |
| `tur-kartlari/` | 14 tür kartı: romantik, genç kurgu, fantastik, polisiye, tarihî, Osmanlı dönemi, erken Cumhuriyet, psikolojik gerilim, bilimkurgu/distopya, korku/doğaüstü, aile dramı, mizah, edebî kurgu, kısa öykü |

## Beceriye özgü kaynaklar

| Beceri | Kaynaklar |
|---|---|
| `roman-yaz` | kurulum, bölüm, günlük yazım ve revizyon iş akışları; yazar raporu; yazım zanaati (açılış, kanca, diyalog, karakter, olay örgüsü, gerilim, duygu, tempo) |
| `oyku-yaz` | öykü tasarımı (duygu tablosu, şablonlar), öykü yazımı, son okuma |
| `roman-cozumle` | çıktı şablonları, yazara anlatım, üslup profili, ilham kütüphanesi |
| `oyku-cozumle` | çözümleme ölçütleri |
| `roman-tara` | tarama yöntemi |
| `metin-incele` | 100 puanlık inceleme ölçütleri |
| `hikaye-ice-aktar` | biçim ve bölümleme, takip ilklendirme |
| `hikaye-kurulum` | tanılama ve kaldırma |
| `hikaye` | güncelleme |
| `kapak-tasarla` | tür ve platforma göre kapak stilleri |
| `wattpad-bolum-planla` | Wattpad ve bölümlü yayın rehberi (erişim durumu dahil) |
| `yayinevi-dosyasi` | dosya hazırlığı: ön yazı, sinopsis, örnek bölüm, biyografi |
| `uyarlama-sinopsis` | uyarlama biçimleri: logline, sinopsis, karakter dosyası, tretman, sezon yayı |
| `sesli-kitap-hazirla` | seslendirme, süre, telaffuz ve platform rehberi |
| `e-kitap-derle` | EPUB, DOCX, ODT, baskı HTML'i ve PDF rehberi, teslim listesi |
| `roman-planla` | proje yapısı, bölüm planı şablonu, tür kartları (yapı yöntemi seçimi için) |
| `kurgu-ansiklopedisi` | proje yapısı, tür kartları (dönem denetimi için Osmanlı ve erken Cumhuriyet kartları) |
| `bolum-dongusu` | proje yapısı, Türkçe yapay zekâ kalıpları (mekanik puanın bir bileşeni) |
| `yazim-panosu` | proje yapısı |

## Kitap klasöründeki yapılandırılmış bilgi (2.0)

Betiklerin okuduğu ve yazdığı dosyalar; ayrıntılı ağaç için `proje-yapisi.md`.

| Dosya | Yazan | Okuyan |
|---|---|---|
| `kurgu/karakterler/`, `mekanlar/`, `nesneler/`, `gruplar/`, `dunya/` | yazar, `kurgu_ansiklopedisi.py olustur` | `dogrula`, `tutarlilik`, `dagilim`, `baglam`, `bilgi_ara.py` |
| `kurgu/sozluk.md`, `kurgu/zaman-cizelgesi.md`, `kurgu/iliskiler.md` | yazar | `kurgu_ansiklopedisi.py`, `grafik` |
| `plan/yapi-*.md`, `plan/kar-tanesi.md`, `plan/sahneler.md` | `kurgu_plani.py baslat/sahneler`, yazar | `kurgu_plani.py denetle/pano`, çalışma masası |
| `kurgu/ses-izi.json` | `ses_izi.py cikar` | `ses_izi.py karsilastir`, `revizyon_dongusu.py olc` |
| `.hikaye/anliklar/` | `anlik_goruntu.py al`, `revizyon_dongusu.py kabul` | `listele`, `fark`, `geri-yukle`, `dogrula` |
| `.hikaye/istatistik.json` | `yazim_istatistik.py hedef/kaydet` | `pano`, çalışma masası |
| `.hikaye/dongu/bolum-NNN/` | `revizyon_dongusu.py kaydet` | `durum`, `brief`, `kabul`, çalışma masası |
| `.hikaye/turnuvalar/` | `turnuva.py` | `siralama`, `listele` |
| `takip/_takip-durumu.json` | `takip_kaydet.py` | `ipucu_defteri.py`, `proje_durumu.py`, `sureklilik_denetle.py` |
