# Yapay zekâ tadı karşılaştırması

Aynı sahnenin iki hâli. `once.md` bilerek yapay zekâ kalıplarıyla yazıldı; `sonra.md`, `yz-tadi-gider` becerisinin önerdiği yönlerle (duyguyu söylemek yerine eylem ve nesneyle göstermek) yeniden yazıldı.

Denetimi kendiniz çalıştırın:

```bash
python3 paylasilan/betikler/ai_kalip_denetle.py ornekler/yz-tadi-karsilastirma/once.md
python3 paylasilan/betikler/ai_kalip_denetle.py ornekler/yz-tadi-karsilastirma/sonra.md
```

| Dosya | Bulgu | Engelleyici | Çıkış kodu |
|---|---|---|---|
| `once.md` | 10 | 6 | 1 |
| `sonra.md` | 0 | 0 | 0 |

`once.md` içinde yakalanan başlıca kalıplar:

- **"X değil, Y" dönüşü**: "Bu sadece bir saat değildi, geçmişin kilitli bir kapısıydı."
- **Bir yandan / diğer yandan**: mekanik paralellik.
- **Olumsuzluk dizisi**: "Korku yoktu. Tereddüt yoktu. Geri dönüş yoktu."
- **Ses karşıtlığı**: "Sesi alçaktı ama…"
- **Fragman kapanışı**: "hiçbir şey eskisi gibi olmayacaktı", "bir yolculuğun başlangıcıydı".
- **Klişe ve benzetme yoğunluğu**: derin nefes, hızla çarpan kalp, duran zaman, "adeta… sanki…" zinciri.

İki metin yaklaşık aynı uzunlukta. Fark şurada: ilki okura ne hissetmesi gerektiğini söylüyor, ikincisi aynı anı görünür eyleme ve nesneye (çentik, bilet, dağılan mürekkep) bırakıyor.

Denetçi bir yazım denetleyicisidir, yapay zekâ dedektörü değildir: amaç okuma deneyimini iyileştirmek, bir tespit aracının puanını düşürmek değil.
