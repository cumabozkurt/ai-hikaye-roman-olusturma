"""Türkçe yapay zekâ klişeleri, yazım hataları ve metin yardımcıları (tek kaynak).

Bu modüldeki listeler ``ai_kalip_denetle.py``, ``yazim_denetle.py`` ve kanca
çekirdeği tarafından ortak kullanılır. Liste değişirse bütün denetçiler aynı
anda güncellenmiş olur.
"""

from __future__ import annotations

import re

HARF = "A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû"
KELIME = re.compile(rf"[{HARF}0-9]+(?:['’][{HARF}]+)?")


def tr_kucuk(metin: str) -> str:
    """Türkçe kurallara uygun küçük harfe çevirme (I→ı, İ→i)."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


def tr_ondalik(sayi: float, basamak: int = 1) -> str:
    """Türkçe ondalık yazımı: 108.7 → "108,7" (TDK: ondalık ayırıcı virgüldür)."""
    return f"{sayi:.{basamak}f}".replace(".", ",")


def tr_buyuk(metin: str) -> str:
    return metin.replace("i", "İ").replace("ı", "I").upper()


def diyalog_satiri_mi(satir: str) -> bool:
    """Konuşma çizgisiyle ya da tırnakla başlayan satır diyalogdur."""
    s = satir.lstrip()
    return s.startswith(("—", "–", "- ", "“", "\"", "«", "‘"))


def tirnak_disi(satir: str) -> str:
    """Tırnak içindeki konuşmaları boşlukla maskeler (sütun numaraları korunur)."""
    return re.sub(r"“[^”]*”|\"[^\"]*\"|«[^»]*»", lambda m: " " * len(m.group(0)), satir)


# ------------------------------------------------------------------ klişeler
# Yapay zekâ metinlerinde anlamca boş, sık tekrar eden kalıplar. Tek tek
# kullanımları yanlış değildir; yoğunlaştıklarında "yapay tat" oluşur.
KLISE_IFADELER: tuple[str, ...] = (
    "derin bir nefes aldı", "derin bir nefes alarak", "gözleri parladı", "gözleri parlıyordu",
    "kalbi hızla çarpıyordu", "kalbi küt küt atıyordu", "kalbi yerinden çıkacakmış gibi",
    "dudaklarında bir gülümseme belirdi", "yüzünde bir gülümseme belirdi", "hafif bir gülümseme",
    "içini bir ürperti kapladı", "tüyleri diken diken oldu", "zaman durmuş gibiydi",
    "sessizlik odayı doldurdu", "ağır bir sessizlik çöktü", "havada asılı kaldı",
    "bir an için", "bir anlığına", "tarif edilemez bir", "kelimelerle anlatılamaz",
    "boğazında bir düğüm", "midesinde kelebekler", "nefesini tuttu", "yutkundu",
    "gözlerini kıstı", "kaşlarını çattı", "başını hafifçe salladı", "omuz silkti",
    "yumruklarını sıktı", "çenesini sıktı", "dudağını ısırdı", "iç çekti",
    "kaderin cilvesi", "kaderin çarkları", "her şeyin değiştiği an", "hiçbir şey eskisi gibi olmayacaktı",
    "bir yolculuğun başlangıcı", "yeni bir sayfa", "sonun başlangıcı",
    "tüm benliğiyle", "ruhunun derinliklerinde", "içindeki fırtına", "yüreği burkuldu",
)

# Anlatımı bulanıklaştıran soyut / resmî doldurucular.
SOYUT_DOLGU: tuple[str, ...] = (
    "bu durum", "söz konusu", "oldukça", "son derece", "büyük bir önem", "kaçınılmaz olarak",
    "bir şekilde", "adeta", "tam anlamıyla", "kelimenin tam anlamıyla", "her ne kadar",
    "bu bağlamda", "bu noktada", "sonuç olarak", "ne var ki", "bununla birlikte",
)

# İngilizceden kelimesi kelimesine çeviri kokan yapılar (öneriyle).
CEVIRI_KALKLARI: dict[str, str] = {
    "günün sonunda": "sonuçta / eninde sonunda",
    "fark yaratmak": "işe yaramak / etkili olmak",
    "fark yarattı": "işe yaradı / etkili oldu",
    "önemli bir rol oynadı": "çok etkili oldu / belirleyiciydi",
    "rol oynamaktadır": "etkilidir",
    "hiçbir fikrim yok": "bilmiyorum / hiç bilmiyorum",
    "bunu kişisel algılama": "üstüne alınma",
    "kalbini takip et": "içinden geleni yap",
    "resmin bütünü": "işin bütünü / genel tablo",
    "ne demek istediğimi biliyorsun": "anladın sen",
    "göz teması kurdu": "gözlerine baktı",
    "göz teması kurmadan": "gözlerine bakmadan",
    "zaman içinde": "zamanla",
    "bir gülümseme ile": "gülümseyerek",
    "emin ol ki": "inan bana / şundan emin ol",
    "senin için orada olacağım": "yanında olacağım",
    "mantıklı geliyor": "akla yatıyor",
    "anlam ifade ediyor": "önemli / değerli",
    "tarafından sevildi": "(etken çatı) X onu sevdi",
    "yapılmakta olan": "yapılan",
}

# Çeviri kokan edilgen/uzatılmış fiil yapıları.
EDILGEN_DESENLER: tuple[tuple[str, str], ...] = (
    (r"\b\w+\s+tarafından\s+\w+(?:ldi|ldı|lmıştı|lmişti|ndi|ndı|nmıştı|nmişti)\b", "etken çatı kullanın: 'X tarafından açıldı' yerine 'X açtı'"),
    (r"\b\w+(?:mekte|makta)(?:ydi|ydı|dir|dır)\b", "'-mekteydi' resmî ve çeviri kokar; '-iyordu' kullanın"),
    (r"\b\w+(?:mesi|ması)\s+gerektiği\s+düşünülüyordu\b", "kimin düşündüğünü söyleyin, etken yazın"),
    (r"\bolduğu\s+(?:görüldü|gözlemlendi|anlaşıldı)\b", "anlatıcı gözlemci gibi konuşmasın; olanı doğrudan gösterin"),
)

# Benzetme işaretleri.
BENZETME_ISARETLERI = re.compile(r"\b(?:sanki|adeta|gibi|misali|andıran|andırıyordu)\b")

# Hikâye sonunda "fragman" gibi kapanan cümleler.
FRAGMAN_KAPANIS: tuple[str, ...] = (
    "henüz bilmiyordu ki", "bilmediği şey", "her şey daha yeni başlıyordu", "asıl hikâye şimdi başlıyordu",
    "kaderin çarkları dönmeye başlamıştı", "bu, sonun başlangıcıydı", "hiçbir şey eskisi gibi olmayacaktı",
    "o gece her şey değişecekti", "fırtına yaklaşıyordu", "ama bu başka bir hikâyeydi", "kimse bilmiyordu",
)

# Yazım: TDK'ya göre sık yapılan hatalar (yanlış → doğru).
YAZIM_HATALARI: dict[str, str] = {
    "herkez": "herkes", "yanlız": "yalnız", "yalnış": "yanlış", "şuanda": "şu anda", "şuan": "şu an",
    "birşey": "bir şey", "herşey": "her şey", "hiçbirşey": "hiçbir şey", "hiç bir": "hiçbir",
    "bir çok": "birçok", "bir kaç": "birkaç", "her hangi": "herhangi", "herhangibir": "herhangi bir",
    "tabiki": "tabii ki", "tabi ki": "tabii ki", "yada": "ya da", "malesef": "maalesef", "maalesefki": "maalesef",
    "orjinal": "orijinal", "eşkiya": "eşkıya", "kirbit": "kibrit", "sarımsak": "sarımsak",
    "yinede": "yine de", "hergün": "her gün", "herzaman": "her zaman", "birgün": "bir gün",
        "entellektüel": "entelektüel", "profösör": "profesör", "şöför": "şoför", "kiprik": "kirpik",
    "yanlışlıkla": "yanlışlıkla", "sürpriz": "sürpriz", "eksper": "eksper", "laboratuar": "laboratuvar",
    "makina": "makine", "meyva": "meyve", "yaşantı": "yaşantı", "egzos": "egzoz", "espiri": "espri",
    "fermuar": "fermuar", "kılavuz": "kılavuz", "klavuz": "kılavuz", "rasgele": "rastgele",
    "birsürü": "bir sürü", "ön görü": "öngörü", "art arda": "art arda",
    "ardarda": "art arda", "peşpeşe": "peş peşe", "yüzyüze": "yüz yüze", "karşılıklı": "karşılıklı",
    "süpriz": "sürpriz", "yalnızlık": "yalnızlık", "doğru dürüst": "doğru dürüst", "birbirine": "birbirine",
    "herbiri": "her biri", "hiçkimse": "hiç kimse", "birazcık": "birazcık", "pekçok": "pek çok",
    "eşşek": "eşek", "kolleksiyon": "koleksiyon", "traş": "tıraş", "antreman": "antrenman",
    "mütahit": "müteahhit", "hakkaten": "hakikaten", "şarz": "şarj", "poaça": "poğaça",
    "dinazor": "dinozor", "eşortman": "eşofman", "birdaha": "bir daha", "birtane": "bir tane",
    "yanız": "yalnız", "sanki de": "sanki", "kardeşim de": "kardeşim de", "yaptırım": "yaptırım",
    "bilimum": "bilumum", "kurallar dahilinde": "kurallar dâhilinde", "sıfır ile": "sıfır ile",
    "orjinallik": "orijinallik", "yöresel": "yöresel", "direkman": "doğrudan", "atmışdı": "atmıştı",
    "kitaplıkda": "kitaplıkta", "yapmışdı": "yapmıştı", "gitmişdi": "gitmişti",
}
# Doğru yazılmış olup yanlışlıkla listeye düşen eşdeğerler temizlenir.
YAZIM_HATALARI = {k: v for k, v in YAZIM_HATALARI.items() if k != v}

# Konuşma dilinde bilinçli kullanılabilen biçimler: diyalogda serbest,
# anlatıda yalnızca uyarı olarak raporlanır.
GAYRIRESMI: dict[str, str] = {
    "bi": "bir", "yapıcam": "yapacağım", "gelicem": "geleceğim", "gidicem": "gideceğim",
    "napıyorsun": "ne yapıyorsun", "naber": "ne haber", "tamam mı yani": "tamam mı",
    "bişey": "bir şey", "bişi": "bir şey", "noldu": "ne oldu", "nası": "nasıl", "gidiyom": "gidiyorum",
    "biliyomusun": "biliyor musun", "şey yani": "şey", "valla": "vallahi",
}

# "ki" bitişik yazılan sözcükler (bağlaç "ki" ayrı yazılır, bunlar istisnadır).
KI_BITISIK: frozenset[str] = frozenset({
    "belki", "çünkü", "sanki", "oysaki", "halbuki", "mademki", "meğerki", "illaki", "hâlbuki",
})
# "-ki" ilgi eki alan yaygın sözcükler (bitişik doğrudur).
KI_ILGI_EKI: re.Pattern[str] = re.compile(
    rf"^(?:[{HARF}]+(?:daki|deki|taki|teki|ndaki|ndeki|nki|ninki|nınki|nunki|nünki)|bugünkü|dünkü|yarınki|akşamki|sabahki|öbürkü|geçenki|önceki|sonraki|yukarıki)$"
)

# "de/da" bitişik yazılması doğru olan (ek olan) yaygın sözcük sonları: bulunma hâli
# ile karışmaması için yalnızca bağlaç olarak kullanılması çok yaygın kalıplar denetlenir.
DE_DA_BAGLAC_ONCESI: frozenset[str] = frozenset({
    "ben", "sen", "o", "biz", "siz", "onlar", "bu", "şu", "bende", "hem", "yine", "ama", "şimdi",
    "sonra", "önce", "bugün", "yarın", "dün", "burada", "orada", "şurada", "evet", "hayır",
})
# Bağlaç "de/da"nın bitiştirildiği yaygın hatalı biçimler.
DE_DA_HATALI: dict[str, str] = {
    "bende": "ben de", "sende": "sen de", "ode": "o da", "bizde": "biz de", "sizde": "siz de",
    "onlarda": "onlar da", "yinede": "yine de", "şimdide": "şimdi de", "sonrada": "sonra da",
    "hemde": "hem de", "amada": "ama da", "bugünde": "bugün de", "yarında": "yarın da",
}
# "bende/sende/bizde/sizde/onlarda" bulunma hâli olarak da doğru olabilir; bağlama bakılır:
# ardından "öyle, gelirim, gideceğim, istiyorum" gibi fiil ya da eşitlik gelirse bağlaçtır.
DE_DA_BAGLAC_IPUCU = re.compile(
    rf"\b(bende|sende|bizde|sizde|onlarda|yinede|hemde|şimdide|sonrada)\s+(?:öyle|aynı|geliyorum|gelirim|gelece|gideceğim|gidiyorum|istiyorum|isterim|bilmiyorum|biliyorum|seni|onu|sizi|bizi|bunu|varım|yokum|düşünüyorum|korktum|korkuyorum|sevdim|seviyorum|[{HARF}]+(?:acağım|eceğim|ıyorum|iyorum|uyorum|üyorum|dım|dim|dum|düm|tım|tim|tum|tüm))\b",
    re.I,
)

# Soru eki "mı/mi/mu/mü" ayrı yazılır: yaygın bitişik hatalar.
SORU_EKI_BITISIK = re.compile(
    rf"\b([{HARF}]{{2,}}?(?:yor|acak|ecek|mış|miş|muş|müş|dı|di|du|dü|tı|ti|tu|tü|r|ar|er|ır|ir|ur|ür))(mı|mi|mu|mü|mısın|misin|musun|müsün|mıyım|miyim|muyum|müyüm|mıydı|miydi|muydu|müydü|mısınız|misiniz|musunuz|müsünüz)\b",
    re.I,
)
SORU_EKI_ISTISNA: frozenset[str] = frozenset({
    # Sonu soru ekine benzeyen gerçek sözcükler.
    "ermişmi", "yurtmu", "durmu", "armu", "ormu", "kırmızı", "karmu", "demir", "samimi", "kimi", "sanmı",
    "birimi", "tanımı", "anlamı", "yarımı", "zamanı", "tamamı", "adımı"
})

# Yapay zekânın kendini ele verdiği ya da üretimi reddettiği cümleler.
YZ_OZ_GONDERME: tuple[str, ...] = (
    "bir yapay zekâ olarak", "bir yapay zeka olarak", "bir dil modeli olarak", "size yardımcı olmaktan memnuniyet",
    "elbette! işte", "elbette, işte", "işte bölümün devamı", "işte hikâyenin devamı", "umarım beğenirsiniz",
    "bu içeriği oluşturamam", "bu isteği yerine getiremem", "as an ai", "i cannot", "here is the",
)

# Metne sızmaması gereken çalışma/mühendislik sözcükleri.
MUHENDISLIK_SIZINTILARI: tuple[str, ...] = (
    "hedef uzunluk:", "bölüm planı", "sahne tablosu", "duygu hedefi:", "kanca türü", "todo", "fixme",
    "```", "json", "kelime sayısı:", "[yer tutucu]", "{{", "}}", "<!--", "ipucu f0", "olay e0",
)
