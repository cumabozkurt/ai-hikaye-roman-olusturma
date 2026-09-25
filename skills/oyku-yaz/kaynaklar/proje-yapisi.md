# Proje Yapısı

Klasör ve dosya adları ASCII'dir (Türkçe karakter içermez); böylece Windows, git ve bulut eşitleme araçlarında kodlama sorunu çıkmaz. Dosyaların içeriği tamamen Türkçedir.

## Uzun roman

```
{Kitap}/
├── metin/                     # bölümler: bolum-001_baslik.md
├── plan/
│   ├── genel-plan.md          # tür, okur sözleşmesi, ciltler
│   ├── cilt-plani_1.md        # "> Kapsam:" satırlarıyla bölümlenmiş
│   └── bolum-plani_001.md     # her bölüm için (Hedef uzunluk zorunlu)
├── kurgu/
│   ├── ton.md                 # üslup dosyası
│   ├── tur-konumu.md          # tür ve okur konumu
│   ├── iliskiler.md           # "Kimden | Kime | İlişki | Bölüm | Not" tablosu
│   ├── karakterler/{ad}.md    # Yaş / Göz rengi / Saç rengi satırlarıyla
│   └── dunya/{konu}.md
├── takip/                     # yalnızca takip_kaydet.py yazar
│   ├── _takip-durumu.json
│   ├── baglam.md
│   ├── ipuclari.md
│   ├── karakter-durumu/{ad}.md
│   ├── zaman-cizelgesi/{yazar-gercegi,okur-bilgisi}.md
│   └── bolum-kayitlari/bolum-NNN.md
├── arastirma/                 # hikaye-arastirmaci notları
├── karsilastirma/{kitap}/     # örnek alınan kitaplardan seçilmiş çözümleme parçaları
├── .yz-beyaz-liste            # bilinçli tercih edilen kalıplar (isteğe bağlı)
└── .hikaye/
    ├── calisma/bolum-NNN/     # geçici dosyalar (bölüm kaydedilince silinir)
    └── yazar-hafizasi/        # kitaba özgü tercihler
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
