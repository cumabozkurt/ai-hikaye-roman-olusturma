---
name: yazim-panosu
description: "Yazma alışkanlığını ve sürümleri yönetir: kitap, bitiş tarihi ve günlük kelime hedefi; yazma serisi, 7 günlük hız, tahmini bitiş, gereken günlük hız, bölüm ilerlemesi ve HTML pano; anlık görüntü, iki sürüm arasında satır ve kelime farkı, geri yükleme; nerede kaldım raporu. Tetikleyiciler: /yazim-panosu, \"günlük hedef\", \"ne kadar yazdım\", \"ne zaman biter\", \"sürüm al\", \"eski hâline döndür\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kitaplık)."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "yeni"}
---

# yazim-panosu: Hedefler, İstatistikler ve Sürümler

Yazarın düzenli yazmasına ve hiçbir cümlesini kaybetmemesine yardım edersin. Bu becerideki betikler yazarın metnine dokunmaz; yalnızca `geri-yukle`, yazarın açık isteğiyle dosyaları eski sürüme döndürür.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## Oturum başında

```bash
python3 betikler/proje_durumu.py durum --proje <kitap>
python3 betikler/yazim_istatistik.py pano --proje <kitap>
```

## Hedefler ve günlük kayıt

```bash
python3 betikler/yazim_istatistik.py hedef --proje <kitap> --toplam 90000 --bitis 2027-03-01 --gunluk 1000
python3 betikler/yazim_istatistik.py kaydet --proje <kitap>     # her yazma oturumunun sonunda
python3 betikler/yazim_istatistik.py pano --proje <kitap> --html pano.html
```

Veri `.hikaye/istatistik.json` dosyasında tutulur. İlk kayıt başlangıç çizgisidir (o güne kadar yazılanlar "bugün yazıldı" sayılmaz). Pano: toplam kelime, bugün yazılan, yazma serisi, son 7 günün ortalaması, hedefe yüzde, bu hızla tahmini bitiş, bitiş tarihine yetişmek için gereken günlük hız, son 30 günün grafiği, bölümlerin plan hedefine göre ilerlemesi, sayfa (250 kelime/sayfa) ve okuma süresi (dakikada 200 kelime) tahmini. Rakamlar yazarı suçlamak için değil, gerçekçi takvim kurmak içindir.

## Anlık görüntüler (sürümler)

```bash
python3 betikler/anlik_goruntu.py al --proje <kitap> --not "3. bölüm revizyonundan önce"
python3 betikler/anlik_goruntu.py listele --proje <kitap>
python3 betikler/anlik_goruntu.py fark --proje <kitap> --a son~1 --b son          # iki sürüm arası
python3 betikler/anlik_goruntu.py fark --proje <kitap> --a son --kelime            # son sürüm ile şu anki hâl, kelime düzeyinde
python3 betikler/anlik_goruntu.py geri-yukle --proje <kitap> --kimlik son~1 --dosya metin/bolum-003_kapi.md
python3 betikler/anlik_goruntu.py geri-yukle --proje <kitap> --kimlik 20260925-101500 --hepsi --onayla
python3 betikler/anlik_goruntu.py dogrula --proje <kitap>
python3 betikler/anlik_goruntu.py temizle --proje <kitap> --tut 30
```

- `metin/`, `plan/`, `kurgu/`, `takip/` ve `arastirma/` altındaki metin dosyaları `.hikaye/anliklar/` içinde içerik adresli (SHA-256) saklanır: değişmeyen dosya ikinci kez yer kaplamaz; hiçbir şey değişmediyse yeni görüntü alınmaz.
- `geri-yukle` önce mevcut hâlin güvenlik görüntüsünü alır, sonra döndürür; bu yüzden geri yükleme de geri alınabilir. `--hepsi` yalnızca `--onayla` ile çalışır; yazar açıkça istemeden kullanma.
- Git kullanan yazar için bu, Git'in yerine değil yanına bir güvenlik ağıdır.

Ne zaman görüntü al: büyük revizyondan önce, `bolum-dongusu` kabulünden önce (otomatik alınır), her yazma haftasının sonunda.

## Çalışma masası

`/hikaye` becerisindeki `calisma_masasi.py`, bu verilerin hepsini tarayıcıda salt okunur bir panelde gösterir (yalnızca 127.0.0.1): sıradaki adım, istatistikler, kurgu ansiklopedisi ve dağılım ısı haritası, sahne kartları, ipucu şeridi, döngü puanları ve sürümler. Yazar "panoyu aç" derse `/hikaye` becerisinin 5. adımına geç.
