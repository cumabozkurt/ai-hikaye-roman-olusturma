---
name: sureklilik-denetle
description: "Uzun romanda tutarlılık hatası avı: ölü ya da kayıp karakterin sahnede görünmesi, süresi geçmiş ipuçları, henüz açılmamış sırların erken sızması, karakter adı kayması ve benzer adlar, göz rengi, saç, yaş gibi nitelik çelişkileri. Takip kayıtlarına dayanır. Tetikleyiciler: /sureklilik-denetle, \"tutarlılık hatası var mı\", \"karakter çelişkisi\", \"100 bölümü tara\", \"ipuçlarım unutuldu mu\"."
license: MIT
compatibility: "Python 3.11+. Takip kaydı (takip/_takip-durumu.json) olan romanlar için."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "yeni"}
---

# sureklilik-denetle: Süreklilik Denetimi

Uzun bir romanda okurun yakalayacağı tutarlılık hatalarını yazar yakalamadan önce bulursun. Kaynak, `roman-yaz` ve `hikaye-ice-aktar` becerilerinin tuttuğu takip kaydıdır (`kaynaklar/takip-protokolu.md`).

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## Ön koşul

`<kitap>/takip/_takip-durumu.json` yoksa kitap takipte değildir: yazmaya yeni başlanıyorsa `/roman-yaz`, taslak dışarıdan geliyorsa `/hikaye-ice-aktar` öner. Takip bozuk görünüyorsa önce:

```bash
python3 betikler/takip_kaydet.py denetle --proje <kitap>
```

## Akış

1. **Tara:**

```bash
python3 betikler/sureklilik_denetle.py --proje <kitap>              # bütün bölümler
python3 betikler/sureklilik_denetle.py --proje <kitap> --bolum 42   # tek bölüm
python3 betikler/sureklilik_denetle.py --proje <kitap> --json
```

| Kural | Ne yakalar |
|---|---|
| olu-karakter | `öldü` ya da `kayıp` işaretli karakterin sonraki bölümde konuşması ya da eylemi |
| suresi-gecen-ipucu | Planlanan çözüm bölümü geçmiş ama hâlâ `ekili` olan ipuçları |
| gizli-olay-sizintisi | `gizli` durumdaki bir olayın anahtar kelimelerinin metinde erken görünmesi |
| isim-benzerligi | Okuru karıştıracak kadar benzer adlar (Levenshtein ≤ 1–2) |
| isim-kaymasi | Kayıtlı ada çok yakın ama farklı yazımlar (Defne / Defna) |
| nitelik-celiskisi | `kurgu/karakterler/*.md` içindeki `Göz:`, `Saç:`, `Yaş:` bilgisiyle çelişen ifadeler |

**Ek taramalar** (varsa):

```bash
python3 betikler/kurgu_ansiklopedisi.py tutarlilik --proje <kitap>   # kurgu ansiklopedisiyle karşılaştırma
python3 betikler/kurgu_ansiklopedisi.py dogrula --proje <kitap>      # ansiklopedi kendi içinde tutarlı mı
python3 betikler/ipucu_defteri.py rapor --proje <kitap>              # unutulan, yığılan, plan dışı ipuçları
python3 betikler/donem_denetle.py --proje <kitap>                    # tarihî romanda dönem uyumsuzluğu
```

| Tarama | Ne yakalar |
|---|---|
| ansiklopedi `tutarlilik` | Sözlükteki yanlış yazımlar, `İlk görünüş` bölümünden önce görünme, `Öldüğü bölüm` sonrasında anı bağlamı olmadan görünme, kayıtsız sık özel adlar |
| ansiklopedi `dogrula` | Çift ad, doğumdan önce ya da ölümden sonra olay, ilişki ve zaman çizelgesinde kayıtsız ad |
| `ipucu_defteri.py` | Metinde uzun süredir anılmayan açık ipucu (okur unutur), aynı bölüme yığılan çözümler, planlanan bölüm sayısını aşan çözüm |
| `donem_denetle.py` | Plan dosyasındaki `- Dönem:` yılına göre henüz var olmayan (soyadı, radyo, Latin harfleri...) ya da kaldırılmış (fes, hilafet, rumi takvim...) şeyler; yasa ve yıl kaynağıyla |

2. **Doğrula:** Her bulguyu metinde bağlamıyla oku. Anı sahnesi, rüya, yanlış inanç ya da bilinçli yanıltma olabilir; o zaman "yanlış alarm" olarak işaretle.
3. **Anlam düzeyi:** Betiğin göremediklerini `tutarlilik-denetcisi` ajanıyla ya da okuyarak ara: karakterin bilmediği bir şeyi bilmesi, mekân ve yolculuk süreleri, mevsim ve hava, yaralanmaların iyileşme süresi, para ve fiyatlar (dönem ve enflasyon).
4. **Rapor:**

```
Süreklilik raporu: Saatçinin Kızı (1–48. bölümler)
🔴 Kesin hata (2)
- Bölüm 37: Nuri Usta konuşuyor, oysa 29. bölümde öldü (takip: öldü, 29).
- Bölüm 41: Defne'nin gözleri "yeşil"; karakter dosyası: ela.
🟡 İnceleme gerekli (3)
- F007 (kapaktaki tarih) 30. bölümde çözülecekti, hâlâ açık.
⚪ Yanlış alarm (1)
- Bölüm 33: Nuri Usta anı sahnesinde (bilinçli).
```

5. **Düzelt:** Yazar onaylarsa metni düzelt; olay değişiyorsa `/roman-yaz` revizyon akışıyla takibi de güncelle. `takip/` dosyalarını asla elle düzenleme.
