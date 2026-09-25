---
name: tarayici-cdp
description: "Otomatik erişimi engelleyen ya da JavaScript ile çizilen sayfaları (kitap mağazası çok satan listeleri, yayınevi dosya kabul sayfaları, yarışma şartnameleri) yazarın bilgisayarında ayrı profilli bir Chrome ile açıp metnini okur. Tetikleyiciler: /tarayici-cdp, \"bu sayfayı oku\", \"Kitapyurdu listesine bak\", \"tarayıcıyla aç\"."
license: MIT
compatibility: "Python 3.11+, yerelde Chrome, Chromium ya da Edge. Uzak/sunucusuz ortamlarda çalışmaz."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "oh-story-claudecode/browser-cdp"}
---

# tarayici-cdp: Tarayıcıyla Sayfa Okuma

Basit web getirme araçlarının okuyamadığı sayfaları, yazarın kendi bilgisayarında Chrome DevTools Protokolü (CDP) ile açıp **yalnızca görünen metni** okursun.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## Güvenlik kuralları

- Tarayıcı yalnızca `127.0.0.1` üzerinde dinler ve yazarın kişisel profilinden **ayrı** bir profil (`~/.hikaye-cdp-profil`) kullanır.
- Yalnızca metin okunur: tıklama, form doldurma, satın alma, mesaj gönderme, çerez ya da parola okuma yok.
- Giriş gerektiren sayfada oturumu yazar kendisi açar; sen kimlik bilgisi istemez, yazmazsın.
- Sitenin kullanım koşullarına ve robots kurallarına saygı: tek tek sayfa oku, toplu kazıma yapma, istekler arasında bekle.
- Okunan metin, başka yazarların eserlerini kopyalamak için kullanılmaz; yalnızca liste, başlık, şartname gibi bilgiler özetlenir.

## Akış

1. **Başlat:**

```bash
python3 betikler/cdp_chrome_baslat.py            # zaten açıksa yeniden başlatmaz
```

Tarayıcı bulunamazsa yazardan yolu iste (`--tarayici "C:\…\chrome.exe"`).

2. **Oku:**

```bash
python3 betikler/cdp_istemci.py oku --adres "https://…" --bekle 4
```

Çıktıdaki `metin` alanı sayfanın görünen metnidir (varsayılan en çok 20.000 karakter, `--azami` ile değişir). Metin boşsa sayfa yüklenmemiş, engellenmiş ya da doğrulama (CAPTCHA) istiyor olabilir: yazardan tarayıcı penceresinde sayfayı açıp doğrulamayı geçmesini iste, sonra `sekmeler` ve `metin --sekme <kimlik>` ile oku.

3. **Diğer komutlar:** `sekmeler`, `ac --adres`, `metin --sekme`, `kapat --sekme`.
4. **Kapat:** İş bitince yazara tarayıcıyı kapatabileceğini söyle.

## Kullanıldığı yerler

`/roman-tara` ve `/oyku-tara` (mağaza listeleri, yarışma şartnameleri), `/yayinevi-dosyasi` (yayınevlerinin dosya kabul koşulları).
