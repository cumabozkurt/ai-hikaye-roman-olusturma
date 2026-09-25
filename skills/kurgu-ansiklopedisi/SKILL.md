---
name: kurgu-ansiklopedisi
description: "Romanın kurgu ansiklopedisini (story bible) tutar ve metinle karşılaştırır: karakter, mekân, nesne, grup, dünya kayıtları, karakter mülakatı, ilişki grafiği, zaman çizelgesi, terim sözlüğü; tutarlılık denetimi, bölümlere dağılım, bölüm bağlam paketi, Türkçe tam metin arama, ipucu defteri, dönem uyumsuzluğu. Tetikleyiciler: /kurgu-ansiklopedisi, \"karakter kartı\", \"story bible\", \"zaman çizelgesi\", \"şu olay nerede geçmişti\"."
license: MIT
compatibility: "Python 3.11+ (yalnızca standart kitaplık). Proje yapısı: kaynaklar/proje-yapisi.md."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "yeni"}
---

# kurgu-ansiklopedisi: Kurgu Ansiklopedisi ve Bilgi Tabanı

Romanın değişmez gerçeklerini düz Markdown dosyalarında tutarsın ve metnin bu gerçeklerden sapmadığını betikle denetlersin. Dosyalar yazarındır; sen şablon açar, yazarın verdiği bilgiyi işler, çelişkiyi raporlarsın.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `kurgu/karakterler/*.md`, `mekanlar/`, `nesneler/`, `gruplar/`, `dunya/` | `# Ad` başlığı ve `- Alan: değer` satırları (`Diğer adlar`, `Rol`, `Yaş`, `Doğum yılı`, `Göz rengi`, `İlk görünüş`, `Öldüğü bölüm`...) |
| `kurgu/iliskiler.md` | `\| Kimden \| Kime \| İlişki \| Bölüm \| Not \|` (ilişki değiştikçe yeni satır, bölüm numarasıyla) |
| `kurgu/zaman-cizelgesi.md` | `\| Tarih \| Olay \| Kişiler \| Bölüm \|` |
| `kurgu/sozluk.md` | `\| Terim \| Anlamı \| Yanlış yazımlar \|` |

## Kayıt aç

```bash
python3 betikler/kurgu_ansiklopedisi.py olustur --proje <kitap> --tur karakter --ad "Defne Aras"
python3 betikler/kurgu_ansiklopedisi.py listele --proje <kitap>
```

Karakter şablonunda 10 soruluk **karakter mülakatı** vardır (sabah uyanınca ilk ne düşünür, kimseye söylemediği utancı, hikâye başladığında neyi yanlış biliyor...). Soruları yazara tek tek sor; cevapları karakterin sesiyle birinci tekil yaz.

## Denetle

```bash
python3 betikler/kurgu_ansiklopedisi.py dogrula --proje <kitap>          # kayıtlar kendi içinde tutarlı mı
python3 betikler/kurgu_ansiklopedisi.py tutarlilik --proje <kitap>       # metin ansiklopediyle çelişiyor mu
python3 betikler/kurgu_ansiklopedisi.py tutarlilik --proje <kitap> --bolum 12
python3 betikler/ipucu_defteri.py rapor --proje <kitap>                  # ekilen ipuçları unutuldu mu
python3 betikler/donem_denetle.py --proje <kitap>                        # dönemde olmayan şey var mı
```

- `dogrula`: aynı ad ya da takma ad iki kayıtta, sayı olmayan yaş, doğumdan önceki olay, ölümden sonraki olay, ilişki tablosunda ve zaman çizelgesinde kayıtsız ad, kendisiyle ilişki.
- `tutarlilik`: ölü karakterin anı bağlamı olmadan görünmesi, `İlk görünüş` bölümünden önce görünme, sözlükteki yanlış yazımlar, ad kayması (Defne / Defna), metinde sık geçen ama kaydı olmayan özel adlar. Türkçe ekler (`Defne'nin`, `Kerem'e`) ve ünsüz yumuşaması (`Kara Kitap` / `Kara Kitabı`) tanınır.
- `ipucu_defteri.py`: her ipucunun ekildiği bölüm, metinde en son anıldığı bölüm ve planlanan çözümü; süresi geçen, uzun süre anılmayan (varsayılan 8 bölüm), plan dışına taşan ve aynı bölüme yığılan ipuçları. `serit` alt komutu bölüm ekseninde şerit çizer.
- `donem_denetle.py`: plan dosyasındaki `- Dönem: 1919–1923` satırına göre henüz var olmayan (soyadı 1934, radyo yayını 1927, harf devrimi 1928...) ya da kaldırılmış (fes 1925, hilafet 1924...) şeyleri yasa ve yıl kaynağıyla bildirir. İstisnalar `<kitap>/.donem-istisnalari` dosyasına yazılır.

Her bulguyu bağlamında oku: anı sahnesi, rüya, bilinçli anakronizm ya da yanlış inanç olabilir.

## Dağılım ve ilişki grafiği

```bash
python3 betikler/kurgu_ansiklopedisi.py dagilim --proje <kitap> --html dagilim.html
python3 betikler/kurgu_ansiklopedisi.py grafik --proje <kitap> --bolum 20 --bicim mermaid
```

`dagilim`, her kaydın hangi bölümde kaç kez geçtiğini ve bölüm planındaki `Bakış açısı:` satırını tabloya döker; 4+ bölüm görünmeyen ana karakteri ve hiç geçmeyen kaydı uyarır. `grafik`, ilişkilerin **o bölüm itibarıyla** hâlini çizer (20. bölümde düşman olan iki kişi 5. bölümde dost görünür).

## Bölüm yazmadan önce: bağlam paketi

```bash
python3 betikler/kurgu_ansiklopedisi.py baglam --proje <kitap> --bolum 13 --cikti .hikaye/baglam-013.md
```

Bölüm planında ve önceki bölümün son paragrafında adı geçen kayıtları, aralarındaki ilişkileri, zaman çizelgesi olaylarını, sözlük terimlerini ve açık ipuçlarını tek bir pakette toplar (`--sinir` bayt bütçesiyle). Yazar ajanına bütün ansiklopediyi değil bunu ver.

## Bilgi arama

```bash
python3 betikler/bilgi_ara.py --proje <kitap> --sorgu "kırmızı defter"
python3 betikler/bilgi_ara.py --proje <kitap> --sorgu "\"gizli kapak\" saat" --kapsam metin --adet 5
```

Metin, plan, kurgu, araştırma ve takip dosyalarında paragraf düzeyinde BM25 arama yapar; Türkçe büyük/küçük harf ve ek farklarını tolere eder (5 harflik gövde). "Bu olay hangi bölümde geçmişti?" sorusunu metni baştan okumadan cevaplamak için kullan.
