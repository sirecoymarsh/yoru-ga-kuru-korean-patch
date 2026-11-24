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
    "Usage: node update_project_metadata.mjs <project-root> --non-runtime-sync\n",
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

function readJson(relativePath) {
  const filePath = safeChild(projectRoot, relativePath, "JSON input");
  assertNoSymbolicLinkAncestor(projectRoot, filePath, "JSON input");
  const bytes = fs.readFileSync(filePath);
  return {
    filePath,
    originalBytes: bytes,
    value: JSON.parse(bytes.toString("utf8")),
  };
}

function sha256Bytes(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function sha256File(filePath) {
  return sha256Bytes(fs.readFileSync(filePath));
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

const projectDocument = readJson("project.json");
const contractDocument = readJson("language_contract.json");
const pilotMapDocument = readJson("catalog/pilot_translation_map.json");
const originalInventoryDocument = readJson("audit/original_inventory.json");
const integrityDocument = readJson("audit/original_integrity_recheck.json");
const pilotBundleDocument = readJson("audit/pilot_bundle_validation.json");
const project = projectDocument.value;
const contract = contractDocument.value;
const pilotMap = pilotMapDocument.value;
const originalInventory = originalInventoryDocument.value;
const integrity = integrityDocument.value;
const pilotBundle = pilotBundleDocument.value;

if (project.schema !== "contextual-game-localization.legacy-project.v1") {
  throw new Error(`Unexpected project.json schema: ${project.schema}`);
}
if (!samePath(project.game_root, forbiddenGameRoot)) {
  throw new Error("project.json does not identify the expected original game root");
}
if (
  project.game_root_policy !== "read_only_until_explicit_install" ||
  project.live_install_approved !== false ||
  project.patched_game_dir !== null
) {
  throw new Error("project.json does not preserve the required read-only/no-install state");
}
if (
  contract.schema !== "contextual-game-localization.language-contract.v1" ||
  contract.semantic_source?.locale !== "ja-JP" ||
  contract.target_language !== "ko-KR"
) {
  throw new Error("language_contract.json has an unexpected schema or language pair");
}
if (
  contract.translation_policy?.provider !== "Codex internal model" ||
  contract.translation_policy?.external_translation_api_allowed !== false ||
  contract.translation_policy?.generic_machine_translation_allowed !== false ||
  contract.translation_policy?.intermediate_language !== null
) {
  throw new Error("language_contract.json violates the approved direct Codex translation policy");
}

const replacementSlotApproved =
  contract.approval_status?.replacement_slot === true ||
  contract.replacement_slot !== null ||
  contract.status !== "pending_replacement_slot_approval";
if (replacementSlotApproved) {
  throw new Error(
    "This pre-approval metadata sync refuses to overwrite an approved or changed replacement-slot decision",
  );
}

if (
  pilotMap.schema !== "contextual-game-localization.translation-map.v1" ||
  pilotMap.status !== "pilot_frozen_after_independent_review" ||
  pilotMap.semantic_source_language !== "ja-JP" ||
  pilotMap.target_language !== "ko-KR" ||
  pilotMap.translation_provider !== "Codex internal model" ||
  pilotMap.intermediate_language !== null ||
  !Array.isArray(pilotMap.entries) ||
  !Number.isInteger(pilotMap.entry_count) ||
  pilotMap.entry_count !== pilotMap.entries.length
) {
  throw new Error("pilot_translation_map.json is missing, inconsistent, or not a frozen reviewed map");
}
const pilotMapSha256 = sha256File(pilotMapDocument.filePath);
if (
  originalInventory.schema !== "contextual-game-localization.original-inventory.v1" ||
  !samePath(originalInventory.game_root, forbiddenGameRoot) ||
  integrity.schema !== "contextual-game-localization.original-integrity-recheck.v1" ||
  !samePath(integrity.game_root, forbiddenGameRoot) ||
  integrity.inventory?.sha256 !== sha256File(originalInventoryDocument.filePath) ||
  integrity.missing_count !== 0 ||
  integrity.unexpected_count !== 0 ||
  integrity.hash_or_size_mismatch_count !== 0 ||
  integrity.original_game_modified !== false
) {
  throw new Error("Original-integrity evidence is missing, stale, or reports a source change");
}
if (
  pilotBundle.schema !== "contextual-game-localization.pilot-bundle-validation.v1" ||
  pilotBundle.translation?.map_sha256 !== pilotMapSha256 ||
  pilotBundle.language_contract?.replacement_slot_approved !== false ||
  pilotBundle.staged_runtime_asset_count !== 0 ||
  pilotBundle.runtime_assets_generated !== false ||
  pilotBundle.release_ready !== false
) {
  throw new Error("Pilot bundle does not preserve the pre-approval non-runtime state");
}

project.status = "discovery_and_reviewed_pilot_pending_replacement_slot_approval";
project.requested_delivery = "staged_trial_patch";
project.delivery_basis =
  "Proceed with a reversible staged trial patch only after replacement-slot approval; live-game installation has not been approved.";
project.live_install_approved = false;
project.original_game_modified = false;
project.runtime_assets_generated = false;
project.patched_game_dir = null;
project.launch_this_exe = null;
project.stage_gate =
  "Await explicit approval to replace the active Japanese runtime corpus in patched files.";
project.last_updated_utc = new Date().toISOString();
project.pilot = {
  translation_map: "catalog/pilot_translation_map.json",
  translation_map_sha256: pilotMapSha256,
  reviewed_translation_count: pilotMap.entry_count,
  semantic_source_language: pilotMap.semantic_source_language,
  target_language: pilotMap.target_language,
  translation_provider: pilotMap.translation_provider,
  runtime_asset_built: false,
};

contract.source_encoding =
  "CP932/Shift-JIS engine strings; alice-tools text interchange is UTF-8";
contract.target_encoding =
  "planned CP932 proxy codepoints with Korean glyphs injected into NightRemasterFont.fnl";
contract.selector = {
  mode: "single complete Japanese runtime corpus plus a small partial Jap/Eng embedded table",
  label: null,
};
contract.slot_audit = {
  complete_dialogue_and_scenario_slots: [
    {
      slot: "NightRemaster.ain message/string corpus",
      language: "ja-JP",
      completeness: "complete",
      replacement_candidate: true,
    },
  ],
  partial_embedded_tables: [
    {
      slot: "NightRemasterEX.ex::埋め込みテキスト.Jap",
      language: "ja-JP",
      completeness: "small generic/system subset",
    },
    {
      slot: "NightRemasterEX.ex::埋め込みテキスト.Eng",
      language: "en",
      completeness: "small generic/system subset; not a complete scenario language",
    },
  ],
  finding:
    "A complete simultaneous secondary-language slot was not found. A full Korean patch therefore needs an explicit decision to replace the active Japanese runtime corpus in patched files while preserving Japanese through untouched originals/restore media.",
};
contract.replacement_options = [
  {
    id: "replace_active_japanese_in_patch",
    description:
      "Recommended: Korean replaces the active Japanese runtime text in patched files; the trusted original Japanese files remain preserved separately and are restorable.",
  },
  {
    id: "stop_after_translation_assets",
    description:
      "Do not build runtime assets; deliver only translation maps and research artifacts.",
  },
];
contract.preservation_decision_status = "pending_user_replacement_slot_choice";
contract.status = "pending_replacement_slot_approval";

const pendingWrites = [
  {
    filePath: projectDocument.filePath,
    originalBytes: projectDocument.originalBytes,
    serialized: Buffer.from(`${JSON.stringify(project, null, 2)}\n`, "utf8"),
  },
  {
    filePath: contractDocument.filePath,
    originalBytes: contractDocument.originalBytes,
    serialized: Buffer.from(`${JSON.stringify(contract, null, 2)}\n`, "utf8"),
  },
];

const temporaryPaths = [];
try {
  // Prepare and verify every temporary file before replacing either metadata document.
  for (const item of pendingWrites) {
    JSON.parse(item.serialized.toString("utf8"));
    const temporaryPath =
      `${item.filePath}.${process.pid}.${crypto.randomBytes(8).toString("hex")}.tmp`;
    fs.writeFileSync(temporaryPath, item.serialized, {
      flag: "wx",
    });
    const temporaryBytes = fs.readFileSync(temporaryPath);
    if (
      temporaryBytes.length !== item.serialized.length ||
      sha256Bytes(temporaryBytes) !== sha256Bytes(item.serialized)
    ) {
      throw new Error(`Temporary metadata verification failed: ${item.filePath}`);
    }
    temporaryPaths.push(temporaryPath);
  }

  const mutatedIndexes = [];
  try {
    for (let index = 0; index < pendingWrites.length; index += 1) {
      // Unlink first rather than overwriting through a possible hard link or file reparse point.
      fs.rmSync(pendingWrites[index].filePath, { force: true });
      mutatedIndexes.push(index);
      fs.renameSync(temporaryPaths[index], pendingWrites[index].filePath);
    }
    for (const item of pendingWrites) {
      const writtenBytes = fs.readFileSync(item.filePath);
      JSON.parse(writtenBytes.toString("utf8"));
      if (
        writtenBytes.length !== item.serialized.length ||
        sha256Bytes(writtenBytes) !== sha256Bytes(item.serialized)
      ) {
        throw new Error(`Written metadata verification failed: ${item.filePath}`);
      }
    }
  } catch (writeError) {
    const rollbackErrors = [];
    for (const index of mutatedIndexes) {
      const item = pendingWrites[index];
      try {
        fs.rmSync(item.filePath, { force: true });
        fs.writeFileSync(item.filePath, item.originalBytes);
      } catch (rollbackError) {
        rollbackErrors.push(rollbackError);
      }
    }
    if (rollbackErrors.length > 0) {
      throw new AggregateError(
        [writeError, ...rollbackErrors],
        "Metadata update failed and rollback was incomplete",
      );
    }
    throw writeError;
  }
} finally {
  for (const temporaryPath of temporaryPaths) {
    fs.rmSync(temporaryPath, { force: true });
  }
}

process.stdout.write(
  `${JSON.stringify(
    {
      updated: [
        {
          path: projectDocument.filePath,
          sha256: sha256File(projectDocument.filePath),
        },
        {
          path: contractDocument.filePath,
          sha256: sha256File(contractDocument.filePath),
        },
      ],
      reviewed_translation_count: pilotMap.entry_count,
      original_game_modified: false,
      runtime_assets_generated: false,
      replacement_slot_approval: "pending",
    },
    null,
    2,
  )}\n`,
);
