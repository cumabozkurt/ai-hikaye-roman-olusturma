---
name: yazim-denetle
description: "TDK yazım kurallarına göre Türkçe yazım ve noktalama denetimi: bitişik yazılan de/da, ki ve mi, kesme işareti, sık yazım yanlışları, konuşma çizgisi, üç nokta, noktalama boşlukları ve anlatıdaki gayriresmî kullanımlar. Güvenli düzeltmeleri otomatik uygular. Tetikleyiciler: /yazim-denetle, \"yazım hatalarını bul\", \"TDK'ya uygun mu\", \"noktalamayı düzelt\", \"imla kontrolü\"."
license: MIT
compatibility: "Python 3.11+. Claude Code, Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.0.0", "ust-kaynak": "yeni"}
---

# yazim-denetle: TDK Yazım ve Noktalama Denetimi

Türkçe metinlerin yazım ve noktalamasını Türk Dil Kurumu kurallarına göre denetler, güvenli düzeltmeleri uygular, geri kalanları gerekçesiyle yazara sunarsın.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Kural kaynağı: `kaynaklar/tdk-yazim-rehberi.md` (ayrıntı için https://tdk.gov.tr ve TDK Yazım Kılavuzu).

## Akış

1. **Noktalama (güvenli, otomatik):**

```bash
python3 betikler/noktalama_duzelt.py <dosya...>          # yalnızca göster
python3 betikler/noktalama_duzelt.py <dosya...> --yaz    # uygula
```

Düzeltilenler: satır başı konuşma çizgisi (`-` / `–` → `— `), noktalama öncesi boşluk, virgül ve noktadan sonra eksik boşluk, `...` → `…`, kesme işaretinin tek biçimi (’ → '), çoklu boşluk ve boş satırlar. Tipografik tırnak isteniyorsa `--tipografik-tirnak`; yazar diyaloğu tırnakla yazıyorsa `--diyalog-tiresi-yok`.

2. **Yazım (öneri):**

```bash
python3 betikler/yazim_denetle.py <dosya...> [--json] [--kati]
```

| Kural | Örnek | Düzey |
|---|---|---|
| yazim-hatasi | herkez → herkes, yanlız → yalnız, birşey → bir şey | hata | <!-- turkce-uyum: yoksay -->
| de-da-bitisik | bende geldim → ben de geldim | hata / uyarı |
| ki-bitisik | bilki → bil ki (bağlaç) | hata |
| soru-eki-bitisik | gelecekmisin → gelecek misin | hata |
| kesme-isareti | Ankaraya → Ankara'ya | uyarı |
| gayriresmi | napıcaz, bi, tmm (yalnızca anlatıda; diyalogda serbest) | uyarı |
| cumle-basi-kucuk | nokta sonrası küçük harf | uyarı |
| yz-yogunlugu | 300+ kelimede yapay zekâ kalıbı yoğunluğu özeti | uyarı |

3. **Bağlam kararı:** Her `uyarı` bulgusunu cümlenin içinde değerlendir. Özellikle "de/da" ve "ki" kuralları bağlama bağlıdır: "evde kaldım" (hâl eki, bitişik) ile "ben de kaldım" (bağlaç, ayrı) farklıdır. Karakter konuşmasındaki bilinçli ağız ve argo düzeltilmez.
4. **Uygula:** Kesin hataları düzelt; tartışmalı olanları yazara liste hâlinde sor.
5. **Rapor:**

```
Yazım denetimi: metin/bolum-005_mektup.md (2.310 kelime)
Noktalama: 11 düzeltme uygulandı (7 konuşma çizgisi, 3 üç nokta, 1 boşluk)
Yazım: 4 hata düzeltildi (herkez, bilki, gelecekmisin, yanlız) · 2 uyarı yazara soruldu
```

## Sınırlar

Betik bir sözlük denetçisi değildir; sık yapılan yanlışları kurala dayalı yakalar. Özel adlar, yabancı sözcükler ve terimler için `kaynaklar/tdk-yazim-rehberi.md` içindeki listeler ve TDK Güncel Türkçe Sözlük esas alınır. Yapay zekâ tadı için `/yz-tadi-gider` kullanılır.
