---
name: wattpad-bolum-planla
description: "Wattpad ve benzeri bölümlü çevrim içi yayın için bölüm planlaması: bölüm uzunluklarını 1.500–3.000 kelime aralığına göre denetler, uzun bölümleri sahne sınırlarından böler, telefonda okunurluğu ve bölüm sonu kancalarını kontrol eder, düzenli yayın takvimi ve tampon önerisi üretir; etiket, tanıtım ve yazar notu hazırlar. Tetikleyiciler: /wattpad-bolum-planla, \"Wattpad'e yükleyeceğim\", \"yayın takvimi\", \"bölümü böl\", \"Wattpad etiketleri\"."
license: MIT
compatibility: "Python 3.11+."
metadata: {"kaynak": "https://github.com/cumabozkurt/ai-hikaye-roman-olusturma", "surum": "1.0.0", "ust-kaynak": "yeni"}
---

# wattpad-bolum-planla: Wattpad Bölüm ve Yayın Planı

Kitabı Wattpad ve benzeri bölümlü yayın platformlarının okur alışkanlıklarına göre bölümlere ve bir yayın düzenine oturtursun. Metnin içeriğine dokunmazsın; bölme, sıralama ve yayın hazırlığı yaparsın.

**Önemli:** Wattpad Türkiye'de Temmuz 2024'ten beri mahkeme kararıyla erişime kapalıdır (ayrıntı: `kaynaklar/wattpad-rehberi.md`). Yazar Türkiye'den yayın yapacaksa bunu ilk adımda hatırlat; erişim engelini aşma yöntemi önerme. Bu becerinin ölçüleri ve takvimi her bölümlü platformda geçerlidir.

Yollar bu SKILL.md dosyasının klasörüne görelidir (Claude Code'da `${CLAUDE_SKILL_DIR}`). Python komutu `python3`; bulunamazsa `python`, Windows'ta `py -3`. Önce `kaynaklar/wattpad-rehberi.md` ve `kaynaklar/platformlar-turkiye.md` (§1) dosyalarını oku.

## Akış

1. **Denetle:**

```bash
python3 betikler/wattpad_planla.py denetle --proje <kitap> [--alt 1500 --ust 3000]
```

Her bölüm için kelime sayısı, uzun paragraflar (telefonda 120+ kelime duvar gibi görünür), ilk paragraf uzunluğu ve sezgisel kanca puanı (0–4). Kanca puanı yalnızca bir işarettir; son sahneyi kendin oku.

2. **Böl (gerekirse):** Uzun bölüm için önce öneri al, yazar onaylarsa yaz:

```bash
python3 betikler/wattpad_planla.py bol --dosya <kitap>/metin/bolum-012_x.md --hedef 2000
python3 betikler/wattpad_planla.py bol --dosya <kitap>/metin/bolum-012_x.md --hedef 2000 --cikti <kitap>/wattpad/
```

Parçalar `wattpad/` klasörüne yazılır; asıl bölüm dosyaları ve takip değişmez (Wattpad bölümlemesi yayın katmanıdır). Bölme noktası kancasız kalıyorsa yazara son paragraf için öneri sun, metni kendiliğinden değiştirme.

3. **Takvim:**

```bash
python3 betikler/wattpad_planla.py takvim --proje <kitap> --baslangic 2026-10-02 --gunler cuma,salı --saat 20:00 --cikti <kitap>/plan/wattpad-takvimi.md
```

En az 3 bölümlük tampon önerilir; tampon azsa uyar.

4. **Yayın hazırlığı** (`kaynaklar/wattpad-rehberi.md` şablonları): kitap tanıtımı (ilk cümle kanca, 150–250 kelime), 10–20 etiket (Türkçe + yaygın İngilizce karşılıklar), içerik derecelendirmesi (Genel / Yetişkin), telif seçimi, kapak (`/kapak-tasarla`), bölüm başlıkları, isteğe bağlı kısa yazar notu.
5. **Rapor:** denetim özeti, bölme önerileri, takvim, hazırlık listesi.
