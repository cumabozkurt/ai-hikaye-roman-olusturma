# Üslup Kararı

Bölüm yazmadan, yeniden yazmadan ya da incelemeden önce **üslup kararı** verilir ve aynı karar bütün yürütücülere (ana oturum, anlati-yazari, inceleyiciler) iletilir.

## Öncelik sırası

1. **Anlık istek**: Yazarın bu görevde açıkça söylediği ("bu bölüm daha kısa cümlelerle olsun").
2. **Kitabın üslup dosyası**: `kurgu/ton.md` (anlatıcı, zaman kipi, cümle ritmi, duyular, diyalog biçimi, yasaklar).
3. **Yazar hafızası**: `yazar_hafizasi.py sorgula` ile gelen etkin tercihler (≤ 2 KB).
4. **Tür düzyazı kartı**: `tur-kartlari/` içinden kitabın türü.
5. **Genel kaynaklar**: yz-tadi, TDK rehberi.

Her boyut ayrı değerlendirilir: anlık istek yalnızca diyalogdan söz ediyorsa, anlatıcı seçimi hâlâ üslup dosyasından gelir.

## Karar notu

Karar, yürütücüye verilen isteme kısa bir blok olarak yazılır:

```
Üslup kararı
- Anlatıcı: üçüncü tekil, Defne'ye yakın (kurgu/ton.md)
- Zaman: di'li geçmiş
- Diyalog: konuşma çizgisi (—) (yazar hafızası KP003)
- Ritim: orta uzunlukta cümle; gerilimde kısa (kurgu/ton.md)
- Bu görevde: bölüm sonu daha sert (anlık istek)
```

`kurgu/ton.md` yoksa önce yazara iki üç soruyla bir üslup dosyası önerilir; yanıt beklenemiyorsa tür kartına göre yazılır ve bu açıkça bildirilir.
