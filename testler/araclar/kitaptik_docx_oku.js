// Kitaptik yazar ekranındaki toplu yükleme kuralını bağımsız olarak uygular (mammoth ile):
// her Başlık 1 yeni bölümdür; başlık 77 karakterle sınırlıdır; kelime = etiketler atılınca boşlukla ayrılan parça.
// Kullanım: node kitaptik_docx_oku.js dosya.docx  → JSON: {bolumler: [{baslik, kelime}], onsoz, uyarilar}
"use strict";
const mammoth = require("mammoth");

function sade(html) {
  return html.replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
}
function kelime(html) {
  return sade(html).split(/\s+/).filter(Boolean).length;
}

mammoth.convertToHtml({ path: process.argv[2] }).then((sonuc) => {
  const html = sonuc.value || "";
  const desen = /<h1[^>]*>([\s\S]*?)<\/h1>/gi;
  const basliklar = [];
  let m;
  while ((m = desen.exec(html)) !== null) {
    basliklar.push({ bas: m.index, son: m.index + m[0].length, metin: sade(m[1]).replace(/\s+/g, " ").trim() });
  }
  const onsoz = basliklar.length ? sade(html.slice(0, basliklar[0].bas)).trim() : sade(html).trim();
  const bolumler = basliklar.map((b, i) => {
    const govde = html.slice(b.son, i + 1 < basliklar.length ? basliklar[i + 1].bas : html.length);
    return { baslik: b.metin, baslik_uzunluk: b.metin.length, kelime: kelime(govde),
             h2: (govde.match(/<h[2-6]/g) || []).length, gorsel: (govde.match(/<img/g) || []).length };
  });
  process.stdout.write(JSON.stringify({ bolumler, onsoz, uyarilar: sonuc.messages.map((x) => x.message) }));
}).catch((hata) => { process.stderr.write(String(hata)); process.exit(2); });
