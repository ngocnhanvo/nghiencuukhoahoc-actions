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
  const row = {id:page.id, slug:page.slug, key, title, knownMissingImageNames:refs};
  console.log(JSON.stringify(row));
  if (refs.length) affected.push(row);
}
console.log('AUDIT_COUNTS '+JSON.stringify({totalPublishedPages:pages.length,affectedPages:affected.length,affectedIds:affected.map(x=>x.id),knownMissing:knownMissing.size}));
if (!pages.length) throw Error('No published Pages found: audit result is inconclusive');
