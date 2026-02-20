#!/usr/bin/env node
'use strict';

/**
 * register_learning.cjs
 *
 * Registers a spectre learning and manages the project-level recall skill.
 *
 * Responsibilities:
 * 1. Create/update registry at .claude/skills/spectre-recall/references/registry.toon
 * 2. Read recall-template.md from plugin
 * 3. Generate .claude/skills/spectre-recall/SKILL.md with embedded registry
 *
 * Usage:
 *   node register_learning.cjs \
 *     --project-root "/path/to/project" \
 *     --skill-name "feature-my-feature" \
 *     --category "feature" \
 *     --triggers "keyword1, keyword2" \
 *     --description "Use when doing X or Y"
 */

const fs = require('fs');
const path = require('path');

function getRegistryHeader() {
  return [
    '# SPECTRE Knowledge Registry',
    '# Format: skill-name|category|triggers|description',
    ''
  ];
}

function updateRegistry(registryPath, entry, skillName) {
  const entryPrefix = skillName + '|';
  let lines;

  if (fs.existsSync(registryPath)) {
    const content = fs.readFileSync(registryPath, 'utf8').trim();
    lines = content ? content.split('\n') : [];
  } else {
    lines = getRegistryHeader();
  }

  let entryExists = false;
  const updatedLines = [];

  for (const line of lines) {
    if (line.startsWith(entryPrefix)) {
      updatedLines.push(entry);
      entryExists = true;
    } else {
      updatedLines.push(line);
    }
  }

  if (!entryExists) {
    updatedLines.push(entry);
  }

  let content = updatedLines.join('\n');
  if (!content.endsWith('\n')) {
    content += '\n';
  }

  fs.writeFileSync(registryPath, content);
  return content;
}

function generateFindSkill(findSkillPath, templatePath, registryContent) {
  if (!fs.existsSync(templatePath)) {
    process.stderr.write(`Warning: Template not found at ${templatePath}\n`);
    return;
  }

  const template = fs.readFileSync(templatePath, 'utf8');
  const skillContent = template.replace('{{REGISTRY}}', registryContent.trim());

  fs.mkdirSync(path.dirname(findSkillPath), { recursive: true });
  fs.writeFileSync(findSkillPath, skillContent);
}

function parseArgs(argv) {
  const args = {};
  const flags = ['--project-root', '--skill-name', '--category', '--triggers', '--description'];

  for (let i = 0; i < argv.length; i++) {
    if (flags.includes(argv[i]) && i + 1 < argv.length) {
      // Convert --project-root to projectRoot
      const key = argv[i].slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      args[key] = argv[i + 1];
      i++;
    }
  }

  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  const required = ['projectRoot', 'skillName', 'category', 'triggers', 'description'];
  for (const key of required) {
    if (!args[key]) {
      process.stderr.write(`Error: missing required argument --${key.replace(/[A-Z]/g, c => '-' + c.toLowerCase())}\n`);
      process.exit(1);
    }
  }

  const projectRoot = args.projectRoot;

  // New paths: registry lives inside spectre-recall skill
  const recallDir = path.join(projectRoot, '.claude', 'skills', 'spectre-recall');
  const registryDir = path.join(recallDir, 'references');
  const registryPath = path.join(registryDir, 'registry.toon');
  const recallSkillPath = path.join(recallDir, 'SKILL.md');

  // Template is in the plugin — resolve via env var (hooks) or __filename (manual invocation)
  let pluginRoot;
  if (process.env.CLAUDE_PLUGIN_ROOT) {
    pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;
  } else {
    // Fallback: resolve relative to this script
    // Script is at: <plugin_root>/hooks/scripts/register_learning.cjs
    pluginRoot = path.resolve(__dirname, '..', '..');
  }
  const templatePath = path.join(pluginRoot, 'skills', 'spectre-learn', 'references', 'recall-template.md');

  // Ensure directories exist
  fs.mkdirSync(registryDir, { recursive: true });

  // Build the registry entry
  const entry = `${args.skillName}|${args.category}|${args.triggers}|${args.description}`;

  // Update registry and get full content
  const registryContent = updateRegistry(registryPath, entry, args.skillName);

  // Generate recall skill with embedded registry
  generateFindSkill(recallSkillPath, templatePath, registryContent);

  process.stdout.write(`Registered: ${entry}\n`);
}

main();
