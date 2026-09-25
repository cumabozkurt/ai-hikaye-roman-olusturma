# Takibi İçe Aktarılan Kitap İçin Başlatma

1. **Karakterler (`karakter_anliklari`):** Adı geçen her karakter için son bilinen `konum`, `durum`, `hedef`, `bildikleri`, `yasam_durumu` (hayatta / öldü / kayıp / bilinmiyor). Ana karakterlerde `kimlik` alanı ayrıntılı olsun.
2. **İpuçları (`ipuclari`):** Metinde ekilmiş ama çözülmemiş her merak unsuru `F001` biçiminde numaralanır; `ekildigi_bolum` gerçek bölüm, `planlanan_cozum_bolumu` yazarın planına göre (bilinmiyorsa boş).
3. **Olaylar (`zaman_olaylari`):** Okurun bilmediği ama yazarın bildiği gerçekler `gizli`; okura yarım gösterilenler `kısmen` (+ `acilma_bolumu`); açığa çıkanlar `açık`. `anahtar_kelimeler` sızıntı denetimi için 2–5 sözcük.
4. **Zaman çizelgesi:** Bölüm başına kısa bir satır; tarih ya da göreli zaman ("ertesi sabah").
5. **Bağlam (`baglam`):** kalıcı kısıtlar (dünya kuralları, yazarın yasakları), süreklilik riskleri (benzer adlar, karışabilecek olaylar).
6. **Son bölüm:** `son_bolum` = içe aktarılan son bölümün numarası (betik bunu `son_kaydedilen_bolum` ve `ice_aktarilan_son_bolum` olarak saklar).

Başlangıç girdisinin tam örneği: depo içindeki `ornekler/roman/islem-ornekleri/baslangic.json`.

Emin olmadığın hiçbir bilgiyi uydurma; `[belirsiz]` yaz ve rapordaki "Belirsizler" listesine ekle.
