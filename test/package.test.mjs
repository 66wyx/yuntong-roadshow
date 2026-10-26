import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { listFiles, normalizeBase, rebaseText } from '../scripts/prepare.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const site = path.join(root, 'site');
const inventory = JSON.parse(await readFile(path.join(root, 'package-integrity.json'), 'utf8'));
const hash = (data) => createHash('sha256').update(data).digest('hex');
const readJson = async (file) => JSON.parse(await readFile(path.join(site, file), 'utf8'));

test('base validation rejects origins, traversals and ambiguous paths', () => {
  for (const base of ['https://example.com/', '/../', '/x/../y/', '//x/', 'x/', '/x', '/x/?q=1', '/x/#foo']) assert.throws(() => normalizeBase(base));
  assert.equal(normalizeBase('/nested/repo/'), '/nested/repo/');
  assert.equal(normalizeBase('/'), '/');
});

test('rebasing supports HTML, JS, JSON and CSS without rewriting external evidence', () => {
  const input = `<script src="/assets/a.js"></script> const c='/projects/index.json'; const t=\`/projects/a\`; .x{background:url(/assets/a.webp)} {"url":"/projects/a","source":"https://example.org/projects/a"}<link href="/favicon.svg">`;
  const rebased = rebaseText(input, '/yuntong-roadshow/');
  assert.ok(rebased.includes('src="/yuntong-roadshow/assets/a.js"'));
  assert.ok(rebased.includes("c='/yuntong-roadshow/projects/index.json'"));
  assert.ok(rebased.includes('t=`/yuntong-roadshow/projects/a`'));
  assert.ok(rebased.includes('url(/yuntong-roadshow/assets/a.webp)'));
  assert.ok(rebased.includes('"url":"/yuntong-roadshow/projects/a"'));
  assert.ok(rebased.includes('https://example.org/projects/a'));
  assert.ok(rebased.includes('href="/yuntong-roadshow/favicon.svg"'));
  assert.equal(rebaseText(rebased, '/yuntong-roadshow/'), rebased);
  assert.equal(rebaseText(input, '/'), input);
});

test('Vite dynamic preload URLs use the project prefix instead of the account root', () => {
  const vite = 'const __vite__mapDeps=(i)=>i;var Fl=function(e){return`/`+e};';
  assert.equal(rebaseText(vite, '/yuntong-roadshow/'), 'const __vite__mapDeps=(i)=>i;var Fl=function(e){return`/yuntong-roadshow/`+e};');
  assert.equal(rebaseText(rebaseText(vite, '/yuntong-roadshow/'), '/yuntong-roadshow/'), rebaseText(vite, '/yuntong-roadshow/'));
  const shared = 'const __vite__mapDeps=(i)=>i;import{t as e}from"./index-abc.js";';
  assert.equal(rebaseText(shared, '/yuntong-roadshow/'), shared);
  assert.throws(() => rebaseText('const __vite__mapDeps=(i)=>i;', '/yuntong-roadshow/'), /Unrecognized Vite/);
  assert.throws(() => rebaseText(vite + 'var Other=function(t){return`/`+t};', '/yuntong-roadshow/'), /Unrecognized Vite/);
});

test('the published runtime has exactly the reviewed files and SHA-256 values', async () => {
  const files = (await listFiles(site)).map((file) => path.relative(site, file).split(path.sep).join('/')).sort();
  assert.deepEqual(files, [...inventory.runtimeFiles.map((entry) => entry.file), ...inventory.extraFiles].sort());
  assert.equal(files.length, 29);
  let bytes = 0;
  for (const record of inventory.runtimeFiles) {
    assert.ok(!record.file.startsWith('/') && !record.file.split('/').includes('..'));
    const data = await readFile(path.join(site, record.file));
    assert.equal(data.length, record.bytes, record.file);
    assert.equal(hash(data), record.publishedSha256, record.file);
    if (record.binary) assert.equal(record.publishedSha256, record.sourceSha256, `Binary changed: ${record.file}`);
    assert.ok(data.length < 25 * 1024 * 1024, record.file);
    bytes += data.length;
  }
  assert.ok(bytes < 50 * 1024 * 1024);
  assert.equal((await readFile(path.join(site, '.nojekyll'))).length, 0);
});

test('root URLs cannot escape the Pages repository prefix', async () => {
  assert.equal(inventory.base, '/yuntong-roadshow/');
  for (const record of inventory.runtimeFiles.filter((entry) => !entry.binary)) {
    const text = await readFile(path.join(site, record.file), 'utf8');
    assert.ok(!/(["'`(])\/(?:projects|assets)\//.test(text), record.file);
    assert.ok(!/(["'`(])\/favicon\.svg/.test(text), record.file);
    assert.ok(!/function\([A-Za-z_$][\w$]*\)\{return(["'`])\/\1\+/.test(text), record.file);
    assert.ok(!/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(text), record.file);
    assert.ok(!/(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}/.test(text), record.file);
    assert.ok(!/[A-Z]:[\\/](?:Users|claude code)[\\/]/i.test(text), record.file);
  }
  const html = await readFile(path.join(site, 'index.html'), 'utf8');
  for (const [, url] of html.matchAll(/(?:src|href)="(\/[^"?#]+)"/g)) {
    assert.ok(url.startsWith(inventory.base));
    assert.ok((await readFile(path.join(site, url.slice(inventory.base.length)))).length > 0);
  }
});

test('runtime JSON URLs resolve to actual files and evidence remains a concept', async () => {
  const index = await readJson('projects/index.json');
  const manifest = await readJson('projects/ams-asm/manifest.json');
  async function walk(value) {
    if (typeof value === 'string' && value.startsWith(inventory.base)) {
      const filename = value.slice(inventory.base.length).split(/[?#]/)[0];
      assert.ok(!filename.split('/').includes('..'));
      assert.ok((await readFile(path.join(site, filename))).length > 0, value);
    } else if (Array.isArray(value)) for (const child of value) await walk(child);
    else if (value && typeof value === 'object') for (const child of Object.values(value)) await walk(child);
  }
  await walk(index);
  await walk(manifest);
  assert.equal(index.projects.length, 1);
  assert.equal(index.projects[0].placeholderCount, 60);
  assert.equal(index.projects[0].provisionalCount, 23);
  assert.equal(index.projects[0].demonstration.label, '概念演示');
  assert.equal(manifest.chapters.length, 9);
  assert.equal(manifest.clusters.length, 15);
  assert.equal(manifest.brand.themeId, 'monochrome-product');
  assert.equal(manifest.assets.source, undefined);
  assert.equal(manifest.assets.campusSource, undefined);
  assert.equal(inventory.evidence.formalRelease, false);
  const note = manifest.chapters.find((chapter) => chapter.id === 'ask').blocks.find((block) => block.id === 'ask-note');
  assert.equal(note.status, 'placeholder');
  assert.equal(note.required, true);
  assert.equal(note.gap, 'G-03');
  assert.match(note.content['zh-CN'], /不代表已批准预算/);
});

test('complete product and original art hashes are pinned, not recoloured or simplified', async () => {
  const expected = {
    'projects/ams-asm/assets/model/blender-product.glb': '74d6609e25e087cc1555a3534ce2fabd381e416f1d5671064c17247c0ec17e79',
    'projects/ams-asm/assets/render/hero-desert-wide.webp': '7b2c23d7a7a97e91145e2fe78d5f357e16de5efdac650c15ba8d4d6359421325',
    'projects/ams-asm/assets/render/hero-studio-transparent.webp': '1bd08ca057138544538ee60643b35396f6d6d174fc741858b798d99fe8cf0459',
    'projects/ams-asm/assets/render/product-structure.webp': 'f9ff874dc69f2464f6e66e3c1c78fee8b96d9ec749582794b6d0db5ce1609a79'
  };
  for (const [file, digest] of Object.entries(expected)) assert.equal(hash(await readFile(path.join(site, file))), digest, file);
  const campus = await readFile(path.join(site, 'projects/ams-asm/assets/model/sztu-campus.glb'));
  assert.equal(campus.length, 24545000);
  assert.equal(campus.toString('ascii', 0, 4), 'glTF');
  for (const record of inventory.runtimeFiles) assert.ok(!/\.(?:step|stp|spline|blend|map|py|yaml|toml|ps1|pem|key)$/i.test(record.file), record.file);
});
