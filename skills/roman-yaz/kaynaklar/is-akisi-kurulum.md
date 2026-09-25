# İş Akışı: Kitabı Kurmak (Aşama 1–4)

Bu dosya yapı tartışmasından ilk bölüm yazılmaya hazır olana kadar geçen dört aşamayı anlatır. Her aşamanın sonunda yazardan açık onay al; onaysız bir sonraki aşamaya geçme.

## 1. Yapı tartışması

Amaç: kitabın okur sözleşmesini netleştirmek.

1. Yazara sor: **"Bu kitabı bitiren okur ne hissetmeli, hangi soruyu merak ederek sayfa çevirmeli?"**
2. Tür yoksa `kaynaklar/tur-kartlari/README.md` dizininden en fazla üç aday öner; her aday için okur beklentisi, Türkiye'deki yayın yolu (Wattpad, basılı, e-kitap; `kaynaklar/platformlar-turkiye.md`) ve tipik uzunluğu yaz.
3. Seçilen türün kartını sonuna kadar oku. Karttaki "Kaçınılacaklar" listesini öncül tartışmasında kullan.
4. Üç öncül seçeneği sun. Her biri: bir cümlelik öncül, ana çatışma, kahramanın arzusu ve korkusu, ana merak sorusu, ilk bölümün kancası.
5. Yazar seçince `kurgu/tur-konumu.md` ve `kurgu/ton.md` dosyalarını oluştur:
   - `tur-konumu.md`: tür, alt tür, hedef okur, yayın yolu, okur sözleşmesi (3–5 madde), kıyaslanabilir kitaplar (yalnızca ad; alıntı yok).
   - `ton.md`: anlatıcı (birinci tekil / yakın üçüncü tekil / her şeyi bilen), zaman kipi, cümle ritmi, diyalog biçimi (konuşma çizgisi —), argo ve küfür sınırı, mizah dozu, yasak kalıplar.

## 2. Genel plan

`hikaye-mimari` ajanıyla `plan/genel-plan.md` dosyasını hazırla:

- **Öncül ve tema** (tek paragraf).
- **Beş aşamalı omurga:** Başlangıç, Gelişme, Dönüm, Doruk, Kapanış. Her aşama için kabaca bölüm aralığı, ana olay ve kahramanın içsel değişimi.
- **Ciltler / kısımlar:** Wattpad dizisi için 25–40 bölümlük kısımlar; basılı roman için tek cilt ya da seri.
- **Karakter kadrosu:** ana karakterler için `kurgu/karakterler/<ad>.md` (`karakter-tasarimcisi`). Her dosyada `Göz:`, `Saç:`, `Yaş:` satırları süreklilik denetiminde kullanılır.
- **Dünya:** mekânlar ve kurallar `kurgu/dunya/` altında. Gerçek bir Türkiye mekânı kullanılıyorsa `hikaye-arastirmaci` ile doğrula.
- **İlişkiler:** `kurgu/iliskiler.md` (kim kime ne borçlu, kim kimden ne saklıyor).
- **Ana gizemler ve ipuçları:** hangi sır hangi aşamada açılacak.

Kontrol: Omurga okur sözleşmesindeki soruyu Doruk'ta yanıtlıyor mu? Kahramanın arzusu ile korkusu Dönüm'de çatışıyor mu?

## 3. Cilt ve bölüm planı

1. `plan/cilt-plani_1.md`: cildin bölüm listesi, her bölüme bir satırlık işlev, cilt sonu kancası.
2. İlk 3 bölüm için `plan/bolum-plani_NNN.md` dosyalarını `kaynaklar/bolum-plani-sablonu.md` şablonuyla doldur. Şablondaki 16 alanın, 4 alt başlığın ve akış tablosunun tamamı zorunludur.
3. Her planı denetle:

```bash
python3 betikler/plan_gorunumu.py plan/bolum-plani_001.md --denetle
```

4. Plan metni düzyazı olmamalı: sahneyi değil işlevi yaz ("Defne kapağın içindeki tarihi fark eder → Kerem'e yalan söyler" gibi).

## 4. Kitabı aç

1. Takibi başlat. Başlangıç girdisi karakterleri, mekânları, açık ipuçlarını ve kalıcı kısıtları içerir (örnek: `ornekler/roman/islem-ornekleri/baslangic.json`, biçim: `kaynaklar/takip-protokolu.md`):

```bash
python3 betikler/takip_kaydet.py baslat --proje <kitap> --girdi baslangic.json
```

2. Birden fazla kitap varsa çalışma alanı kökündeki `.aktif-kitap` dosyasına kitap klasörünün adını yaz.
3. Yazar hafızası yoksa başlat: `python3 betikler/yazar_hafizasi.py baslat --calisma-alani .`
4. Yazara kısa bir "kitap açıldı" raporu ver: tür, hedef bölüm sayısı, bölüm başına hedef uzunluk, ilk bölümün işlevi.
