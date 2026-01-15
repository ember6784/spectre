#!/usr/bin/env node

import { createInterface } from 'readline';
import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const MARKETPLACE_PATH = join(ROOT, '.claude-plugin/marketplace.json');

const rl = createInterface({
  input: process.stdin,
  output: process.stdout,
});

const ask = (q) => new Promise((resolve) => rl.question(q, resolve));

const readJSON = (path) => JSON.parse(readFileSync(path, 'utf8'));
const writeJSON = (path, data) => writeFileSync(path, JSON.stringify(data, null, 2) + '\n');

const bumpVersion = (version, type) => {
  const [major, minor, patch] = version.split('.').map(Number);
  switch (type) {
    case 'major': return `${major + 1}.0.0`;
    case 'minor': return `${major}.${minor + 1}.0`;
    case 'patch': return `${major}.${minor}.${patch + 1}`;
    default: return version;
  }
};

const run = (cmd) => {
  console.log(`\n$ ${cmd}`);
  try {
    execSync(cmd, { stdio: 'inherit', cwd: ROOT });
    return true;
  } catch (e) {
    console.error(`Command failed: ${cmd}`);
    return false;
  }
};

async function main() {
  console.log('\n🚀 SPECTRE Release Script\n');

  // Read marketplace to discover plugins
  const marketplace = readJSON(MARKETPLACE_PATH);
  const pluginRoot = marketplace.metadata?.pluginRoot || './plugins';

  // Build plugin info from marketplace
  const plugins = marketplace.plugins.map((p) => ({
    name: p.name,
    path: join(ROOT, pluginRoot, p.name, 'plugin.json'),
    marketplaceEntry: p,
  }));

  // Read current versions from each plugin
  for (const plugin of plugins) {
    try {
      const data = readJSON(plugin.path);
      plugin.version = data.version;
      plugin.data = data;
    } catch (e) {
      console.error(`Warning: Could not read ${plugin.path}`);
      plugin.version = 'unknown';
    }
  }

  // Display current versions
  console.log('Current versions:');
  const maxNameLen = Math.max(...plugins.map((p) => p.name.length));
  for (const plugin of plugins) {
    console.log(`  ${plugin.name.padEnd(maxNameLen)}  ${plugin.version}`);
  }
  console.log(`  ${'marketplace'.padEnd(maxNameLen)}  ${marketplace.version}\n`);

  // Build plugin selection menu
  console.log('Which plugin(s) to release?');
  plugins.forEach((p, i) => {
    console.log(`  ${i + 1}. ${p.name} only`);
  });
  const allOption = plugins.length + 1;
  console.log(`  ${allOption}. all (recommended)\n`);

  const pluginChoice = await ask(`Choice [${allOption}]: `);
  const choice = parseInt(pluginChoice.trim() || String(allOption), 10);

  let selectedPlugins;
  if (choice === allOption) {
    selectedPlugins = plugins;
  } else if (choice >= 1 && choice <= plugins.length) {
    selectedPlugins = [plugins[choice - 1]];
  } else {
    console.log('Invalid choice. Exiting.');
    rl.close();
    process.exit(1);
  }

  // Choose version bump type (use first selected plugin's version as reference)
  const currentVersion = selectedPlugins[0].version;
  console.log(`\nVersion bump type for ${currentVersion}:`);
  console.log(`  1. patch → ${bumpVersion(currentVersion, 'patch')}`);
  console.log(`  2. minor → ${bumpVersion(currentVersion, 'minor')}`);
  console.log(`  3. major → ${bumpVersion(currentVersion, 'major')}\n`);

  const bumpChoice = await ask('Choice [1]: ');
  const bumpType = { '1': 'patch', '2': 'minor', '3': 'major' }[bumpChoice.trim() || '1'] || 'patch';
  const newVersion = bumpVersion(currentVersion, bumpType);

  console.log(`\nNew version: ${newVersion}`);
  console.log(`Updating: ${selectedPlugins.map((p) => p.name).join(', ')}`);

  // Confirm
  const confirm = await ask('\nProceed with release? [Y/n]: ');
  if (confirm.toLowerCase() === 'n') {
    console.log('Aborted.');
    rl.close();
    process.exit(0);
  }

  // Update plugin files
  console.log('\nUpdating version files...');

  const selectedNames = new Set(selectedPlugins.map((p) => p.name));

  for (const plugin of selectedPlugins) {
    if (plugin.data) {
      plugin.data.version = newVersion;
      writeJSON(plugin.path, plugin.data);
      console.log(`  ✓ ${pluginRoot}/${plugin.name}/plugin.json → ${newVersion}`);
    }
  }

  // Update marketplace
  marketplace.version = newVersion;
  for (const plugin of marketplace.plugins) {
    if (selectedNames.has(plugin.name)) {
      plugin.version = newVersion;
    }
  }
  writeJSON(MARKETPLACE_PATH, marketplace);
  console.log(`  ✓ .claude-plugin/marketplace.json → ${newVersion}`);

  // Git operations
  console.log('\nGit operations...');

  const commitMsg = `release: v${newVersion}`;
  const tagName = `v${newVersion}`;

  run('git add -A');
  run(`git commit -m "${commitMsg}"`);

  const pushConfirm = await ask('\nPush to remote and create tag? [Y/n]: ');
  if (pushConfirm.toLowerCase() !== 'n') {
    run('git push');
    run(`git tag ${tagName}`);
    run('git push --tags');
    console.log(`\n✅ Released v${newVersion}`);
  } else {
    console.log(`\n✅ Committed locally as v${newVersion} (not pushed)`);
  }

  rl.close();
}

main().catch((err) => {
  console.error(err);
  rl.close();
  process.exit(1);
});
