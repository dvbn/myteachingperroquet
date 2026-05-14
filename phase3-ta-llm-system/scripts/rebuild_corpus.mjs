#!/usr/bin/env node
// ============================================================
// Corpus Builder — Lecture chunks + Exercise hints → Tutor corpus
// ============================================================
//
// Reads:
//   - lecture_chunks.json        (from chunk_lectures.mjs — course material)
//   - exercise_tutor_chunks.json (from transform_exercises.mjs — hints)
//
// Produces:
//   - tutor_corpus.json  (lecture chunks with "tutor" in mode_allowed + hint chunks)
//   - Calculated IDF and avg_dl
//
// Note: Quiz mode uses exercise_index.json directly (deterministic state
// machine), so no quiz corpus is needed.
//
// Usage:
//   node scripts/rebuild_corpus.mjs [--data-dir <path>] [--out-dir <path>]
//
// Defaults (resolve from project root via process.cwd()):
//   --data-dir  ./data
//   --out-dir   ./data
// ============================================================

import fs from "fs";
import path from "path";

// ── CLI args ─────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(name, fallback) {
  const idx = args.indexOf(name);
  return idx >= 0 && args[idx + 1] ? args[idx + 1] : fallback;
}

const DATA_DIR = path.resolve(
  process.cwd(),
  getArg("--data-dir", "./data")
);
const OUT_DIR = path.resolve(
  process.cwd(),
  getArg("--out-dir", "./data")
);
const COURSE_ID = getArg("--course-id", "default");
const TERM = getArg("--term", "default");

// ── IDF calculation ──────────────────────────────────────────
function buildIDF(chunks) {
  const N = chunks.length;
  const df = {};

  for (const chunk of chunks) {
    const uniqueTerms = new Set(chunk.tokens || []);
    for (const term of uniqueTerms) {
      df[term] = (df[term] || 0) + 1;
    }
  }

  // BM25 IDF: log((N - df + 0.5) / (df + 0.5) + 1)
  const idf = {};
  for (const [term, count] of Object.entries(df)) {
    idf[term] = Math.log((N - count + 0.5) / (count + 0.5) + 1);
  }

  return idf;
}

// ── Average document length ──────────────────────────────────
function computeAvgDl(chunks) {
  if (chunks.length === 0) return 0;
  const totalTokens = chunks.reduce((sum, c) => sum + (c.tokens?.length || 0), 0);
  return totalTokens / chunks.length;
}

// ── Load JSON ────────────────────────────────────────────────
function loadJSON(filepath) {
  if (!fs.existsSync(filepath)) {
    console.error(`ERROR: File not found: ${filepath}`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(filepath, "utf-8"));
}

// ── Main ─────────────────────────────────────────────────────
function main() {
  console.log(`Corpus Builder`);
  console.log(`  Data dir : ${DATA_DIR}`);
  console.log(`  Out dir  : ${OUT_DIR}`);
  console.log(`  Course   : ${COURSE_ID}`);
  console.log();

  // Load chunk sources
  const lectureChunks = loadJSON(path.join(DATA_DIR, "lecture_chunks.json"));
  const exerciseTutorChunks = loadJSON(path.join(DATA_DIR, "exercise_tutor_chunks.json"));

  console.log(`Lecture chunks:        ${lectureChunks.length}`);
  console.log(`Exercise tutor hints:  ${exerciseTutorChunks.length}`);

  // Keep only lecture chunks allowed for tutor mode
  const tutorLectures = lectureChunks.filter(
    (c) => c.meta?.mode_allowed?.includes("tutor")
  );

  console.log(`\nLecture chunks for tutor: ${tutorLectures.length}`);

  // Build tutor corpus: lecture (tutor-allowed) + hint chunks
  const tutorChunks = [...tutorLectures, ...exerciseTutorChunks];

  // Check for ID uniqueness
  const tutorIds = new Set();
  let tutorDupes = 0;
  for (const c of tutorChunks) {
    if (tutorIds.has(c.id)) tutorDupes++;
    tutorIds.add(c.id);
  }
  if (tutorDupes > 0) console.warn(`WARNING: ${tutorDupes} duplicate IDs in tutor corpus`);

  console.log(`\nTutor corpus: ${tutorChunks.length} chunks (${tutorLectures.length} lecture + ${exerciseTutorChunks.length} hints)`);

  // Build IDF and avg_dl
  console.log(`\nBuilding IDF...`);
  const tutorIDF = buildIDF(tutorChunks);
  const tutorAvgDl = computeAvgDl(tutorChunks);

  console.log(`Tutor: ${Object.keys(tutorIDF).length} unique terms, avg_dl=${tutorAvgDl.toFixed(2)}`);

  // Build output corpus
  const tutorCorpus = {
    metadata: {
      course_id: COURSE_ID,
      term: TERM,
      built_at: new Date().toISOString(),
      num_chunks: tutorChunks.length,
      lecture_chunks: tutorLectures.length,
      exercise_hint_chunks: exerciseTutorChunks.length,
    },
    chunks: tutorChunks,
    idf: tutorIDF,
    avg_dl: tutorAvgDl,
  };

  // Write output
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const tutorOutPath = path.join(OUT_DIR, "tutor_corpus.json");
  fs.writeFileSync(tutorOutPath, JSON.stringify(tutorCorpus));

  console.log(`\nWritten: ${tutorOutPath} (${(fs.statSync(tutorOutPath).size / 1024 / 1024).toFixed(1)} MB)`);

  // Summary
  console.log(`\n── Summary ──────────────────────────────────────`);
  console.log(`           | Lectures | Hints | Total`);
  console.log(`  Tutor    | ${String(tutorLectures.length).padStart(8)} | ${String(exerciseTutorChunks.length).padStart(5)} | ${String(tutorChunks.length).padStart(5)}`);

  // Chunk type breakdown
  const typeBreakdown = {};
  for (const c of tutorChunks) {
    const t = c.meta?.chunk_type || c.meta?.source_type || "unknown";
    typeBreakdown[t] = (typeBreakdown[t] || 0) + 1;
  }
  console.log(`\nChunk types: ${JSON.stringify(typeBreakdown)}`);
}

main();
