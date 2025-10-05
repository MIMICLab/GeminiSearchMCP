#!/usr/bin/env node

const { spawn } = require('child_process');

const pythonCmds = [process.env.PYTHON, 'python3', 'python'].filter(Boolean);
const moduleName = 'gemini_search_mcp';

function run(idx) {
  if (idx >= pythonCmds.length) {
    console.error('Unable to locate Python interpreter. Set the PYTHON environment variable.');
    process.exit(1);
    return;
  }

  const cmd = pythonCmds[idx];
  const args = ['-m', moduleName, ...process.argv.slice(2)];
  const child = spawn(cmd, args, { stdio: 'inherit' });

  child.on('error', () => run(idx + 1));
  child.on('exit', (code) => process.exit(code ?? 0));
}

run(0);
