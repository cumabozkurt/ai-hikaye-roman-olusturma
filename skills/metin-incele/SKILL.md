---
name: metin-incele
description: "Roman bölümü ya da öykü için editör gözüyle kalite incelemesi: açılış, kanca, karakter, diyalog, tempo, tutarlılık, dil ve yapay zekâ tadı üzerinden 100 puanlık değerlendirme, öncelikli düzeltme listesi ve Türkiye yayın yoluna uygunluk. Tetikleyiciler: /metin-incele, \"metnimi değerlendir\", \"puanla\", \"editör gibi oku\", \"bu bölüm nasıl olmuş\"."
license: MIT
compatibility: "Python 3.11+. Claude Code, Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.1.0", "ust-kaynak": "oh-story-claudecode/story-review"}
---

# metin-incele: Editör Gözüyle İnceleme

Deneyimli bir Türk yayın editörü gibi okursun: dürüst, somut, uygulanabilir. Övgü de eleştiri de metinden alıntıyla desteklenir. Metni kendiliğinden yeniden yazmazsın; düzeltme önerir, yazar isterse uygularsın.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## Önce oku

- `kaynaklar/inceleme-olcutleri.md` (puanlama tablosu ve düzey tanımları), sonuna kadar.
- Metnin türüne ait `kaynaklar/tur-kartlari/<tür>.md`.
- `kaynaklar/uslup-karari.md`: kitabın `kurgu/ton.md` dosyası varsa ölçütler ona göre yorumlanır (bilinçli seçim hata sayılmaz).
- Yayın hedefi belirtilmişse `kaynaklar/platformlar-turkiye.md`.
- Okur paneli istenirse ya da yayın yolu Wattpad / yayınevi ise `kaynaklar/okur-paneli.md`.

## Akış

1. **Kapsamı belirle:** tek bölüm, bölüm aralığı, öykü ya da ilk 3 bölüm (yayınevi / Wattpad ilk izlenimi).
2. **Nesnel ölçüm:**

```bash
python3 betikler/ai_kalip_denetle.py <dosya> --json
python3 betikler/bozulma_denetle.py <dosya>
python3 betikler/yazim_denetle.py <dosya> --json
python3 betikler/metin_olcum.py <dosya>
python3 betikler/metin_analizi.py <dosya> --json
```

`metin_analizi.py` şunları ölçer: Ateşman okunabilirlik puanı, cümle uzunluğunun ortalaması ve sapması, diyalog oranı, yakın tekrarlar, art arda aynı kelimeyle başlayan cümleler, duyu dağılımı ve bitmemiş metin işaretleri ([TK], [DOLDUR]). Bu sayılar puanın yerine geçmez; okurken bakılacak yerleri gösterir.

Roman bölümüyse ve takip varsa: `python3 betikler/sureklilik_denetle.py --proje <kitap> --bolum N` ve `python3 betikler/takip_kaydet.py goster --proje <kitap>` (bağlamla karşılaştırmak için).

3. **Okuma:** metni baştan sona oku; her ölçüt için en az bir alıntı topla.
4. **Puanla:** `inceleme-olcutleri.md` tablosuyla 100 üzerinden. Her ölçüt için puan + tek cümlelik gerekçe + alıntı.
5. **Okur paneli (isteğe bağlı):** `kaynaklar/okur-paneli.md` içinden 3 okur seç, her biri için bırakma noktası, tutan an ve aklında kalan soruyu yaz.
6. **Öncelik listesi:** en çok etki edecek 3–5 düzeltme, her biri "sorun → neden önemli → nasıl" biçiminde.
7. **Yayın yolu notu (istenirse):** Wattpad için ilk bölüm kancası ve bölüm uzunluğu; yayınevi için ilk 30 sayfanın gücü ve dosya hazırlığı (`/yayinevi-dosyasi`).

## Rapor biçimi

```
## İnceleme: Bölüm 3 — "Gece Nöbeti"  (2.140 kelime)

**Genel puan: 74/100 · Düzey: Yayına yakın, bir tur revizyon**

| Ölçüt | Puan | Gerekçe |
|---|---|---|
| Açılış ve kanca | 12/15 | İlk cümle güçlü (“Saat üçü on dört geçe durmuştu.”), bölüm sonu kancası zayıf |
| … | … | … |

### Güçlü yanlar
- …

### Öncelikli düzeltmeler
1. **Sorun:** … **Neden:** … **Nasıl:** …

### Ölçüm
Yapay zekâ kalıbı: 3 güçlü sinyal · Yazım: 2 hata · Süreklilik: 0 bulgu
Okunabilirlik (Ateşman): 71,4 kolay · Ortalama cümle: 9,8 kelime · Diyalog: %34
```

## Dikkat

- Puanı şişirme; 85 üstü gerçekten yayına hazır metin içindir.
- Yazarın bilinçli üslup seçimlerini (şimdiki zaman, uzun cümleler, argo) kusur sayma; tutarlılığını değerlendir.
- İnceleme sonrası yazar düzeltme isterse: dil ve yapay zekâ tadı için `/yz-tadi-gider`, yazım için `/yazim-denetle`, olay değişikliği için `/roman-yaz` revizyon akışı.
- Yazarın kalıcı inceleme tercihi (ör. "puan verme, sadece öneri yaz") yazar hafızasına kaydedilir.

## Dil

Yazarla onun dilinde konuş; rapor varsayılan olarak Türkçedir.
