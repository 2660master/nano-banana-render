// Builds SkyFX-preview.html: inlines the mod's real GLSL include files into preview/template.html,
// so the preview always runs exactly the same sky and glint shaders as the mod.
//
//   node preview/build-preview.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const includeDir = join(here, '..', 'src', 'client', 'resources', 'assets', 'skyfx', 'shaders', 'include');
const template = readFileSync(join(here, 'template.html'), 'utf8');

const html = template.replace(/\/\*@include ([\w.]+)\*\//g, (_, file) => {
	const source = readFileSync(join(includeDir, file), 'utf8');
	if (source.includes('</script')) throw new Error(`${file} must not contain </script`);
	return `// ---- ${file} (from the mod) ----\n${source}`;
});

const out = join(here, '..', 'SkyFX-preview.html');
writeFileSync(out, html);
console.log(`wrote ${out} (${(html.length / 1024).toFixed(1)} KiB)`);
