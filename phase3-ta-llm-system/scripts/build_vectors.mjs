#!/usr/bin/env node
// ============================================================
// Vector Embedding Builder
// ============================================================
//
// Reads a corpus JSON file and produces a vectors JSON file
// using OpenAI's text-embedding-3-small model.
//
// Usage:
//   node scripts/build_vectors.mjs --corpus <path> [--output <path>] [--dry-run]
//
// Options:
//   --corpus      Path to corpus JSON (e.g. tutor_corpus.json)
//   --output      Output path (default: replaces _corpus with _vectors in filename)
//   --batch-size  Texts per API call (default: 500, max: 2048)
//   --model       Embedding model (default: text-embedding-3-small)
//   --dry-run     Show cost estimate without calling API
//   --yes         Skip cost confirmation prompt
//
// Requires:
//   OPENAI_API_KEY environment variable
//
// Output format (matches V1 build_vectors.py):
//   {
//     "meta": { "model", "dimensions", "chunk_count", "built_at" },
//     "vectors": [ [0.123, -0.456, ...], ... ]  // one 1536-dim vector per chunk
//   }
// ============================================================

import fs from "fs";
import path from "path";
import readline from "readline";

// Load .env.local from the repo root so `npm run vectors` works without an
// extra `export OPENAI_API_KEY=...` step. Existing process.env wins (so CI /
// shell-set vars override the file). Minimal parser, no dependency.
function loadEnvLocal() {
  const candidates = [
    path.resolve(process.cwd(), ".env.local"),
    path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", ".env.local"),
  ];
  for (const file of candidates) {
    if (!fs.existsSync(file)) continue;
    const text = fs.readFileSync(file, "utf-8");
    for (const raw of text.split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      const eq = line.indexOf("=");
      if (eq < 0) continue;
      const key = line.slice(0, eq).trim();
      let val = line.slice(eq + 1).trim();
      // Skip if the key already has a non-empty value in the environment.
      // Empty-string env values (e.g. exported but unset) should NOT win — the
      // file value is more useful than an explicit empty.
      if (!key || (key in process.env && process.env[key] !== "")) continue;
      // Strip surrounding quotes if present
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      process.env[key] = val;
    }
    return file;
  }
  return null;
}
loadEnvLocal();

// ── CLI args ─────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(name, fallback) {
  const idx = args.indexOf(name);
  return idx >= 0 && args[idx + 1] ? args[idx + 1] : fallback;
}
function hasFlag(name) {
  return args.includes(name);
}

const CORPUS_PATH = getArg("--corpus", null);
const MODEL = getArg("--model", "text-embedding-3-small");
const BATCH_SIZE = Math.min(2048, parseInt(getArg("--batch-size", "500")));
const DRY_RUN = hasFlag("--dry-run");
const SKIP_CONFIRM = hasFlag("--yes");
const API_KEY = getArg("--api-key", process.env.OPENAI_API_KEY || "");

if (!CORPUS_PATH) {
  console.error("Usage: node scripts/build_vectors.mjs --corpus <path> [--output <path>] [--dry-run]");
  process.exit(1);
}

if (!API_KEY && !DRY_RUN) {
  console.error("ERROR: OPENAI_API_KEY not set. Add it to .env.local, pass --api-key, or export it in your shell.");
  process.exit(1);
}

// Default output: replace _corpus with _vectors in filename
const OUTPUT_PATH = getArg("--output",
  CORPUS_PATH.replace(/_corpus\.json$/, "_vectors.json")
);

// ── Cost estimation ──────────────────────────────────────────
// text-embedding-3-small: $0.02 per 1M tokens
const COST_PER_1M_TOKENS = 0.02;

function estimateTokens(texts) {
  // Conservative estimate: ~4 chars per token
  const totalChars = texts.reduce((sum, t) => sum + t.length, 0);
  return Math.ceil(totalChars / 4);
}

// ── Batch embedding with retry ───────────────────────────────
async function embedBatch(texts, attempt = 0, maxRetries = 5) {
  try {
    const res = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: MODEL, input: texts }),
    });

    if (res.status === 429) {
      // Rate limited
      if (attempt < maxRetries) {
        const wait = Math.pow(2, attempt) * 1000;
        console.warn(`  Rate limited. Retrying in ${wait / 1000}s... (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(r => setTimeout(r, wait));
        return embedBatch(texts, attempt + 1, maxRetries);
      }
      throw new Error(`Rate limited after ${maxRetries} retries`);
    }

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`OpenAI API error ${res.status}: ${body.slice(0, 200)}`);
    }

    const data = await res.json();
    // Sort by index to ensure correct ordering
    const sorted = data.data.sort((a, b) => a.index - b.index);
    return sorted.map(item => item.embedding);
  } catch (err) {
    if (attempt < maxRetries && err.message?.includes("429")) {
      const wait = Math.pow(2, attempt) * 1000;
      console.warn(`  Error (retrying in ${wait / 1000}s): ${err.message}`);
      await new Promise(r => setTimeout(r, wait));
      return embedBatch(texts, attempt + 1, maxRetries);
    }
    throw err;
  }
}

// ── Confirmation prompt ──────────────────────────────────────
function askConfirm(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.toLowerCase().startsWith("y"));
    });
  });
}

// ── Main ─────────────────────────────────────────────────────
async function main() {
  console.log("Vector Embedding Builder");
  console.log(`  Corpus : ${CORPUS_PATH}`);
  console.log(`  Output : ${OUTPUT_PATH}`);
  console.log(`  Model  : ${MODEL}`);
  console.log(`  Batch  : ${BATCH_SIZE}`);
  console.log();

  // Load corpus
  if (!fs.existsSync(CORPUS_PATH)) {
    console.error(`ERROR: Corpus not found: ${CORPUS_PATH}`);
    process.exit(1);
  }

  const corpus = JSON.parse(fs.readFileSync(CORPUS_PATH, "utf-8"));
  const chunks = corpus.chunks;
  if (!chunks || chunks.length === 0) {
    console.error("ERROR: Corpus has no chunks");
    process.exit(1);
  }

  // text-embedding-3-small has an 8192-token context limit.
  // Truncate oversized texts (~4 chars/token → ~30000 char safe limit).
  const MAX_CHARS = 30000;
  let truncatedCount = 0;
  const texts = chunks.map(c => {
    let t = c.text || "";
    if (t.length > MAX_CHARS) {
      t = t.slice(0, MAX_CHARS);
      truncatedCount++;
    }
    return t;
  });
  if (truncatedCount > 0) {
    console.warn(`WARNING: ${truncatedCount} chunks truncated to ${MAX_CHARS} chars (8192 token limit)`);
  }
  const emptyCount = texts.filter(t => t.trim().length === 0).length;
  if (emptyCount > 0) {
    console.warn(`WARNING: ${emptyCount} chunks have empty text`);
  }

  console.log(`Chunks to embed: ${texts.length}`);

  // Cost estimate
  const estTokens = estimateTokens(texts);
  const estCost = (estTokens / 1_000_000) * COST_PER_1M_TOKENS;
  const numBatches = Math.ceil(texts.length / BATCH_SIZE);

  console.log(`Estimated tokens: ~${estTokens.toLocaleString()}`);
  console.log(`Estimated cost:   ~$${estCost.toFixed(4)}`);
  console.log(`API calls:        ${numBatches} batches of ${BATCH_SIZE}`);
  console.log();

  if (DRY_RUN) {
    console.log("[DRY RUN] No API calls made.");
    process.exit(0);
  }

  if (!SKIP_CONFIRM) {
    const confirmed = await askConfirm(`Proceed with embedding ${texts.length} chunks (~$${estCost.toFixed(4)})? (y/n) `);
    if (!confirmed) {
      console.log("Aborted.");
      process.exit(0);
    }
  }

  // Embed in batches
  const allVectors = [];
  let totalTokensUsed = 0;
  const startTime = Date.now();

  for (let i = 0; i < texts.length; i += BATCH_SIZE) {
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const batch = texts.slice(i, i + BATCH_SIZE);

    process.stdout.write(`  Batch ${batchNum}/${numBatches} (${batch.length} texts)...`);

    const vectors = await embedBatch(batch);
    allVectors.push(...vectors);

    process.stdout.write(` done (${allVectors.length}/${texts.length})\n`);
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

  // Validate
  if (allVectors.length !== texts.length) {
    console.error(`ERROR: Expected ${texts.length} vectors, got ${allVectors.length}`);
    process.exit(1);
  }

  const dimensions = allVectors[0]?.length || 0;
  console.log();
  console.log(`Embedding complete in ${elapsed}s`);
  console.log(`  Vectors: ${allVectors.length}`);
  console.log(`  Dimensions: ${dimensions}`);

  // Write output
  const output = {
    meta: {
      model: MODEL,
      dimensions,
      chunk_count: allVectors.length,
      built_at: new Date().toISOString(),
    },
    vectors: allVectors,
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output));
  const sizeMB = (fs.statSync(OUTPUT_PATH).size / 1024 / 1024).toFixed(1);
  console.log(`  Written: ${OUTPUT_PATH} (${sizeMB} MB)`);
}

main().catch(err => {
  console.error("FATAL:", err.message);
  process.exit(1);
});
