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
  if (!version || version === 'unknown') return version;
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
      // Fall back to marketplace version if plugin.json lacks version
      plugin.version = data.version || plugin.marketplaceEntry.version;
      plugin.data = data;
    } catch (e) {
      console.error(`Warning: Could not read ${plugin.path}`);
      plugin.version = plugin.marketplaceEntry.version || 'unknown';
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

  // Ask version bump for each selected plugin
  const askBumpType = async (name, currentVersion) => {
    console.log(`\n${name} (${currentVersion}):`);
    console.log(`  1. patch → ${bumpVersion(currentVersion, 'patch')}`);
    console.log(`  2. minor → ${bumpVersion(currentVersion, 'minor')}`);
    console.log(`  3. major → ${bumpVersion(currentVersion, 'major')}`);
    console.log(`  4. skip (no change)`);

    const choice = await ask('Choice [1]: ');
    const type = { '1': 'patch', '2': 'minor', '3': 'major', '4': 'skip' }[choice.trim() || '1'] || 'patch';
    return type === 'skip' ? null : bumpVersion(currentVersion, type);
  };

  // Collect version bumps per plugin
  console.log('\n--- Plugin Version Bumps ---');
  for (const plugin of selectedPlugins) {
    plugin.newVersion = await askBumpType(plugin.name, plugin.version);
  }

  // Ask for marketplace version separately
  console.log('\n--- Marketplace Version ---');
  const marketplaceNewVersion = await askBumpType('marketplace', marketplace.version);

  // Show summary
  console.log('\n--- Release Summary ---');
  let hasChanges = false;
  for (const plugin of selectedPlugins) {
    if (plugin.newVersion) {
      console.log(`  ${plugin.name}: ${plugin.version} → ${plugin.newVersion}`);
      hasChanges = true;
    } else {
      console.log(`  ${plugin.name}: (skip)`);
    }
  }
  if (marketplaceNewVersion) {
    console.log(`  marketplace: ${marketplace.version} → ${marketplaceNewVersion}`);
    hasChanges = true;
  } else {
    console.log(`  marketplace: (skip)`);
  }

  if (!hasChanges) {
    console.log('\nNo changes selected. Exiting.');
    rl.close();
    process.exit(0);
  }

  // Confirm
  const confirm = await ask('\nProceed with release? [Y/n]: ');
  if (confirm.toLowerCase() === 'n') {
    console.log('Aborted.');
    rl.close();
    process.exit(0);
  }

  // Update plugin files
  console.log('\nUpdating version files...');

  for (const plugin of selectedPlugins) {
    if (plugin.newVersion && plugin.data) {
      plugin.data.version = plugin.newVersion;
      writeJSON(plugin.path, plugin.data);
      console.log(`  ✓ ${pluginRoot}/${plugin.name}/plugin.json → ${plugin.newVersion}`);
    }
  }

  // Update marketplace
  if (marketplaceNewVersion) {
    marketplace.version = marketplaceNewVersion;
  }
  for (const plugin of selectedPlugins) {
    if (plugin.newVersion) {
      const entry = marketplace.plugins.find((p) => p.name === plugin.name);
      if (entry) entry.version = plugin.newVersion;
    }
  }
  writeJSON(MARKETPLACE_PATH, marketplace);
  console.log(`  ✓ .claude-plugin/marketplace.json`);

  // Git operations
  console.log('\nGit operations...');

  // Build version string for commit/tag (use marketplace version, or highest plugin version)
  const releaseVersion = marketplaceNewVersion ||
    selectedPlugins.map((p) => p.newVersion).filter(Boolean).sort().pop();
  const commitMsg = `release: v${releaseVersion}`;
  const tagName = `v${releaseVersion}`;

  run('git add -A');
  run(`git commit -m "${commitMsg}"`);

  const pushConfirm = await ask('\nPush to remote and create tag? [Y/n]: ');
  if (pushConfirm.toLowerCase() !== 'n') {
    run('git push');
    run(`git tag ${tagName}`);
    run('git push --tags');
    console.log(`\n✅ Released ${tagName}`);
  } else {
    console.log(`\n✅ Committed locally as ${tagName} (not pushed)`);
  }

  rl.close();
}

main().catch((err) => {
  console.error(err);
  rl.close();
  process.exit(1);
});
