# Çıktı Yapısı ve Şablonları

```
cozumleme-kutuphanesi/<kitap>/
├── kaynak/metin.txt            # yalnızca yerelde; depoya ve paylaşıma konmaz
├── bolum-dizini.csv            # mekanik dizin (bolum_dizini.py)
├── _ilerleme.json              # aşama ve grup durumu (cozumleme_calismasi.py)
├── _onbellek/grup-A-B.json     # bölüm çıkarıcı çıktıları (kurtarma kanıtı)
├── hizli-bakis.md
├── ozet.md
├── cozumleme-raporu.md         # okuma girişi
├── bolumler/
│   ├── ilk-uc-bolum.md
│   └── bolum-NNN_ozet.md
├── olay-orgusu/{hikaye-hatti,tempo,duygu-mekanizmalari}.md
├── karakterler/{ad}.md, iliskiler.md
├── dunya/{konu}.md
├── iliski-semasi.md            # Mermaid
└── uslup.md
```

## hizli-bakis.md

```markdown
# Hızlı Bakış: <Kitap>
- Tür / alt tür:
- Yayın yeri ve okur kitlesi:
- Tek cümlelik öncül:
- Okurun peşinden gittiği soru:
- İlk bölümün kancası:
- En güçlü 3 mekanizma:
- Kendi kitabınız için tek cümlelik ders:
```

## cozumleme-raporu.md

1. Kapsam (kaç bölüm, hangi aşamalar)
2. Temel bulgular (5 madde)
3. Okur neyin peşinde
4. Hikâye nasıl ilerliyor (aşamalar: Başlangıç, Gelişme, Dönüm, Doruk, Kapanış)
5. Karakterler ve ilişkiler (şemaya bağlantı)
6. Okur ile karakter arasındaki bilgi farkı
7. Tempo (tempo.md'den en belirgin 3 örüntü)
8. Temel mekanizmalar (DM kartlarına bağlantı)
9. Alınabilecek teknikler (soyut)
10. Alınmaması gerekenler (özgün unsurlar, telif ve klişe riskleri)

## Duygu mekanizması kartı

```markdown
## DM-001: Haksız suçlama ve gecikmiş aklanma
- Etiketler: aile, adalet, intikam
- Mekanizma: Okurun bildiği masumiyet ile karakterlerin inandığı suç arasındaki fark, aklanma ertelendikçe beklenti biriktirir.
- Kurulum: (bölüm numaralarıyla)
- Ödeme: (bölüm numaralarıyla)
- Yeniden kullanım koşulu: Okur masumiyeti kanıtla bilmeli; erteleme 3–5 bölümü geçmemeli.
```
