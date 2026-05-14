#!/usr/bin/env node
// Interactive setup wizard — substitutes {{PLACEHOLDER}} tokens in
// templates/ta-widget.template.html → frontend/ta-widget.html, and scaffolds
// data/course_config.json + .env.local.
//
// Run from the repo root:
//   node scripts/setup.mjs

import { input, select, confirm } from "@inquirer/prompts";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

console.log("\nTA-LLM Setup Wizard\n");
console.log("Fills {{PLACEHOLDER}} tokens in ta-widget.html, scaffolds data/course_config.json, and writes .env.local.\n");

// ── Deployment type ─────────────────────────────────────────────────────────

const profile = await select({
  message: "What kind of deployment?",
  choices: [
    {
      name: "Content companion — chat over a paper, book, manual, or any structured content (no quiz)",
      value: "content_companion",
    },
    {
      name: "Course teaching assistant — chat + quiz mode for courses with exercise banks",
      value: "course_ta",
    },
  ],
});
const isCourse = profile === "course_ta";

// ── Identity ────────────────────────────────────────────────────────────────

const courseId = await input({
  message: isCourse
    ? "Course ID (short identifier, e.g. ECON101):"
    : "Project ID (short identifier, e.g. mybook, climate-paper):",
  validate: v => /^[A-Za-z0-9_-]+$/.test(v.trim()) || "Only letters, numbers, hyphens, and underscores allowed",
});

const courseName = await input({
  message: isCourse ? "Full course name:" : "Project / content title:",
  validate: v => v.trim().length > 0 || "Required",
});

const institution = await input({
  message: isCourse ? "Institution name:" : "Author / organization (optional, Enter to skip):",
  default: "",
});

const instructorName = await input({
  message: isCourse ? "Instructor name:" : "Your name (optional, Enter to skip):",
  default: "",
});

const instructorUrl = await input({
  message: "Personal website URL (optional, Enter to skip):",
  default: "",
});

// ── Look & feel ─────────────────────────────────────────────────────────────

const primaryColor = await input({
  message: "Primary color (hex, e.g. #002855):",
  default: "#002855",
  validate: v => /^#[0-9a-fA-F]{6}$/.test(v) || "Must be a 6-digit hex color like #002855",
});

const accentColor = await input({
  message: "Accent color (hex, e.g. #0072CE):",
  default: "#0072CE",
  validate: v => /^#[0-9a-fA-F]{6}$/.test(v) || "Must be a 6-digit hex color like #0072CE",
});

// ── Language ────────────────────────────────────────────────────────────────

const bilingual = await confirm({
  message: "Bilingual (English + French) with an in-widget language switch button?",
  default: false,
});

const language = bilingual
  ? await select({
      message: "Default language on first visit:",
      choices: [
        { name: "English", value: "en" },
        { name: "French / Français", value: "fr" },
      ],
    })
  : "en";

// ── Quiz mode ───────────────────────────────────────────────────────────────

const quizEnabled = isCourse
  ? await confirm({
      message: "Enable quiz mode (requires sources/exercises/ JSON banks)?",
      default: true,
    })
  : false;

// ── Auth ────────────────────────────────────────────────────────────────────

const authRequired = await confirm({
  message: isCourse
    ? "Require a shared access password (recommended for student deployments)?"
    : "Require a shared access password (recommended if costs are billed to you)?",
  default: isCourse,
});

// ── Site URL ────────────────────────────────────────────────────────────────

const siteUrl = await input({
  message: "Netlify site URL — leave default and find-replace API_URL in frontend/ta-widget.html after first deploy:",
  default: "https://YOUR-SITE.netlify.app",
});
const siteUrlIsDefault = /YOUR-SITE/i.test(siteUrl);

// ── UI label defaults ───────────────────────────────────────────────────────

const UI_DEFAULTS = {
  en: {
    HERO_TITLE: courseName + (isCourse ? " Teaching Assistant" : " — Companion"),
    HERO_SUBTITLE: isCourse
      ? "Ask questions about course material" + (quizEnabled ? " or practice with exercises." : ".")
      : "Ask questions about " + courseName + ".",
    HERO_CTA: "Get started",
    LOGIN_TITLE: "Enter the access password",
    LOGIN_SUBTITLE: "",
    LOGIN_PLACEHOLDER: "Access password",
    LOGIN_BUTTON: "Continue",
    MODE_TUTOR_LABEL: "Chat",
    TOGGLE_TO_QUIZ_LABEL: "Switch to Quiz",
    TITLE_SEND: "Send",
    TITLE_NEW_CHAT: "New chat",
    TITLE_FULLSCREEN: "Fullscreen",
    TITLE_CLOSE: "Close",
    ARIA_OPEN_CHAT: "Open chat assistant",
    CHAT_PLACEHOLDER: "Ask a question…",
    ASSISTANT_LABEL: isCourse ? "Teaching Assistant" : "Companion",
  },
  fr: {
    HERO_TITLE: (isCourse ? "Assistant pédagogique — " : "Compagnon — ") + courseName,
    HERO_SUBTITLE: isCourse
      ? "Posez vos questions sur le cours" + (quizEnabled ? " ou entraînez-vous avec des exercices." : ".")
      : "Posez vos questions sur " + courseName + ".",
    HERO_CTA: "Commencer",
    LOGIN_TITLE: "Entrez le mot de passe d'accès",
    LOGIN_SUBTITLE: "",
    LOGIN_PLACEHOLDER: "Mot de passe d'accès",
    LOGIN_BUTTON: "Continuer",
    MODE_TUTOR_LABEL: "Discussion",
    TOGGLE_TO_QUIZ_LABEL: "Passer au Quiz",
    TITLE_SEND: "Envoyer",
    TITLE_NEW_CHAT: "Nouvelle discussion",
    TITLE_FULLSCREEN: "Plein écran",
    TITLE_CLOSE: "Fermer",
    ARIA_OPEN_CHAT: "Ouvrir l'assistant",
    CHAT_PLACEHOLDER: "Posez votre question…",
    ASSISTANT_LABEL_FR: isCourse ? "Assistant pédagogique" : "Compagnon",
  },
};

const labels = UI_DEFAULTS[language];
// Always include the FR label too — bilingual deployments need both, single-EN
// deployments don't render the FR string but it's harmless to substitute.
const assistantLabelFr = UI_DEFAULTS.fr.ASSISTANT_LABEL_FR;

// API URL: keep the placeholder visible if the user accepted the default,
// otherwise substitute the real URL. This keeps the post-deploy find-replace
// honest instead of silently baking YOUR-SITE.netlify.app into the bundle.
const apiUrl = siteUrlIsDefault
  ? "{{API_URL}}"  // intentionally unsubstituted; replace after first deploy
  : siteUrl.replace(/\/$/, "") + "/api/ta-chat";

// CORS origin: reuse the site URL (origin only, no path) when known. Default
// to "*" when the user kept YOUR-SITE so local dev works; the operator must
// tighten it in production.
const allowedOrigin = siteUrlIsDefault
  ? "*"
  : siteUrl.replace(/\/$/, "");

// HTML escape for safe injection into attributes / text content
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ── Replacements map ────────────────────────────────────────────────────────

const replacements = {
  // Identity
  "{{COURSE_CODE}}":        esc(courseId),
  "{{COURSE_NAME}}":        esc(courseName),
  "{{COURSE_ID_LOWER}}":    courseId.toLowerCase(),
  "{{INSTITUTION}}":        esc(institution),
  "{{INSTRUCTOR_NAME}}":    esc(instructorName),
  "{{INSTRUCTOR_TITLE}}":   "",

  // Page / header
  "{{HTML_LANG}}":          language,
  "{{PRIMARY_LANG}}":       language,
  "{{AUTH_REQUIRED}}":      String(authRequired),
  "{{BILINGUAL_ENABLED}}":  String(bilingual),
  "{{QUIZ_MODE_ENABLED}}":  String(quizEnabled),
  "{{PAGE_TITLE}}":         esc(courseName),
  "{{HEADER_TITLE}}":       esc(courseId),

  // CSS palette
  "{{CSS_NAVY}}":           primaryColor,
  "{{CSS_NAVY_SOFT}}":      primaryColor + "cc",
  "{{CSS_NAVY_MID}}":       primaryColor + "99",
  "{{CSS_BLUE}}":           accentColor,
  "{{CSS_BLUE_ACCENT}}":    accentColor,
  "{{CSS_BLUE_LIGHT}}":     accentColor + "33",
  "{{CSS_CREDIT_GRAY}}":    "#6b7280",

  // Endpoints
  "{{API_URL}}":            apiUrl,
  "{{WEBSITE_URL}}":        instructorUrl,
  "{{WEBSITE_LABEL}}":      esc(institution || courseName),

  // Hero / login
  "{{HERO_TITLE}}":         esc(labels.HERO_TITLE),
  "{{HERO_SUBTITLE}}":      esc(labels.HERO_SUBTITLE),
  "{{HERO_CTA}}":           esc(labels.HERO_CTA),
  "{{LOGIN_TITLE}}":        esc(labels.LOGIN_TITLE),
  "{{LOGIN_SUBTITLE}}":     esc(labels.LOGIN_SUBTITLE),
  "{{LOGIN_PLACEHOLDER}}":  esc(labels.LOGIN_PLACEHOLDER),
  "{{LOGIN_BUTTON}}":       esc(labels.LOGIN_BUTTON),

  // Chat UI
  "{{TITLE_SEND}}":             esc(labels.TITLE_SEND),
  "{{TITLE_NEW_CHAT}}":         esc(labels.TITLE_NEW_CHAT),
  "{{TITLE_FULLSCREEN}}":       esc(labels.TITLE_FULLSCREEN),
  "{{TITLE_CLOSE}}":            esc(labels.TITLE_CLOSE),
  "{{ARIA_OPEN_CHAT}}":         esc(labels.ARIA_OPEN_CHAT),
  "{{CHAT_PLACEHOLDER}}":       esc(labels.CHAT_PLACEHOLDER),
  "{{MODE_TUTOR_LABEL}}":       esc(labels.MODE_TUTOR_LABEL),
  "{{TOGGLE_TO_QUIZ_LABEL}}":   esc(labels.TOGGLE_TO_QUIZ_LABEL),

  // Footer credit suffix (see ta_suffix in template STRINGS)
  "{{ASSISTANT_LABEL}}":     esc(language === "en" ? labels.ASSISTANT_LABEL : UI_DEFAULTS.en.ASSISTANT_LABEL),
  "{{ASSISTANT_LABEL_FR}}":  esc(assistantLabelFr),

  // Optional intro HTML blocks (advanced — leave empty unless you know what you're doing)
  "{{INSTRUCTIONS_EN}}":    "",
  "{{INSTRUCTIONS_FR}}":    "",
};

// ── Substitute tokens ────────────────────────────────────────────────────────

const templateCandidates = [
  join(ROOT, "ta-widget.html"),
  join(ROOT, "templates", "ta-widget.template.html"),
];
const templatePath = templateCandidates.find(existsSync);
if (!templatePath) {
  console.error("ERROR: ta-widget.html not found. Run from repo root.");
  process.exit(1);
}

let widgetSrc = readFileSync(templatePath, "utf-8");
for (const [token, value] of Object.entries(replacements)) {
  widgetSrc = widgetSrc.replaceAll(token, value);
}

// Sanity: warn about any unsubstituted tokens we didn't intend to leave open
const leftovers = [...widgetSrc.matchAll(/\{\{[A-Z0-9_]+\}\}/g)]
  .map(m => m[0])
  .filter(t => t !== "{{API_URL}}");  // intentionally left if siteUrl was default
if (leftovers.length > 0) {
  console.warn("WARN: unsubstituted template tokens remain:", [...new Set(leftovers)].join(", "));
}

const outputPath = templatePath.endsWith(".template.html")
  ? join(ROOT, "frontend", "ta-widget.html")
  : templatePath;

mkdirSync(join(ROOT, "frontend"), { recursive: true });
writeFileSync(outputPath, widgetSrc, "utf-8");
console.log("OK: " + outputPath + " written");

if (siteUrlIsDefault) {
  console.log("NOTE: {{API_URL}} left as-is. After first deploy, find-replace it in frontend/ta-widget.html with https://<your-site>.netlify.app/api/ta-chat then redeploy.");
}

// ── Scaffold data/course_config.json ────────────────────────────────────────

mkdirSync(join(ROOT, "data"), { recursive: true });
const configPath = join(ROOT, "data", "course_config.json");
let writeConfig = true;

if (existsSync(configPath)) {
  writeConfig = await confirm({
    message: "data/course_config.json already exists. Overwrite?",
    default: false,
  });
}

if (writeConfig) {
  const config = {
    prompt_profile: profile,             // "course_ta" | "content_companion"
    course_topics: [],
    academic_signals: [],
    abbreviations: {},
    terminology_fr: bilingual ? "" : "", // empty by default; populate for bilingual deploys with terminology preferences
    question_type_labels: {},
    hidden_question_types: [],
    features: {
      auth_required: authRequired,
      quiz_mode_enabled: quizEnabled,
    },
  };
  writeFileSync(configPath, JSON.stringify(config, null, 2), "utf-8");
  console.log("OK: data/course_config.json scaffolded");
} else {
  console.log("Skipped: data/course_config.json kept as-is");
}

// ── Write .env.local (Mistral-first, comment Anthropic) ─────────────────────

const envLines = [
  "# Generated by setup.mjs — do NOT commit this file (it's in .gitignore)",
  "",
  "# TA chat/query model API — defaults to Mistral Medium.",
  "# This is separate from the embedding API and from Phase 2 agent subscriptions.",
  "MISTRAL_API_KEY=replace-with-mistral-key",
  "",
  "# Embedding API — OpenAI is required for vector build and each retrieval query.",
  "OPENAI_API_KEY=replace-with-openai-key",
  "",
  "# Identity + auth",
  "COURSE_ID=" + courseId,
  authRequired ? "TA_CHAT_PASSWORD=set-a-shared-password" : "# TA_CHAT_PASSWORD=  (auth_required is false; password not enforced)",
  "JWT_SECRET=replace-this-with-a-long-random-string",
  "",
  "# CORS — restricts which origin can call the function. Default '*' is",
  "# fine for local dev but lets any site use your password in production.",
  siteUrlIsDefault
    ? "ALLOWED_ORIGIN=*  # tighten to https://your-site.netlify.app before going live"
    : "ALLOWED_ORIGIN=" + allowedOrigin,
  "",
  "# To use Anthropic instead of Mistral, uncomment these and remove MISTRAL_API_KEY:",
  "# LLM_PROVIDER=anthropic",
  "# ANTHROPIC_API_KEY=replace-with-anthropic-key",
  "",
  "# To use OpenAI / Groq directly, set:",
  "# LLM_BASE_URL=https://api.openai.com/v1   # or https://api.groq.com/openai/v1",
  "# LLM_API_KEY=...",
  "# MODEL_ID=gpt-4o-mini   # or llama-3.3-70b-versatile for Groq",
];
writeFileSync(join(ROOT, ".env.local"), envLines.join("\n") + "\n", "utf-8");
console.log("OK: .env.local written — fill in your API keys before running `netlify dev` or deploying");

// Build numbered next-steps so the order matches the README quickstart:
// edit content (and optionally exercises), fill keys, run pipeline, deploy.
const steps = [
  "(Optional) Edit data/course_config.json — vocabulary, abbreviations, hidden exercise types, etc.",
  "Replace the demo content in sources/lectures/ with your own markdown (one file per section, organized in S1/, S2/, ...).",
];
if (quizEnabled) {
  steps.push("Add exercise banks to sources/exercises/S1/exercises_EN.json (and exercises_FR.json if bilingual).");
}
steps.push("Fill in API keys in .env.local (OPENAI_API_KEY is required for the next step; MISTRAL_API_KEY or your chosen provider's key is required at runtime).");
steps.push(
  "Run the pipeline:\n" +
  "       npm run preflight\n" +
  "       npm run chunk\n" +
  "       npm run transform\n" +
  "       npm run rebuild\n" +
  "       npm run vectors            # auto-loads OPENAI_API_KEY from .env.local"
);
steps.push("Deploy: netlify login && netlify init && netlify deploy --prod");
if (siteUrlIsDefault) {
  steps.push("After the first deploy, find-replace {{API_URL}} in frontend/ta-widget.html with the live Netlify URL, then redeploy.");
}

console.log("\nSetup complete.\n\nNext:");
steps.forEach((s, i) => console.log(`  ${i + 1}. ${s}`));
console.log("");
