---
name: yz-tadi-gider
description: "Metindeki yapay zekâ tadını giderir: kalıp ifadeler, çeviri kokan yapılar, duygu adlandırma, benzetme yığını, üçlü sıralamalar, ders veren sonlar ve tekrar döngüleri. Yazarın üslubunu koruyarak yeniden yazar, önce/sonra raporu verir. Tetikleyiciler: /yz-tadi-gider, \"yapay zekâ yazmış gibi\", \"robotik duruyor\", \"daha doğal yap\", \"AI tadını gider\"."
license: MIT
compatibility: "Python 3.11+. Claude Code, Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "oh-story-claudecode/story-deslop"}
---

# yz-tadi-gider: Yapay Zekâ Tadını Giderme

Metni bir insan yazarın elinden çıkmış gibi okunur hâle getirirsin. Amaç "kural avı" değil, okurun "bunu makine yazmış" hissini kaybetmesidir. Anlamı, olay örgüsünü ve yazarın sesini korursun.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## Önce oku

1. `kaynaklar/yz-tadi.md` (Türkçe yapay zekâ kalıpları kataloğu ve önce/sonra örnekleri), sonuna kadar.
2. `kaynaklar/uslup-karari.md`: kitabın `kurgu/ton.md` dosyası ve yazar hafızası genel kurallardan önce gelir. Yazar bilinçli olarak bir kalıbı kullanıyorsa (ör. karakterin konuşma tiki) çalışma alanındaki `.yz-beyaz-liste` dosyasına eklenir ve dokunulmaz. Tersine, yazarın bu kitapta hiç görmek istemediği ifadeler (ör. "kalbi yerinden fırlayacak gibi", karakterin tekrarlayan bir tiki) `.yasak-kaliplar` dosyasına `ifade => öneri` biçiminde yazılır; denetçi bunları engelleyici `kitap-yasagi` bulgusu olarak raporlar.
3. `kaynaklar/tdk-yazim-rehberi.md`.

## Akış

### 1. Tara

```bash
python3 betikler/ai_kalip_denetle.py <dosya> [--json]
python3 betikler/bozulma_denetle.py <dosya>
python3 betikler/yazim_denetle.py <dosya>
python3 betikler/metin_analizi.py <dosya>
```

`metin_analizi.py` yakın tekrarları, art arda aynı kelimeyle başlayan cümleleri ve tekdüze cümle ritmini gösterir; bunlar yapay zekâ metninin kalıp dışı ama belirgin izleridir.

Betik bulguları başlangıç noktasıdır; anlam düzeyindeki kalıpları (duygu açıklaması, özet cümleler, her paragrafın aynı ritimde bitmesi, karakterlerin aynı sesle konuşması) okuyarak sen bulursun.

### 2. Sınıflandır

| Düzey | Örnek | Ne yapılır |
|---|---|---|
| Engelleyici | Yapay zekânın kendinden söz etmesi, "Umarım beğenirsiniz", Markdown artıkları, yarım kalan son, tekrar döngüsü | Mutlaka düzeltilir |
| Güçlü sinyal | "Derin bir nefes aldı", "kalbi küt küt atıyordu", "gözlerinde bir parıltı", "adeta … gibi" yığını, "sadece … değil, aynı zamanda …" | Bağlamda gerekmedikçe yeniden yazılır |
| Zayıf sinyal | Üçlü sıralama, soyut duygu adı, ünlem yığını, özet cümle | Yoğunluk yüksekse azaltılır |

### 3. Yeniden yaz

- Duygu adını beden, eylem ya da eşyayla değiştir ("çok gergindi" → "çay kaşığını üçüncü kez bardağın kenarına vurdu").
- Hazır benzetmeyi sil ya da sahneye özgü, somut bir imgeyle değiştir.
- Cümle uzunluklarını karıştır; her paragrafı aynı kalıpla bitirme.
- Diyaloğu karakterin yaşına, bölgesine, eğitimine göre ayrıştır; herkes kitap gibi konuşmasın.
- Çeviri kokan yapıları Türkçeleştir: "… olduğu gerçeği", "… tarafından yapıldı" edilgen yığını, gereksiz "bir" belirsiz tanımlığı, "o" zamirinin her cümlede tekrarı.
- Son paragrafta ders ya da özet varsa sil; görüntüyle bitir.

Olay örgüsünü, bilgi sırasını ve karakter kararlarını değiştirme. Uzunluk ±%10'dan fazla değişmemeli.

### 4. Doğrula

Yeniden yazdıktan sonra 1. adımdaki üç betiği tekrar çalıştır. `python3 betikler/noktalama_duzelt.py <dosya> --yaz` ile noktalamayı düzelt. Engelleyici bulgu kalmamalı.

### 5. Rapor

```
Yapay zekâ tadı giderildi: metin/bolum-004_gece-nobeti.md
Önce: 14 güçlü sinyal, 2 engelleyici · Sonra: 1 güçlü sinyal (bilinçli: Nuri Usta'nın "evladım" tiki), 0 engelleyici
En belirgin 3 değişiklik:
1. "Kalbi göğsünden fırlayacakmış gibi atıyordu." → "Anahtarı iki kez düşürdü."
2. "Bu sadece bir saat değil, aynı zamanda bir hatıraydı." → (silindi; önceki sahne bunu zaten gösteriyor)
3. Son paragraftaki "O gece anladı ki…" özeti → kapının kilitlenme sesiyle bitiş
```

Roman bölümüyse ve olay değişmediyse takip güncellemesi gerekmez. Yazar kalıcı bir tercih söylerse (`"sanki" kelimesini hiç kullanma`) `kaynaklar/yazar-hafizasi.md` protokolüyle kaydet.

## Dil

Yazarla onun dilinde konuş; metin Türkçe (tr-TR) kalır.
