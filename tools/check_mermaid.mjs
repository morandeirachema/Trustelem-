// Parse every Mermaid source in tools/diagrams with the Mermaid library.
// Usage: npm install --no-save mermaid@11 jsdom@24 && node tools/check_mermaid.mjs
import { JSDOM } from "jsdom";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const dir = path.join(here, "diagrams");
const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const mermaid = (await import("mermaid")).default;
mermaid.initialize({ startOnLoad: false });

let bad = 0;
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".mmd")).sort()) {
  const src = fs.readFileSync(path.join(dir, f), "utf8");
  try {
    await mermaid.parse(src);
    console.log("OK   " + f);
  } catch (e) {
    bad++;
    console.log("FAIL " + f + ": " + String(e.message || e).split("\n")[0]);
  }
}
console.log(`${bad} failing diagram(s)`);
process.exit(bad ? 1 : 0);
