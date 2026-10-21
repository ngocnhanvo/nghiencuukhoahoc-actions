// Read-only audit of published WordPress Pages/media URLs for EduResearch.
// Does not fetch student content, authenticate, modify Pages, or alter build.
const base = 'https://api-nghiencuukhoahoc.webnvn.com';
const knownMissing = new Set([
  '255A5708.jpg', '255A5533.jpg', 'h7_01.jpg', 'Banner-Page-PC.jpg',
  'gioithieu.jpg', 'tieu-chuan-iso-2015.png', 'h6_01.jpg',
  'tieu-chuan-QR.png', 'h3_01.jpg', '255A6030.jpg', '255A5787.jpg',
]);
const pages = [];
for (let page = 1; page <= 10; page++) {
  const url = new URL('/wp-json/wp/v2/pages', base);
  url.searchParams.set('status', 'publish');
  url.searchParams.set('page', String(page));
  url.searchParams.set('per_page', '50');
  url.searchParams.set('_fields', 'id,slug,title,acf,content,yoast_head_json');
  const response = await fetch(url, { headers: {Accept:'application/json'}, signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error('Public WP Pages HTTP ' + response.status + ' at page ' + page);
  const rows = await response.json();
  if (!Array.isArray(rows)) throw Error('WordPress Pages response not an array');
  pages.push(...rows);
  const total = Number(response.headers.get('X-WP-TotalPages') || '1');
  if (page >= total) break;
}
const affected = [];
for (const page of pages) {
  const title = String(page.title?.rendered || '').replace(/<[^>]*>/g, '').slice(0,95);
  const key = String(page.acf?.key || '');
  const source = JSON.stringify({content:page.content?.rendered,acf:page.acf,seo:page.yoast_head_json?.og_image});
  const refs = [...new Set(
    (source.match(/\/wp-content\/uploads\/20\d{2}\/\d{2}\/[a-zA-Z0-9_.%+@()~-]+/g)||[])
      .map(x => x.split('/').at(-1))
      .filter(x=>knownMissing.has(x))
  )];
  const sourceLower = source.toLowerCase();
  const markerTerms = ['xuongmunonbaohiem','blue sea','mũ bảo hiểm','mũ nón bảo hiểm','nón bảo hiểm','pse','tieu-chuan-iso-2015','nghiên cứu khoa học','eduresearch'];
  const markerHits = markerTerms.filter(term => sourceLower.includes(term.toLowerCase()));
  const textPreview = String(page.content?.rendered || '')
    .replace(/<[^>]*>/g, ' ').replace(/&[a-z]+;/gi, ' ').replace(/\\s+/g,' ').trim().slice(0,400);
  const row = {
    id:page.id, slug:page.slug, key, title, knownMissingImageNames:refs,
    markerHits, contentPreview: textPreview,
    acfKeys: Object.keys(page.acf || {}).slice(0,35),
    contentChars: String(page.content?.rendered || '').length
  };
  console.log(JSON.stringify(row));
  if (refs.length) affected.push(row);
}
console.log('AUDIT_COUNTS '+JSON.stringify({totalPublishedPages:pages.length,affectedPages:affected.length,affectedIds:affected.map(x=>x.id),knownMissing:knownMissing.size}));
if (!pages.length) throw Error('No published Pages found: audit result is inconclusive');

const menuResp = await fetch(base + '/wp-json/esc-api/v1/menus', {
  headers: { Accept: 'application/json' }, signal: AbortSignal.timeout(15000)
});
if (!menuResp.ok) throw Error('WP header menu HTTP ' + menuResp.status);
const menuPayload = await menuResp.json();
const refs = [];
const visit = (x, path = 'root', depth = 0) => {
  if (depth > 10 || refs.length > 100) return;
  if (Array.isArray(x)) { x.forEach((v, i) => visit(v, path + '/' + i, depth + 1)); return; }
  if (!x || typeof x !== 'object') return;
  const parts = [x.label, x.title, x.slug, x.url, x.href, x.link].map(v=>typeof v==='string'?v:'').filter(Boolean);
  if (parts.length && (parts.some(v => /ve-chung-toi|lien-he|liên hệ|giới thiệu|blue sea|mũ bảo hiểm/i.test(v))
      || ((x.key === 'about' || x.key === 'contact')))) refs.push({path, key:x.key||'', label:parts.slice(0,3), id:x.id||null});
  Object.entries(x).forEach(([k, v])=>{ if (!['label','title','content','description','url','href','link','css'].includes(k)) visit(v, path + '/' + k, depth + 1); });
};
visit(menuPayload);
console.log('MENU_AUDIT ' + JSON.stringify({topLevelKeys:Object.keys(menuPayload||{}),references:refs}));

const frontend = 'https://nghiencuukhoahoc.webnvn.com';
for (const path of ['/ve-chung-toi', '/lien-he']) {
  const res = await fetch(frontend + path + '?nckh_legacy_audit=20261021', {
    headers: { Accept: 'text/html' }, signal: AbortSignal.timeout(15000)
  });
  const text = await res.text();
  const lingering = /blue\s*sea|xuongmunonbaohiem|công ty tnhh đầu tư thương mại blue sea/i.test(text);
  console.log('PUBLIC_RETIRED_ROUTE_CHECK '+JSON.stringify({
    path, status:res.status, contentType:res.headers.get('content-type'),
    hasCopiedBlueSeaBrand:lingering, bodyChars:text.length
  }));
  if (lingering) throw new Error('Legacy Blue Sea content is still publicly served at '+path);
}
