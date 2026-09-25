# AI Hikaye & Roman Oluşturma

**Türkçe roman ve öykü yazımı için yapay zekâ becerileri (Agent Skills).** Pazar taramasından çözümlemeye, bölüm bölüm yazımdan 100+ bölümlük süreklilik takibine, TDK yazım denetiminden yapay zekâ tadı gidermeye, kapaktan yayınevi dosyasına kadar bütün yazım hattını, zaten kullandığınız kodlama ajanının içine kurar.

[![Testler](https://github.com/cumabozkurt/ai-hikaye-roman-olusturma/actions/workflows/test.yml/badge.svg)](https://github.com/cumabozkurt/ai-hikaye-roman-olusturma/actions/workflows/test.yml)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-green)
![Dil: Türkçe](https://img.shields.io/badge/Dil-T%C3%BCrk%C3%A7e-E30A17)

Bu depo, [oh-story-claudecode](https://github.com/zenstory-ai/oh-story-claudecode) projesinin Türkiye Türkçesine (tr-TR) ve Türkiye yayın dünyasına göre baştan yazılmış hâlidir. Çeviri değil, yerelleştirmedir: tür kartları, platformlar, yazım kuralları, örnek metinler ve denetçiler Türkçe için yeniden kurulmuştur.

## Ne yapar?

- **Dosya sistemi hafızadır.** Kurgu, plan, metin ve süreklilik takibi ayrı dosyalarda tutulur. Yüzlerce bölümlük bir roman sohbet hafızasına yaslanmaz; bağlam sıkıştırılsa bile ipuçları kaybolmaz.
- **Belirlenimci denetimler ve kapılar.** Bölüm planı olmadan metin yazılamaz; her yazımdan sonra yarım kalan metin, döngüye giren tekrarlar, yapay zekâ kalıpları ve uzunluk otomatik taranır.
- **19 beceri, 7 uzman ajan, 9 kanca olayı.** Beceriler ve kaynak dosyaları yalnızca gerektiğinde yüklenir.
- **8 ortamda çalışır:** Claude Code · OpenAI Codex · OpenCode · Google Antigravity · ZCode · OpenClaw · Reasonix ve proje dosyalarını okuyabilen her ajan.
- **Türkiye'ye göre:** TDK yazım kuralları, Türkçe yapay zekâ klişeleri, kitap mağazası ve yayınevi pratikleri, dergi ve öykü yarışmaları, sesli kitap ve dizi/film uyarlama yolu.
- **Ek model ya da GPU gerekmez.** Yazan model, kullandığınız ajanın modelidir. Yerelde yalnızca standart kütüphaneyle yazılmış Python denetim betikleri çalışır.

> **Wattpad notu:** Wattpad, Türkiye'de 12 Temmuz 2024'ten beri mahkeme kararıyla erişime kapalıdır (Eylül 2026 itibarıyla engel sürüyor). `wattpad-bolum-planla` ve `roman-tara` becerileri bu durumu bilir; ölçüler bütün bölümlü yayın platformlarında geçerlidir ve paket erişim engelini aşma yöntemi önermez.

## Kurulum

Python 3.11 ya da üstü gerekir (denetim betikleri ve kancalar için).

### Claude Code (eklenti pazar yeri)

```text
/plugin marketplace add cumabozkurt/ai-hikaye-roman-olusturma
/plugin install ai-hikaye-roman-olusturma@ai-hikaye-roman-olusturma
```

Eklentiyle kurulan beceriler ad alanıyla çağrılır: `/ai-hikaye-roman-olusturma:roman-yaz`. Güncellemek için `/plugin marketplace update ai-hikaye-roman-olusturma`.

### Her ajan için tek komut (npx skills)

```bash
npx skills add cumabozkurt/ai-hikaye-roman-olusturma -y -g
```

`-g` bütün klasörler için (kullanıcı düzeyinde) kurar; yalnızca bulunduğunuz klasöre kurmak için kaldırın. Güncellemek için aynı komutu yeniden çalıştırın.

### OpenAI Codex

```bash
codex plugin marketplace add cumabozkurt/ai-hikaye-roman-olusturma
```

Ardından Codex içinde `/plugins` menüsünden **AI Hikaye & Roman Oluşturma** eklentisini kurun. Beceriler `$roman-yaz` ya da `/skills` ile çağrılır. Depoyu klonladıysanız `.agents/skills` bağlantısı sayesinde beceriler kendiliğinden bulunur.

### OpenCode, Antigravity, ZCode, OpenClaw, Reasonix ve diğerleri

Depoyu klonlayıp kurulum betiğini çalıştırın:

```bash
git clone https://github.com/cumabozkurt/ai-hikaye-roman-olusturma.git
cd ai-hikaye-roman-olusturma
bash betikler/kur.sh            # Claude Code, Codex ve OpenCode kullanıcı klasörlerine kopyalar
# Windows: powershell -ExecutionPolicy Bypass -File betikler\kur.ps1
```

ZCode için depo kökündeki `marketplace.json`, Reasonix için `reasonix-plugin.json` kullanılabilir. Ev sahiplerine göre ayrıntılar ve sorun giderme: [docs/ev-sahipleri.md](docs/ev-sahipleri.md).

### Yazım projesine kurulum (her ortamda bir kez)

Yazım projenizin kök klasöründe ajanınıza şunu söyleyin ya da komutu çalıştırın:

```text
/hikaye-kurulum
```

(Codex'te `$hikaye-kurulum`.) Bu adım ajanları, kancaları, proje kurallarını ve ortak kaynakları projeye güvenle kurar; kendi `CLAUDE.md`/`AGENTS.md` içeriğiniz ve ayarlarınız korunur. **Kurulumdan sonra yeni bir oturum açın.** Codex kancaları ilk kullanımda `/hooks` ile güven onayı ister. Her sürüm yükseltmesinden sonra `/hikaye-kurulum` komutunu yeniden çalıştırın.

## İlk isteğiniz

Size uyanı kopyalayın, köşeli parantez içindeki yer tutucuları değiştirip gönderin:

1. **Yeni kitap:** "[tür/öncül] bir roman başlatmak istiyorum. Önce elimdeki malzemede kesinleşmiş olgularla açık kararları ayır. Yalnızca açılışı planla: ana çatışma, bakış açısı ve bilgi verme sınırları, ilk üç bölümdeki değişim ve benim onaylamam gereken kararlar. Metin yazma."
2. **Var olan taslak:** "Bu taslağı devam ettirilebilir bir projeye dönüştür. 1–[N]. bölümler tamam; [dosya] yarım bir bölüm. Özgün metne dokunma, yarım bölümü tamam sayma, çıkarımla bulduğun bilgileri onayıma sun. Henüz devam yazma."
3. **Beğenmediğim bir bölüm:** "Bu bölüm [bulanık/tekrarlı/fazla açıklayıcı] okunuyor. Hikâye olgularını, karakterlerin bildiklerini ve açıklanmamış bilgileri koruyarak sorunu adlandır; yalnızca bu parçanın düzeltme önerisini, önce/sonra karşılaştırmasını ve gerekçelerini ver."

## Beceriler

| Beceri | Ne işe yarar | Üst kaynak karşılığı |
|---|---|---|
| `hikaye` | Giriş noktası ve yönlendirici; çoklu kitap, yazar hafızası, yerel çalışma masası | `story` |
| `hikaye-kurulum` | Ajan, kanca, kural ve kaynakları 8 ev sahibine güvenle kurar | `story-setup` |
| `roman-tara` | Türkiye roman pazarı ve Wattpad taraması; gerekçeli tür/konu önerisi | `story-long-scan` |
| `oyku-tara` | Öykü yayın yerleri (dergi, yarışma, seçki) ve eğilim taraması | `story-short-scan` |
| `roman-cozumle` | Romanı yapısal olarak çözümler; bölüm dizini, özetler, üslup profili, ilham kütüphanesi | `story-long-analyze` |
| `oyku-cozumle` | Kısa öyküyü çekirdek, yapı, duygu yayı ve dönüm noktası açısından çözümler | `story-short-analyze` |
| `roman-yaz` | Genel plan, cilt ve bölüm planı, bölüm bölüm yazım, günlük yazım, revizyon | `story-long-write` |
| `oyku-yaz` | 1.500–10.000 kelimelik öykü: duygu hedefi, sahne planı, yazım, son okuma | `story-short-write` |
| `yz-tadi-gider` | Türkçe yapay zekâ kalıplarını satır satır bulur ve giderir | `story-deslop` |
| `metin-incele` | Editör gözüyle 100 puanlık çok bakışlı inceleme | `story-review` |
| `hikaye-ice-aktar` | Word/TXT/Markdown taslağı ya da yayımlanmış bölümleri projeye aktarır | `story-import` |
| `kapak-tasarla` | Tür ve platforma göre kapak istemi, isteğe bağlı görsel üretim ve kırpma | `story-cover` |
| `tarayici-cdp` | Otomatik erişimi engelleyen sayfalar için yazarın kendi tarayıcısıyla okuma | `browser-cdp` |
| `yazim-denetle` | TDK Yazım Kılavuzu'na göre yazım ve noktalama denetimi | yeni |
| `sureklilik-denetle` | Ölü karakter, süresi geçen ipucu, gizli bilgi sızıntısı, ad kayması avı | yeni |
| `wattpad-bolum-planla` | Bölüm uzunluğu, bölme, telefonda okunurluk, yayın takvimi ve tampon | yeni |
| `yayinevi-dosyasi` | Yayınevine gönderilecek paket: künye, örnek bölümler, sinopsis, ön yazı | yeni |
| `uyarlama-sinopsis` | Dizi, film ve dijital platform için sinopsis, karakter dosyası, tretman | yeni |
| `sesli-kitap-hazirla` | Seslendirme metni, süre tahmini, telaffuz sözlüğü | yeni |

Doğal dil de tetikler: "roman yazalım" → `roman-yaz`, "bu çok yapay zekâ gibi" → `yz-tadi-gider`, "taslağımı içeri al" → `hikaye-ice-aktar`, "çalışma masasını aç" → `hikaye`, "Defne şu an nerede?" → `proje-kasifi` ajanı.

## Nasıl çalışır?

Ayrıntılar: [docs/mimari.md](docs/mimari.md).

1. **Dosya sistemi hafızadır.** Kitap klasöründe `kurgu/`, `plan/`, `metin/` ve `takip/` ayrı tutulur. `takip/_takip-durumu.json` tek yapılandırılmış kaynaktır; bağlam kartı, ipuçları, karakter durumları ve **yazar gerçeği / okur bilgisi** ikili zaman çizelgesi bu dosyadan üretilir. Türetilmiş görünümleri elle değiştirmek `denetle` tarafından yakalanır.
2. **Yedi uzman ajan:** hikaye-mimari (yapı), anlati-yazari (metin), tutarlilik-denetcisi (süreklilik), karakter-tasarimcisi, hikaye-arastirmaci, proje-kasifi ve bolum-cikarici. `/hikaye-kurulum` ile projeye kurulur.
3. **Kancalar kaliteyi korur, yalnızca biri engeller:** bölüm planı yoksa ya da önceki bölüm takibe kaydedilmemişse metin yazımı durdurulur. Diğerleri (oturum bağlamı, yazım sonrası tarama, sıkıştırma öncesi devir notu, kayıt öncesi hatırlatma, oturum günlüğü) yalnızca uyarır.

Bir bölümün yolu: `bolum-plani_007.md` → yazar istemi → anlati-yazari → `hikayectl.py bolum denetle` (sözleşme, bozulma, yapay zekâ kalıpları, uzunluk, plan kopyası) → yazım ve süreklilik denetimi → `hikayectl.py bolum kaydet` (takip tek seferde, atomik olarak güncellenir).

## Örnekler

- [`ornekler/roman/saatcinin-kizi/`](ornekler/roman/saatcinin-kizi/): Kuzguncuk'ta geçen özgün bir polisiye; kurgu, plan, iki bölüm ve takip dosyaları. Takip, `islem-ornekleri/` altındaki işlemlerden bayt bayt yeniden üretilebilir (testlerde doğrulanır).
- [`ornekler/oyku/son-vapur/`](ornekler/oyku/son-vapur/): 434 kelimelik, üç sahnelik özgün bir öykü; öykü kapılarından geçer.
- [`ornekler/yz-tadi-karsilastirma/`](ornekler/yz-tadi-karsilastirma/README.md): aynı sahnenin yapay zekâ tadı taşıyan ve giderilmiş hâli (10 bulgu → 0 bulgu).

## Geliştirme ve testler

```bash
python3 -m pip install pytest
python3 -m pytest                          # bütün testler
python3 betikler/statik_denetim.py         # beceri biçimi, bağlantılar, sürüm, eşitlik
python3 betikler/turkce_uyum_denetle.py    # CJK karakteri ve Türkçe karakter hataları
python3 betikler/paylasilanlari_esitle.py  # paylasilan/ değişince kopyaları güncelle
python3 betikler/eklenti_dosyalari_uret.py # eklenti/pazar yeri bildirimlerini üret
```

Katkı kuralları: [CONTRIBUTING.md](CONTRIBUTING.md). İnceleme raporu: [docs/INCELEME-RAPORU.md](docs/INCELEME-RAPORU.md).

## Sık sorulanlar

**Yapay zekâ tespit araçları metni hâlâ yapay zekâ olarak işaretliyor.** `yz-tadi-gider` bir yazım denetleyicisidir; hedefi okuma deneyimidir, tespit aracını atlatmak değil.

**Yarım bir romanım var, devam edebilir miyim?** Evet: `/hikaye-kurulum`, yeni oturum, `/hikaye-ice-aktar`, çıkarımları onaylayın, sonra `/roman-yaz`.

**Bölüm uzunlukları tutmuyor.** Her bölüm planında `Hedef uzunluk: 2.200 kelime` satırı zorunludur; ölçü tek ve makinedir (`gorunur_kelime_v1`). Kısa bölüm yeni olayla şişirilmez, uzun bölüme en çok bir sıkıştırma geçişi yapılır.

**Güncellemeden sonra ne yapmalıyım?** `/hikaye-kurulum` komutunu yeniden çalıştırıp yeni oturum açın.

## Kaynak ve Teşekkür

Bu proje, [zenstory-ai/oh-story-claudecode](https://github.com/zenstory-ai/oh-story-claudecode) (MIT, v0.7.11) projesinin mimarisine ve iş akışlarına dayanır: beceri yapısı, takip durumu ve türetilmiş görünümler, kanca tasarımı, ajan rolleri ve ev sahibi uyarlamaları oradan gelir. Özgün projeyi geliştiren ve açık kaynak olarak paylaşan oh-story-claudecode katkıcılarına teşekkür ederiz.

Türkçe sürümde bütün metinler, istemler, tür kartları, denetçiler ve örnekler yeniden yazılmıştır. Özgün depodaki Çince örnek metinler, çözümlenen üçüncü taraf eserlerden alıntılar ve kapak görselleri telif nedeniyle bu depoya alınmamıştır. Aktarılmayan diğer parçalar ve nedenleri: [docs/INCELEME-RAPORU.md](docs/INCELEME-RAPORU.md).

## Lisans

[MIT](LICENSE). Telif hakkı © 2025-2026 oh-story-claudecode · © 2026 Cuma Bozkurt.
