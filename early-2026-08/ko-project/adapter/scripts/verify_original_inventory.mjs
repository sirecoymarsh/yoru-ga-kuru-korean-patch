#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const inventoryPath = process.argv[2];
const outputPath = process.argv[3];
if (!inventoryPath || !outputPath) {
  process.stderr.write(
    "Usage: node verify_original_inventory.mjs <original_inventory.json> <output.json>\n",
  );
  process.exit(1);
}

function normalizeRelative(relativePath) {
  return relativePath.replaceAll("\\", "/");
}

function collectFiles(directory, relative = "") {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const entryRelative = relative
      ? `${relative}/${entry.name}`
      : entry.name;
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectFiles(entryPath, entryRelative));
    } else if (entry.isFile()) {
      files.push(normalizeRelative(entryRelative));
    }
  }
  return files;
}

function hashFile(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash("sha256");
    const stream = fs.createReadStream(filePath);
    stream.on("error", reject);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.on("end", () => resolve(hash.digest("hex")));
  });
}

const inventoryBytes = fs.readFileSync(inventoryPath);
const inventory = JSON.parse(inventoryBytes.toString("utf8"));
const gameRoot = inventory.game_root;
const expectedEntries = inventory.entries.filter((entry) => entry.type === "file");
const expectedByPath = new Map(
  expectedEntries.map((entry) => [normalizeRelative(entry.path), entry]),
);
const actualPaths = collectFiles(gameRoot).sort((a, b) => a.localeCompare(b, "en"));
const actualSet = new Set(actualPaths);
const missing = [...expectedByPath.keys()].filter((entry) => !actualSet.has(entry));
const unexpected = actualPaths.filter((entry) => !expectedByPath.has(entry));
const mismatches = [];
let checkedBytes = 0;

for (const [relativePath, expected] of expectedByPath) {
  if (!actualSet.has(relativePath)) {
    continue;
  }
  const absolutePath = path.join(gameRoot, ...relativePath.split("/"));
  const stat = fs.statSync(absolutePath);
  const actualHash = await hashFile(absolutePath);
  checkedBytes += stat.size;
  if (stat.size !== expected.size || actualHash.toLowerCase() !== expected.sha256.toLowerCase()) {
    mismatches.push({
      path: relativePath,
      expected_size: expected.size,
      actual_size: stat.size,
      expected_sha256: expected.sha256.toLowerCase(),
      actual_sha256: actualHash.toLowerCase(),
    });
  }
}

const verdict =
  missing.length === 0 && unexpected.length === 0 && mismatches.length === 0
    ? "pass"
    : "fail";
const report = {
  schema: "contextual-game-localization.original-integrity-recheck.v1",
  checked_utc: new Date().toISOString(),
  game_root: gameRoot,
  inventory: {
    path: inventoryPath,
    sha256: crypto.createHash("sha256").update(inventoryBytes).digest("hex"),
    expected_file_count: expectedEntries.length,
    expected_total_bytes: expectedEntries.reduce((sum, entry) => sum + entry.size, 0),
  },
  actual_file_count: actualPaths.length,
  checked_file_count: expectedEntries.length - missing.length,
  checked_total_bytes: checkedBytes,
  missing_count: missing.length,
  unexpected_count: unexpected.length,
  hash_or_size_mismatch_count: mismatches.length,
  missing,
  unexpected,
  mismatches,
  original_game_modified: verdict !== "pass",
  verdict,
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const temporaryPath = `${outputPath}.tmp`;
fs.writeFileSync(temporaryPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
fs.renameSync(temporaryPath, outputPath);
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (verdict !== "pass") {
  process.exitCode = 2;
}
