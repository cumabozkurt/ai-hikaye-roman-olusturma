---
name: hikaye-ice-aktar
description: "Mevcut taslağı, Word/TXT/Markdown dosyasını ya da Wattpad'de yayımlanmış bölümleri sistemin proje yapısına aktarır: bölümlere böler, plan ve kurgu dosyalarını tersine çıkarır, karakter durumlarını ve ipuçlarını takip kaydına işler, sonra /roman-yaz ile devam edilebilir hâle getirir. Tetikleyiciler: /hikaye-ice-aktar, \"elimde yazılmış bölümler var\", \"romanımı içeri al\", \"taslağımı aktar\"."
license: MIT
compatibility: "Python 3.11+. DOCX için pandoc ya da python-docx isteğe bağlıdır; yoksa yazardan Markdown/TXT istenir."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.0.0", "ust-kaynak": "oh-story-claudecode/story-import"}
---

# hikaye-ice-aktar: Taslağı İçeri Aktarma

Yazarın dışarıda yazdığı metni kaybetmeden, değiştirmeden sistemin yapısına taşırsın. **Yazarın metnine dokunulmaz**: yalnızca bölünür, adlandırılır ve biçim (başlık, satır sonu) normalleştirilir.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Hedef yapı: `kaynaklar/proje-yapisi.md`.

## 1. Uzunluğa göre yönlendir

Kaynak dosyayı ölç (`python3 betikler/metin_olcum.py <dosya>`):

| Durum | Yol |
|---|---|
| 10.000 kelimeden az, tek olay | Kısa öykü: `oyku/<ad>/metin.md` + tersine `kurgu.md`, `sahne-plani.md` |
| Bölümlere ayrılmış ya da 10.000+ kelime | Uzun roman: aşağıdaki akış |

## 2. Biçim ve bölümleme (uzun roman)

1. Dosya türü: `.md`/`.txt` doğrudan; `.docx` için `pandoc -t gfm` (yoksa yazardan Markdown/TXT dışa aktarmasını iste). Kodlama UTF-8 değilse (Windows-1254) dönüştür.
2. Bölüm sınırlarını bul: "Bölüm 1", "BÖLÜM BİR", "1.", "#", "***" gibi desenler. Belirsizse ilk 3 sınırı yazara göster, onay al. Ayrıntı: `kaynaklar/bicim-ve-bolumleme.md`.
3. Her bölümü `metin/bolum-NNN_kisa-baslik.md` olarak yaz; ilk satır `# Bölüm N: Başlık`. Metin gövdesi bayt olarak aynı kalır (yalnızca satır sonları `\n`).
4. Doğrula: bölüm dosyalarının kelime toplamı kaynakla ±%1 içinde olmalı; değilse metin kaybı var, dur.

## 3. Tersine planlama

`proje-kasifi` ve `hikaye-mimari` ajanlarıyla (yoksa ana oturumda):

1. Her bölüm için `plan/bolum-plani_NNN.md` dosyasını `kaynaklar/bolum-plani-sablonu.md` ile doldur; `Hedef uzunluk` = mevcut kelime sayısı. Planı metinden kopyalama, işlevini yaz.
2. `kurgu/tur-konumu.md`, `kurgu/ton.md` (metnin gerçek üslubundan çıkar), `kurgu/karakterler/*.md` (`Göz:`, `Saç:`, `Yaş:` satırları dâhil), `kurgu/iliskiler.md`.
3. `plan/genel-plan.md`: yazılmış kısmın özeti + yazarın anlattığı devam planı. Belirsiz kısımları `[doldurulacak]` bırak ve yazara sor.
4. Denetle: `python3 betikler/plan_denetle.py sozlesme <kitap>/plan/bolum-plani_*.md` ve her bölüm için `python3 betikler/plan_denetle.py kopya --plan … --metin …`.

## 4. Takibi başlat

Ayrıntı `kaynaklar/takip-ilklendirme.md` ve `kaynaklar/takip-protokolu.md`.

1. Son bölüme göre başlangıç durumu hazırla: karakterlerin son konumu ve durumu, kim neyi biliyor, açık ipuçları (`F001…`), gizli/kısmen/açık olaylar, zaman çizelgesi.
2. Başlangıç girdisindeki `son_bolum` alanını son bölüm numarasıyla doldur; betik bunu `son_kaydedilen_bolum` ve `ice_aktarilan_son_bolum` olarak kaydeder, böylece `roman-yaz` N+1'den devam eder.

```bash
python3 betikler/takip_kaydet.py baslat --proje <kitap> --girdi baslangic.json
python3 betikler/takip_kaydet.py denetle --proje <kitap>
```

## 5. Rapor

```
✅ İçe aktarıldı: "Rüzgârgülü" · 23 bölüm · 51.240 kelime (kaynakla fark: 0)
Oluşturulanlar: 23 metin · 23 bölüm planı · 6 karakter · genel plan (12–40 [doldurulacak])
Takip: son bölüm 23 · 9 açık ipucu · 2 gizli olay
Belirsizler: Selin'in yaşı (17 mi 19 mu?), 14. bölümdeki tarih
Sıradaki: /roman-yaz ile Bölüm 24 planı
```
