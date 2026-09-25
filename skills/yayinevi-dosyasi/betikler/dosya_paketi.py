#!/usr/bin/env python3
"""Yayınevine gönderilecek dosya paketini hazırlar.

Kullanım::

    dosya_paketi.py --proje KITAP --yazar "Ad Soyad" [--kelime-siniri 9000] [--tam] [--docx] [--cikti KITAP/yayinevi]

Üretilenler (``<cikti>/GG-AA-YYYY/``):
  * ``kunye.md``          kitap adı, tür, toplam kelime, tahmini sayfa, bölüm sayısı, hedef okur
  * ``ornek-bolumler.md`` baştan itibaren sınırı aşmayan tam bölümler (varsayılan ≈30 sayfa)
  * ``tam-metin.md``      ``--tam`` ile bütün bölümler
  * ``sinopsis.md``, ``ust-yazi.md``, ``yazar-biyografisi.md``  doldurulacak şablonlar
    (varsa kurgu/ ve plan/ dosyalarından ön bilgi eklenir)
  * ``denetim.json``      örnek bölümlerde yazım denetimi özeti
  * ``--docx``            pandoc varsa .md dosyalarının .docx kopyaları
Var olan dosyaların üzerine yazılmaz.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metin_olcum  # noqa: E402
import yazim_denetle  # noqa: E402

try:  # argparse iletilerini ve hata iletilerini Türkçeleştirir
    import turkce_argparse  # noqa: F401
    from turkce_argparse import hata_iletisi
except ImportError:  # pragma: no cover
    hata_iletisi = str

SAYFA_KELIME = 280  # 13,5×21 cm, 11 punto kitap sayfası için kaba ortalama


def sayi(n: int) -> str:
    return f"{n:,}".replace(",", ".")


class PaketHatasi(RuntimeError):
    pass


def kitap_adi(proje: Path) -> str:
    durum = proje / "takip" / "_takip-durumu.json"
    if durum.is_file():
        try:
            ad = json.loads(durum.read_text(encoding="utf-8")).get("kitap_adi")
            if ad:
                return str(ad)
        except ValueError:
            pass
    genel = proje / "plan" / "genel-plan.md"
    if genel.is_file():
        m = re.search(r"^#\s+(.+)$", genel.read_text(encoding="utf-8"), re.M)
        if m:
            return re.sub(r"^(Genel Plan\s*[:—-]\s*)", "", m.group(1)).strip()
    return proje.name


def bolum_basligi(metin: str) -> str:
    m = re.search(r"^#\s+(.+)$", metin, re.M)
    return m.group(1).strip() if m else ""


def satir_ara(yol: Path, anahtar: str) -> str:
    if not yol.is_file():
        return ""
    m = re.search(rf"^\s*[-*]?\s*\**{anahtar}\**\s*:\s*(.+)$", yol.read_text(encoding="utf-8"), re.M | re.I)
    return m.group(1).strip() if m else ""


def yaz(yol: Path, icerik: str, yazilan: list[str]) -> None:
    if yol.exists():
        raise PaketHatasi(f"{yol} zaten var; üzerine yazılmaz (klasörü silin ya da --cikti değiştirin)")
    yol.write_text(icerik, encoding="utf-8", newline="\n")
    yazilan.append(str(yol))


def paket(proje: Path, yazar: str, sinir: int, tam: bool, docx: bool, cikti: Path) -> dict[str, Any]:
    bolumler = sorted((proje / "metin").glob("bolum-*.md"))
    if not bolumler:
        raise PaketHatasi(f"{proje}/metin altında bölüm yok")
    metinler = [(b, b.read_text(encoding="utf-8")) for b in bolumler]
    sayilar = [metin_olcum.kelime_say(m) for _, m in metinler]
    toplam = sum(sayilar)
    ornek: list[tuple[Path, str]] = []
    birikim = 0
    for (b, m), n in zip(metinler, sayilar):
        if ornek and birikim + n > sinir:
            break
        ornek.append((b, m))
        birikim += n
    hedef = cikti / date.today().strftime("%d-%m-%Y")
    hedef.mkdir(parents=True, exist_ok=True)
    ad = kitap_adi(proje)
    tur = satir_ara(proje / "kurgu" / "tur-konumu.md", "Tür") or satir_ara(proje / "plan" / "genel-plan.md", "Tür")
    okur = satir_ara(proje / "kurgu" / "tur-konumu.md", "Hedef okur") or satir_ara(proje / "plan" / "genel-plan.md", "Hedef okur")
    yazilan: list[str] = []
    yaz(hedef / "kunye.md", "\n".join([
        f"# {ad}", "", f"- Yazar: {yazar}", f"- Tür: {tur or '[doldurulacak]'}", f"- Hedef okur: {okur or '[doldurulacak]'}",
        f"- Toplam uzunluk: {sayi(toplam)} kelime (yaklaşık {sayi(round(toplam / SAYFA_KELIME))} kitap sayfası)",
        f"- Bölüm sayısı: {len(bolumler)}", f"- Durum: {'tamamlandı' if tam else '[tamamlandı / devam ediyor]'}",
        f"- Örnek bölümler: {len(ornek)} bölüm, {sayi(birikim)} kelime", ""]), yazilan)
    govde = [f"# {ad}", "", f"{yazar}", ""]
    for _, m in ornek:
        govde += [m.strip(), "", "\\newpage" if docx else "", ""]
    yaz(hedef / "ornek-bolumler.md", "\n".join(s for s in govde if s is not None) + "\n", yazilan)
    if tam:
        yaz(hedef / "tam-metin.md", "\n\n".join([f"# {ad}\n\n{yazar}"] + [m.strip() for _, m in metinler]) + "\n", yazilan)
    ozet = satir_ara(proje / "plan" / "genel-plan.md", "Öncül")
    yaz(hedef / "sinopsis.md", "\n".join([
        f"# {ad}: Sinopsis", "", f"**Öncül:** {ozet or '[tek cümle]'}", "",
        "[1 sayfa (400–600 kelime), üçüncü tekil, şimdiki zaman. Başlangıç, ana çatışma, dönüm, doruk ve SON açıkça yazılır; "
        "editör sonu bilmek ister. Yan karakterlerden yalnızca olay örgüsünü etkileyenler.]", ""]), yazilan)
    yaz(hedef / "ust-yazi.md", "\n".join([
        "Sayın [Editörün adı / Yayın Kurulu],", "",
        f"{tur or '[tür]'} türündeki, yaklaşık {sayi(toplam)} kelimelik \"{ad}\" adlı romanımı değerlendirmenize sunuyorum.", "",
        "[Tek paragraf tanıtım: kahraman, istek, engel, risk. 80–120 kelime.]", "",
        "[Neden bu yayınevi: yayın çizgisiyle bağ, benzer kitaplar (en çok iki).]", "",
        "[Kısa yazar tanıtımı: ilgili yayın, ödül, Wattpad okur sayısı varsa.]", "",
        "Ekte sinopsisi ve ilk bölümleri bulabilirsiniz. Değerlendirmeniz için teşekkür ederim.", "",
        f"Saygılarımla,\n{yazar}\n[e-posta] · [telefon]", ""]), yazilan)
    yaz(hedef / "yazar-biyografisi.md", f"# {yazar}\n\n[Üçüncü tekil, 80–150 kelime: doğum yeri/yılı (isteğe bağlı), eğitim ve meslek (ilgiliyse), yayımlanmış öykü/kitaplar, ödüller.]\n", yazilan)
    denetim = []
    for b, m in ornek:
        bulgular = yazim_denetle.denetle_metin(m, b.name)
        denetim.append({"dosya": b.name, "hata": sum(1 for x in bulgular if x.duzey == "hata"),
                        "uyari": sum(1 for x in bulgular if x.duzey == "uyari")})
    yaz(hedef / "denetim.json", json.dumps(denetim, ensure_ascii=False, indent=2) + "\n", yazilan)
    docx_notu = None
    if docx:
        if shutil.which("pandoc"):
            for md in list(hedef.glob("*.md")):
                subprocess.run(["pandoc", str(md), "-o", str(md.with_suffix(".docx"))], check=True)  # noqa: S603,S607
                yazilan.append(str(md.with_suffix(".docx")))
        else:
            docx_notu = "pandoc bulunamadı; .md dosyalarını Word/LibreOffice ile açıp .docx olarak kaydedin"
    return {"tamam": True, "klasor": str(hedef), "toplam_kelime": toplam, "ornek_bolum": len(ornek),
            "ornek_kelime": birikim, "yazilan": yazilan, "docx_notu": docx_notu,
            "yazim_hatasi": sum(d["hata"] for d in denetim)}


def main(argv: list[str] | None = None) -> int:
    ayr = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ayr.add_argument("--proje", required=True, type=Path)
    ayr.add_argument("--yazar", required=True)
    ayr.add_argument("--kelime-siniri", type=int, default=9000, help="örnek bölümler için üst sınır (≈30 sayfa)")
    ayr.add_argument("--tam", action="store_true")
    ayr.add_argument("--docx", action="store_true")
    ayr.add_argument("--cikti", type=Path)
    arg = ayr.parse_args(argv)
    try:
        sonuc = paket(arg.proje, arg.yazar, arg.kelime_siniri, arg.tam, arg.docx, arg.cikti or arg.proje / "yayinevi")
    except (PaketHatasi, OSError, subprocess.CalledProcessError) as hata:
        print(json.dumps({"tamam": False, "hata": hata_iletisi(hata)}, ensure_ascii=False))
        return 2
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
