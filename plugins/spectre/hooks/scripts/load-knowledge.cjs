#!/usr/bin/env node
'use strict';

/**
 * load-knowledge.cjs
 *
 * SessionStart hook that injects the apply skill content with embedded registry
 * directly into Claude's context.
 *
 * Reads:
 * - Apply skill from plugin: skills/spectre-apply/SKILL.md
 * - Registry from project: .claude/skills/spectre-recall/references/registry.toon
 *
 * Combines them by replacing the Registry Location section with actual registry content.
 */

const fs = require('fs');
const path = require('path');

function countRegistryEntries(lines) {
  let count = 0;
  for (const line of lines) {
    if (line.trim() && line.includes('|') && !line.startsWith('#')) {
      count++;
    }
  }
  return count;
}

function stripFrontmatter(content) {
  if (content.startsWith('---')) {
    const end = content.indexOf('---', 3);
    if (end !== -1) {
      return content.slice(end + 3).trim();
    }
  }
  return content;
}

function main() {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || '';

  const applySkillPath = path.join(pluginRoot, 'skills', 'spectre-apply', 'SKILL.md');

  if (!fs.existsSync(applySkillPath)) {
    process.exit(0);
  }

  // Paths - check new name first, fall back to old names for migration
  let registryPath = path.join(projectDir, '.claude', 'skills', 'spectre-recall', 'references', 'registry.toon');
  const oldRegistryPath = path.join(projectDir, '.claude', 'skills', 'spectre-find', 'references', 'registry.toon');

  // Support old "spectre-find" path for projects that haven't migrated
  if (!fs.existsSync(registryPath) && fs.existsSync(oldRegistryPath)) {
    registryPath = oldRegistryPath;
  }

  // Read registry if it exists
  let registryContent = '';
  let entryCount = 0;
  if (fs.existsSync(registryPath)) {
    registryContent = fs.readFileSync(registryPath, 'utf8').trim();
    const lines = registryContent ? registryContent.split('\n') : [];
    entryCount = countRegistryEntries(lines);
  }

  // Read apply skill and strip frontmatter
  let applyContent = fs.readFileSync(applySkillPath, 'utf8');
  applyContent = stripFrontmatter(applyContent);

  // Replace the Registry Location section with embedded registry or empty notice
  let registrySection;
  if (entryCount > 0) {
    registrySection =
      '## Registry\n\n' +
      '**Format**: `skill-name|category|triggers|description`\n\n' +
      '```\n' +
      registryContent + '\n' +
      '```\n\n' +
      'Each entry corresponds to a skill that can be loaded via `Skill({skill-name})`\n\n' +
      '**Categories:** feature, gotchas, patterns, decisions, procedures, integration, performance, testing, ux, strategy';
  } else {
    registrySection =
      '## Registry\n\n' +
      'No knowledge has been captured for this project yet. The behavioral rules in this document still apply.\n\n' +
      'To capture knowledge from this session, use `/spectre:learn` after completing significant work.\n\n' +
      '**Categories:** feature, gotchas, patterns, decisions, procedures, integration, performance, testing, ux, strategy';
  }

  // Replace the Registry Location section
  applyContent = applyContent.replace(
    /## Registry Location[\s\S]*?(?=## Workflow)/,
    registrySection + '\n\n'
  );

  // Build final context
  const context = `<spectre-knowledge>\n${applyContent}\n</spectre-knowledge>`;

  // Visible notice
  let visibleNotice;
  if (entryCount > 0) {
    visibleNotice = `\ud83d\udc7b spectre: ${entryCount} knowledge skills available`;
  } else {
    visibleNotice = '\ud83d\udc7b spectre: ready \u2014 capture knowledge with /spectre:learn';
  }

  const output = {
    systemMessage: visibleNotice,
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: context
    }
  };

  process.stdout.write(JSON.stringify(output) + '\n');
  process.exit(0);
}

main();
