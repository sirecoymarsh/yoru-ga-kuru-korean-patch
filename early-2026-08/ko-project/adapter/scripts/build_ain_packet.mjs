#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) fail(`Unexpected argument: ${arg}`);
    const key = arg.slice(2);
    const value = argv[i + 1];
    if (value === undefined || value.startsWith("--")) fail(`Missing value for --${key}`);
    args[key] = value;
    i += 1;
  }
  return args;
}

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function classify(source) {
  if (source === "") return "blank";
  if (/^[　\s]+$/u.test(source)) return "spacing";
  if (/^【.+】$/u.test(source)) return "speaker_label";
  if (/^[「『].*[」』]$/u.test(source)) return "dialogue";
  if (/^[（(].*[）)]$/u.test(source)) return "inner_monologue";
  if (/^[・…―ー〜～・\s]+$/u.test(source)) return "pause_or_effect";
  return "narration_or_continuation";
}

function cleanSpeaker(label) {
  const match = /^【(.+)】$/u.exec(label);
  return match ? match[1].trim() : null;
}

const args = parseArgs(process.argv.slice(2));
const required = ["input", "output", "function", "first-id", "last-id", "glossary"];
for (const key of required) {
  if (!(key in args)) fail(`Required option missing: --${key}`);
}

const firstId = Number(args["first-id"]);
const lastId = Number(args["last-id"]);
if (!Number.isInteger(firstId) || !Number.isInteger(lastId) || firstId > lastId) {
  fail("--first-id and --last-id must be an ascending integer range");
}

const rows = fs
  .readFileSync(args.input, "utf8")
  .split(/\r?\n/u)
  .filter(Boolean)
  .map((line, index) => {
    try {
      return JSON.parse(line);
    } catch (error) {
      fail(`Invalid JSONL at line ${index + 1}: ${error.message}`);
    }
  })
  .filter(
    (row) =>
      row.kind === "message" &&
      row.id >= firstId &&
      row.id <= lastId &&
      Array.isArray(row.contexts) &&
      row.contexts.includes(args.function),
  )
  .sort((a, b) => a.id - b.id);

if (rows.length === 0) {
  fail("No matching message entries found");
}

let activeSpeaker = null;
const entries = rows.map((row, index) => {
  const role = classify(row.source);
  if (role === "speaker_label") activeSpeaker = cleanSpeaker(row.source);
  const previous = index > 0 ? rows[index - 1].source : null;
  const next = index + 1 < rows.length ? rows[index + 1].source : null;
  const shouldTranslate = !["blank", "spacing", "pause_or_effect"].includes(role);
  return {
    stable_id: row.stable_id,
    kind: row.kind,
    numeric_id: row.id,
    source_sha256: row.source_sha256,
    source: row.source,
    function: args.function,
    role,
    speaker: role === "speaker_label" ? cleanSpeaker(row.source) : activeSpeaker,
    previous_source: previous,
    next_source: next,
    protected_tokens: row.protected_tokens ?? [],
    translation_required: shouldTranslate,
    target: shouldTranslate ? "" : row.source,
    translator_notes: "",
    review_status: shouldTranslate ? "pending" : "not_applicable",
  };
});

const packetId =
  args["packet-id"] ??
  `${args.function.replace(/[^\p{L}\p{N}]+/gu, "_")}_m${firstId}_m${lastId}`;

const packet = {
  schema: "contextual-game-localization.translation-packet.v1",
  packet_id: packetId,
  source_asset: "NightRemaster.ain",
  semantic_source_language: "ja-JP",
  target_language: "ko-KR",
  translation_provider: "Codex internal model",
  intermediate_language: null,
  function: args.function,
  requested_numeric_range: { first: firstId, last: lastId },
  actual_numeric_range: {
    first: entries[0].numeric_id,
    last: entries.at(-1).numeric_id,
  },
  entry_count: entries.length,
  translatable_count: entries.filter((entry) => entry.translation_required).length,
  glossary: {
    path: path.basename(args.glossary),
    sha256: sha256File(args.glossary),
  },
  rules: [
    "Translate directly from Japanese into natural Korean.",
    "Do not use an intermediate language or external translation API.",
    "Preserve every stable_id, source, source_sha256, protected token, and entry order.",
    "Speaker labels are translated according to the locked glossary.",
    "Write split lines as one coherent thought while retaining the original field count.",
    "Do not translate numeric voice IDs, lookup keys, control codes, or asset names.",
  ],
  entries,
};

fs.mkdirSync(path.dirname(args.output), { recursive: true });
fs.writeFileSync(args.output, `${JSON.stringify(packet, null, 2)}\n`, "utf8");
process.stdout.write(
  `${args.output}\nentries=${packet.entry_count}\ntranslatable=${packet.translatable_count}\n`,
);
