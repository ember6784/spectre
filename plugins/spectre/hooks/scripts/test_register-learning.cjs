#!/usr/bin/env node
'use strict';

/**
 * Tests for register_learning.cjs
 *
 * Run with: node --test plugins/spectre/hooks/scripts/test_register-learning.cjs
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');

const SCRIPT_PATH = path.join(__dirname, 'register_learning.cjs');

function createTmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'spectre-rl-'));
}

function cleanup(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function runScript(args, opts) {
  opts = opts || {};
  const env = Object.assign({}, process.env);
  if (opts.pluginRoot) {
    env.CLAUDE_PLUGIN_ROOT = opts.pluginRoot;
  } else {
    delete env.CLAUDE_PLUGIN_ROOT;
  }

  try {
    const stdout = execFileSync(process.execPath, [SCRIPT_PATH, ...args], {
      env,
      timeout: 10000,
      encoding: 'utf8'
    });
    return { stdout, exitCode: 0 };
  } catch (err) {
    return { stdout: err.stdout || '', stderr: err.stderr || '', exitCode: err.status };
  }
}

describe('register_learning', () => {
  it('creates new registry with entry', () => {
    const tmp = createTmpDir();
    try {
      const result = runScript([
        '--project-root', tmp,
        '--skill-name', 'feature-auth',
        '--category', 'feature',
        '--triggers', 'auth, login',
        '--description', 'Use when working on authentication'
      ]);

      assert.equal(result.exitCode, 0);
      assert.ok(result.stdout.includes('Registered:'));

      const registryPath = path.join(tmp, '.claude', 'skills', 'spectre-recall', 'references', 'registry.toon');
      assert.ok(fs.existsSync(registryPath));

      const content = fs.readFileSync(registryPath, 'utf8');
      assert.ok(content.includes('# SPECTRE Knowledge Registry'));
      assert.ok(content.includes('feature-auth|feature|auth, login|Use when working on authentication'));
    } finally {
      cleanup(tmp);
    }
  });

  it('updates existing entry by skill name', () => {
    const tmp = createTmpDir();
    try {
      // First registration
      runScript([
        '--project-root', tmp,
        '--skill-name', 'feature-auth',
        '--category', 'feature',
        '--triggers', 'auth',
        '--description', 'Old description'
      ]);

      // Second registration with same skill name
      runScript([
        '--project-root', tmp,
        '--skill-name', 'feature-auth',
        '--category', 'feature',
        '--triggers', 'auth, login, oauth',
        '--description', 'Updated description'
      ]);

      const registryPath = path.join(tmp, '.claude', 'skills', 'spectre-recall', 'references', 'registry.toon');
      const content = fs.readFileSync(registryPath, 'utf8');

      // Should have the updated entry, not the old one
      assert.ok(content.includes('Updated description'));
      assert.ok(!content.includes('Old description'));

      // Should only have one entry for feature-auth
      const entries = content.split('\n').filter(l => l.startsWith('feature-auth|'));
      assert.equal(entries.length, 1);
    } finally {
      cleanup(tmp);
    }
  });

  it('generates recall skill with template', () => {
    const tmp = createTmpDir();
    const pluginRoot = path.join(tmp, 'plugin');

    // Create template
    const templateDir = path.join(pluginRoot, 'skills', 'spectre-learn', 'references');
    fs.mkdirSync(templateDir, { recursive: true });
    fs.writeFileSync(
      path.join(templateDir, 'recall-template.md'),
      '# Recall Skill\n\nRegistry:\n{{REGISTRY}}\n\nEnd.\n'
    );

    try {
      runScript([
        '--project-root', tmp,
        '--skill-name', 'feature-test',
        '--category', 'feature',
        '--triggers', 'test',
        '--description', 'Test skill'
      ], { pluginRoot });

      const skillPath = path.join(tmp, '.claude', 'skills', 'spectre-recall', 'SKILL.md');
      assert.ok(fs.existsSync(skillPath));

      const content = fs.readFileSync(skillPath, 'utf8');
      assert.ok(content.includes('# Recall Skill'));
      assert.ok(content.includes('feature-test|feature|test|Test skill'));
    } finally {
      cleanup(tmp);
    }
  });

  it('fails with missing required arguments', () => {
    const result = runScript(['--project-root', '/tmp/fake']);
    assert.notEqual(result.exitCode, 0);
  });
});
