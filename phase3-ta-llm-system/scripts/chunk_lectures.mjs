#!/usr/bin/env node
// ============================================================
// Lecture Markdown → Corpus Chunk Builder
// ============================================================
//
// Reads raw markdown lecture files from sources/lectures/S{n}/
// and produces corpus-compatible chunks for BM25 + vector search.
//
// Chunking strategy (mirrors V1 build_index.py):
//   - Split at heading boundaries (### or ####, the slide-level headings)
//   - # and ## serve as section markers (kept as context for sub-chunks)
//   - If a chunk exceeds MAX_CHUNK_TOKENS, split at paragraph boundaries
//   - Each chunk gets metadata: session, source_file, heading, etc.
//
// Usage:
//   node scripts/chunk_lectures.mjs [--lectures-dir <path>] [--out-dir <path>]
//
// Defaults (resolve from project root via process.cwd()):
//   --lectures-dir  ./sources/lectures
//   --out-dir       ./data
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
const OUT_DIR = path.resolve(
  process.cwd(),
  getArg("--out-dir", "./data")
);
const COURSE_ID = getArg("--course-id", "default");
const TERM = getArg("--term", "default");

const MAX_CHUNK_TOKENS = 1000; // Split chunks exceeding this

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

// ── Clean heading text ───────────────────────────────────────
function cleanHeading(raw) {
  return raw
    .replace(/<[^>]+>/g, "")           // strip HTML tags (span, etc.)
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1") // [text](url) → text
    .replace(/\*+/g, "")               // strip bold/italic markers
    .replace(/\s+/g, " ")
    .trim();
}

// ── Detect language from filename or content ─────────────────
function detectLanguage(filename, text) {
  // French indicators in filename
  const frenchFilenames = /[éèêëàâùûîïôöç]/i;
  if (frenchFilenames.test(filename)) return "fr";

  // Quick content check: count French vs English stopwords in first 500 chars
  const sample = text.slice(0, 500).toLowerCase();
  const frWords = (sample.match(/\b(le|la|les|une|des|dans|pour|avec|sur|est|cette|nous|vous|sont|ont|peut)\b/g) || []).length;
  const enWords = (sample.match(/\b(the|a|an|is|and|or|for|with|in|on|at|are|this|that|we|you)\b/g) || []).length;
  return frWords > enWords ? "fr" : "en";
}

// ── Classify source type from filename ───────────────────────
function classifySourceType(filename) {
  const lower = filename.toLowerCase();
  if (lower.includes("solution")) return "solution";
  if (lower.includes("code") || lower.includes("script") || lower.includes("program")) return "code";
  if (lower.includes("exercise") || lower.includes("practice") || lower.includes("problem")) return "exercise_statement";
  if (lower.includes("table") || lower.includes("reference")) return "reference_table";
  return "lecture";
}

// ── Split markdown into heading-based sections ───────────────
function splitByHeadings(markdown, fallbackHeading) {
  const lines = markdown.split("\n");
  const sections = [];
  let currentHeading = fallbackHeading || ""; // default for content before first heading
  let currentSection = "";
  let buffer = [];

  for (const line of lines) {
    // Match heading lines: # through ####
    const headingMatch = line.match(/^(#{1,4})\s+(.+)/);

    if (headingMatch) {
      const level = headingMatch[1].length;
      const rawHeading = headingMatch[2];
      const heading = cleanHeading(rawHeading);

      // Skip empty headings
      if (!heading) {
        buffer.push(line);
        continue;
      }

      // # or ## = major section marker
      if (level <= 2) {
        // Flush current buffer as a chunk
        if (buffer.length > 0 && currentHeading) {
          sections.push({
            heading: currentHeading,
            section: currentSection,
            text: buffer.join("\n").trim(),
          });
        }
        currentSection = heading;
        currentHeading = heading;
        buffer = [];
        continue;
      }

      // ### or #### = slide-level chunk boundary
      if (buffer.length > 0 && currentHeading) {
        sections.push({
          heading: currentHeading,
          section: currentSection,
          text: buffer.join("\n").trim(),
        });
      }
      currentHeading = heading;
      buffer = [];
    } else {
      buffer.push(line);
    }
  }

  // Flush last buffer
  if (buffer.length > 0 && currentHeading) {
    sections.push({
      heading: currentHeading,
      section: currentSection,
      text: buffer.join("\n").trim(),
    });
  }

  return sections;
}

// ── Split oversized sections at paragraph boundaries ─────────
function splitOversizedSection(section, maxTokens) {
  const tokens = tokenize(section.text);
  if (tokens.length <= maxTokens) return [section];

  const paragraphs = section.text.split(/\n\n+/);
  const parts = [];
  let current = [];
  let currentTokenCount = 0;

  for (const para of paragraphs) {
    const paraTokens = tokenize(para).length;

    if (currentTokenCount + paraTokens > maxTokens && current.length > 0) {
      parts.push({
        heading: `${section.heading} (part ${parts.length + 1})`,
        section: section.section,
        text: current.join("\n\n").trim(),
      });
      current = [para];
      currentTokenCount = paraTokens;
    } else {
      current.push(para);
      currentTokenCount += paraTokens;
    }
  }

  if (current.length > 0) {
    const suffix = parts.length > 0 ? ` (part ${parts.length + 1})` : "";
    parts.push({
      heading: `${section.heading}${suffix}`,
      section: section.section,
      text: current.join("\n\n").trim(),
    });
  }

  return parts;
}

// ── Build corpus chunk from a section ────────────────────────
function buildChunk(section, chunkIdx, sourceId, sourceFile, session, language, sourceType) {
  const text = section.text;
  const heading = section.heading;
  const headingText = heading.replace(/\s*\(part \d+\)$/, "");

  const textTokens = tokenize(text);
  const headingTokens = tokenize(heading);
  const allTokens = [...textTokens, ...headingTokens];
  const tf = buildTF(allTokens);

  // Strict separation: lectures/code/tables → tutor only, solutions → quiz only
  const policy = sourceType === "solution" ? "OK_SOLVE" : "NO_SOLVE";
  const modeAllowed = sourceType === "solution"
    ? ["quiz"]
    : ["tutor"];

  return {
    id: `${sourceId}_chunk_${chunkIdx}`,
    heading,
    heading_text: headingText,
    text,
    tokens: allTokens,
    tf,
    source_file: sourceFile,
    meta: {
      source_id: sourceId,
      source_type: sourceType,
      title: `${sourceId}: ${headingText}`,
      policy,
      mode_allowed: modeAllowed,
      topic_tags: [],
      course_id: COURSE_ID,
      term: TERM,
      heading,
      chunk_type: sourceType,
      session,
      language,
      section: section.section || null,
    },
  };
}

// ── Process one markdown file ────────────────────────────────
function processFile(filepath, session) {
  const filename = path.basename(filepath, ".md");
  const content = fs.readFileSync(filepath, "utf-8");
  const language = detectLanguage(filename, content);
  const sourceType = classifySourceType(filename);
  const sourceId = `${session}_${filename.replace(/[^a-zA-Z0-9_]/g, "_")}`;
  const relPath = `${session}/${path.basename(filepath)}`;

  // Split into heading-based sections (pass filename as fallback for pre-heading content)
  let sections = splitByHeadings(content, filename);

  // Filter out empty/trivial sections (< 10 words of content)
  sections = sections.filter((s) => {
    const words = s.text.split(/\s+/).filter((w) => w.length > 0);
    return words.length >= 10;
  });

  // Split oversized sections
  const allSections = [];
  for (const section of sections) {
    allSections.push(...splitOversizedSection(section, MAX_CHUNK_TOKENS));
  }

  // Build chunks
  return allSections.map((section, idx) =>
    buildChunk(section, idx, sourceId, relPath, session, language, sourceType)
  );
}

// ── Discover lecture files (dynamic — any S{n} directory) ────
function discoverLectureFiles(lecturesDir) {
  const files = [];
  const sessions = fs.readdirSync(lecturesDir)
    .filter(d => fs.statSync(path.join(lecturesDir, d)).isDirectory() && /^S\d+/.test(d))
    .sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1)));
  for (const session of sessions) {
    const dir = path.join(lecturesDir, session);
    const mdFiles = fs.readdirSync(dir).filter(f => f.endsWith(".md")).sort();
    for (const f of mdFiles) {
      files.push({ path: path.join(dir, f), session, filename: f });
    }
  }
  return files;
}

// ── Main ─────────────────────────────────────────────────────
function main() {
  console.log(`Lecture Markdown → Corpus Chunks`);
  console.log(`  Lectures dir : ${LECTURES_DIR}`);
  console.log(`  Out dir      : ${OUT_DIR}`);
  console.log(`  Course       : ${COURSE_ID}`);
  console.log(`  Term         : ${TERM}`);
  console.log();

  if (!fs.existsSync(LECTURES_DIR)) {
    console.error(`ERROR: Lectures directory not found: ${LECTURES_DIR}`);
    process.exit(1);
  }

  fs.mkdirSync(OUT_DIR, { recursive: true });

  const files = discoverLectureFiles(LECTURES_DIR);
  console.log(`Found ${files.length} markdown files.\n`);

  const allChunks = [];
  const stats = { sessions: {}, byType: {}, byLang: {} };

  for (const { path: fp, session, filename } of files) {
    const chunks = processFile(fp, session);
    allChunks.push(...chunks);

    const sourceType = classifySourceType(filename);
    stats.sessions[session] = (stats.sessions[session] || 0) + chunks.length;
    stats.byType[sourceType] = (stats.byType[sourceType] || 0) + chunks.length;

    console.log(`  ${session}/${filename}: ${chunks.length} chunks (${sourceType})`);
  }

  // Count by language
  for (const chunk of allChunks) {
    const lang = chunk.meta.language;
    stats.byLang[lang] = (stats.byLang[lang] || 0) + 1;
  }

  console.log();
  console.log(`── Summary ──────────────────────────────────────`);
  console.log(`Total chunks: ${allChunks.length}`);
  console.log(`By session:   ${JSON.stringify(stats.sessions)}`);
  console.log(`By type:      ${JSON.stringify(stats.byType)}`);
  console.log(`By language:  ${JSON.stringify(stats.byLang)}`);

  // Token stats
  const tokenCounts = allChunks.map((c) => c.tokens.length);
  if (tokenCounts.length === 0) {
    console.warn("WARNING: no chunks produced — check sources/lectures/ for markdown files.");
  }
  const avgTokens = tokenCounts.length > 0
    ? (tokenCounts.reduce((a, b) => a + b, 0) / tokenCounts.length).toFixed(1)
    : "0";
  const maxTokens = tokenCounts.length > 0 ? Math.max(...tokenCounts) : 0;
  const minTokens = tokenCounts.length > 0 ? Math.min(...tokenCounts) : 0;
  console.log(`Token stats:  avg=${avgTokens}, min=${minTokens}, max=${maxTokens}`);

  // Write output
  const outPath = path.join(OUT_DIR, "lecture_chunks.json");
  fs.writeFileSync(outPath, JSON.stringify(allChunks, null, 2));
  console.log(`\nWritten: ${outPath} (${(fs.statSync(outPath).size / 1024 / 1024).toFixed(1)} MB)`);

  // Spot-check
  if (allChunks.length > 0) {
    const sample = allChunks[Math.floor(allChunks.length / 2)];
    console.log();
    console.log(`── Sample chunk (middle) ──`);
    console.log(`  id:      ${sample.id}`);
    console.log(`  heading: ${sample.heading}`);
    console.log(`  session: ${sample.meta.session}`);
    console.log(`  type:    ${sample.meta.source_type}`);
    console.log(`  tokens:  ${sample.tokens.length}`);
    console.log(`  text:    ${sample.text.slice(0, 120)}...`);
  }
}

main();
