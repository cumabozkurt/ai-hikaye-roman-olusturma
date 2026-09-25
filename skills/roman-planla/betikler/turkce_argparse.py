"""argparse'ın yerleşik İngilizce iletilerini (usage, options, error …) Türkçeleştirir.

Yalnızca içe aktarmak yeter::

    import turkce_argparse  # noqa: F401

argparse iletilerini ``gettext`` üzerinden çevirir; bu modül argparse'ın modül düzeyindeki
``_`` ve ``ngettext`` adlarını bir çeviri tablosuyla değiştirir. Tabloda olmayan ileti
olduğu gibi kalır; böylece yeni bir Python sürümü çalışmayı bozmaz.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

CEVIRI: dict[str, str] = {
    "usage: ": "kullanım: ",
    "options": "seçenekler",
    "optional arguments": "seçenekler",
    "positional arguments": "konumsal argümanlar",
    "subcommands": "alt komutlar",
    "%(heading)s:": "%(heading)s:",
    "show this help message and exit": "bu yardım iletisini gösterir ve çıkar",
    "show program's version number and exit": "program sürümünü gösterir ve çıkar",
    " (default: %(default)s)": " (varsayılan: %(default)s)",
    "%(prog)s: error: %(message)s\n": "%(prog)s: hata: %(message)s\n",
    "%(prog)s: warning: %(message)s\n": "%(prog)s: uyarı: %(message)s\n",
    "the following arguments are required: %s": "şu argümanlar zorunlu: %s",
    "unrecognized arguments: %s": "tanınmayan argümanlar: %s",
    "argument %(argument_name)s: %(message)s": "%(argument_name)s argümanı: %(message)s",
    "invalid choice: %(value)r (choose from %(choices)s)": "geçersiz seçim: %(value)r (seçenekler: %(choices)s)",
    "invalid choice: %(value)r, maybe you meant %(closest)r? (choose from %(choices)s)":
        "geçersiz seçim: %(value)r; %(closest)r mı demek istediniz? (seçenekler: %(choices)s)",
    "invalid %(type)s value: %(value)r": "geçersiz %(type)s değeri: %(value)r",
    "expected one argument": "bir değer bekleniyor",
    "expected at least one argument": "en az bir değer bekleniyor",
    "expected at most one argument": "en çok bir değer bekleniyor",
    "expected %s argument": "%s değer bekleniyor",
    "expected %s arguments": "%s değer bekleniyor",
    "not allowed with argument %s": "%s argümanıyla birlikte kullanılamaz",
    "one of the arguments %s is required": "şu argümanlardan biri zorunlu: %s",
    "ambiguous option: %(option)s could match %(matches)s": "belirsiz seçenek: %(option)s şunlarla eşleşebilir: %(matches)s",
    "can't open '%(filename)s': %(error)s": "'%(filename)s' açılamadı: %(error)s",
    "ignored explicit argument %r": "yok sayılan açık argüman: %r",
    "unexpected option string: %s": "beklenmeyen seçenek: %s",
    "unknown parser %(parser_name)r (choices: %(choices)s)": "bilinmeyen alt komut %(parser_name)r (seçenekler: %(choices)s)",
    "argument '%(argument_name)s' is deprecated": "'%(argument_name)s' argümanı kullanımdan kalktı",
    "option '%(option)s' is deprecated": "'%(option)s' seçeneği kullanımdan kalktı",
    "command '%(parser_name)s' is deprecated": "'%(parser_name)s' komutu kullanımdan kalktı",
}


def cevir(ileti: str) -> str:
    return CEVIRI.get(ileti, ileti)


def _ngettext(tekil: str, cogul: str, sayi: int) -> str:
    return cevir(tekil if sayi == 1 else cogul)


argparse._ = cevir  # type: ignore[attr-defined]
argparse.ngettext = _ngettext  # type: ignore[attr-defined]


# Yardım metni verilmemiş ortak seçenekler için tutarlı Türkçe açıklamalar.
ORTAK_YARDIM: dict[str, str] = {
    "json": "sonucu JSON olarak yaz",
    "proje": "kitap ya da öykü klasörü (ör. saatcinin-kizi)",
    "cikti": "çıktı dosyası ya da klasörü",
    "kok": "çalışma kökü (çözümleme ya da çalışma alanı klasörü)",
    "girdi": "girdi dosyası (çoğunlukla JSON)",
    "dosya": "okunacak metin dosyası",
    "calisma-alani": "yazım çalışma alanının kök klasörü",
    "bolum": "bölüm numarası (1'den başlar)",
    "kitap": "kitap klasörü (çalışma alanına göre)",
    "yazar": "yazar adı (künyede ve kapakta görünür)",
    "port": "tarayıcı hata ayıklama bağlantı noktası (varsayılan 9222)",
    "kutuphane": "ilham kütüphanesi klasörü",
    "sekme": "sekme kimliği (sekmeler komutunun çıktısından)",
    "not": "ek istek ya da not",
    "denetle": "yazmadan yalnızca denetle",
    "bekle": "sayfa yüklenmesi için beklenecek saniye",
    "baslik": "kitap başlığı",
    "azami": "okunacak en çok karakter",
    "adres": "açılacak sayfa adresi (http ya da https)",
    "yz-ozeti-yok": "yapay zekâ kalıbı özetini ekleme",
    "yeniden": "var olan çıktı dosyalarının üzerine yaz",
    "alt": "bölüm uzunluğu alt sınırı (kelime)",
    "ust": "bölüm uzunluğu üst sınırı (kelime)",
    "tur-adi": "özel tercih türünün adı",
    "tum-diller": "yalnızca Türkçe değil, bütün dillerdeki öyküleri say",
    "tarayici": "Chrome/Chromium/Edge yürütülebilir dosyasının yolu",
    "tampon": "yayına başlamadan önce hazır tutulacak bölüm sayısı",
    "tam": "örnek bölümler yerine tam metni pakete koy",
    "sozlesme": "bölüm planının sözleşme alanlarını göster",
    "sinir": "gösterilecek en çok kayıt",
    "saat": "yayın saati (SS:DD, ör. 20:00)",
    "profil": "ayrı tarayıcı profili klasörü",
    "plan": "bölüm planı dosyası",
    "metin": "bölüm metni dosyası",
    "kuru": "hiçbir şey yazmadan yapılacakları göster",
    "kaynak": "kaynak metin dosyası (TXT ya da Markdown)",
    "is-akisi": "iş akışı adı (ör. gunluk-yazim)",
    "icindekiler": "içindekiler görünümünü üret",
    "gecmis": "geçmiş birimleri de göster",
    "etiket": "süzülecek etiket",
    "docx": "Word (.docx) çıktısı da üret (pandoc gerekir)",
    "birim": "gösterilecek plan birimi (ör. L1-02)",
    "baslangic": "ilk yayın tarihi (YYYY-AA-GG)",
    "aralik-ozeti": "plan komutunun verdiği aralık özeti (SHA-256)",
    "hedef": "hedef uzunluk (kelime, ör. 2200)",
    "hiz": "seslendirme hızı (dakikada kelime)",
    "dosyalar": "denetlenecek metin dosyaları",
    "yol": "dosya ya da klasör yolu",
    "klasor": "öykü klasörü",
}

_ozgun_ekle = argparse._ActionsContainer.add_argument  # type: ignore[attr-defined]


def _yardimli_ekle(self, *args, **kw):  # type: ignore[no-untyped-def]
    if kw.get("help") is None:
        ad = next((a[2:] for a in args if isinstance(a, str) and a.startswith("--")), None)
        if ad is None and args and isinstance(args[0], str) and not args[0].startswith("-"):
            ad = args[0]
        if ad in ORTAK_YARDIM:
            kw["help"] = ORTAK_YARDIM[ad]
    return _ozgun_ekle(self, *args, **kw)


argparse._ActionsContainer.add_argument = _yardimli_ekle  # type: ignore[attr-defined]


JSON_ILETILERI: dict[str, str] = {
    "Expecting value": "değer bekleniyordu",
    "Expecting property name enclosed in double quotes": "çift tırnak içinde alan adı bekleniyordu",
    "Expecting ',' delimiter": "virgül bekleniyordu",
    "Expecting ':' delimiter": "iki nokta bekleniyordu",
    "Extra data": "fazladan veri var",
    "Unterminated string starting at": "kapanmamış tırnak",
    "Invalid control character at": "geçersiz denetim karakteri",
    "Invalid \\escape": "geçersiz kaçış dizisi",
    "Illegal trailing comma before end of object": "nesnenin sonunda fazladan virgül",
    "Illegal trailing comma before end of array": "dizinin sonunda fazladan virgül",
}


def json_iletisi(hata: json.JSONDecodeError) -> str:
    """JSON ayrıştırma hatasını Türkçe konum bilgisiyle anlatır."""
    return f"geçersiz JSON (satır {hata.lineno}, sütun {hata.colno}): {JSON_ILETILERI.get(hata.msg, 'sözdizimi hatası')}"


def hata_iletisi(hata: BaseException) -> str:
    """Yakalanmamış bir hatayı kullanıcıya dönük Türkçe tek satıra çevirir."""
    ad = getattr(hata, "filename", None) or ""
    if isinstance(hata, FileNotFoundError):
        return f"dosya ya da klasör bulunamadı: {ad}"
    if isinstance(hata, IsADirectoryError):
        return f"dosya bekleniyordu, klasör verildi: {ad}"
    if isinstance(hata, NotADirectoryError):
        return f"klasör bekleniyordu, dosya verildi: {ad}"
    if isinstance(hata, PermissionError):
        return f"erişim izni yok: {ad}"
    if isinstance(hata, UnicodeDecodeError):
        return "dosya UTF-8 metin değil (ikili ya da başka bir kodlamada olabilir); dosyayı UTF-8 olarak kaydedin"
    if isinstance(hata, json.JSONDecodeError):
        return json_iletisi(hata)
    if isinstance(hata, OSError):
        return f"dosya işlemi başarısız: {hata.strerror or hata} {ad}".rstrip()
    if type(hata).__module__ != "builtins" and str(hata):
        return str(hata)  # betiklerin kendi Türkçe hata sınıfları
    ileti = str(hata)
    if isinstance(hata, (ValueError, RuntimeError)) and any(h in ileti for h in "çğıöşüÇĞİÖŞÜ"):
        return ileti  # betiğin kendi Türkçe iletisi
    if isinstance(hata, ValueError):
        if "time data" in ileti or "out of range" in ileti or "must be in" in ileti:
            return "geçersiz tarih ya da saat (ör. 2026-10-01 ve 20:00)"
        return "geçersiz değer; girdiyi ve seçenekleri denetleyin"
    return f"beklenmeyen hata ({type(hata).__name__}). Ayrıntı için HIKAYE_AYIKLA=1 ile yeniden çalıştırın ve hata bildirin."


def _hata_kancasi(tur, hata, iz):  # type: ignore[no-untyped-def]
    if os.environ.get("HIKAYE_AYIKLA") or not isinstance(hata, Exception):
        sys.__excepthook__(tur, hata, iz)
        return
    program = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "betik"
    print(f"{program}: hata: {hata_iletisi(hata)}", file=sys.stderr)


# Yakalanmamış hatalarda İngilizce yığın izi yerine Türkçe tek satır (çıkış kodu 1).
sys.excepthook = _hata_kancasi
