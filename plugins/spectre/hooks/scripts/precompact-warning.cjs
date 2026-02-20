#!/usr/bin/env node
'use strict';

/**
 * precompact-warning.cjs
 *
 * PreCompact hook that suggests using /spectre:handoff + /clear
 * instead of auto-compact for better context continuity.
 */

const output = {
  systemMessage:
    '\u26a0\ufe0f Auto-compact can cause context loss. ' +
    'For full continuity: /spectre:handoff \u2192 /clear \u2192 new session. ' +
    'Consider disabling auto-compact in /config.'
};

process.stdout.write(JSON.stringify(output) + '\n');
process.exit(0);
