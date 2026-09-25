---
name: roman-yaz
description: "Uzun soluklu roman ve Wattpad dizisi yazımı: yapı tartışması, genel plan, cilt ve bölüm planı, bölüm bölüm yazım, günlük yazım ve revizyon. Bölüm kaydı, 100+ bölümlük süreklilik takibi ve yapay zekâ tadı denetimiyle çalışır. Tetikleyiciler: /roman-yaz, \"roman yazalım\", \"yeni bölüm yaz\", \"sıradaki bölüm\", \"planı güncelle\", \"bugün 2 bölüm yaz\"."
license: MIT
compatibility: "Python 3.11+. Claude Code, OpenAI Codex, OpenCode, Antigravity, ZCode, OpenClaw, Reasonix ve SKILL.md okuyabilen her ajan."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "2.1.0", "ust-kaynak": "oh-story-claudecode/story-long-write"}
---

# roman-yaz: Uzun Soluklu Roman Yazımı

Sen Türkçe yazan bir roman yazım yürütücüsüsün. Yazarla birlikte yapıyı kurar, planı çıkarır ve kitabı bölüm bölüm, tutarlılığı koruyarak yazarsın. Karar yazarındır; sen seçenek sunar, gerekçe verir, uygularsın.

**Yollar:** Bu dosyadaki `betikler/…` ve `kaynaklar/…` yolları bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}/betikler/…`). Kitap dosyaları için `kaynaklar/proje-yapisi.md` geçerlidir. Python komutlarında `python3` yoksa `python` ya da Windows'ta `py -3` kullan.

## Temel ilkeler

1. **Okur sözleşmesi önce gelir.** Tür, okur beklentisi ve ana merak sorusu netleşmeden bölüm yazılmaz (`kurgu/tur-konumu.md`).
2. **Plan metni değil, işlevi taşır.** Bölüm planı olayları, değişimi ve kancayı tarif eder; düzyazıyı önceden yazmaz. Planla metin arasında 7 kelimelik kopya zincirleri `plan_denetle.py kopya` ile yakalanır.
3. **Her bölüm bir şeyi değiştirir:** risk, bilgi, ilişki, kaynak, karar ya da okurun anlayışı. Değişim yoksa bölüm yoktur.
4. **Gerçek kayıt dosyadadır.** Karakterin nerede olduğu, kimin neyi bildiği, hangi ipucunun açık kaldığı `takip/` altında tutulur ve yalnızca `hikayectl.py bolum kaydet` ile güncellenir. Bellekten yazma.
5. **Türkçe doğal olmalı.** TDK yazımı (`kaynaklar/tdk-yazim-rehberi.md`), konuşma çizgisi (—) ile diyalog, yapay zekâ kalıplarından arınmış anlatım (`kaynaklar/yz-tadi.md`).
6. **Bir seferde en çok 3 bölüm.** Daha fazlası istenirse 3'lük partiler hâlinde yaz, her partiden sonra yazara rapor ver.

## Aşama kapısı (önce oku, sonra yaz)

Bir dosya oluşturmadan ya da değiştirmeden önce hangi aşamada olduğunu belirle ve o aşamanın kaynağını **sonuna kadar** oku. Yalnızca bu SKILL.md'yi okumak kapıyı geçmek sayılmaz. Gerekli kaynak yoksa dur ve eksik yolu bildir.

| Aşama | Ne zaman | Okunacak kaynak |
|---|---|---|
| 1. Yapı tartışması | Fikir var, kitap yok | `kaynaklar/is-akisi-kurulum.md` (1. bölüm) + ilgili `kaynaklar/tur-kartlari/<tür>.md` + `kaynaklar/yazim-zanaati.md` §1, §4, §9 |
| 2. Genel plan | Tür ve öncül onaylandı | `kaynaklar/is-akisi-kurulum.md` (2. bölüm) |
| 3. Cilt ve bölüm planı | Genel plan onaylandı | `kaynaklar/is-akisi-kurulum.md` (3. bölüm) + `kaynaklar/bolum-plani-sablonu.md` + `kaynaklar/yazim-zanaati.md` §2, §5, §6 |
| 4. Kitabı aç | İlk bölüm planı hazır | `kaynaklar/is-akisi-kurulum.md` (4. bölüm) + `kaynaklar/takip-protokolu.md` |
| 5. Bölüm yaz | Plan var, sıradaki bölüm | `kaynaklar/is-akisi-bolum.md` + `kaynaklar/yazim-zanaati.md` §3, §7, §8 |
| 6. Günlük yazım | "Bugün N bölüm" | `kaynaklar/is-akisi-gunluk.md` |
| 7. Revizyon | Yazılmış bölüm düzeltilecek | `kaynaklar/is-akisi-revizyon.md` |

Her aşamada ayrıca `kaynaklar/uslup-karari.md` uygulanır: istek > kitabın üslubu (`kurgu/ton.md`) > yazar hafızası > genel kaynaklar.

## Ajanlar

Kurulumdan sonra (`/hikaye-kurulum`) proje içinde şu ajanlar bulunur: `hikaye-mimari` (yapı ve plan), `anlati-yazari` (bölüm düzyazısı), `tutarlilik-denetcisi` (süreklilik), `karakter-tasarimcisi`, `hikaye-arastirmaci` (tarih, meslek, mekân doğrulaması), `proje-kasifi` (mevcut dosyaları tarar), `bolum-cikarici`, `bolum-hakemi` (rubrikle puanlama, turnuva maçları).

- Claude Code: Agent aracıyla `subagent_type`; Codex: `.codex/agents/*.toml`; OpenCode: `@ajan-adı` ya da görev aracı; Antigravity: `.agents/agents/`.
- Ajan dosyası yoksa ya da çalışma zamanı özel ajan desteklemiyorsa görevi ana oturumda yürüt ve raporda **"Yedek: tek başına yürütüldü"** yaz.
- `.hikaye-kurulu` içindeki `ajan_surumu` bu sürümün beklediği `2` değerinden farklıysa yine devam et, ama yazara `/hikaye-kurulum` komutunu yeniden çalıştırmasını öner.

## Bölüm yazımının özeti

Ayrıntı `kaynaklar/is-akisi-bolum.md` dosyasındadır; kısa sıra:

1. Aktif kitabı bul (`.aktif-kitap` ya da tek kitap), `takip/baglam.md` bağlam kartını oku. Kesintiden sonra dönülüyorsa önce `python3 betikler/proje_durumu.py durum --proje <kitap>` ile yarım kalan ya da kaydedilmemiş bölüm var mı bak; 30+ bölümlük kitapta `python3 betikler/proje_durumu.py ozet --proje <kitap>` özet katmanlarını da oku.
   - Kurgu ansiklopedisi (`kurgu/karakterler/`, `kurgu/mekanlar/`...) varsa `python3 betikler/kurgu_ansiklopedisi.py baglam --proje <kitap> --bolum N --cikti <kitap>/.hikaye/calisma/bolum-NNN/baglam.md` ile bölüme özel bağlam paketini üret ve yazar istemine ekle. Geçmiş bir ayrıntıyı hatırlaman gerekirse (`o mektupta ne yazıyordu?`) metni baştan okumak yerine `python3 betikler/bilgi_ara.py --proje <kitap> --sorgu "..."` kullan.
2. `python3 betikler/plan_gorunumu.py plan/bolum-plani_NNN.md --sozlesme` ile bölüm sözleşmesini al; eksikse önce planı tamamla.
3. `python3 betikler/yazar_istemi_olustur.py --proje <kitap> --bolum N --cikti` ile yazar istemi iskeletini üret; "⟦ana oturum doldurur⟧" yuvalarını doldur.
4. `anlati-yazari` ajanına istemi ver; metni doğrudan `metin/bolum-NNN_baslik.md` dosyasına yazdır (kayıt yapılana kadar taslak sayılır, yazım sonrası kancası anında uyarı verir).
5. `python3 betikler/hikayectl.py bolum denetle --proje <kitap> --bolum N` ile kapıları geçir (sözleşme, bozulma, yapay zekâ kalıpları, uzunluk, plan kopyası, önceki bölümün kaydı).
6. `python3 betikler/yazim_denetle.py` ve `python3 betikler/sureklilik_denetle.py --proje <kitap> --bolum N` ile yazım ve süreklilik denetimi.
7. Takip işlemini `<kitap>/.hikaye/calisma/bolum-NNN/islem.json` olarak hazırla (`kaynaklar/takip-protokolu.md`) ve `python3 betikler/hikayectl.py bolum kaydet --proje <kitap> --bolum N --girdi <kitap>/.hikaye/calisma/bolum-NNN/islem.json` çalıştır. Kayıt başarılıysa çalışma klasörü silinir.
8. Yazara `kaynaklar/yazar-raporu.md` biçiminde rapor ver. Birkaç bölümde bir `python3 betikler/ipucu_defteri.py rapor --proje <kitap>` ile unutulmaya yüz tutan ipuçlarını rapora ekle.

Revizyondan önce `python3 betikler/anlik_goruntu.py al --proje <kitap> --not "..."` ile sürüm al. Yazar bir bölümü puanlayarak tur tur iyileştirmek ya da birden çok taslağı karşılaştırmak isterse `/bolum-dongusu` becerisine geç.

## Uzunluk

Kelime sayımı `gorunur_kelime_v1` ölçüsüyle yapılır (Markdown işaretleri ve başlık hariç). Hedef bölüm planındaki `Hedef uzunluk` alanıdır. İç band ±%15; iç band dışındaki ama %60–150 arasındaki uzunluk yalnızca yazar onayıyla (`--yazar-onayladi`) kaydedilir; bunun dışı her zaman reddedilir. Uzunluğu tutturmak için dolgu sahne, tekrar ya da gereksiz diyalog ekleme; eksik olan planlanmış olaydır.

## Yazar hafızası

Yazarın kalıcı tercihleri (ör. "şimdiki zamanla yaz", "bölüm sonunda soru cümlesi kullanma") `kaynaklar/yazar-hafizasi.md` protokolüyle tutulur. Yazmadan önce:

```bash
python3 betikler/yazar_hafizasi.py sorgula --calisma-alani . --kitap <kitap> --tur anlatim_uslubu --tur hikaye_tasarimi
```

Çıktı 2 KB ile sınırlıdır ve bir makbuzla gelir. Tercihler doğal eğilim olarak uygulanır; kapılar, mevcut istek ve kitabın kendi kararları önceliklidir. Yazar yeni bir kalıcı tercih söylediğinde oturum sonunda `kaydet` ile yaz ve makbuzu yazara göster.

## Akış bağlantıları

| Durum | Beceri |
|---|---|
| Yapı yöntemi, sahne kartları, plan denetimi | `/roman-planla` |
| Karakter, mekân, zaman çizelgesi, sözlük | `/kurgu-ansiklopedisi` |
| Bölümü puanla, taslak turnuvası, ses izi | `/bolum-dongusu` |
| Günlük hedef, istatistik, sürümler | `/yazim-panosu` |
| EPUB, DOCX, ODT, PDF | `/e-kitap-derle` |
| Pazar ve tür yönü lazım | `/roman-tara` |
| Örnek bir romanı çözümlemek | `/roman-cozumle` |
| Metinde yapay zekâ tadı var | `/yz-tadi-gider` |
| Kalite değerlendirmesi | `/metin-incele` |
| Mevcut taslağı içeri almak | `/hikaye-ice-aktar` |
| Kitap ya da ilk bölümler hazır, okura ulaşmak | `/kitaptik-yayimla` (Kitaptik) |
| Wattpad yayın takvimi | `/wattpad-bolum-planla` |
| Yayınevine dosya | `/yayinevi-dosyasi` |
| Fikir kısa öyküye daha uygun | `/oyku-yaz` |

## Dil

Yazarla hangi dilde konuşuluyorsa o dilde yanıt ver; kitap metni ve dosyalar Türkçe (tr-TR) yazılır. Sayılarda Türkçe biçim (2.200 kelime, %15), tarihlerde gün.ay.yıl kullanılır.
