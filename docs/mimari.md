# Mimari: beceriler, ajanlar, kancalar ve proje yapısı

## Üç katman

**1. Dosya sistemi hafızadır.** Uzun bir roman yüz binlerce kelimedir; sohbet onu aklında tutamaz. Kurgu (`kurgu/`), plan (`plan/`), metin (`metin/`) ve takip (`takip/`) ayrı klasörlerde, ayrı ayrı bakımı yapılan dosyalardır. Sohbet yazar, hatırlamaz. Proje yapısının tamamı: [`paylasilan/kaynaklar/proje-yapisi.md`](../paylasilan/kaynaklar/proje-yapisi.md).

**2. Yedi uzman ajan.** `/hikaye-kurulum` ajan şablonlarını ev sahibinin biçimine çevirip projeye yazar:

| Ajan | Görev | Yazma yetkisi |
|---|---|---|
| `hikaye-mimari` | Genel plan, cilt ve bölüm planı; perde yapısı, ipucu ekme ve hasat | var |
| `anlati-yazari` | Bölüm planından Türkçe düzyazı; üslup dosyasına ve TDK'ya uyar | var |
| `tutarlilik-denetcisi` | Olgu çelişkisi, zaman çizelgesi, bilgi sızıntısı | salt okunur |
| `karakter-tasarimcisi` | İstek/ihtiyaç, yara, ses, ilişki ağı, gelişim yayı | var |
| `hikaye-arastirmaci` | Tarih, meslek, mekân, hukuk, tıp; kaynaklı notlar | var |
| `proje-kasifi` | "Defne şu an nerede?" gibi soruları dosyalardan yanıtlar | salt okunur |
| `bolum-cikarici` | Çözümleme ve içe aktarmada bölüm grubu özetleri | var |

Özel ajan desteklemeyen ortamlarda (OpenClaw, Reasonix, genel) görev ana oturumda yürütülür ve bu durum yazara bildirilir.

**3. Kancalar.** Bütün ev sahipleri için tek Python çekirdeği vardır: `.hikaye/kancalar/hikaye_kanca.py`. Ev sahibine özgü kayıtlar (Claude `settings.local.json`, Codex `hooks.json`, OpenCode eklentisi, Antigravity `hooks.json`, ZCode `config.json`) yalnızca bu çekirdeği çağırır.

| Olay | Davranış | Engeller mi? |
|---|---|---|
| `oturum-basla`, `sikistirma-sonrasi` | Etkin kitabın bağlam kartı ve devir notu (en çok 10.000 karakter) | hayır |
| `yazi-oncesi` | Bölüm planı yoksa, planda `Hedef uzunluk` yoksa ya da önceki bölüm takibe kaydedilmemişse yazımı durdurur | **evet** |
| `kayit-oncesi` | `git commit` öncesi kaydedilmemiş bölüm uyarısı | hayır |
| `yazi-sonrasi` | Bozulma, yapay zekâ kalıbı ve uzunluk bulguları | hayır |
| `sikistirma-oncesi` | `.hikaye/devir-notu.md` yazar | hayır |
| `oturum-sonu`, `dur` | Oturum günlüğü; Antigravity'de bekleyen bulgu varsa bir kez devam ettirir | hayır |
| `cagri-oncesi` | Antigravity `PreInvocation`: bağlam ve bekleyen bulgular | hayır |

Kancalar `.hikaye-kurulu` işareti olmayan projede hiçbir şey yapmaz; kendi iç hatalarında akışı kilitlemez, izin verir.

## Takip durumu

`takip/_takip-durumu.json` tek yapılandırılmış kaynaktır. Model yalnızca küçük, anlamsal bir işlem JSON'u verir; `takip_kaydet.py` işlemi doğrular, bellekte birleştirir, bütün görünümleri (`baglam.md`, `ipuclari.md`, `karakter-durumu/`, `zaman-cizelgesi/`, `bolum-kayitlari/`) yeniden üretir ve en son durum dosyasını atomik olarak yazar. Proje kilidi aynı anda çalışan yazımları sıraya sokar; `beklenen_revizyon` eski bir işlemin yeni durumu ezmesini önler.

- **Yazar gerçeği / okur bilgisi:** Olaylar iki zaman çizelgesinde tutulur. Açığa çıkmamış bir olay okur bilgisine yazılmaz; `sureklilik_denetle.py` metinde erken sızıntıyı yakalar.
- **İpucu yaşam döngüsü:** `ekili` → `çözüldü` / `süresi geçti` / `vazgeçildi`; planlanan çözüm bölümü geçen açık ipucu uyarı üretir.
- **Türetilmiş görünümler elle değiştirilmez:** `takip_kaydet.py denetle` farkı yakalar.

## Bir bölümün yolu

1. `plan/bolum-plani_NNN.md` (şablon: `bolum-plani-sablonu.md`; `Hedef uzunluk` zorunlu).
2. `yazar_istemi_olustur.py` → `.hikaye/calisma/bolum-NNN/yazar-istemi.md`.
3. `anlati-yazari` metni yazar (kanca: plan ve önceki kayıt kapısı).
4. `hikayectl.py bolum denetle`: plan sözleşmesi, metin dosyası, bozulma, yapay zekâ kalıpları, uzunluk bandı, önceki bölümün kaydı.
5. `yazim_denetle.py`, `sureklilik_denetle.py`.
6. `hikayectl.py bolum kaydet --girdi islem.json`: uzunluk kaydı eklenir, takip tek seferde işlenir, çalışma klasörü silinir.

## Paylaşılan dosyalar ve üretilen dosyalar

- `paylasilan/betikler` ve `paylasilan/kaynaklar` tek doğru kaynaktır; `betikler/paylasilanlari_esitle.py` bunları `betikler/paylasilan_dosyalar.json` eşlemine ve içe aktarma bağımlılıklarına göre becerilere kopyalar. Böylece her beceri tek başına kurulabilir (`npx skills`, elle kopyalama).
- `betikler/eklenti_dosyalari_uret.py` bütün eklenti ve pazar yeri bildirimlerini tek kaynaktan üretir.
- `betikler/statik_denetim.py` ve `betikler/turkce_uyum_denetle.py` CI'da biçim, bağlantı, sürüm ve dil uyumunu denetler.
