#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const expectedProjectRoot = path.resolve(
  "P:\\AI\\Codex\\game_localization\\YoruGaKuru_Remastered_KO_Project",
);
const forbiddenGameRoot = path.resolve(
  "P:\\GAME\\Compacted Files\\[Ryuugames] RY-r119676\\夜が来る！-Square of the MOON- Remastered",
);
const projectRootArgument = process.argv[2];
const mode = process.argv[3];

if (!projectRootArgument || mode !== "--non-runtime-sync") {
  process.stderr.write(
    "Usage: node generate_artifact_index.mjs <project-root> --non-runtime-sync\n",
  );
  process.exit(1);
}

function samePath(left, right) {
  if (typeof left !== "string" || typeof right !== "string") {
    return false;
  }
  return path.resolve(left).toLocaleLowerCase("en-US") ===
    path.resolve(right).toLocaleLowerCase("en-US");
}

function isInside(root, candidate) {
  const relative = path.relative(path.resolve(root), path.resolve(candidate));
  return relative !== "" && !relative.startsWith("..") && !path.isAbsolute(relative);
}

function safeChild(root, relativePath, label) {
  if (typeof relativePath !== "string" || relativePath.length === 0) {
    throw new Error(`${label} is empty or not a string`);
  }
  if (path.isAbsolute(relativePath)) {
    throw new Error(`${label} must be relative: ${relativePath}`);
  }
  const absolutePath = path.resolve(root, ...relativePath.split("/"));
  if (!isInside(root, absolutePath)) {
    throw new Error(`${label} escapes the project root: ${relativePath}`);
  }
  return absolutePath;
}

function assertNoSymbolicLinkAncestor(root, childPath, label) {
  let current = path.dirname(childPath);
  while (samePath(current, root) || isInside(root, current)) {
    if (fs.existsSync(current) && fs.lstatSync(current).isSymbolicLink()) {
      throw new Error(`${label} traverses a symbolic link or junction: ${current}`);
    }
    if (samePath(current, root)) {
      break;
    }
    current = path.dirname(current);
  }
}

const projectRoot = path.resolve(projectRootArgument);
if (!samePath(projectRoot, expectedProjectRoot)) {
  throw new Error(`Refusing unexpected project root: ${projectRoot}`);
}
if (samePath(projectRoot, forbiddenGameRoot) || isInside(forbiddenGameRoot, projectRoot)) {
  throw new Error("The project root resolves inside the original game");
}
if (!fs.statSync(projectRoot).isDirectory()) {
  throw new Error(`Project root is not a directory: ${projectRoot}`);
}
if (fs.lstatSync(projectRoot).isSymbolicLink()) {
  throw new Error(`Project root must not be a symbolic link: ${projectRoot}`);
}

const outputRelativePath = "audit/artifact_index.json";
const relativePaths = [
  "project.json",
  "language_contract.json",
  "semantic_allowlist.json",
  "adapter/contract.json",
  "glossary/glossary.tsv",
  "glossary/style_guide.md",
  "packets/pilot_e00001_part01.json",
  "packets/pilot_e00001_part02.json",
  "packets/pilot_e00001_part03.json",
  "packets/pilot_e00001_part04.json",
  "packets/drafts/result_pilot_e00001_part01.json",
  "packets/drafts/result_pilot_e00001_part02.json",
  "packets/drafts/result_pilot_e00001_part03.json",
  "packets/drafts/result_pilot_e00001_part04.json",
  "packets/reviews/crossreview_pilot_e00001_part01.json",
  "packets/reviews/crossreview_pilot_e00001_part02.json",
  "packets/reviews/crossreview_pilot_e00001_part03.json",
  "packets/reviews/crossreview_pilot_e00001_part04.json",
  "catalog/pilot_translation_map.json",
  "catalog/ain_message_packet_plan.json",
  "catalog/ain_string_triage_plan.json",
  "catalog/pe_surface_catalog_reviewed.json",
  "audit/original_inventory.json",
  "audit/ain_text_summary.json",
  "audit/ex_string_summary.json",
  "audit/archive_list_summary.json",
  "audit/fnl_audit.json",
  "audit/proxy_capacity.json",
  "audit/fnl_dump_scope.json",
  "audit/archive_lists/NightRemasterCG.afa.list.txt",
  "audit/archive_lists/NightRemasterPact.afa.list.txt",
  "audit/archive_lists/NightRemasterSound.afa.list.txt",
  "audit/archive_lists/NightRemasterVoice.afa.list.txt",
  "audit/language_qa_pilot.json",
  "audit/translation_map_validator_pilot.json",
  "audit/ain_proxy_validation_pilot.json",
  "audit/fnl_proxy_map_validation_pilot.json",
  "audit/pilot_bundle_validation.json",
  "audit/pe_surface_catalog_validation.json",
  "audit/original_integrity_recheck.json",
  "audit/ain_roundtrip_audit.json",
  "audit/pact_archive_roundtrip_audit.json",
  "audit/ex_roundtrip_audit.json",
  "audit/surface_inventory.json",
  "audit/audit.json",
  "audit/discovery_report_ko.md",
  "staging/pilot/proxy/pilot_proxy_map.json",
  "evidence/font/pilot_proxy_preview.png",
  "adapter/scripts/analyze_discovery.py",
  "adapter/scripts/analyze_fnl.py",
  "adapter/scripts/analyze_proxy_capacity.py",
  "adapter/scripts/build_ain_packet.mjs",
  "adapter/scripts/build_ain_proxy_text.py",
  "adapter/scripts/build_fnl_proxy_patch.py",
  "adapter/scripts/extract_fnl_samples.py",
  "adapter/scripts/freeze_translation_map.py",
  "adapter/scripts/plan_ain_translation.py",
  "adapter/scripts/pe_resource_audit.ps1",
  "adapter/scripts/verify_original_inventory.mjs",
  "adapter/scripts/update_project_metadata.mjs",
  "adapter/scripts/generate_artifact_index.mjs",
  "adapter/scripts/sync_project_artifacts.ps1",
];

const forbiddenRuntimeExtensions = new Set([
  ".afa",
  ".ain",
  ".apeg",
  ".dcf",
  ".dll",
  ".ex",
  ".exe",
  ".fnl",
  ".ogg",
  ".pactex",
  ".pcf",
  ".qnt",
]);

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

if (relativePaths.includes(outputRelativePath)) {
  throw new Error("The artifact index must not include or hash itself");
}
if (new Set(relativePaths.map((value) => value.toLocaleLowerCase("en-US"))).size !==
    relativePaths.length) {
  throw new Error("Duplicate artifact-index path");
}

const projectMetadataPath = safeChild(projectRoot, "project.json", "project metadata");
const project = JSON.parse(fs.readFileSync(projectMetadataPath, "utf8"));
if (!samePath(project.game_root, forbiddenGameRoot)) {
  throw new Error("project.json does not identify the expected original game root");
}
if (
  project.game_root_policy !== "read_only_until_explicit_install" ||
  project.live_install_approved !== false ||
  project.original_game_modified !== false ||
  project.runtime_assets_generated !== false
) {
  throw new Error("project.json does not preserve the required non-runtime safety state");
}

function readRequiredJson(relativePath) {
  const absolutePath = safeChild(projectRoot, relativePath, "required JSON evidence");
  assertNoSymbolicLinkAncestor(projectRoot, absolutePath, "required JSON evidence");
  const bytes = fs.readFileSync(absolutePath);
  return {
    absolutePath,
    bytes,
    value: JSON.parse(bytes.toString("utf8")),
  };
}

const inventoryDocument = readRequiredJson("audit/original_inventory.json");
const integrityDocument = readRequiredJson("audit/original_integrity_recheck.json");
const pilotMapDocument = readRequiredJson("catalog/pilot_translation_map.json");
const pilotBundleDocument = readRequiredJson("audit/pilot_bundle_validation.json");
const inventory = inventoryDocument.value;
const integrity = integrityDocument.value;
const pilotMap = pilotMapDocument.value;
const pilotBundle = pilotBundleDocument.value;

if (
  inventory.schema !== "contextual-game-localization.original-inventory.v1" ||
  !samePath(inventory.game_root, forbiddenGameRoot) ||
  integrity.schema !== "contextual-game-localization.original-integrity-recheck.v1" ||
  !samePath(integrity.game_root, forbiddenGameRoot) ||
  integrity.inventory?.sha256 !== sha256(inventoryDocument.bytes) ||
  integrity.missing_count !== 0 ||
  integrity.unexpected_count !== 0 ||
  integrity.hash_or_size_mismatch_count !== 0 ||
  integrity.original_game_modified !== false
) {
  throw new Error("Original-integrity evidence is missing, stale, or reports a source change");
}
if (
  pilotMap.schema !== "contextual-game-localization.translation-map.v1" ||
  pilotMap.status !== "pilot_frozen_after_independent_review" ||
  pilotBundle.schema !== "contextual-game-localization.pilot-bundle-validation.v1" ||
  pilotBundle.translation?.map_sha256 !== sha256(pilotMapDocument.bytes) ||
  pilotBundle.language_contract?.replacement_slot_approved !== false ||
  pilotBundle.staged_runtime_asset_count !== 0 ||
  pilotBundle.runtime_assets_generated !== false ||
  pilotBundle.release_ready !== false
) {
  throw new Error("Pilot evidence does not preserve the reviewed pre-approval non-runtime state");
}

const entries = relativePaths.map((relativePath) => {
  if (forbiddenRuntimeExtensions.has(path.extname(relativePath).toLocaleLowerCase("en-US"))) {
    throw new Error(`Runtime asset is forbidden in the index scope: ${relativePath}`);
  }
  const absolutePath = safeChild(projectRoot, relativePath, "indexed artifact");
  assertNoSymbolicLinkAncestor(projectRoot, absolutePath, "indexed artifact");
  const stat = fs.statSync(absolutePath);
  if (!stat.isFile()) {
    throw new Error(`Required artifact is not a file: ${relativePath}`);
  }
  const bytes = fs.readFileSync(absolutePath);
  return {
    path: relativePath,
    size: bytes.length,
    sha256: sha256(bytes),
  };
});

// Detect an input that changed while the snapshot was being assembled.
for (const entry of entries) {
  const absolutePath = safeChild(projectRoot, entry.path, "indexed artifact");
  assertNoSymbolicLinkAncestor(projectRoot, absolutePath, "indexed artifact");
  const bytes = fs.readFileSync(absolutePath);
  if (bytes.length !== entry.size || sha256(bytes) !== entry.sha256) {
    throw new Error(`Artifact changed during index generation: ${entry.path}`);
  }
}

const index = {
  schema: "contextual-game-localization.artifact-index.v1",
  generated_utc: new Date().toISOString(),
  scope: "Discovery, reviewed Japanese-to-Korean pilot, and non-runtime validation artifacts",
  hash_algorithm: "SHA-256",
  original_game_root: forbiddenGameRoot,
  original_game_modified: false,
  runtime_assets_generated: false,
  self_reference_policy: "audit/artifact_index.json is deliberately excluded",
  excluded_paths: [outputRelativePath],
  entry_count: entries.length,
  total_bytes: entries.reduce((sum, entry) => sum + entry.size, 0),
  entries,
};

const outputPath = safeChild(projectRoot, outputRelativePath, "artifact-index output");
assertNoSymbolicLinkAncestor(projectRoot, outputPath, "artifact-index output");
const temporaryPath = `${outputPath}.${process.pid}.${crypto.randomBytes(8).toString("hex")}.tmp`;
const serialized = `${JSON.stringify(index, null, 2)}\n`;
const previousOutput = fs.existsSync(outputPath) ? fs.readFileSync(outputPath) : null;
let outputMutationStarted = false;

try {
  fs.writeFileSync(temporaryPath, serialized, {
    encoding: "utf8",
    flag: "wx",
  });
  const temporaryBytes = fs.readFileSync(temporaryPath);
  JSON.parse(temporaryBytes.toString("utf8"));
  if (temporaryBytes.length !== Buffer.byteLength(serialized) ||
      sha256(temporaryBytes) !== sha256(Buffer.from(serialized, "utf8"))) {
    throw new Error("Temporary artifact index failed content verification");
  }

  // Unlink first rather than overwriting through a possible hard link or file reparse point.
  fs.rmSync(outputPath, { force: true });
  outputMutationStarted = true;
  fs.renameSync(temporaryPath, outputPath);
  const outputBytes = fs.readFileSync(outputPath);
  JSON.parse(outputBytes.toString("utf8"));
  if (sha256(outputBytes) !== sha256(temporaryBytes)) {
    throw new Error("Written artifact index failed SHA-256 verification");
  }
} catch (error) {
  if (outputMutationStarted) {
    if (previousOutput !== null) {
      fs.writeFileSync(outputPath, previousOutput);
    } else {
      fs.rmSync(outputPath, { force: true });
    }
  }
  throw error;
} finally {
  fs.rmSync(temporaryPath, { force: true });
}

process.stdout.write(
  `${JSON.stringify(
    {
      output: outputPath,
      entry_count: index.entry_count,
      total_bytes: index.total_bytes,
      self_indexed: false,
      original_game_modified: false,
      runtime_assets_generated: false,
      sha256: sha256(fs.readFileSync(outputPath)),
    },
    null,
    2,
  )}\n`,
);
