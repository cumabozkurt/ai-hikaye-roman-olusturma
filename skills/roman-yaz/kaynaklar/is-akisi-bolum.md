# İş Akışı: Bir Bölüm Yazmak (13 adım)

Bu akış her bölüm için aynen uygulanır. Adım atlanmaz; bir kapı kalırsa sorun düzeltilir ve aynı kapı yeniden çalıştırılır.

## Hazırlık

1. **Kitabı ve bölümü belirle.** `.aktif-kitap` dosyası ya da tek kitap. Bölüm numarası = son kayıtlı bölüm + 1 (`takip/_takip-durumu.json` içindeki `son_kaydedilen_bolum`). Önceki bölüm kaydedilmemişse önce onu kaydet.
2. **Bağlamı oku.** `takip/baglam.md` (yedi bölümlü bağlam kartı: son durum, karakter konumları, kim neyi biliyor, açık ipuçları, kalıcı kısıtlar, süreklilik riskleri, sonraki bölüm için notlar). Gerekirse önceki bölümün son 300 kelimesini oku.
3. **Plan sözleşmesini al.**

```bash
python3 betikler/plan_gorunumu.py <kitap>/plan/bolum-plani_NNN.md --sozlesme
```

Plan yoksa ya da `--denetle` hata veriyorsa önce planı `kaynaklar/bolum-plani-sablonu.md` ile tamamla ve yazara onaylat.

4. **Üslup kararını ver.** `kaynaklar/uslup-karari.md`: istek > `kurgu/ton.md` > yazar hafızası (`yazar_hafizasi.py sorgula`) > tür kartı > genel kaynaklar.
5. **Yazar istemini üret.**

```bash
python3 betikler/yazar_istemi_olustur.py --proje <kitap> --bolum N --cikti
```

İskelet `<kitap>/.hikaye/calisma/bolum-NNN/yazar-istemi.md` dosyasına yazılır. "⟦ana oturum doldurur⟧" işaretli sekiz yuvayı doldur: tür düzyazı kartı (tür kartından 5–8 madde), üslup kararı, yazar hafızası makbuzu, sahne akışı, karakter sesleri, yasak kalıplar, önceki bölümün son sahnesi, özel notlar. Bir yuva boş kalamaz; bilgi yoksa "yok" yaz.

## Yazım

6. **Yazdır.** `anlati-yazari` ajanına istemi ver. Metin doğrudan `<kitap>/metin/bolum-NNN_kisa-baslik.md` dosyasına yazılır; ilk satır `# Bölüm N: Başlık`. Ajan yoksa aynı istemle ana oturumda yaz ve "Yedek: tek başına yürütüldü" notu düş.
7. **Ajan raporunu oku.** Yazar ajan `===` ile ayrılmış raporunda plan dışı kararları ve belirsizlikleri bildirir. Plan dışı karar varsa yazara sor ya da metni plana döndür.

## Kapılar

8. **Sert kapılar.**

```bash
python3 betikler/hikayectl.py bolum denetle --proje <kitap> --bolum N
```

Denetlenenler: plan sözleşmesi, metin dosyası, bozulma (kesik son, tekrar döngüleri, yapay zekâ öz göndermesi, Markdown artıkları), yapay zekâ kalıplarının engelleyici olanları, uzunluk bandı, planla metin arasında kopya ve önceki bölümün kaydı. Çıkış 1 ise raporu oku, düzelt, tekrar çalıştır.

9. **Yazım ve noktalama.**

```bash
python3 betikler/noktalama_duzelt.py <metin> --yaz
python3 betikler/yazim_denetle.py <metin>
```

`hata` düzeyindeki bulguları düzelt; `uyarı` düzeyindekileri bağlama göre değerlendir (karakter konuşmasındaki gayriresmî dil bilinçli olabilir).

10. **Süreklilik.**

```bash
python3 betikler/sureklilik_denetle.py --proje <kitap> --bolum N
```

Ölü karakterin konuşması, süresi geçmiş ipucu, henüz açılmamış bir sırrın sızması, isim kayması ve nitelik çelişkisi (göz rengi, yaş) yakalanır. Bulgu yanlış alarmsa gerekçesini rapora yaz.

11. **Anlam düzeyinde okuma.** Betikler kalıpları yakalar, anlamı yakalayamaz. Metni baştan sona bir kez oku: bölüm planındaki değişim gerçekleşti mi, kanca çalışıyor mu, karakterler kendi sesiyle mi konuşuyor? Gerekirse `tutarlilik-denetcisi` ajanını çağır.

## Kayıt ve rapor

12. **Kaydet.** Takip işlemini `<kitap>/.hikaye/calisma/bolum-NNN/islem.json` olarak hazırla: `beklenen_revizyon`, `kip: "ekle"`, bölüm özeti, karakter değişimleri, ana karakterlerin anlık durumu, olaylar (gizli / kısmen / açık), ipuçları, zaman çizelgesi, bağlamın tamamı.

```bash
python3 betikler/hikayectl.py bolum kaydet --proje <kitap> --bolum N --girdi <kitap>/.hikaye/calisma/bolum-NNN/islem.json
```

Uzunluk iç bandın dışındaysa ve yazar bunu onayladıysa `--yazar-onayladi` ekle. Revizyon uyuşmazlığı hatası alırsan `takip_kaydet.py goster` ile güncel revizyonu oku ve işlemi yeniden hazırla; asla elle `takip/` dosyası düzenleme.

13. **Rapor ver.** `kaynaklar/yazar-raporu.md` biçimini kullan.

## Parti yazımı

Yazar birden fazla bölüm isterse en çok 3 bölümlük partiler hâlinde çalış. Her bölüm 1–12. adımları tamamlamadan bir sonrakine geçilmez (önceki bölüm kaydedilmeden yeni bölüm denetimi geçmez). Parti sonunda tek bir toplu rapor ver ve devam için onay iste.
