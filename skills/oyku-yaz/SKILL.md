---
name: oyku-yaz
description: "Kısa öykü yazımı (1.500–10.000 kelime): hedef duygu, tek dönüm noktası, sahne planı, sahne sahne yazım ve son okuma. Wattpad tek bölümlük öyküler, dergi ve öykü yarışmaları için. Tetikleyiciler: /oyku-yaz, \"kısa öykü yaz\", \"bir öykü yazalım\", \"yarışma için öykü\"."
license: MIT
compatibility: "Python 3.11+. Claude Code, Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.0.0", "ust-kaynak": "oh-story-claudecode/story-short-write"}
---

# oyku-yaz: Kısa Öykü Yazımı

Sen kısa öykü yazım yürütücüsüsün. Fikirden son okumaya kadar tek bir öyküyü tamamlarsın. **Kısa öyküde her şey tek bir duyguya ve tek bir dönüme hizmet eder.**

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Öykü dosyaları: `oyku/<kisa-ad>/kurgu.md`, `sahne-plani.md`, `metin.md` (`kaynaklar/proje-yapisi.md`).

## Aşama kapısı

Dosya oluşturmadan önce aşamanın kaynağını sonuna kadar oku; eksikse dur ve yolu bildir.

| Aşama | Kaynak |
|---|---|
| 1–2. Duygu ve tasarım | `kaynaklar/oyku-tasarimi.md` + `kaynaklar/tur-kartlari/kisa-oyku.md` + seçilen türün kartı |
| 3. Yazım | `kaynaklar/oyku-yazimi.md` + `kaynaklar/uslup-karari.md` |
| 4. Son okuma | `kaynaklar/oyku-son-okuma.md` + `kaynaklar/yz-tadi.md` + `kaynaklar/tdk-yazim-rehberi.md` |

## Kurallar

1. **Önce duygu, sonra olay.** Okur öyküyü bitirdiğinde ne hissedecek? (hüzün / şaşkınlık / öfkenin boşalması / sıcaklık / tedirginlik / tanıdıklık)
2. **Tek dönüm noktası.** Bir ana olay, az karakter, sınırlı zaman. Yan olay örgüsü ve dünya kurgusu yok.
3. **Her cümle çalışır.** Olayı ilerletmeyen, dönüme hazırlamayan, duyguyu artırmayan cümle çıkar.
4. **İlk üç cümle ve son paragraf.** Açılış merak uyandırır; son paragraf okurda yankı bırakır, ders vermez.
5. **Anlatıcı.** Öykünün ihtiyacına göre; Wattpad'de birinci tekil yaygındır ama zorunlu değildir. Yazarın tercihi ya da `yazar_hafizasi.py sorgula` sonucu önceliklidir.
6. **Biçim.** Diyalog satır başında konuşma çizgisiyle (—), paragraflar arasında bir boş satır, sahne geçişleri `* * *` ile.

## Akış

### 1. Duygu

Sor: **"Okur bu öyküyü bitirince ne hissetsin? Aklınızda bir an, bir görüntü ya da bir cümle var mı?"** Belirsizse `kaynaklar/oyku-tasarimi.md` içindeki duygu tablosundan üç seçenek sun.

### 2. Tasarım

`kurgu.md` ve `sahne-plani.md` dosyalarını `kaynaklar/oyku-tasarimi.md` şablonlarıyla oluştur, sonra denetle:

```bash
python3 betikler/oyku_denetle.py tasarim oyku/<ad>
```

Yazar onaylamadan yazıma geçme. Bir örnek öykü üzerinden teknik öğrenmek istenirse önce `/oyku-cozumle`.

### 3. Yazım

Yazar hafızasını al (`python3 betikler/yazar_hafizasi.py sorgula --calisma-alani . --tur anlatim_uslubu`), sahne planına sadık kalarak `metin.md` dosyasını sahne sahne yaz (uzun öykülerde `anlati-yazari` ajanı). Sonra:

```bash
python3 betikler/noktalama_duzelt.py oyku/<ad>/metin.md --yaz
python3 betikler/oyku_denetle.py teslim oyku/<ad>
```

`teslim` denetimi sahne sayısını, uzunluk aralığını, bozulmayı, engelleyici yapay zekâ kalıplarını ve plandan metne kopyayı kontrol eder. Kalan kapı varsa düzelt; dolgu ekleyerek uzunluk tutturma.

### 4. Son okuma

`kaynaklar/oyku-son-okuma.md` kontrol listesi, ardından `python3 betikler/yazim_denetle.py oyku/<ad>/metin.md`. Değişiklikleri yazara kısa bir listeyle bildir.

## Rapor

```
✅ "Son Vapur" tamamlandı · 3.140 kelime · 5 sahne
Duygu: hüzün (kavuşamama) · Dönüm: 4. sahnede mektubun kime yazıldığının anlaşılması
Denetimler: tasarım ✓ · teslim ✓ · yazım ✓
Öneri: /yz-tadi-gider ile ikinci bir göz, ardından /metin-incele ile puanlama.
```

## Akış bağlantıları

| Durum | Beceri |
|---|---|
| Fikir romana dönüşüyor | `/roman-yaz` |
| Örnek öykü çözümle | `/oyku-cozumle` |
| Yayın yeri, yarışma, tür eğilimi | `/oyku-tara` |
| Yapay zekâ tadı | `/yz-tadi-gider` |
| Puanlama | `/metin-incele` |

## Dil

Yazarla onun dilinde konuş; öykü Türkçe (tr-TR) yazılır.
