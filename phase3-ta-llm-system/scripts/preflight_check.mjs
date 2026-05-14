#!/usr/bin/env node
// ============================================================
// Pre-flight Content Validator
// ============================================================
//
// Scans lecture and exercise source directories before the RAG
// pipeline runs. Detects files that are likely NOT lectures
// (exercises, solutions, software tutorials, reference tables)
// using filename and content heuristics.
//
// Course-agnostic: no hardcoded course terms, professor names,
// or domain vocabulary.
//
// Usage:
//   node scripts/preflight_check.mjs [--lectures-dir <path>] [--bank-dir <path>]
//
// Defaults (resolve from project root via process.cwd()):
//   --lectures-dir  ./sources/lectures
//   --bank-dir      ./sources/exercises
//
// Exit codes:
//   0  No FAIL items
//   1  FAIL items found
// ============================================================

import fs from "fs";
import path from "path";

// ── CLI args ─────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(name, fallback) {
  const idx = args.indexOf(name);
  return idx >= 0 && args[idx + 1] ? args[idx + 1] : fallback;
}

const LECTURES_DIR = path.resolve(
  process.cwd(),
  getArg("--lectures-dir", "./sources/lectures")
);
const BANK_DIR = path.resolve(
  process.cwd(),
  getArg("--bank-dir", "./sources/exercises")
);

// ── Filename signals ─────────────────────────────────────────

const FILENAME_FAIL_PATTERNS = [
  {
    keywords: ["solution", "correction", "answer", "corrigé", "corrige"],
    label: "solution",
  },
  {
    keywords: [
      "exercise",
      "exercice",
      "practice",
      "problem",
      "problème",
      "probleme",
      "worksheet",
    ],
    label: "exercise",
  },
];

function checkFilename(filename) {
  const lower = filename.toLowerCase();
  for (const pattern of FILENAME_FAIL_PATTERNS) {
    for (const kw of pattern.keywords) {
      if (lower.includes(kw)) {
        return { fail: true, label: pattern.label, keyword: kw };
      }
    }
  }
  return null;
}

// ── Content signals ──────────────────────────────────────────

function scoreContent(text) {
  let score = 0;
  const reasons = [];
  const lines = text.split("\n");

  // --- Solution markers (+3 each) ---
  if (/^#+.*\bsolutions?\b/im.test(text)) {
    score += 3;
    reasons.push('heading contains "Solution"');
  }
  if (/^#+.*\bcorrections?\b/im.test(text)) {
    score += 3;
    reasons.push('heading contains "Correction"');
  }
  if (
    /^\*{0,2}(Solution|Réponse|Reponse|Answer|Correction)\s*:?\*{0,2}/im.test(
      text
    )
  ) {
    score += 3;
    reasons.push("body line starts with answer label");
  }

  // --- Exercise markers (+3 each) ---
  if (/^#+.*\b(exercises?|exercices?|practice|problems?)\b/im.test(text)) {
    score += 3;
    reasons.push('heading contains "Exercise/Problem"');
  }
  if (/^#+.*\bCase\s*[-–—:]/im.test(text) || /^#+.*\bCas\s*[-–—:]/im.test(text)) {
    score += 3;
    reasons.push("case study heading detected");
  }

  // "Question N" / "Part N)" density
  const questionPatterns = text.match(
    /\b(Question|Part)\s+\d+[.)]/gi
  );
  if (questionPatterns && questionPatterns.length > 3) {
    score += 3;
    reasons.push(`${questionPatterns.length} "Question/Part N" patterns`);
  }

  // --- Software tutorial markers ---
  // Count fenced code blocks
  const codeBlockMarkers = text.match(/^```/gm) || [];
  const codeBlockCount = Math.floor(codeBlockMarkers.length / 2);
  if (codeBlockCount > 10) {
    score += 4;
    reasons.push(`${codeBlockCount} code blocks`);
  } else if (codeBlockCount > 5) {
    score += 2;
    reasons.push(`${codeBlockCount} code blocks`);
  }

  // Software command prompts
  const promptLines = lines.filter(
    (l) =>
      /^\. /.test(l) || // Stata dot-prefix
      /^> (?![>])/.test(l) || // R prompt (not markdown blockquote >>)
      /^>>> /.test(l) || // Python prompt
      /^In \[\d+\]/.test(l) // Jupyter
  );
  if (promptLines.length > 5) {
    score += 2;
    reasons.push(`${promptLines.length} software prompt lines`);
  }

  // Code block line ratio
  let inCodeBlock = false;
  let codeLines = 0;
  const nonEmptyLines = lines.filter((l) => l.trim().length > 0);
  for (const line of lines) {
    if (/^```/.test(line)) {
      inCodeBlock = !inCodeBlock;
      continue;
    }
    if (inCodeBlock && line.trim().length > 0) codeLines++;
  }
  const codeRatio =
    nonEmptyLines.length > 0 ? codeLines / nonEmptyLines.length : 0;
  if (codeRatio > 0.4) {
    score += 3;
    reasons.push(`${Math.round(codeRatio * 100)}% code`);
  }

  // --- Reference table markers (+3 each) ---
  const nonEmptyNonHeading = nonEmptyLines.filter(
    (l) => !l.startsWith("#")
  );
  const pipeLines = nonEmptyNonHeading.filter((l) => l.includes("|"));
  const pipeRatio =
    nonEmptyNonHeading.length > 0
      ? pipeLines.length / nonEmptyNonHeading.length
      : 0;
  if (pipeRatio > 0.5) {
    score += 3;
    reasons.push(
      `${Math.round(pipeRatio * 100)}% table lines`
    );
  }

  // Minimal prose alongside tables
  const nonTableNonHeading = nonEmptyLines.filter(
    (l) => !l.startsWith("#") && !l.includes("|") && !l.startsWith("---")
  );
  if (pipeRatio > 0.5 && nonTableNonHeading.length < 20) {
    score += 3;
    reasons.push("minimal prose (reference table)");
  }

  // --- Lecture positive signals (-2 each) ---
  const lectureHeadingPatterns = [
    /^#+.*\b(Learning\s+objectives?|Objectifs?)\b/im,
    /^#+.*\b(Outline|Plan\s+du\s+cours)\b/im,
    /^#+.*\b(Theorems?|Théorèmes?|Theoremes?)\b/im,
    /^#+.*\b(Definitions?|Définitions?|Definitions?)\b/im,
    /^#+.*\b(Proofs?|Démonstrations?|Demonstrations?)\b/im,
    /^#+.*\b(Lemma|Lemme)\b/im,
    /^#+.*\b(Recall|Rappel)\b/im,
    /^#+.*\b(Summary|Résumé|Resume)\b/im,
  ];
  for (const pat of lectureHeadingPatterns) {
    if (pat.test(text)) {
      score -= 2;
      reasons.push(`lecture signal: ${pat.source.slice(0, 40)}`);
    }
  }

  // Numbered theory sections (### 1. / ### 2.)
  const numberedSections = text.match(/^#{2,3}\s+\d+\.\s/gm);
  if (numberedSections && numberedSections.length >= 3) {
    score -= 2;
    reasons.push(`${numberedSections.length} numbered theory sections`);
  }

  return { score, reasons, codeBlockCount, codeRatio };
}

// ── Lecture file checks ──────────────────────────────────────

function checkLectures(lecturesDir) {
  const results = [];

  if (!fs.existsSync(lecturesDir)) {
    console.log(`  (directory not found: ${lecturesDir})`);
    return results;
  }

  const sessionDirs = fs
    .readdirSync(lecturesDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^S\d+/i.test(d.name))
    .sort((a, b) => {
      const na = parseInt(a.name.match(/\d+/)?.[0] || "0");
      const nb = parseInt(b.name.match(/\d+/)?.[0] || "0");
      return na - nb;
    });

  for (const dir of sessionDirs) {
    const dirPath = path.join(lecturesDir, dir.name);
    const mdFiles = fs
      .readdirSync(dirPath)
      .filter((f) => f.endsWith(".md"))
      .sort();

    if (mdFiles.length > 1) {
      results.push({
        path: dir.name,
        status: "FAIL",
        label: "multiple lecture files",
        detail: `expected one approved topic-merged lecture file; found ${mdFiles.length}: ${mdFiles.join(", ")}`,
      });
      continue;
    }

    for (const file of mdFiles) {
      const relPath = `${dir.name}/${file}`;
      const fullPath = path.join(dirPath, file);

      // A. Filename check
      const fnResult = checkFilename(file);
      if (fnResult) {
        results.push({
          path: relPath,
          status: "FAIL",
          label: fnResult.label,
          detail: `filename: "${fnResult.keyword}"`,
        });
        continue;
      }

      // B. Content check
      const content = fs.readFileSync(fullPath, "utf-8");
      const { score, reasons, codeBlockCount, codeRatio } =
        scoreContent(content);

      if (score >= 6) {
        const detail = reasons.join(", ");
        // Pick the most descriptive label
        let label = "non-lecture";
        if (reasons.some((r) => r.includes("Solution") || r.includes("answer")))
          label = "solution";
        else if (
          reasons.some((r) => r.includes("Exercise") || r.includes("Question"))
        )
          label = "exercise";
        else if (reasons.some((r) => r.includes("code block") || r.includes("% code")))
          label = "code tutorial";
        else if (reasons.some((r) => r.includes("table")))
          label = "reference table";

        results.push({ path: relPath, status: "FAIL", label, detail });
      } else if (score >= 3) {
        const shortReasons = [];
        if (codeBlockCount > 5)
          shortReasons.push(`${codeBlockCount} code blocks`);
        if (codeRatio > 0.4)
          shortReasons.push(`${Math.round(codeRatio * 100)}% code`);
        const otherReasons = reasons.filter(
          (r) => !r.includes("code block") && !r.includes("% code")
        );
        shortReasons.push(...otherReasons);

        let label = "ambiguous content";
        if (reasons.some((r) => r.includes("code")))
          label = "possible code tutorial";
        else if (reasons.some((r) => r.includes("table")))
          label = "possible reference table";
        else if (reasons.some((r) => r.includes("Solution") || r.includes("answer")))
          label = "possible solution";
        else if (reasons.some((r) => r.includes("Exercise") || r.includes("Question")))
          label = "possible exercise";

        results.push({
          path: relPath,
          status: "WARN",
          label,
          detail: shortReasons.join(", "),
        });
      } else {
        results.push({ path: relPath, status: "PASS", label: "lecture" });
      }
    }
  }

  return results;
}

// ── Exercise file checks ─────────────────────────────────────

const EXERCISE_PATTERN = /^(exercises|stata)_[A-Z]{2}\.json$/;

function checkExercises(bankDir) {
  const results = [];

  if (!fs.existsSync(bankDir)) {
    console.log(`  (directory not found: ${bankDir})`);
    return results;
  }

  const sessionDirs = fs
    .readdirSync(bankDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^S\d+/i.test(d.name))
    .sort((a, b) => {
      const na = parseInt(a.name.match(/\d+/)?.[0] || "0");
      const nb = parseInt(b.name.match(/\d+/)?.[0] || "0");
      return na - nb;
    });

  for (const dir of sessionDirs) {
    const dirPath = path.join(bankDir, dir.name);
    const files = fs.readdirSync(dirPath).sort();

    for (const file of files) {
      const relPath = `${dir.name}/${file}`;
      const fullPath = path.join(dirPath, file);

      if (!EXERCISE_PATTERN.test(file)) {
        results.push({
          path: relPath,
          status: "SKIP",
          detail: "not exercises/stata pattern",
        });
        continue;
      }

      // Validate JSON structure
      try {
        const raw = fs.readFileSync(fullPath, "utf-8");
        const data = JSON.parse(raw);

        if (!Array.isArray(data)) {
          results.push({
            path: relPath,
            status: "WARN",
            detail: "JSON is not an array",
          });
          continue;
        }

        // Validate every exercise, not just the first
        const badIds = [];
        for (let i = 0; i < data.length; i++) {
          const ex = data[i];
          const missing = [];
          if (!ex.id) missing.push("id");
          if (!ex.hints) missing.push("hints");
          if (!ex.solution) missing.push("solution");
          if (missing.length > 0) {
            badIds.push(`[${i}]${ex.id ? `(${ex.id})` : ""}: missing ${missing.join(", ")}`);
          }
        }
        if (badIds.length > 0) {
          results.push({
            path: relPath,
            status: "WARN",
            detail: `${badIds.length} invalid exercise(s): ${badIds.slice(0, 3).join("; ")}${badIds.length > 3 ? " …" : ""}`,
          });
          continue;
        }

        results.push({
          path: relPath,
          status: "PASS",
          count: data.length,
        });
      } catch (e) {
        results.push({
          path: relPath,
          status: "WARN",
          detail: `invalid JSON: ${e.message.slice(0, 60)}`,
        });
      }
    }
  }

  return results;
}

// ── Output formatting ────────────────────────────────────────

const ICONS = { PASS: "PASS", WARN: "WARN", FAIL: "FAIL", SKIP: "-" };

function padRight(str, len) {
  return str.length >= len ? str : str + " ".repeat(len - str.length);
}

function printResults(lectureResults, exerciseResults) {
  console.log();
  console.log("Pre-flight Content Check");
  console.log(`  Lectures dir : ${LECTURES_DIR}`);
  console.log(`  Bank dir     : ${BANK_DIR}`);

  // ── Lecture Files ──
  console.log();
  console.log("── Lecture Files ─────────────────────────────────");

  if (lectureResults.length === 0) {
    console.log("  (no .md files found)");
  }

  // Find max path length for alignment
  const maxPathLen = Math.max(
    ...lectureResults.map((r) => r.path.length),
    10
  );

  for (const r of lectureResults) {
    const icon = ICONS[r.status];
    const pathStr = padRight(r.path, maxPathLen);
    if (r.status === "PASS") {
      console.log(`  ${pathStr}   ${icon} ${r.label}`);
    } else if (r.status === "FAIL") {
      console.log(`  ${pathStr}   ${icon} ${r.label} (${r.detail})`);
    } else {
      console.log(`  ${pathStr}   ${icon} ${r.label} (${r.detail})`);
    }
  }

  // ── Exercise Files ──
  console.log();
  console.log("── Exercise Files ───────────────────────────────");

  if (exerciseResults.length === 0) {
    console.log("  (no files found)");
  }

  const maxExPathLen = Math.max(
    ...exerciseResults.map((r) => r.path.length),
    10
  );

  for (const r of exerciseResults) {
    const icon = ICONS[r.status];
    const pathStr = padRight(r.path, maxExPathLen);
    if (r.status === "PASS") {
      console.log(
        `  ${pathStr}   ${icon} ${r.count} exercises`
      );
    } else if (r.status === "SKIP") {
      console.log(
        `  ${pathStr}   ${icon} skipped (${r.detail})`
      );
    } else {
      console.log(
        `  ${pathStr}   ${icon} ${r.detail}`
      );
    }
  }

  // ── Summary ──
  console.log();
  console.log("── Summary ──────────────────────────────────────");

  const lPassed = lectureResults.filter((r) => r.status === "PASS").length;
  const lWarned = lectureResults.filter((r) => r.status === "WARN").length;
  const lFailed = lectureResults.filter((r) => r.status === "FAIL").length;
  const lTotal = lectureResults.length;

  console.log(`  Lectures:  ${lTotal} files`);
  console.log(
    `    ${ICONS.PASS} ${lPassed} passed    ${ICONS.WARN} ${lWarned} warning${lWarned !== 1 ? "s" : ""}    ${ICONS.FAIL} ${lFailed} failure${lFailed !== 1 ? "s" : ""}`
  );

  const eMatched = exerciseResults.filter((r) => r.status !== "SKIP").length;
  const eSkipped = exerciseResults.filter((r) => r.status === "SKIP").length;
  console.log(
    `  Exercises: ${eMatched} matched, ${eSkipped} skipped`
  );

  if (lFailed > 0) {
    console.log();
    console.log(
      "  FAIL Remove or relocate FAIL items before running the pipeline."
    );
  }

  return lFailed;
}

// ── Main ─────────────────────────────────────────────────────

const lectureResults = checkLectures(LECTURES_DIR);
const exerciseResults = checkExercises(BANK_DIR);
const failCount = printResults(lectureResults, exerciseResults);

console.log();
process.exit(failCount > 0 ? 1 : 0);
