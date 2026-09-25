---
name: kapak-tasarla
description: "Roman ya da öykü kapağı tasarlar: türe göre görsel dil, Türkçe karakterleri doğru çizilmiş kitap adı ve yazar adı, Wattpad, e-kitap, basılı ve sesli kitap boyutları. Ajan ortamının yerleşik görsel aracını kullanır; yoksa ve yazar isterse görsel API'sine başvurur. Tetikleyiciler: /kapak-tasarla, \"kapak yap\", \"Wattpad kapağı\", \"kitap kapağı tasarla\"."
license: MIT
compatibility: "Python 3.11+. Yerleşik görsel üretim aracı (ör. Codex imagegen) ya da GPT_IMAGE_API_KEY; kırpma için isteğe bağlı Pillow."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.0.0", "ust-kaynak": "oh-story-claudecode/story-cover"}
---

# kapak-tasarla: Kapak Tasarımı

Kitabın türünü ve atmosferini bir bakışta anlatan, küçük boyutta bile okunur bir kapak hazırlarsın.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Stil rehberi: `kaynaklar/kapak-stilleri.md`.

## 1. Bilgi topla

Zorunlu: **kitap adı**, **yazar adı ya da mahlas**, **platform** (wattpad / e-kitap / basili / sesli-kitap), çıktı klasörü (varsayılan `kapaklar/<kitap>/`). Biri eksikse sor; asla uydurma. İsteğe bağlı: tür, kısa tanıtım, renk ya da imge tercihi, referans görsel.

Tür belirtilmemişse `kurgu/tur-konumu.md` ya da tanıtım metninden `kaynaklar/kapak-stilleri.md` içindeki tür eşleme tablosuyla seç.

## 2. İstem

```bash
python3 betikler/kapak_olustur.py istem --baslik "…" --yazar "…" --tur polisiye --platform wattpad --not "tek kırmızı cep saati"
```

İstemi yazara göster; tipografi ve imge tercihini onaylat.

## 3. Üret

- **Yerleşik araç öncelikli:** Ortamda görsel üretim aracı varsa (ör. Codex'te `$imagegen`) istemi doğrudan ona ver; ek anahtar gerekmez. Oranı istemde belirt.
- **API yedeği (yalnızca yazar açıkça isterse, ücretli olabilir):** Yazar anahtarını terminalde `export GPT_IMAGE_API_KEY=…` ile tanımlar; anahtarı sohbete yazmasını isteme.

```bash
python3 betikler/kapak_olustur.py uret --baslik "…" --yazar "…" --tur polisiye --platform wattpad --cikti kapaklar/<kitap> --kuru   # önce isteği göster
python3 betikler/kapak_olustur.py uret --baslik "…" --yazar "…" --tur polisiye --platform wattpad --cikti kapaklar/<kitap>
```

Yerleşik araç hata verirse bunu bildir; sessizce ücretli API'ye geçme.

## 4. Denetle ve boyutla

Görseli aç ve kontrol et: kitap adı ve yazar adı **harfi harfine** doğru mu (özellikle ı/i, ğ, ş)? Yanlışsa yeniden üret ya da yazara metni bir tasarım aracında (Canva, Photopea, GIMP) elle yerleştirmesini öner. Platform boyutu:

```bash
python3 betikler/kapak_olustur.py kirp --girdi kapaklar/<kitap>/kapak-01.png --platform wattpad --cikti kapaklar/<kitap>/kapak-01-wattpad.png
```

## 5. Rapor

Dosya yolları, kullanılan istem, platform boyutu ve yazarın gözden geçirmesi gerekenler (yazım, telif, okunaklılık).

## Telif ve etik

Gerçek kişilerin, başka kitap ya da film kapaklarının tanınabilir öğeleri istenmez. Basılı yayında yayınevinin kapak hakları sözleşmesi geçerlidir; yapay zekâ ile üretilmiş görsel kullanımını yayınevine bildirmek iyi uygulamadır.
