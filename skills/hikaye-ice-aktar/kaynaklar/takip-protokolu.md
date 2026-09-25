# Süreklilik Takibi Protokolü

Uzun romanda süreklilik tek bir yapılandırılmış dosyayla tutulur: `takip/_takip-durumu.json`. Diğer bütün takip dosyaları bu dosyadan **belirlenimci olarak üretilen görünümlerdir** ve elle düzenlenmez. Bütün yazma işlemleri `takip_kaydet.py` (ya da onu çağıran `hikayectl.py bolum kaydet`) ile yapılır.

## Dosyalar

| Dosya | İçerik | Kim yazar |
|---|---|---|
| `takip/_takip-durumu.json` | Tek yetkili durum | yalnızca `takip_kaydet.py` |
| `takip/baglam.md` | 7 bölümlük bağlam kartı (en fazla 12 KB) | üretilir |
| `takip/ipuclari.md` | Açık ve kapanmış ipuçları (F###) | üretilir |
| `takip/karakter-durumu/{ad}.md` | Ana karakterlerin anlık durumu | üretilir |
| `takip/zaman-cizelgesi/yazar-gercegi.md` | Gerçekte ne oldu (E###) | üretilir |
| `takip/zaman-cizelgesi/okur-bilgisi.md` | Okur ne kadarını biliyor | üretilir |
| `takip/bolum-kayitlari/bolum-NNN.md` | Bölüm başına kısa değişim kaydı (≤ 4 KB) | üretilir |

Bağlam kartının yedi başlığı: **Şu Anki Konum, Kalıcı Kısıtlar, Ana Karakterlerin Durumu, Açık İpuçları, Son Üç Bölüm, Sonraki Bölüm Sözleri, Süreklilik Riskleri.**

## Başlatma

Yeni kitapta (hiç bölüm yokken) `son_bolum: 0`; içe aktarılan kitapta son yazılmış bölüm numarası verilir.

```json
{
  "sema_surumu": 1,
  "kitap_adi": "Saatçinin Kızı",
  "son_bolum": 0,
  "baglam": {
    "konum": {"cilt": "1. Cilt", "cilt_baslangic_bolumu": 1, "hikaye_zamani": "Kasım", "sahne": "Dükkân"},
    "kalici_kisitlar": ["…"], "aktif_karakterler": ["Defne Aras"], "sureklilik_riskleri": [],
    "son_bolumler": [], "sonraki_bolum_sozleri": ["…"]
  },
  "karakter_anliklari": {"Defne Aras": {"kimlik": "…", "durum": "…", "hedef": "…", "yasam_durumu": "hayatta"}},
  "ipuclari": [],
  "zaman_olaylari": []
}
```

Komut: `python3 takip_kaydet.py baslat --proje KITAP --girdi baslangic.json`

## Bölüm işlemi

Her bölümden sonra küçük bir **anlamsal işlem** hazırlanır; uzunluk kaydını `hikayectl.py` kendisi ekler.

```json
{
  "sema_surumu": 1,
  "kip": "ekle",
  "bolum": 7,
  "bolum_basligi": "Bakkal Sabri",
  "beklenen_revizyon": 6,
  "degisim": {
    "sonuc": "İki cümlelik olay özeti.",
    "karakter_degisimleri": [{"ad": "Defne Aras", "degisim": "…"}],
    "ipucu_degisimleri": [{"islem": "ekle", "id": "F005", "ozet": "…", "onem": "orta", "durum": "ekili", "ekildigi_bolum": 7, "planlanan_cozum_bolumu": 12}],
    "zaman_olaylari": [{"islem": "guncelle", "id": "E001", "nesnel_olgu": "…", "aciga_cikma": "kısmen", "acilma_bolumu": 7, "anahtar_kelimeler": ["kırmızı defter"]}],
    "sonraki_bolum_sozleri": ["…"],
    "emekliye_ayrilan_baglam": [],
    "emekliye_ayrilan_karakterler": []
  },
  "baglam": {"konum": {…}, "kalici_kisitlar": […], "aktif_karakterler": […], "sureklilik_riskleri": […]},
  "karakter_anliklari": {"Defne Aras": {…}}
}
```

Komut: `python3 hikayectl.py bolum kaydet --proje KITAP --bolum 7 --girdi .hikaye/calisma/bolum-007/takip.json`

### Kurallar

- **İyimser kilit**: `beklenen_revizyon` durumun şu anki `durum_revizyonu` değerine eşit olmalıdır; değilse durum başka biri tarafından değişmiştir, işlem yeniden hazırlanır.
- **Bağlam bütün gönderilir**: Kalıcı kısıtlar ve süreklilik riskleri her işlemde eksiksiz yeniden yazılır. Düşen bir madde `emekliye_ayrilan_baglam` içinde açıkça bildirilmelidir; sessiz kayıp reddedilir.
- **Ana karakter değişirse anlık durumu gönderilir**: `karakter_degisimleri` içinde adı geçen bir ana karakterin güncel `karakter_anliklari` kaydı zorunludur.
- **Emeklilik yalnızca "ekle" kipinde**: Revizyon, geçmiş bir bölümü düzeltir; karakter emekliye ayırmaz.
- **Olay açığa çıkma**: `gizli` olayın açılma bölümü olmaz; `kısmen` ve `açık` olaylar için `acilma_bolumu` zorunludur. `anahtar_kelimeler`, süreklilik denetiminin sızıntı araması için kullanılır.
- **Yaşam durumu**: `hayatta`, `öldü`, `kayıp`, `bilinmiyor`. Süreklilik denetimi ölü karakterin sahnede görünmesini yakalar.

## Kurtarma

- `takip_kaydet.py denetle --proje KITAP`: görünümler durumla aynı mı?
- `takip_kaydet.py onar --proje KITAP`: görünümleri durumdan yeniden üretir (elle yapılan değişiklikler silinir).
- İşlem hata verirse durum dosyası değişmez: durum en son yazılır (tek kayıt noktası) ve proje kilidi (`takip/.kilit`) aynı anda iki yazımı engeller.
