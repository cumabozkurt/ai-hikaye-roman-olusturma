# Proje Yapısı

Klasör ve dosya adları ASCII'dir (Türkçe karakter içermez); böylece Windows, git ve bulut eşitleme araçlarında kodlama sorunu çıkmaz. Dosyaların içeriği tamamen Türkçedir.

## Uzun roman

```
{Kitap}/
├── metin/                     # bölümler: bolum-001_baslik.md
├── plan/
│   ├── genel-plan.md          # tür, okur sözleşmesi, ciltler, "Tek cümlelik öz:" ve "Bölüm sayısı:"
│   ├── cilt-plani_1.md        # "> Kapsam:" satırlarıyla bölümlenmiş
│   ├── bolum-plani_001.md     # her bölüm için (Hedef uzunluk zorunlu)
│   ├── yapi-{yontem}.md       # kurgu_plani.py baslat: üç perde, kahramanın yolculuğu, ... (isteğe bağlı)
│   ├── kar-tanesi.md          # kar tanesi yönteminin 10 adımı (isteğe bağlı)
│   └── sahneler.md            # sahne kartları tablosu (isteğe bağlı)
├── kurgu/
│   ├── ton.md                 # üslup dosyası
│   ├── tur-konumu.md          # tür ve okur konumu
│   ├── iliskiler.md           # "Kimden | Kime | İlişki | Bölüm | Not" tablosu
│   ├── karakterler/{ad}.md    # "- Alan: değer" satırları + karakter mülakatı
│   ├── mekanlar/{ad}.md       # kurgu_ansiklopedisi.py olustur --tur mekan
│   ├── nesneler/{ad}.md
│   ├── gruplar/{ad}.md
│   ├── dunya/{konu}.md
│   ├── sozluk.md              # "Terim | Anlamı | Yanlış yazımlar" tablosu
│   ├── zaman-cizelgesi.md     # "Tarih | Olay | Kişiler | Bölüm" tablosu (hikâye kronolojisi)
│   └── ses-izi.json           # ses_izi.py cikar ile çıkarılan üslup profili
├── takip/                     # yalnızca takip_kaydet.py yazar
│   ├── _takip-durumu.json
│   ├── baglam.md
│   ├── ipuclari.md
│   ├── karakter-durumu/{ad}.md
│   ├── zaman-cizelgesi/{yazar-gercegi,okur-bilgisi}.md
│   └── bolum-kayitlari/bolum-NNN.md
├── arastirma/                 # hikaye-arastirmaci notları
├── karsilastirma/{kitap}/     # örnek alınan kitaplardan seçilmiş çözümleme parçaları
├── yayin/                     # e_kitap_derle.py çıktıları (EPUB, DOCX, ODT, HTML, PDF)
│   ├── kitaptik.md            # Kitaptik yayın bilgisi: kategori, etiket, açıklama (kitaptik_hazirla.py baslat)
│   └── kitaptik/              # Kitaptik paketi: toplu yükleme DOCX'i, kitap bilgileri, karakterler, kontrol listesi
├── .yz-beyaz-liste            # bilinçli tercih edilen kalıplar (isteğe bağlı)
├── .yasak-kaliplar            # kitaba özgü yasak ifadeler: ifade => öneri (isteğe bağlı)
├── .donem-istisnalari         # donem_denetle.py'nin bilerek geçeceği sözcükler (isteğe bağlı)
└── .hikaye/
    ├── calisma/bolum-NNN/     # geçici dosyalar (bölüm kaydedilince silinir)
    ├── yazar-hafizasi/        # kitaba özgü tercihler
    ├── anliklar/              # anlik_goruntu.py: kayitlar/ (sürüm listesi) ve nesneler/ (içerik deposu)
    ├── istatistik.json        # yazim_istatistik.py: hedefler ve günlük kelime kayıtları
    ├── dongu/bolum-NNN/       # revizyon_dongusu.py: tur taslakları ve dongu.json
    ├── turnuvalar/{ad}.json   # turnuva.py: adaylar, maçlar, Elo puanları
    └── ice-aktarma/           # belge_ice_aktar.py: on-metin.md ve rapor.json
```

## Kısa öykü

```
oyku/{ad}/
├── kurgu.md          # öz, karakterler, dünya, ton
├── sahne-plani.md    # sahne sahne plan (Hedef uzunluk dahil)
└── metin.md          # öykünün kendisi
```

## Çalışma alanı kökü

```
.hikaye-kurulu          # kurulum işareti (JSON)
.aktif-kitap            # birden fazla kitap varsa etkin kitabın göreli yolu
.hikaye/kancalar/       # kanca çekirdeği ve denetleyiciler
.hikaye/kaynaklar/      # ajanların okuduğu ortak kaynaklar
.hikaye/yazar-hafizasi/ # genel yazar tercihleri
cozumleme-kutuphanesi/{kitap}/   # roman-cozumle / oyku-cozumle çıktıları
pazar/                  # roman-tara / oyku-tara raporları (ör. roman-taramasi-GG-AA-YYYY.md)
```
