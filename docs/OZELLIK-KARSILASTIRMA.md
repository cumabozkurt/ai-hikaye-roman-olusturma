# Özellik Karşılaştırması

Bu belge, 2.0.0 sürümü hazırlanırken dokuz açık kaynak roman yazım projesinin incelenmesinin sonucudur. Amaç, Türkçe roman yazan birinin bu paketi kullandıktan sonra başka bir araca ihtiyaç duymamasıydı. Her projenin README'si, belgeleri, veri modeli, iş akışları, istemleri, arayüz özellikleri, dışa aktarma biçimleri, testleri ve lisansı okundu.

> **Yöntem ve sınırlar.** Tablo, projelerin varsayılan dallarının 25 Eylül 2026 tarihli hâline dayanır. `✓` belgelenmiş ve kodda bulunan özellik, `◐` kısmi ya da farklı biçimde karşılanan özellik, `—` incelediğimiz belge ve kodda bulamadığımız özellik demektir; "kesinlikle yok" anlamına gelmez. Projeler gelişmeye devam eder. Yanlış bir hücre görürseniz lütfen [bildirin](https://github.com/cumabozkurt/ai-hikaye-roman-olusturma/issues), düzeltelim.

## Lisanslar ve lisans hijyeni

| Proje | Lisans | Bu depoya etkisi |
|---|---|---|
| [PenglongHuang/chinese-novelist-skill](https://github.com/PenglongHuang/chinese-novelist-skill) | MIT | Fikir düzeyinde esinlenildi; kod ya da metin alınmadı |
| [saga-soft/novelWriter](https://github.com/saga-soft/novelWriter) (üst kaynak [vkbo/novelWriter](https://github.com/vkbo/novelWriter)) | GPL-3.0 | Yalnızca fikir; kod, metin, varlık alınmadı |
| [ExplosiveCoderflome/AI-Novel-Writing-Assistant](https://github.com/ExplosiveCoderflome/AI-Novel-Writing-Assistant) | AGPL-3.0 (ayrıca ticari lisans) | Yalnızca fikir |
| [olivierkes/manuskript](https://github.com/olivierkes/manuskript) | GPL-3.0 | Yalnızca fikir |
| [NousResearch/autonovel](https://github.com/NousResearch/autonovel) | Lisans dosyası yok (bütün hakları saklı sayılır) | Yalnızca fikir |
| [RhythmicWave/NovelForge](https://github.com/RhythmicWave/NovelForge) | AGPL-3.0 | Yalnızca fikir |
| [EthanYoQ/AI-Novel-Writer](https://github.com/EthanYoQ/AI-Novel-Writer) | GPL-3.0 | Yalnızca fikir |
| [andreafeccomandi/bibisco](https://github.com/andreafeccomandi/bibisco) | GPL-3.0 | Yalnızca fikir |
| [heider-x/vela](https://github.com/heider-x/vela) | GPL-3.0 | Yalnızca fikir |

Bu depo MIT lisanslıdır. GPL, AGPL ya da lisanssız projelerden **hiçbir kod, istem, metin, şablon ya da görsel alınmadı**; fikirler Türkçe yazım pratiğine göre baştan tasarlanıp bağımsız olarak yazıldı. Tek MIT lisanslı proje olan chinese-novelist-skill'den de metin alınmadı, yalnızca yaklaşım incelendi. Bütün şablon başlıkları, sorular, puanlama ölçütleri ve örnekler bu depo için özgün olarak Türkçe yazıldı.

## Özellik matrisi

Kısaltmalar: **CNS** chinese-novelist-skill · **nW** novelWriter · **ANWA** AI-Novel-Writing-Assistant · **Msk** manuskript · **AN** autonovel · **NF** NovelForge · **ANW** AI-Novel-Writer · **bib** bibisco · **vela** Vela · **Biz** AI Hikaye & Roman Oluşturma 2.0.

### Planlama

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| Katmanlı soru-cevapla fikir toplama | ✓ | — | ◐ | — | ◐ | ◐ | ◐ | ◐ | ◐ | ✓ |
| Kar tanesi yöntemi | — | — | ◐ | ✓ | — | ◐ | — | — | — | ✓ |
| Yapı şablonları (üç perde, kahramanın yolculuğu vb.) | ◐ | — | ◐ | ◐ | ◐ | ◐ | ✓ | ◐ | ✓ | ✓ |
| Vuruşların beklenen konumunu ölçen plan denetimi | — | — | — | — | — | — | — | — | — | ✓ |
| Sahne kartları (bakış açısı, amaç, çatışma, sonuç, değer) | — | ◐ | ◐ | ✓ | ◐ | ◐ | ◐ | ◐ | ◐ | ✓ |
| Mantar pano görünümü | — | — | — | ✓ | — | ◐ | — | — | — | ✓ |
| Bölüm planı sözleşmesi ve "plan yoksa yazma" kapısı | ◐ | — | ◐ | — | ◐ | — | ◐ | — | — | ✓ |

### Kurgu ansiklopedisi ve süreklilik

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| Karakter kayıtları (istek, ihtiyaç, sır, yara) | ◐ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Karakter mülakatı | — | — | — | — | — | — | — | ✓ | — | ✓ |
| Mekân, nesne, grup kayıtları | — | ◐ | ◐ | ◐ | ◐ | ✓ | ◐ | ✓ | ◐ | ✓ |
| Zaman çizelgesi | — | ◐ | ✓ | — | ◐ | ◐ | ◐ | ✓ | ◐ | ✓ |
| İlişki haritası | — | — | ◐ | — | — | ✓ | ✓ | ◐ | — | ✓ (Mermaid/DOT) |
| Kitaba özgü sözlük ve yanlış yazım avı | — | — | — | — | ◐ | — | — | — | — | ✓ |
| Kayıt–metin tutarlılık denetimi (göz rengi, ad kayması, ölü karakter) | — | — | ◐ | — | ◐ | ◐ | ✓ | — | ◐ | ✓ |
| Doğum yılı / ölüm bölümü ile zaman çizelgesi çelişkisi | — | — | — | — | — | — | — | — | — | ✓ |
| Kimin hangi bölümde geçtiği dağılımı | — | ◐ | — | ◐ | — | — | — | ✓ | — | ✓ |
| Yazar gerçeği / okur bilgisi ayrımı | — | — | ◐ | — | — | — | ◐ | — | — | ✓ |
| Dönem uyumsuzluğu (anakronizm) denetimi | — | — | — | — | — | — | — | — | — | ✓ |

### Uzun roman belleği

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| Bölüme özel bağlam paketi (yalnızca sahnedeki kişiler, açık ipuçları) | ◐ | — | ✓ | — | ◐ | ✓ | ✓ | — | ◐ | ✓ |
| Katmanlı özet (kitap → cilt → bölüm) | ◐ | — | ✓ | — | ◐ | ◐ | ✓ | — | ◐ | ✓ |
| Proje içi arama | — | ✓ | ✓ | ✓ | — | ◐ | ✓ | ◐ | ✓ | ✓ (BM25 + Türkçe kök) |
| Anlamsal (vektör) arama | — | — | ✓ | — | — | ◐ | ◐ | — | ✓ | — |
| Kaldığı yerden devam ("nerede kaldım") | ✓ | ◐ | ✓ | — | ✓ | ◐ | ◐ | — | ◐ | ✓ |
| Kayıttan sonra değişen bölümü bildirme | — | — | — | — | — | — | ◐ | — | — | ✓ |

### İpuçları ve kurgu mühendisliği

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| İpucu (ekme–hasat) takibi | ◐ | — | ✓ | — | ✓ | ◐ | ✓ | — | ◐ | ✓ |
| Süresi geçen / unutulan ipucu uyarısı | — | — | ◐ | — | ◐ | — | ✓ | — | — | ✓ |
| İpucunun metinde son anıldığı bölümü bulma | — | — | — | — | — | — | — | — | — | ✓ |
| Tek bölümde çözüm yığılması uyarısı | — | — | — | — | — | — | — | — | — | ✓ |
| Bölüm sonu kanca rehberi | ✓ | — | ◐ | — | ◐ | — | ◐ | — | — | ✓ |

### Yazım, eleştiri ve revizyon

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| Çok ajanlı iş akışı | ◐ | — | ✓ | — | ✓ | ◐ | ✓ | — | ◐ | ✓ (8 ajan) |
| Yaz → eleştir → düzelt döngüsü | ✓ | — | ✓ | — | ✓ | — | ✓ | — | ✓ | ✓ |
| Ölçülebilir puan (mekanik + hakem) ve durma koşulu | ◐ | — | ◐ | — | ✓ | — | ◐ | — | — | ✓ |
| Bölüm turnuvası (Elo) | — | — | — | — | ✓ | — | — | — | — | ✓ |
| Ses izi (üslup parmak izi) karşılaştırması | — | — | ✓ | — | ✓ | — | ◐ | — | — | ✓ |
| Yapay zekâ kalıbı denetimi | ◐ | — | ◐ | — | ✓ | — | ◐ | — | — | ✓ (Türkçe) |
| Yazım kılavuzuna göre yazım denetimi | — | ◐ | — | ◐ | — | — | — | ◐ | ◐ | ✓ (TDK) |
| Okunabilirlik ve ritim ölçümü | — | ◐ | — | ✓ | ◐ | — | — | ✓ | — | ✓ (Ateşman) |
| Okur paneli simülasyonu | — | — | — | — | ✓ | — | — | — | ◐ | ✓ |

### Proje, sürüm ve istatistik

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| Düz metin (Markdown) proje biçimi | ✓ | ◐ | — | ◐ | ✓ | — | — | — | — | ✓ |
| Anlık görüntü, fark ve geri yükleme | — | ◐ | ✓ | ✓ | ◐ | ◐ | ✓ | ◐ | ◐ | ✓ |
| Kelime hedefi, bitiş tarihi, günlük hedef | — | ✓ | ◐ | ✓ | ◐ | ◐ | ◐ | ✓ | — | ✓ |
| Günlük yazım geçmişi ve seri | — | ✓ | — | — | — | — | ◐ | ◐ | — | ✓ |
| Yerel çalışma paneli | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ (salt okunur, tarayıcıda) |

### Dışa ve içe aktarma

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| EPUB | — | ✓ | ◐ | ✓ | ✓ | — | ✓ | ✓ | — | ✓ (EPUBCheck hatasız) |
| DOCX | — | ✓ | ◐ | ✓ | — | — | — | ✓ | — | ✓ |
| ODT | — | ✓ | — | ✓ | — | — | — | — | — | ✓ |
| Baskıya hazır HTML / PDF | — | ✓ | ◐ | ✓ | ✓ | — | ◐ | ✓ | — | ✓ |
| Markdown / TXT | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DOCX / ODT / EPUB taslağını bölümlere bölerek içe aktarma | — | ◐ | ◐ | ◐ | — | ◐ | ✓ | ◐ | ◐ | ✓ |

### Dil ve pazar

| Yetenek | CNS | nW | ANWA | Msk | AN | NF | ANW | bib | vela | Biz |
|---|---|---|---|---|---|---|---|---|---|---|
| Türkçe arayüz ya da yönerge | — | — | — | ✓ | — | — | — | ✓ | — | ✓ (yalnızca Türkçe) |
| Türkçe yazım kuralları, Türkçe kök bulma, Türkçe bölüm başlığı tanıma | — | — | — | — | — | — | — | — | — | ✓ |
| Türkiye yayın pazarı (yayınevi dosyası, dergi, bölümlü yayın, sesli kitap, dizi) | — | — | — | — | — | — | — | — | — | ✓ |
| Türkçe tür kartları (Osmanlı dönemi, erken Cumhuriyet dahil 14 kart) | — | — | — | — | — | — | — | — | — | ✓ |
| Ek bağımlılık gerektirmeyen araçlar | ◐ | — | — | — | — | — | — | — | — | ✓ (yalnızca Python standart kitaplığı) |

## Her projeden ne öğrendik, nerede karşılığı var?

Aşağıdaki fikirlerin hiçbiri kod ya da metin kopyalanarak alınmadı. Sağ sütundaki dosyalar bu depo için sıfırdan yazıldı ve testleri `testler/` altında.

| Proje | Esinlenilen yaklaşım | Bu depodaki karşılığı |
|---|---|---|
| chinese-novelist-skill | Katmanlı soru-cevapla fikir toplama; kaldığı yerden sürdürülebilir yazım planı; otomatik doğrulama ve yeniden yazım turları; kanca rehberi | `roman-planla`, `proje_durumu.py durum`, `revizyon_dongusu.py`, tür kartlarındaki kanca seçenekleri |
| novelWriter | Proje ağacı ve düz metin dosyalar; oturum günlüğü ve istatistik; yazı biçimi seçenekleriyle derleme | `yazim_istatistik.py`, `e_kitap_derle.py` (DOCX, ODT, baskı HTML'i, PDF, TXT, Markdown) |
| manuskript | Kar tanesi yöntemi; karakter motivasyon alanları; olay örgüsü hatları; dizin kartları; sıklık analizi; hedefler; revizyonlar | `kurgu_plani.py` (kar tanesi, sahne kartları, pano), `kurgu_ansiklopedisi.py`, `anlik_goruntu.py` |
| bibisco | Karakter mülakatı; mekân, nesne ve grup kayıtları; zaman çizelgesi; bölümlere dağılım analizi; son tarihli kelime hedefi | `kurgu_ansiklopedisi.py` (mülakat, dağılım, zaman çizelgesi), `yazim_istatistik.py hedef` |
| autonovel | Mekanik puan + model hakemi; plato tespiti; revizyon talimatı; Elo turnuvası; ses izi; ipucu defteri | `revizyon_dongusu.py` (yazar onaylı), `turnuva.py`, `ses_izi.py`, `ipucu_defteri.py`, `bolum-hakemi` ajanı |
| AI-Novel-Writing-Assistant | Bölümdeki kişilere göre süzülen bağlam; olgu ve ipucu geri yazımı; kontrol noktaları | `kurgu_ansiklopedisi.py baglam`, `takip_kaydet.py`, `anlik_goruntu.py` |
| NovelForge | Şemalı kayıt kartları; bağlam başvuruları; bilgi grafiği; kelime sayısı denetimi | Ansiklopedi şablonları, `grafik` (Mermaid/DOT), `metin_olcum.py` |
| AI-Novel-Writer | Kaynağı belli süreklilik bulguları; hedef hedef bölüm incelemesi; birleştirmeden önce fark; süresi geçen ipucu; EPUB içe aktarma; tam metin arama | `sureklilik_denetle.py` (satır numaralı bulgular), `bolum-hakemi` plan maddesi kararları, `anlik_goruntu.py fark`, `belge_ice_aktar.py`, `bilgi_ara.py` |
| vela | Yapı şablonları; yeniden yaz → cilala → incele zinciri; yerel bilgi tabanı; kendi anahtarını getir yaklaşımı | Beş yapı yöntemi, döngü turları, `bilgi_ara.py`; model seçimi ev sahibi ajana bırakılır |

## Bilerek farklı yaptıklarımız

- **Zengin metin düzenleyici yok.** Paket, yazarın zaten kullandığı ajanın (Claude Code, Codex, OpenCode…) ve editörün içinde çalışır; metin Markdown dosyalarındadır. Görsel ihtiyaç için salt okunur yerel çalışma masası vardır.
- **Vektör arama yok.** Ek bağımlılık istememek için arama sözcükseldir (BM25, Türkçe ek budama, düzeltme işaretine duyarsız). Anlamsal yakınlık gerekiyorsa ajanın kendi modeli bağlam paketi üzerinde çalışır.
- **Döngü yazarın elindedir.** Otomatik döngüler puan tutar ve öneri verir; bölüm dosyasına yazmak için `--yazar-onayladi` şarttır ve önceki hâl her zaman anlık görüntüye alınır.
- **Model yönlendirme yok.** Yazan model, kullandığınız ajanın modelidir; denetçiler ve kapılar her modelde aynı çalışır.
- **PDF, tarayıcıyla üretilir.** Baskıya hazır HTML (A5, ayna kenar boşlukları, bölüm başı yeni sayfa) çıkar; Chrome, Chromium ya da Edge kuruluysa `--bicim pdf` bunu PDF'e çevirir; DOCX ve ODT çıktıları LibreOffice ya da Word ile de PDF'e dönüştürülebilir.

## Türkçe için ekledikleri

Hiçbir incelenen projede karşılığı olmayan, Türkçe yazan yazar için eklenen yetenekler: TDK yazım denetimi, Türkçe yapay zekâ kalıpları ve çeviri kalkları, Ateşman okunabilirliği, Türkçe bölüm başlıklarını ("Birinci Bölüm", "BÖLÜM BİR", "3. bölüm: …") tanıyan içe aktarma, Türkçe binlik ve ondalık yazımı, Türkiye yayın pazarı becerileri, Osmanlı ve erken Cumhuriyet tür kartları ile dönem denetçisi.
