---
name: bolum-dongusu
description: "Bir bölümü yazar kontrolünde ölçülebilir puanla iyileştirir: mekanik ölçüm (YZ kalıpları, ritim, tekrar, uzunluk, ses izi), bölüm planından çıkarılan maddelerle hakem rubriği, tur kaydı, plato ve hedef kararı, revizyon talimatı, yazar onayıyla kabul; taslakları Elo ile sıralayan bölüm turnuvası; üslup parmak izi. Tetikleyiciler: /bolum-dongusu, \"bölümü puanla\", \"bu bölümü iyileştir\", \"hangi taslak daha iyi\", \"üslubum kaydı mı\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kitaplık). Hakem için alt ajan desteği (Claude Code, Codex, OpenCode) önerilir; yoksa ana oturum hakemlik yapar."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "yeni"}
---

# bolum-dongusu: Yaz → Eleştir → Düzelt Döngüsü, Turnuva ve Ses İzi

Bir bölümü "bence daha iyi oldu" ile değil, tur tur kaydedilen ve karşılaştırılabilen puanlarla iyileştirirsin. **Direksiyon yazardadır**: döngü hiçbir zaman bölüm dosyasını kendiliğinden değiştirmez; her turdan sonra yazara sonucu gösterir, kabul yalnızca yazar onayıyla yapılır.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## 0. Ses izi (bir kez)

Yazarın kendi yazdığı en az 3.000 kelimelik metinden üslup profili çıkar:

```bash
python3 betikler/ses_izi.py cikar --proje <kitap> --bolumler 1-5      # kurgu/ses-izi.json
python3 betikler/ses_izi.py cikar --proje <kitap> --dosya ornek1.md ornek2.md
python3 betikler/ses_izi.py karsilastir --proje <kitap> --dosya taslak.md
```

Profil; cümle uzunluğu ortalaması ve değişkenliği, paragraf uzunluğu, diyalog oranı, sözcük çeşitliliği, noktalama sıklıkları, işlev sözcükleri ve Türkçe zarf-fiiller (`-ken`, `-ınca`, `-ıp`, `-arak`) gibi ölçülerden oluşur. `karsilastir`, her ölçünün sapmasını z puanıyla ve 0–100 benzerlikle verir. Sapma bir hata değil, soru işaretidir: yazara "Burada cümleleriniz her zamankinden iki kat uzun; bilinçli mi?" diye sor.

## 1. Tur akışı

1. **Taslak:** `/roman-yaz` akışıyla ya da yazarın verdiği metinle bir taslak dosyası (`.hikaye/calisma/bolum-NNN/taslak.md` gibi).
2. **Mekanik ölçüm:**

```bash
python3 betikler/revizyon_dongusu.py olc --proje <kitap> --bolum 7 --dosya taslak.md
```

0–10 arası alt puanlar: `yz_kaliplari`, `ritim`, `tekrar`, `uzunluk` (plan hedefine göre), `ses` (profil varsa). `[TK]`, `[doldurulacak]` gibi bitmemiş işaretler kapıdır: varken hedefe ulaşıldı kararı verilmez.

3. **Hakem:** Rubriği al ve **taze bağlamlı** bir hakeme ver (`bolum-hakemi` ajanı; yoksa ana oturumda yazarın metnini yazmamış gibi oku):

```bash
python3 betikler/revizyon_dongusu.py rubrik --proje <kitap> --bolum 7
```

Rubrik altı ölçüt (`plan_sadakati`, `gerilim`, `karakter`, `somutluk`, `diyalog`, `dil`), her biri için ölçek çıpaları ve bölüm planından çıkarılmış maddeler (ana olay, kanca, doyum anı, olay akışı satırları, açığa çıkmaması gerekenler) içerir. Hakem JSON'u `hakem.json` olarak kaydedilir.

4. **Kaydet ve karar:**

```bash
python3 betikler/revizyon_dongusu.py kaydet --proje <kitap> --bolum 7 --dosya taslak.md --hakem hakem.json --hedef 8 --en-fazla-tur 4
```

Toplam = 0,4 × mekanik + 0,6 × hakem. Karar: `devam`, `dur-hedef` (hedefe ulaşıldı, kapı yok, açık plan maddesi yok), `dur-plato` (son iki turda 0,2'den az kazanç), `dur-tur-siniri`. Aynı taslak iki kez kaydedilemez.

5. **Talimat:** `devam` ise en iyi turdan revizyon talimatı üret; yeni taslağı bu talimatla yaz ve 2. adıma dön:

```bash
python3 betikler/revizyon_dongusu.py brief --proje <kitap> --bolum 7
```

6. **Yazara göster, onayla kabul et:**

```bash
python3 betikler/revizyon_dongusu.py durum --proje <kitap> --bolum 7
python3 betikler/revizyon_dongusu.py kabul --proje <kitap> --bolum 7 --tur 3 --yazar-onayladi
```

`kabul` önce bir anlık görüntü alır, sonra seçilen turu bölüm dosyasına yazar. `--yazar-onayladi` bayrağını yalnızca yazar açıkça "bu turu al" dediğinde kullan. Kabulden sonra `/roman-yaz` akışındaki `hikayectl.py bolum kaydet` adımıyla takibi güncelle.

**Sınırlar:** Puan edebî değerin kanıtı değildir; plato kararında durmak, en yüksek puanlı turu değil yazarın beğendiği turu seçmek meşrudur. Döngüyü bir bölümde en fazla 4–5 tur çalıştır; daha fazlası metni düzleştirir.

## 2. Bölüm turnuvası (birden çok taslak)

Aynı bölümün farklı yaklaşımlarla yazılmış 2–12 taslağını ikili karşılaştır:

```bash
python3 betikler/turnuva.py baslat --proje <kitap> --ad bolum-07 --aday A=taslak-a.md --aday B=taslak-b.md --aday C=taslak-c.md
python3 betikler/turnuva.py sirada --proje <kitap> --ad bolum-07       # sıradaki maç ve hakem yönergesi
python3 betikler/turnuva.py sonuc --proje <kitap> --ad bolum-07 --mac 1 --kazanan A --gerekce "Kanca daha güçlü"
python3 betikler/turnuva.py siralama --proje <kitap> --ad bolum-07
```

Her eşleşme varsayılan olarak iki sırayla oynanır (önce okunan metnin avantajını dengelemek için). Maç sonucu girilirken aday dosyası değişmişse sonuç reddedilir. Sıralama Elo puanı, galibiyet/beraberlik/yenilgi sayısıyla verilir; kazanan taslak yazara önerilir, karar yine yazarındır. Kazananın beğenilen sahnelerini diğer taslaklardan birleştirmek serbesttir.
