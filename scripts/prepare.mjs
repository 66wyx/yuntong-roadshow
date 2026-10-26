import { copyFile, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const defaultBase = '/yuntong-roadshow/';
const root = fileURLToPath(new URL('../', import.meta.url));
const textExtensions = new Set(['.html', '.js', '.css', '.json', '.svg', '.txt']);
const hash = (data) => createHash('sha256').update(data).digest('hex');

export function normalizeBase(value = defaultBase) {
  if (value === '/') return '/';
  if (!/^\/[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*\/$/.test(value)) {
    throw new Error('Base must be / or a slash-delimited URL path with no traversal, query or origin');
  }
  return value;
}

export function rebaseText(text, base) {
  const normalized = normalizeBase(base);
  if (normalized === '/') return text;
  let transformed = text;
  if (text.includes('const __vite__mapDeps=')) {
    // Vite also synthesizes preload URLs by prefixing relative dependency names
    // with `/`; these are not root URL literals and must be handled separately.
    // Fail closed on an unrecognized compiler helper instead of hiding 404s.
    const preloadPrefix = /function\(([A-Za-z_$][\w$]*)\)\{return(["'`])\/\2\+\1\}/g;
    const matches = [...text.matchAll(preloadPrefix)];
    const importsSharedHelper = /import\{[^}]+\}from["'`]\.\/index-[^"'`]+\.js["'`]/.test(text);
    const alreadyNormalized = ["'", '"', '`'].some((quote) => text.includes(`return${quote}${normalized}${quote}+`));
    if (matches.length > 1 || (!matches.length && !importsSharedHelper && !alreadyNormalized)) throw new Error('Unrecognized Vite preload base helper; review the new compiler output before publishing');
    transformed = text.replace(preloadPrefix, (_all, argument, quote) => `function(${argument}){return${quote}${normalized}${quote}+${argument}}`);
  }
  // Limit substitutions to actual root URL literal starts. External links,
  // evidence prose, relative chunk imports, geometry and algorithms are unchanged.
  return transformed
    .replace(/(["'`(])\/(projects|assets)\//g, (_all, delimiter, directory) => `${delimiter}${normalized}${directory}/`)
    .replace(/(["'`(])\/favicon\.svg(?=["'`)\s?#])/g, (_all, delimiter) => `${delimiter}${normalized}favicon.svg`);
}

export async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const result = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name, 'en'))) {
    const full = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Symlink not permitted: ${entry.name}`);
    if (entry.isDirectory()) result.push(...await listFiles(full));
    else if (entry.isFile()) result.push(full);
    else throw new Error(`Unsupported file: ${entry.name}`);
  }
  return result;
}

export async function prepare(source, base = defaultBase) {
  const normalized = normalizeBase(base);
  const sourceRoot = path.resolve(source);
  const output = path.join(root, 'site');
  if (sourceRoot === output || sourceRoot.startsWith(output + path.sep)) throw new Error('Source must be outside site output');
  const sourceFiles = await listFiles(sourceRoot);
  const manifestSource = await readFile(path.join(sourceRoot, 'projects/ams-asm/manifest.json'), 'utf8');
  const manifest = JSON.parse(manifestSource);
  if (manifest.chapters.length !== 9 || manifest.assets.source || manifest.assets.campusSource) throw new Error('Not the audited public runtime');
  const inventory = [];
  await mkdir(output, { recursive: true });
  const allowedSourcePaths = new Set(sourceFiles.map((file) => path.relative(sourceRoot, file).split(path.sep).join('/')));
  // Do not recursively delete or silently retain a stale file in an existing site.
  for (const old of await listFiles(output)) {
    const relative = path.relative(output, old).split(path.sep).join('/');
    if (!allowedSourcePaths.has(relative) && relative !== '.nojekyll') throw new Error(`Stale output file; review before replacement: ${relative}`);
  }
  for (const file of sourceFiles) {
    const relative = path.relative(sourceRoot, file).split(path.sep).join('/');
    if (/(?:^|\/)(?:\.git|\.openai|private|node_modules)(?:\/|$)/.test(relative) || /\.(?:stp|step|blend|spline|map|pem|key|py|ps1|yaml)$/i.test(relative)) throw new Error(`Source-only file rejected: ${relative}`);
    const target = path.join(output, relative);
    await mkdir(path.dirname(target), { recursive: true });
    const original = await readFile(file);
    const isText = textExtensions.has(path.extname(file));
    let published;
    try { published = isText ? Buffer.from(rebaseText(original.toString('utf8'), normalized)) : original; }
    catch (error) { throw new Error(`${relative}: ${error.message}`, { cause: error }); }
    if (isText) await writeFile(target, published);
    else await copyFile(file, target);
    inventory.push({ file: relative, bytes: published.length, sourceSha256: hash(original), publishedSha256: hash(published), binary: !isText });
  }
  await writeFile(path.join(output, '.nojekyll'), '');
  const metadata = {
    schemaVersion: 1,
    base: normalized,
    mode: 'public-concept',
    sourceSnapshot: 'd075586b0440ce3f21430ff6202e9a1259a7bde4',
    publicSourceSnapshot: 'a56cf412c2fec606f229a17538e6c779e3323c03',
    evidence: { placeholder: 60, provisional: 23, formalRelease: false },
    runtimeFiles: inventory,
    extraFiles: ['.nojekyll'],
  };
  await writeFile(path.join(root, 'package-integrity.json'), JSON.stringify(metadata, null, 2) + '\n');
  return { base: normalized, files: inventory.length + 1, bytes: inventory.reduce((sum, item) => sum + item.bytes, 0) };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const options = Object.fromEntries(process.argv.slice(2).map((value) => {
    const match = /^--(source|base)=(.+)$/.exec(value);
    if (!match) throw new Error('Usage: node scripts/prepare.mjs --source=<audited-dist> [--base=/repo-name/]');
    return [match[1], match[2]];
  }));
  if (!options.source) throw new Error('Explicit --source is required; never upload the full engineering repository');
  console.log(JSON.stringify(await prepare(options.source, options.base)));
}
