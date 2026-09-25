# Katkı Rehberi

Katkılarınız memnuniyetle karşılanır: yeni beceri, tür kartı, Türkçe yapay zekâ kalıbı, yazım kuralı, platform bilgisi güncellemesi ya da hata düzeltmesi.

## Temel kurallar

1. **Dil:** Kullanıcıya dönük bütün metinler (SKILL.md, kaynaklar, ajanlar, betik iletileri, belgeler) Türkiye Türkçesidir; TDK yazımına ve ç ğ ı İ ö ş ü harflerine dikkat edin. `python3 betikler/turkce_uyum_denetle.py` temiz geçmelidir.
2. **Tek doğru kaynak:** Birden çok becerinin kullandığı betik ve kaynaklar `paylasilan/` altındadır. Orayı düzenleyin, sonra `python3 betikler/paylasilanlari_esitle.py` çalıştırın. Beceri içindeki kopyaları elle düzenlemeyin.
3. **Bildirimler:** Sürüm, ad ve açıklamalar yalnızca `betikler/eklenti_dosyalari_uret.py` içinde değişir; ardından betiği çalıştırın. Sürüm değişince `kur.py` içindeki `SURUM`, SKILL.md `metadata.surum` alanları ve `CHANGELOG.md` de güncellenir (statik denetim tutarsızlığı yakalar).
4. **Beceri biçimi:** Ön bilgi alanları `name`, `description` (çift tırnaklı, tek satır, en çok 500 karakter), `license`, `compatibility`, `metadata` (tek satır JSON). `name` klasör adıyla aynıdır. SKILL.md 500 satırın altında kalır; ayrıntı `kaynaklar/` altına gider. Bir beceri başka bir becerinin dosyasına başvurmaz.
5. **Betikler:** Yalnızca Python standart kütüphanesi (Pillow yalnızca isteğe bağlı kırpma için). Python 3.11+ uyumlu. Kullanıcı dosyalarının üzerine sormadan yazılmaz; yazma atomik yapılır. Ağ erişimi olan betikler yalnızca herkese açık uç noktaları, düşük hızla kullanır; anahtarlar yalnızca ortam değişkeninden okunur ve çıktıya yazılmaz.
6. **Testler:** Her yeni betik için `testler/` altında test yazın (kapsam bekçisi testi eksik betiği yakalar). Her yeni beceri için `evals/<beceri>-tetiklenir/` altında bir `claude plugin eval` vakası ekleyin; `test_degerlendirme_paketi_gecerli_ve_her_beceriyi_kapsiyor` eksik vakayı yakalar. Betik hataları kullanıcıya Türkçe tek satırla gösterilir; geliştirirken tam Python izi için `HIKAYE_AYIKLA=1` kullanın. Örnek projeleri testlerde doğrudan değiştirmeyin; `roman`/`oyku` fikstürleri geçici kopya verir.
7. **Telif:** Üçüncü taraf eserlerden uzun alıntı, görsel ya da metin eklemeyin. Çözümleme örneklerinde en çok iki kısa cümle.

## Yerel denetimler

```bash
python3 -m pip install pytest
python3 -m pytest
python3 betikler/statik_denetim.py
python3 betikler/turkce_uyum_denetle.py
python3 betikler/paylasilanlari_esitle.py --denetle
python3 betikler/eklenti_dosyalari_uret.py --denetle
```

Claude Code yüklüyse eklenti ve SKILL.md ön bilgilerini ayrıca `claude plugin validate .` ile doğrulayabilirsiniz (Claude Code 2.1.233 ve sonrası). Becerilerin doğal isteklerle tetiklenip tetiklenmediğini ölçmek için `claude plugin eval . --runs 1 --ablation none` (Claude hesabı gerekir; sonuçlar `evals/results/` altına yazılır ve depoya eklenmez).

README'deki terminal görselleri gerçek komut çıktısından üretilir; betik çıktıları değiştiğinde `python3 betikler/terminal_gorseli.py` ile yenileyin.

CI (`.github/workflows/test.yml`) aynı denetimleri Linux, macOS ve Windows'ta Python 3.11–3.14 ile çalıştırır.

## Bilinçli yanlış yazım örnekleri

Yazım kurallarını anlatan belgelerde yanlış örnek vermeniz gerekirse satırın sonuna `<!-- turkce-uyum: yoksay -->` ekleyin; Türkçe uyum denetimi o satırdaki yazım kuralını atlar. `tdk-yazim-rehberi.md` dosyaları zaten muaftır.

## Hata bildirimi

GitHub Issues'taki formları kullanın: hata, özellik isteği ya da çıktı kalitesi örneği. Yeniden üretilebilir adımlar ve mümkünse kısa bir çıktı örneği ekleyin.
