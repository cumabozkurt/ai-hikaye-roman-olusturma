"""argparse'ın yerleşik İngilizce iletilerini (usage, options, error …) Türkçeleştirir.

Yalnızca içe aktarmak yeter::

    import turkce_argparse  # noqa: F401

argparse iletilerini ``gettext`` üzerinden çevirir; bu modül argparse'ın modül düzeyindeki
``_`` ve ``ngettext`` adlarını bir çeviri tablosuyla değiştirir. Tabloda olmayan ileti
olduğu gibi kalır; böylece yeni bir Python sürümü çalışmayı bozmaz.
"""

from __future__ import annotations

import argparse

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
