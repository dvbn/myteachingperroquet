#!/usr/bin/env node
// ============================================================
// Exercise Bank → Corpus Chunk Transformer
// ============================================================
//
// Reads exercise bank JSON files and produces:
//   - Tutor hint chunks: one per hint level (NO_SOLVE) — for BM25 retrieval
//   - Exercise index: full exercise records for quiz state machine lookup
//
// Usage:
//   node scripts/transform_exercises.mjs [--bank-dir <path>] [--out-dir <path>]
//
// Defaults (resolve from project root via process.cwd()):
//   --bank-dir  ./sources/exercises
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

const BANK_DIR = path.resolve(
  process.cwd(),
  getArg("--bank-dir", "./sources/exercises")
);
const OUT_DIR = path.resolve(
  process.cwd(),
  getArg("--out-dir", "./data")
);
const COURSE_ID = getArg("--course-id", "default");
const TERM = getArg("--term", "default");

// ── Stopwords (same as ta-chat.mjs) ─────────────────────────
const STOPWORDS = new Set([
  "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
  "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
  "between", "both", "but", "by", "can", "cannot", "could", "did", "do", "does",
  "doing", "down", "during", "each", "few", "for", "from", "further", "had",
  "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
  "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
  "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
  "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
  "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
  "the", "their", "theirs", "them", "themselves", "then", "there", "these",
  "they", "this", "those", "through", "to", "too", "under", "until", "up",
  "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
  "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
]);

const FRENCH_STOPWORDS = new Set([
  "le", "la", "les", "de", "du", "des", "un", "une", "et", "est", "en", "que",
  "qui", "dans", "pour", "pas", "sur", "avec", "ce", "cette", "ces", "je", "tu",
  "il", "elle", "nous", "vous", "ils", "elles", "mon", "ton", "son", "notre",
  "votre", "leur", "me", "te", "se", "ne", "y", "plus", "aussi", "mais", "ou",
  "donc", "car", "ni", "bien", "au", "aux", "par", "sans", "chez", "entre",
  "vers", "pendant", "avant", "apres", "depuis", "sous", "autre", "autres",
  "meme", "ses", "sa", "leurs", "dont", "ete", "fait", "peut", "sont", "ont",
  "cela", "sera", "etait", "avait", "ai", "as", "suis", "sommes",
]);

// ── Tokenization (same logic as ta-chat.mjs) ────────────────
function tokenize(text) {
  return text
    .toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")  // strip diacritics: é→e, è→e, etc.
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 0 && !STOPWORDS.has(t) && !FRENCH_STOPWORDS.has(t));
}

function buildTF(tokens) {
  const tf = {};
  for (const t of tokens) {
    tf[t] = (tf[t] || 0) + 1;
  }
  return tf;
}

const sessionNum = s => parseInt(s.match(/\d+/)?.[0] ?? "0", 10);

// ── Discover exercise files ──────────────────────────────────
function discoverExerciseFiles(bankDir) {
  const files = [];
  const sessions = fs.readdirSync(bankDir).filter((d) => {
    const full = path.join(bankDir, d);
    return fs.statSync(full).isDirectory() && /^S\d+/.test(d);
  });

  // Only load exercises_*.json and stata_*.json — skip batch files,
  // schema.json, and other non-exercise JSON to prevent duplicates.
  const EXERCISE_FILE_RE = /^(exercises|stata)_[A-Z]{2}\.json$/;

  for (const session of sessions.sort((a, b) => sessionNum(a) - sessionNum(b))) {
    const dir = path.join(bankDir, session);
    const dirEntries = fs.readdirSync(dir).filter(f => EXERCISE_FILE_RE.test(f));
    for (const name of dirEntries.sort()) {
      const fp = path.join(dir, name);
      files.push({ path: fp, session, filename: name });
    }
  }
  return files;
}

// ── Build tutor hint chunks ──────────────────────────────────
function buildHintChunks(exercise, sourceFile) {
  const id = exercise.id;
  const lang = exercise.language;
  const hints = exercise.hints || [];
  const session = exercise.session;
  const qType = exercise.question_type;
  const diff = exercise.difficulty;

  return hints.map((hintText, idx) => {
    const level = idx + 1;
    const total = hints.length;

    const headingLabel = lang === "fr"
      ? `Indice pour ${id} (niveau ${level}/${total})`
      : `Hint for ${id} (level ${level}/${total})`;

    const headingText = lang === "fr"
      ? `Indice pour ${id}`
      : `Hint for ${id}`;

    const textTokens = tokenize(hintText);
    const headingTokens = tokenize(headingLabel);
    const tokens = [...textTokens, ...headingTokens];
    const tf = buildTF(tokens);

    return {
      id: `${id}_hint_${level}`,
      heading: headingLabel,
      heading_text: headingText,
      text: hintText,
      tokens,
      tf,
      source_file: sourceFile,
      meta: {
        source_id: id,
        source_type: "exercise_hint",
        title: `${id}_hint_${level}`,
        policy: "NO_SOLVE",
        mode_allowed: ["tutor"],
        topic_tags: exercise.topics || [],
        course_id: COURSE_ID,
        term: TERM,
        heading: headingLabel,
        chunk_type: "hint",
        difficulty: diff,
        question_type: qType,
        session,
        language: lang,
        hint_level: level,
      },
    };
  });
}

function writeEmptyOutputs() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(path.join(OUT_DIR, "exercise_tutor_chunks.json"), "[]");
  fs.writeFileSync(
    path.join(OUT_DIR, "exercise_index.json"),
    JSON.stringify(
      {
        exercises: {},
        sessions: {},
        metadata: {
          course_id: COURSE_ID,
          term: TERM,
          built_at: new Date().toISOString(),
          total_exercises: 0,
          sessions: [],
        },
      },
      null,
      2
    )
  );
}

// ── Main ─────────────────────────────────────────────────────
function main() {
  console.log(`Exercise Bank → Corpus Transformer`);
  console.log(`  Bank dir : ${BANK_DIR}`);
  console.log(`  Out dir  : ${OUT_DIR}`);
  console.log(`  Course   : ${COURSE_ID}`);
  console.log(`  Term     : ${TERM}`);
  console.log();

  fs.mkdirSync(OUT_DIR, { recursive: true });

  // Exercises are optional. If sources/exercises/ doesn't exist or contains
  // no exercise files, write empty index + chunks and exit cleanly so the
  // rest of the pipeline can run (chat-only deployments don't need a quiz).
  if (!fs.existsSync(BANK_DIR)) {
    console.log(`(no exercises directory at ${BANK_DIR} — writing empty index)`);
    writeEmptyOutputs();
    return;
  }

  const files = discoverExerciseFiles(BANK_DIR);
  if (files.length === 0) {
    console.log(`(no exercise files found in ${BANK_DIR} — writing empty index)`);
    writeEmptyOutputs();
    return;
  }
  console.log(`Found ${files.length} exercise files across sessions.\n`);

  const tutorHintChunks = [];
  const exerciseIndex = {};   // id → full exercise record
  const sessionIndex = {};    // session → [exercise ids]
  let totalExercises = 0;

  for (const { path: fp, session, filename } of files) {
    let parsed;
    try {
      parsed = JSON.parse(fs.readFileSync(fp, "utf-8"));
    } catch (err) {
      console.warn(`  SKIP ${fp}: invalid JSON (${err.message})`);
      continue;
    }
    if (!Array.isArray(parsed)) {
      console.warn(`  SKIP ${fp}: not a JSON array (got ${typeof parsed})`);
      continue;
    }
    const exercises = parsed;
    const relPath = `exercise_bank/${session}/${filename}`;

    for (const ex of exercises) {
      totalExercises++;

      // Tutor: one chunk per hint
      tutorHintChunks.push(...buildHintChunks(ex, relPath));

      const softwareCode = ex.software_code ?? ex.stata_code ?? null;
      if (
        ex.software_code &&
        ex.stata_code &&
        ex.software_code !== ex.stata_code
      ) {
        console.warn(`  WARN ${ex.id}: software_code and stata_code differ; using software_code`);
      }

      // Exercise index: full exercise data for random selection + ID lookup
      exerciseIndex[ex.id] = {
        id: ex.id,
        twin_id: ex.twin_id,
        session: ex.session,
        language: ex.language,
        question_type: ex.question_type,
        difficulty: ex.difficulty,
        topics: ex.topics || [],
        lecture_ref: ex.lecture_ref || null,
        question_text: ex.question_text,
        data_table: ex.data_table || null,
        stata_code: softwareCode,
        software_code: softwareCode,
        solution: ex.solution,
        hints: ex.hints || [],
        related_exercises: ex.related_exercises || [],
      };

      if (!sessionIndex[ex.session]) sessionIndex[ex.session] = [];
      sessionIndex[ex.session].push(ex.id);
    }

    console.log(`  ${relPath}: ${exercises.length} exercises`);
  }

  console.log();
  console.log(`Total exercises processed: ${totalExercises}`);
  console.log(`Tutor hint chunks:        ${tutorHintChunks.length}`);
  console.log(`Exercise index entries:    ${Object.keys(exerciseIndex).length}`);

  // Write output
  const tutorOutPath = path.join(OUT_DIR, "exercise_tutor_chunks.json");
  const indexOutPath = path.join(OUT_DIR, "exercise_index.json");

  fs.writeFileSync(tutorOutPath, JSON.stringify(tutorHintChunks, null, 2));
  fs.writeFileSync(indexOutPath, JSON.stringify({
    exercises: exerciseIndex,
    sessions: sessionIndex,
    metadata: {
      course_id: COURSE_ID,
      term: TERM,
      built_at: new Date().toISOString(),
      total_exercises: Object.keys(exerciseIndex).length,
      sessions: Object.keys(sessionIndex).sort((a, b) => sessionNum(a) - sessionNum(b)),
    },
  }, null, 2));

  console.log();
  console.log(`Written: ${tutorOutPath}`);
  console.log(`Written: ${indexOutPath}`);
  for (const [s, ids] of Object.entries(sessionIndex).sort(([a], [b]) => sessionNum(a) - sessionNum(b))) {
    console.log(`  ${s}: ${ids.length} exercises`);
  }

  // Spot-check
  if (tutorHintChunks.length > 0) {
    const sample = tutorHintChunks[0];
    console.log();
    console.log(`── Sample hint chunk ──`);
    console.log(`  id:     ${sample.id}`);
    console.log(`  meta:   hint_level=${sample.meta.hint_level}, session=${sample.meta.session}`);
    console.log(`  text:   ${sample.text.slice(0, 120)}...`);
  }
}

main();
