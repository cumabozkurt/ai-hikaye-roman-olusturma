# İnceleme Raporu

Bu rapor, üst kaynak [zenstory-ai/oh-story-claudecode](https://github.com/zenstory-ai/oh-story-claudecode) (MIT, v0.7.11, `401019ea` işlemesi) ile bu deponun (AI Hikaye & Roman Oluşturma 1.0.0) yayın öncesi ayrıntılı incelemesini kaydeder. İnceleme altı bakış açısından yapıldı; her bakış açısı için bulunan eksik ve hatalar ile yapılan düzeltmeler listelenir.

İnceleme tarihi: 25 Eylül 2026.

## Özet

| Bakış açısı | Bulgu | Düzeltilen | Açık kalan |
|---|---|---|---|
| (a) İşlevsellik ve üst kaynağa göre bütünlük | 9 | 9 | 0 |
| (b) Türkçe dil kalitesi ve tr-TR uyumu | 10 | 10 | 0 |
| (c) Türkiye pazarı ve kültürel uygunluk | 8 | 8 | 0 |
| (d) Güncel teknoloji ve ev sahibi uyumluluğu | 13 | 13 | 0 |
| (e) Kod kalitesi, testler, güvenlik ve sağlamlık | 12 | 12 | 0 |
| (f) Belgeler ve kurulum deneyimi | 9 | 9 | 0 |

Son durum: 90 test geçiyor (Python 3.11, 3.13 ve 3.14 ile yerelde denendi), statik denetim 0 hata, Türkçe uyum denetimi 0 bulgu, depoda CJK karakteri 0.

## (a) İşlevsellik ve üst kaynağa göre bütünlük

Üst kaynakta 13 beceri, 7 ajan, 8 kanca olayı, bölüm takip sistemi, Node.js ve Python betikleri ile Playwright testleri vardı.

| # | Bulgu | Düzeltme |
|---|---|---|
| a1 | 13 becerinin tamamı eşlenmeli, hiçbir özellik kaybolmamalı. | Hepsi eşlendi: `hikaye`, `hikaye-kurulum`, `roman-tara`, `oyku-tara`, `roman-cozumle`, `oyku-cozumle`, `roman-yaz`, `oyku-yaz`, `yz-tadi-gider`, `metin-incele`, `hikaye-ice-aktar`, `kapak-tasarla`, `tarayici-cdp`. Eşleme tablosu README'de. |
| a2 | 7 ajanın görev tanımları Türkçe yazım akışına uyarlanmalı. | 7 ajan Türkçe yeniden yazıldı (`skills/hikaye-kurulum/varliklar/ajanlar/`); Claude, Codex (TOML), OpenCode ve ZCode biçimlerine dönüştürülüyor. |
| a3 | Üst kaynağın takip sistemi (işlem, revizyon, türetilmiş görünüm) korunmalı. | `hikayectl.py` ve `takip_kaydet.py` aynı sözleşmeyi uygular: eski revizyon reddi, atomik yazma, elle düzenleme tespiti. Örnek romanın takip dosyaları işlemlerden bayt bayt yeniden üretiliyor (test). |
| a4 | Kanca olayları: üst kaynakta 8 olay. | 9 olay: oturum başı, sıkıştırma sonrası, çağrı öncesi (Antigravity), yazı öncesi, kayıt öncesi, yazı sonrası, sıkıştırma öncesi, oturum sonu, dur. Tek çekirdek (`hikaye_kanca.py`). |
| a5 | Üst kaynak OpenCode için yalnızca 2.x eklenti API'sini destekliyordu. | Hem 1.x (`ai-hikaye-v1.ts`) hem 2.x (`ai-hikaye-v2.ts`) eklentisi; kurulum sürümü algılıyor. |
| a6 | Playwright uçtan uca ve pano testleri Node gerektiriyordu. | pytest'e taşındı; kurulum, kanca, takip, çözümleme, tarama ve yayın akışlarını kapsayan 90 test. |
| a7 | Üst kaynağın Çin mağazası kazıyıcıları Türkiye'de işe yaramaz. | Wattpad herkese açık API'si + `tarayici-cdp` ile yazarın kendi tarayıcısı; bkz. (c). |
| a8 | Türkiye'deki yazarın ihtiyaç duyduğu yayın sonrası adımlar üst kaynakta yoktu. | 6 yeni beceri: `yazim-denetle`, `sureklilik-denetle`, `wattpad-bolum-planla`, `yayinevi-dosyasi`, `uyarlama-sinopsis`, `sesli-kitap-hazirla`. |
| a9 | Yapay zekâ tadı giderme için önce/sonra örneği yoktu (üst kaynağın örnekleri Çinceydi). | `ornekler/yz-tadi-karsilastirma/`: önceki hâlde 10 bulgu (6 engelleyici), sonraki hâlde 0; test ediliyor. |

## (b) Türkçe dil kalitesi ve %100 tr-TR uyumu

| # | Bulgu | Düzeltme |
|---|---|---|
| b1 | README örnek isteklerinde CJK köşeli ayraçlar (U+3008 ve U+3009) kalmıştı. | `[ ]` ile değiştirildi. |
| b2 | `metin_olcum.py` düzenli ifadesinde tam genişlikli iki nokta (U+FF1A) vardı. | Kaldırıldı; CJK taraması `.py` dosyalarını da kapsıyor. |
| b3 | argparse iletileri İngilizceydi (`usage`, `error`, `the following arguments are required`). | Paylaşılan `turkce_argparse.py` modülü `kullanım`, `seçenekler`, `hata`, `şu argümanlar zorunlu`, `geçersiz seçim` vb. çevirileri uygular; bütün betiklere eklendi, testle doğrulanıyor. |
| b4 | Oranlarda ondalık ayırıcı nokta idi ("108.7"). | `tr_ondalik()` ile virgül: "1.000 kelimede 108,7". |
| b5 | Klasör ve dosya adları ASCII olduğu için denetleyici bunları yanlış yazım sanabilirdi. | Türkçe uyum denetimi kod bloklarını, satır içi kodu, bağlantı hedeflerini, HTML'yi ve tire/alt çizgili tanımlayıcıları atlıyor; düzyazı ile ön bilgi açıklamasını denetliyor. |
| b6 | Otomatik bir Türkçe uyum denetimi yoktu. | `betikler/turkce_uyum_denetle.py`: `cjk` (Han, Hiragana, Katakana, Hangul, tam genişlikli biçimler), `ascii-turkce` (ASCII'leştirilmiş Türkçe sözcükler), `yazim` (herkez, birşey, şuan, yalnış…), `kodlama` (U+FFFD, UTF-8 dışı), `ingilizce` (düzyazıya sızan İngilizce işlev sözcükleri). CI'da ve pytest'te çalışıyor; 5 olumsuz test her kuralın gerçekten hata verdiğini doğruluyor. |
| b7 | Kullanıcıya dönük hata iletilerinde İngilizce kalıntı kalmamalı. | Paylaşılan betiklerde `Error`, `Warning`, `not found` gibi sözcükleri arayan test eklendi. |
| b8 | Yazım kurallarını anlatan belgelerde bilinçli yanlış örnekler denetimi bozar. | `tdk-yazim-rehberi.md` ve bu rapor `yazim` kuralından muaf; diğer belgelerde satır sonuna `<!-- turkce-uyum: yoksay -->` konabiliyor. |
| b9 | Terim birliği: "yapay zekâ" (şapkalı), "bölüm planı", "bağlam kartı", "takip" gibi terimler her yerde aynı olmalı. | Belgeler ve SKILL.md dosyaları tarandı; şapkasız yazım (`yapay zeka`) 0; Türkçe uyum denetimi bunu da yakalıyor. |
| b10 | "Yapay zekâ tadı" kalıpları çeviri değil, Türkçeye özgü olmalı. | Kalıplar Türkçe düzyazıya göre yeniden tanımlandı: "değil…, …ydı" dönüşü, "bir yandan… diğer yandan", "yoktu" dizileri, çeviri kalıpları ("günün sonunda", "fark yaratmak"), edilgen çeviri yapıları. |

## (c) Türkiye pazarı ve kültürel uygunluk

| # | Bulgu | Düzeltme |
|---|---|---|
| c1 | **Wattpad Türkiye'de erişime kapalı.** Ankara 10. Sulh Ceza Hâkimliğinin 2024/6507 sayılı kararıyla 12 Temmuz 2024'ten beri engelli; Eylül 2026 itibarıyla engel sürüyor. İlk taslak Wattpad'i birincil platform gibi sunuyordu. | `platformlar-turkiye.md`, `wattpad-rehberi.md`, `wattpad-bolum-planla` ve `roman-tara` becerileri ile README'ye erişim notu eklendi. Beceri açıklaması "Wattpad ve benzeri bölümlü çevrim içi yayın" oldu. `liste_tara.py` bağlantı hatasında durumu Türkçe açıklıyor ve `--girdi` seçeneğini öneriyor. Engeli aşma yöntemi önerilmiyor. |
| c2 | BluTV, HBO Max'e dönüştü (Nisan 2025). | Uyarlama platformları listesi güncellendi. |
| c3 | Dergi ve yarışma başvurularında eş zamanlı gönderim yasağı gibi yerel kurallar yoktu. | Notos'un güncel gönderim kuralları (Word, 12 punto, 1,5 satır aralığı, 4–5 A4 sayfa, eş zamanlı gönderim yok, 3 ay yanıt gelmezse ret) ve dergilerin genel yasağı eklendi. |
| c4 | Tarama çıktısının klasörü belgelerde farklı adlandırılmıştı. | Bütün belge ve becerilerde `pazar/`. |
| c5 | Kitap mağazaları (Kitapyurdu, D&R, idefix, BKM, Amazon.com.tr) otomatik isteklere kapalı. | Kazıyıcı yazılmadı; yazarın tarayıcısıyla görünen metin okunuyor, veri kaynağıyla yazılıyor. |
| c6 | Türler Türk okurunun raf düzenine uymalı. | 12 tür kartı: romantik, genç kurgu, fantastik, polisiye, tarihî, psikolojik gerilim, bilimkurgu/distopya, korku/doğaüstü, aile dramı, mizah, edebî kurgu, kısa öykü. |
| c7 | Yayınevi başvuru dosyası Türkiye alışkanlıklarına göre olmalı. | `yayinevi-dosyasi`: ön yazı, sinopsis, örnek bölüm, biyografi; sözleşme ve telif için "hukuki danışmanlık değildir" uyarısı. |
| c8 | Diyalog dizgisi Türk yayıncılık geleneğine uymalı. | Konuşma çizgisiyle diyalog ve tırnak kullanımı `tdk-yazim-rehberi.md` içinde; `noktalama_duzelt.py` satır başındaki kısa çizgiyi konuşma çizgisine (—), düz tırnağı isteğe bağlı olarak Türkçe dizgi tırnağına çeviriyor; `yazim_denetle.py` konuşma dili biçimlerini diyalogda serbest bırakıp anlatıda uyarıyor. |

Kaynaklar: [İFÖD, Wattpad erişime engellendi](https://ifade.org.tr/engelliweb/wattpad-erisime-engellendi/), [NTV, Wattpad erişim engelinde son durum](https://www.ntv.com.tr/teknoloji/wattpad-erisim-engelinde-son-durum-wattpad-ne-zaman-acilacak,blKogul2VUuF-Ze7da5Tpw), [Warner Bros. Discovery basın bülteni, Türkiye lansmanı 15 Nisan 2025](https://press.wbd.com/us/media-release/hbo-max/max-launches-turkey-april-15), [Cumhuriyet, Max Türkiye'de yayında](https://www.cumhuriyet.com.tr/kultur-sanat/dunyanin-en-buyuk-dijital-platformlarindan-max-turkiyedeki-yayin-2319213), [HBO Max yardım merkezi, BluTV aboneleri](https://help.hbomax.com/tr-en/answer/detail/000002564), [Notos Kitap, yayımlanma koşulları](https://notoskitap.com/yayimlanma-kosullari/).

## (d) Güncel teknoloji ve ev sahibi uyumluluğu

| # | Bulgu | Düzeltme |
|---|---|---|
| d1 | Agent Skills belirtimi: `name` klasör adıyla aynı, küçük harf/rakam/tire, en çok 64 karakter; `description` en çok 1024 karakter; taşınabilirlik için yalnızca `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. | Ön bilgi yalnızca beş belirtim alanını kullanıyor; açıklamalar 500 karakterle sınırlı (Claude Code listesindeki 1.536 karakter sınırının da altında); `metadata` dizgiden dizgiye eşleme. Statik denetim bunları zorunlu kılıyor. |
| d2 | Claude Code: SKILL.md 500 satırın altında kalmalı, ayrıntı destek dosyalarına taşınmalı. | Statik denetim 500 satırı aşan SKILL.md'yi reddediyor; ayrıntılar `kaynaklar/` altında. |
| d3 | Claude Code eklentileri kök `hooks/hooks.json` dosyasını kendiliğinden yükler. | Kök `hooks/` bilinçli olarak yok; kancalar yalnızca `hikaye-kurulum` ile projeye kuruluyor (bkz. mimari kararlar MK-5). Test bunu koruyor. |
| d4 | Claude Code pazar yeri: `.claude-plugin/marketplace.json` ve eklenti bildirimi güncel şemaya uymalı. | Bildirimler tek üreticiden (`eklenti_dosyalari_uret.py`) çıkıyor; CI `--denetle` ile sapmayı yakalıyor. |
| d5 | Codex kancaları: `Stop` yerine oturum kapanışında `SessionEnd`; `SessionStart` ve `PostToolUse` ek bağlamı varsayılan olarak yaklaşık 2.500 jetonla sınırlı. | Codex kurulumu `SessionStart`, `PreToolUse`, `PostToolUse`, `PreCompact`, `SessionEnd` yazıyor; `additionalContextLimit` 4000 ve 3000; Windows için `commandWindows`. Test güncellendi. |
| d6 | Codex becerileri `~/.agents/skills` ve depo içi `.agents/skills` altında aranıyor; eklenti bildirimi `.codex-plugin/plugin.json`. | `.agents/skills -> ../skills` bağlantısı, `.agents/plugins/marketplace.json` ve `.codex-plugin/plugin.json`. Windows'ta bağlantı yerine düz dosya çıkarsa statik denetim bunu kabul ediyor, CI'da `core.symlinks` açılıyor. |
| d7 | Agent Plugins şeması (`plugin.schema.json` 1.0.0) izin verilen alanları sınırlıyor. | Kök `plugin.json` yalnızca şemadaki alanları kullanıyor; test ediliyor. |
| d8 | OpenCode 2.x eklenti API'si 1.x'ten farklı (göç rehberi). | İki ayrı eklenti dosyası; beceriler `~/.config/opencode/skills` (ya da `$XDG_CONFIG_HOME`) altına kuruluyor, ajanlar OpenCode ajan biçiminde. |
| d9 | Windows'ta `python3` komutu olmayabilir. | Her SKILL.md'de yedek not: önce `python3`, yoksa `python`, Windows'ta `py -3`. |
| d10 | Python sürümleri: güncel kararlı sürüm 3.14; en düşük desteklenen 3.11. | CI Ubuntu'da 3.11–3.14, Windows ve macOS'ta 3.13. Yerelde 3.11.16, 3.13.5 ve 3.14.7 ile bütün testler çalıştırıldı; bütün `.py` dosyaları 3.11 sözdizimiyle derleniyor. |
| d11 | pytest 9: `--strict-markers`, `testpaths`. | `pytest.ini` bu ayarlarla; ağ gerektiren testler `ag` işaretiyle ayrılıyor. |
| d12 | GitHub Actions eylemlerinin eski ana sürümleri Node 20 uyarısı veriyor. | `actions/checkout@v5`, `actions/setup-python@v6`. |
| d13 | İlk CI koşusunda Windows'ta örnek takip dosyaları bayt bayt eşleşmedi: git depoyu CRLF ile açıyor, betikler ise platformun varsayılan satır sonuyla yazıyordu. | `.gitattributes` ile bütün metin dosyaları LF; üretilen dosyalar (takip, istem, takvim, dosya paketi, sesli kitap, kanca durumu) her platformda `newline="\n"` ile yazılıyor. Yazarın kendi dosyasını yerinde düzelten `noktalama_duzelt.py` platform varsayılanını korur. |

## (e) Kod kalitesi, testler, güvenlik ve sağlamlık

| # | Bulgu | Düzeltme |
|---|---|---|
| e1 | `kur.py`, `~/.agents/skills` içindeki kullanıcının başka becerilerini de projeye kopyalayabiliyordu. | Yalnızca SKILL.md'sinde paket kimliği bulunan beceriler kopyalanıyor. |
| e2 | Süreklilik denetimi "Defne Aras" öldüyse metindeki "Defne"yi yakalamıyordu. | Tam adın yanında, karakterler arasında benzersizse ilk ad da eşleşiyor; test eklendi. |
| e3 | Kapak betiği `--kuru` çıktısında API anahtarı görünmemeli. | Anahtar maskeleniyor; anahtar yoksa Türkçe hata ve çıkış kodu; test ediliyor. |
| e4 | Kullanıcı dosyalarının üzerine yazılmamalı. | Dosya paketi, sesli kitap ve kurulum mevcut dosyayı korur; `--yeniden` gibi açık bir seçenek gerekir. Bozuk JSON ayar dosyası üzerine yazılmıyor, sembolik bağlantı hedefine yazma reddediliyor (testli). |
| e5 | Yarım yazılmış durum dosyası takip sistemini bozar. | Bütün durum yazımları geçici dosya + `os.replace` ile atomik. |
| e6 | Geçersiz takip işlemi durumu yarıda değiştirmemeli. | Doğrulama önce, yazma sonra; test durumun değişmediğini doğruluyor. |
| e7 | CDP istemcisi ağdan erişilebilir olmamalı. | Hata ayıklama bağlantı noktası yalnızca `127.0.0.1`; ayrı tarayıcı profili; yalnızca görünen metin okunuyor. |
| e8 | Wattpad API'sine yük bindirilmemeli. | İstekler arasında 1 saniye, sayfa sınırı, oturum ve kişisel veri yok. |
| e9 | Yeni betikler testsiz kalabilir. | "Kapsam bekçisi" testi, her betik adının testlerde geçtiğini denetliyor. |
| e10 | Paylaşılan kopyalar zamanla birbirinden ayrışabilir. | `paylasilanlari_esitle.py --denetle` CI'da; içe aktarma bağımlılıkları da otomatik çözülüyor. |
| e11 | Kurulum betikleri (`kur.sh`, `kur.ps1`) `__pycache__` ve bağlantılı hedefleri taşımamalı. | İkisi de önbellek klasörlerini atıyor, bağlantılı hedefleri atlıyor; `kur.sh` geçici `HOME` ile test ediliyor. |
| e12 | CDP testi Windows'ta JSON çıktısındaki kaçışlı ters eğik çizgiler yüzünden yolu bulamıyordu. | Test çıktıyı JSON olarak çözüp karşılaştırıyor. |

## (f) Belgeler ve kurulum deneyimi

| # | Bulgu | Düzeltme |
|---|---|---|
| f1 | Kurulum komutları depo adıyla tutarlı olmalı. | Bütün komutlar `cumabozkurt/ai-hikaye-roman-olusturma` ve `ai-hikaye-roman-olusturma@ai-hikaye-roman-olusturma` ile. |
| f2 | Eklentiyle kurulan becerilerin ad alanıyla çağrıldığı anlatılmıyordu. | README ve `ev-sahipleri.md`: `/ai-hikaye-roman-olusturma:roman-yaz`. |
| f3 | `npx` ya da eklenti sistemi olmayan kullanıcı için kurulum yolu yoktu. | `betikler/kur.sh` (macOS/Linux) ve `betikler/kur.ps1` (Windows): Claude, Codex, OpenCode ya da hepsi. |
| f4 | Ev sahibine göre sorun giderme yoktu. | `docs/ev-sahipleri.md`: 8 ev sahibi için kurulum, kanca dosyaları, güven onayı (Codex `/hooks`) ve sık sorunlar. |
| f5 | Mimari gerekçeler kayıt altında değildi. | `docs/mimari.md` ve `docs/mimari-kararlar.md` (7 karar). |
| f6 | Kullanım rehberleri eksikti. | `docs/bilgi-tabani.md`, `docs/yz-tadi-giderme.md`, `docs/100-bolum-tutarlilik.md`, `docs/liste-tarama-ve-cozumleme.md`. |
| f7 | Hata bildirimi için yapılandırılmış form yoktu. | `.github/ISSUE_TEMPLATE/`: hata, özellik isteği, çıktı kalitesi örneği. |
| f8 | Katkı kuralları ve yerel denetimler yazılı değildi. | `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`; isteğe bağlı `claude plugin validate .` notu. |
| f9 | Kaynak gösterme ve lisans. | README'de "Kaynak ve Teşekkür" bölümü; LICENSE her iki telif satırını içeriyor; CHANGELOG 1.0.0. |

## Aktarılmayanlar ve gerekçeleri

| Üst kaynak öğesi | Gerekçe |
|---|---|
| ClawHub yayın iş akışı | Gizli anahtar gerektiriyor; bu depo için anlamlı değil. |
| Playwright uçtan uca ve pano testleri | pytest ile yeniden yazıldı. |
| Çin mağaza kazıyıcıları ve yazı tipi karıştırma çözücüsü | Türkiye'de karşılığı yok; Wattpad API'si ve yazarın tarayıcısı kullanılıyor. |
| Çince örnek projeler, üçüncü taraf çözümleme alıntıları, kapak görseli, pano ekran görüntüsü | Telif ve dil; yerine özgün Türkçe örnekler yazıldı. |
| İngilizce README ve iki dilli belgeler | Ürün yalnızca Türkçe. |
| Üst kaynağın geliştirme araçları (belge bütçesi, beceri numaralandırma, npm paketi, Node kancaları) | Python araçlarıyla değiştirildi. |
| Telegram ve topluluk bağlantıları | Üst kaynağa özgü. |

## Başvurulan belgeler

- Claude Code becerileri: <https://code.claude.com/docs/en/skills>
- Claude Code eklenti başvurusu: <https://code.claude.com/docs/en/plugins-reference>
- Claude Code eklenti pazar yerleri: <https://code.claude.com/docs/en/plugin-marketplaces>
- Claude Code kancaları: <https://code.claude.com/docs/en/hooks>
- Agent Skills belirtimi: <https://agentskills.io/specification>
- Agent Plugins şeması: <https://agent-plugins.org/schemas/1.0.0/plugin.schema.json>
- Codex becerileri: <https://developers.openai.com/codex/skills>
- Codex alt ajanları: <https://developers.openai.com/codex/subagents>
- Codex kancaları: <https://developers.openai.com/codex/hooks>
- Codex eklenti oluşturma: <https://developers.openai.com/codex/plugins/build>
- OpenCode becerileri: <https://opencode.ai/docs/skills/>
- OpenCode eklentileri (1.x): <https://opencode.ai/docs/plugins/>
- OpenCode 2.x eklentileri: <https://opencode.ai/v2/docs/plugins>
- OpenCode 1.x'ten 2.x'e göç: <https://opencode.ai/v2/docs/migrate-v1/>
- OpenCode 2.x ajanları: <https://opencode.ai/v2/docs/agents>
- Python sürümleri: <https://www.python.org/downloads/>
- pytest: <https://docs.pytest.org/en/stable/>
- GitHub Actions `setup-python`: <https://github.com/actions/setup-python>
- TDK Yazım Kılavuzu: <https://sozluk.gov.tr/>

---

## İkinci Tur

İnceleme tarihi: 25 Eylül 2026 · Sürüm: 1.0.0 → 1.1.0.

Birinci turdan sonra bütün dosyalar (beceriler, ajanlar, kancalar, betikler, testler, bildirimler, belgeler, CI) üç bağımsız bakışla **yeniden ve baştan** okundu; her bakış bir öncekinin raporuna bakmadan kendi listesini çıkardı. Dördüncü, kısa bir bakış Türkiye pazarına göre ürün önceliklerini değerlendirdi.

### Özet

| Bakış | Bulgu | Düzeltilen | Açık kalan |
|---|---|---|---|
| (i) Kuşkucu kıdemli Python ve araç mühendisi | 9 | 9 | 0 |
| (ii) Türk editör ve romancı | 13 | 13 | 0 |
| (iii) İlk kez kullanan / geliştirici ilişkileri | 10 | 9 | 1 (sosyal önizleme görseli elle yüklenmeli) |
| (iv) Türkiye pazarı ve ürün stratejisi | 4 | 3 | 1 (yol haritasında) |

Son durum: 140 test geçiyor (Python 3.11, 3.13, 3.14 yerelde; CI'da Ubuntu 3.11–3.14, macOS, Windows), statik denetim 0 hata, Türkçe uyum 0 bulgu, CJK 0, 394 bozuk girdi denemesinde 0 Python izi, EPUBCheck 5.1.0 ile 0 hata / 0 uyarı.

### (i) Kuşkucu kıdemli Python ve araç mühendisi

Yöntem: Her betik ve her alt komut gerçekçi ve bozuk girdilerle çalıştırıldı. Depo dışında tutulan bir deneme düzeneği (boş dosya, ikili dosya, Windows-1254 kodlu metin, UTF-8 BOM, CRLF, klasör, bozuk JSON, kök düğümü liste/null olan JSON, bozuk takip durumu, eksi ve metin sayılar) 394 komut üretti; Python izi, 0/1/2 dışı çıkış kodu ya da İngilizce hata iletisi "sorun" sayıldı.

| # | Bulgu | Düzeltme |
|---|---|---|
| i1 | İlk çalıştırmada 357 komutta **60 Python izi** (traceback): kodlama, ikili dosya, klasör yolu, JSON kök türü. | Ortak `dosya_oku.py` (`metin_oku`, `json_nesne_oku`) ve `turkce_argparse.hata_iletisi()`; `sys.excepthook` beklenmeyen hatayı tek satır Türkçe iletiye çevirir (`HIKAYE_AYIKLA=1` ile tam iz). Şimdi 394 komutta 0. |
| i2 | Word'den Windows-1254 olarak dışa aktarılmış metinler `UnicodeDecodeError` ile düşüyordu; BOM kelime sayımına giriyordu. | UTF-8 → BOM temizleme → Windows-1254 geri dönüşü (uyarıyla); ikili dosyada "Word belgesini önce .txt olarak kaydedin" iletisi. |
| i3 | JSON kökü liste ya da `null` olduğunda `AttributeError`. | `json_nesne_oku` kök türünü doğrular; 9 betikte kullanılıyor. |
| i4 | Ham `urlopen`, `json` ve `datetime` iletileri İngilizce sızıyordu. | `JSON_ILETILERI` ve `hata_iletisi` eşlemesi; `cdp_istemci` ham ağ hatasını göstermiyor. |
| i5 | **122 komut satırı seçeneğinde yardım metni yoktu.** | `turkce_argparse`, eksik yardımı `ORTAK_YARDIM` sözlüğünden doldurur; bütün betiklerin bütün alt komutlarını gezen kapsama testi eklendi. |
| i6 | Yerel çalışma masası sunucusu DNS yeniden bağlama (DNS rebinding) saldırısına açıktı. | `127.0.0.1`/`localhost` dışındaki `Host` başlıkları 403 alır; test eklendi. |
| i7 | `turkce_uyum_denetle.py` var olmayan bir yolda **sessizce 0 bulgu** veriyordu (CI'da yanlış güven). | Var olmayan yol artık hata. |
| i8 | `metin_olcum.py --hedef -5` eksi işaretini yutup 5 kabul ediyordu. | İşaret korunur, Türkçe iletiyle çıkış kodu 2. |
| i9 | `liste_tara.py --girdi` liste biçimini doğrulamadan çöküyordu. | Biçim doğrulaması ve Türkçe ileti. |

### (ii) Türk editör ve romancı

Yöntem: SKILL.md dosyaları, tür kartları, örnek bölümler ve inceleme ölçütleri bir yayınevi editörünün gözüyle okundu; ayrıca paketin kendi TDK denetçisi deponun kendi belgelerinde çalıştırıldı ("kendi yemeğini yemek").

| # | Bulgu | Düzeltme |
|---|---|---|
| ii1 | Örnek romanın ilk bölümünde "yelkovanlar on dördün üstünde": saat kadranında 14 yoktur. | "yelkovanlar on dördüncü dakika çizgisinde"; takip durumu ve özet yeniden üretildi (test bayt bayt doğruluyor). |
| ii2 | Tür kartlarındaki basılı uzunluklar İngilizce kelime normlarına göreydi; Türkçe sondan eklemeli olduğu için aynı kitap daha az kelimedir. | Dört kart düzeltildi (edebî kurgu, mizah, polisiye, romantik) ve "basılı sayfa ortalama 230–280 kelime" notu eklendi. |
| ii3 | Tür kartları bölüm yazıldıktan sonra neye bakılacağını söylemiyordu. | 12 karta toplam 36 "öz denetim sorusu"; test her kartta en az 3 soru arar. |
| ii4 | Polisiye kartı soruşturmayı yalnızca savcılık ve emniyetle anlatıyordu; kırsalda yetki jandarmadadır. | Jandarma eklendi. |
| ii5 | `metin-incele` yalnızca editör puanı veriyordu; "okur nerede bırakır?" sorusu yoktu. | `kaynaklar/okur-paneli.md`: altı Türk okur profili (Wattpad okuru, tür tutkunu, yayınevi ilk okuru, dergi okuru, sesli kitap dinleyicisi, gönülsüz okur), bırakma noktası / tutan an / akılda kalan soru tablosu. |
| ii6 | Yazarın "bu kitapta bunu bir daha görmek istemiyorum" dediği ifadeler için yer yoktu (yalnızca beyaz liste vardı). | Kitap kökünde `.yasak-kaliplar` (`ifade => öneri`); `ai_kalip_denetle` engelleyici `kitap-yasagi` bulgusu verir. |
| ii7 | Türkçe için geçerli bir okunabilirlik ölçüsü yoktu. | `metin_analizi.py`: Ateşman (1997) formülü; hece sayısı ünlü sayısından. |
| ii8 | Editörlerin en sık notu olan yakın tekrarlar ve art arda aynı kelimeyle başlayan cümleler yakalanmıyordu. | `metin_analizi.py`: 40 kelimelik pencerede kök tekrarı, cümle başı tekrarı, cümle uzunluğu sapması (tekdüze ritim), diyalog oranı, duyu dağılımı. |
| ii9 | `[TK]`, `[DOLDUR]` ya da yazar istemindeki `⟦…⟧` yuvaları yayın çıktısına sızabilirdi. | `metin_analizi` çıkış kodu 1 verir; `e-kitap-derle` bu işaretlerle derlemeyi durdurur (`--taslak` hariç). |
| ii10 | Beta okura gönderilecek okunabilir bir kopya üretilemiyordu (Wattpad Türkiye'de kapalıyken en önemli geri bildirim yolu). | Yeni `e-kitap-derle` becerisi: EPUB 3 ve tek dosyalık HTML okuma kopyası. |
| ii11 | TDK denetçisi `Türkiye'deki`, `İzmir'deki` sözcüklerini "ki ayrı yazılır" diye **yanlış** işaretliyordu. | Kesme işaretinden sonra gelen `-ki` ilgi eki atlanır; regresyon testi. |
| ii12 | TDK denetçisi `İstanbullu`, `Ankaralı` için "İstanbul'lu" öneriyordu; yapım eki kesme almaz, yani öneri **yanlıştı**. | `-lı/-li/-lu/-lü` çekim eki listesinden çıkarıldı; regresyon testi. |
| ii13 | "ör." kısaltmasından ve "1–[N]." / "XIX." sıra sayılarından sonra küçük harf "cümle başı" uyarısı veriyordu. | Kısaltma ve sıra sayısı istisnaları; regresyon testi. |

### (iii) İlk kez kullanan / geliştirici ilişkileri

Yöntem: Kurulumlar bu makinede gerçekten yapıldı (geçici `HOME` ile, kullanıcı ayarlarına dokunmadan).

| Ortam | Sürüm | Denenen | Sonuç |
|---|---|---|---|
| Claude Code | 2.1.282 | `claude plugin validate .`, `claude plugin validate skills`, `claude plugin marketplace add cumabozkurt/ai-hikaye-roman-olusturma`, `claude plugin install …@…`, `claude plugin details` | Doğrulama geçti (yalnızca geliştirici `CLAUDE.md` uyarısı), eklenti kuruldu ve etkin, beceriler yüklendi. |
| Claude Code | 2.1.282 | `claude plugin eval . --runs 1 --ablation none` (oturum açmadan) | Vakalar yüklendi, eklenti 1.1.0 olarak çözüldü; çalıştırma kimlik doğrulama gerektirdiği için ilk vakada durdu (beklenen). |
| OpenAI Codex CLI | 0.157.0 | `codex plugin marketplace add …`, `codex plugin add …@…` | Kuruldu, bütün beceriler listelendi. |
| OpenCode | 1.18.32 | `opencode debug skill` (klon içinde ve `kur.sh opencode` sonrası), `kur.py --ev opencode`, `opencode debug agent hikaye-mimari` | Bütün beceriler, 7 ajan, komutlar ve eklenti; açılışta uyarı yok. |
| npx skills | güncel | `npx skills add … -g -y` ve `… -g -a claude-code codex opencode -y` | Beceriler `~/.agents/skills` altına, Claude Code için `~/.claude/skills` bağlantılarıyla kuruldu. |

| # | Bulgu | Düzeltme |
|---|---|---|
| iii1 | README Codex'te yalnızca `/plugins` menüsünü anlatıyordu; tek komutluk `codex plugin add` yoktu. | README ve `docs/ev-sahipleri.md` güncellendi. |
| iii2 | `npx skills add … -y -g` bulunan her ajana kurmaya çalışıp çok sayıda "does not support global skill installation" satırı yazıyor; ilk kez kullanan bunu hata sanıyor. | Önerilen komut `-a claude-code codex opencode` ile; sorun giderme tablosuna açıklama. |
| iii3 | `claude plugin validate` çıktısındaki `CLAUDE.md` uyarısı açıklanmamıştı. | Sorun giderme satırı. |
| iii4 | Kurulumun doğru olduğunu anlamanın yolu yoktu. | "Kurulumu doğrulayın" adımı (`claude plugin details`, `opencode debug skill`). |
| iii5 | Üç adımlık hızlı başlangıç yoktu; ilk istek örneği aşağıda kalıyordu. | "Hızlı başlangıç" bölümü. |
| iii6 | Hata ayıklama ve kodlama sorunları için yönlendirme yoktu. | `HIKAYE_AYIKLA=1` ve Windows-1254 satırları. |
| iii7 | **Depo sayfası özgün projeye göre sönüktü:** afiş, görsel, akış şeması, çıktı örneği, karşılaştırma, yol haritası yoktu; rozetler azdı. | README yeniden tasarlandı: özgün SVG afiş, 9 rozet, öne çıkanlar ızgarası, mermaid akış şeması, önce/sonra tablosu, örnek bölüm alıntısı, gerçek komut çıktısından üretilmiş 4 terminal görseli, beceri tablosu (aşamalara göre), özgün projeyle karşılaştırma, kalite güvencesi, açılır SSS, yol haritası, yıldız geçmişi, katkı ve teşekkür. |
| iii8 | Becerilerin doğal isteklerle tetiklenip tetiklenmediği ölçülmüyordu. | `evals/`: `claude plugin eval` biçiminde 23 vaka (her beceri için tetiklenme + sonuç + Türkçe yanıt değerlendiricisi; 3 olumsuz vaka `min: 0, max: 0, arm: both`). Biçim testi her becerinin kapsandığını doğrular. |
| iii9 | GitHub'da Tartışmalar kapalı, sürüm yoktu, konu etiketleri azdı. | `gh repo edit` ile Tartışmalar, ana sayfa ve konular; `v1.1.0` sürümü Türkçe notlarla. |
| iii10 | Sosyal önizleme görseli yok. | `docs/gorseller/sosyal-onizleme.png` (1280×640) üretildi. **Açık:** GitHub API'si bu görseli ayarlamaya izin vermez; Ayarlar → Social preview üzerinden elle yüklenmeli. |

### (iv) Türkiye pazarı ve ürün stratejisi

| # | Bulgu | Durum |
|---|---|---|
| iv1 | Wattpad kapalıyken yazarların beta okura ulaşması zorlaştı; paylaşılabilir okuma kopyası değerli. | `e-kitap-derle` HTML kopyası (tek dosya, gece modu). |
| iv2 | E-kitap mağazaları ve ISBN süreci belgelenmemişti. | `e-kitap-rehberi.md`: biçimler, teslim listesi, ISBN notu (güncel koşulları mağazadan doğrulama uyarısıyla). |
| iv3 | Türkçe kelime normları (ii2) pazar beklentisini etkiliyor. | Düzeltildi. |
| iv4 | Tarihî roman okurunun büyük kısmı Osmanlı ve Cumhuriyet'in ilk yıllarına ilgi duyuyor; dönem kartları yok. | Yol haritasında. |

### Araştırma: incelenen kaynaklar ve alınan fikirler

Üst kaynağın README sunumu (`README.md`, `README_EN.md`: ortalanmış logo ve başlık, bağlantı satırı, rozetler, demo videosu, "ne üretir" görselleri, akış şeması, SSS, katkıcılar, kardeş projeler) ayrıntılı incelendi ve yeni README bu iskeleti Türkçe ve özgün görsellerle izliyor. Aşağıdaki depolardan **kod alınmadı**; yalnızca yaklaşımlar Türkçe için yeniden tasarlandı.

| Kaynak | İncelenen | Alınan fikir |
|---|---|---|
| [zenstory-ai/oh-story-claudecode](https://github.com/zenstory-ai/oh-story-claudecode) | README sunumu, demo klasörü | Sayfa iskeleti, "ne üretir" bölümü, rozet ve bağlantı satırı |
| [anthropics/skills](https://github.com/anthropics/skills) | skill-creator, `evals/evals.json` | Beceri başına değerlendirme vakası fikri |
| [Claude Code plugin eval](https://code.claude.com/docs/en/plugin-evals) | vaka ve değerlendirici biçimi | `evals/` paketi, `tool_used: Skill` tetiklenme denetimi, olumsuz vakalar |
| [Skill yazım iyi uygulamaları](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | açıklama yazımı, değerlendirme | Beceri başına en az bir gerçekçi istem, üçüncü şahıs açıklamalar |
| [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills) | okur simülasyonu, sorun takibi | Okur paneli |
| [tchr-dev/autonovel](https://github.com/tchr-dev/autonovel) | okur paneli, bölüm turnuvası, ses parmak izi | Okur paneli; turnuva ve ses parmak izi yol haritasında |
| [mrskwiw/claude-novel-writer](https://github.com/mrskwiw/claude-novel-writer) | belirlenimci düzyazı ölçümleri, [TK] taraması, revizyon öncesi anlık görüntü | `metin_analizi.py`, bitmemiş işaret kapısı; anlık görüntü yol haritasında |
| [MintoTsukino/claude-novel-workflow](https://github.com/MintoTsukino/claude-novel-workflow) | `forbidden_patterns.md`, üslup rehberi | `.yasak-kaliplar` |
| [howells/fiction](https://github.com/howells/fiction) | EPUB derleme, kelime yankısı düzeltmesi | `e-kitap-derle`, yakın tekrar ölçümü |
| [PhosAQy/novel-skills](https://github.com/PhosAQy/novel-skills) | 5 boyutlu puanlama, duygu eğrisi | İnceleme ölçütleri zaten 8 boyutlu; değişiklik gerekmedi |
| [GonsonInter/novel-writer-workflow](https://github.com/GonsonInter/novel-writer-workflow) | aşama yönlendirici, P0/P1/P2 önem düzeyi | Aşama kapısı ve engelleyici/uyarı düzeyleri zaten var |
| [chianglianglin/novel-writer](https://github.com/chianglianglin/novel-writer) | HTML okuyucu çıktısı | HTML okuma kopyası |
| Ateşman, E. (1997), "Türkçede okunabilirliğin ölçülmesi", *Dil Dergisi*, 58, 71–74 | okunabilirlik formülü | `metin_analizi.py` |
| [W3C EPUBCheck](https://github.com/w3c/epubcheck) 5.1.0 | EPUB doğrulama | Üretilen EPUB'lar 0 hata / 0 uyarı ile doğrulandı |

### İkinci turda eklenen testler

`test_saglamlik.py` (33 test: bozuk girdiler, kodlamalar, JSON kökü, Türkçe hata iletileri, bütün seçeneklerde yardım metni), `test_yeni_ozellikler.py` (15 test: Ateşman hesabı, yankı ve cümle başı tekrarı, bitmemiş işaretler, `.yasak-kaliplar`, EPUB yapısı ve yeniden üretilebilirlik, kapak, hata yolları, değerlendirme paketi biçimi, tür kartı soruları, terminal görselleri, README görsel bağlantıları, TDK yanlış alarm regresyonları) ve çalışma masası `Host` testi.
