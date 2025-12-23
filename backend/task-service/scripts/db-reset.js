#!/usr/bin/env node
// scripts/db-reset.js
// Run: node scripts/db-reset.js [--no-undo] [--skip-seed]

const { spawnSync } = require('child_process');

const args = process.argv.slice(2);
const noUndo = args.includes('--no-undo');
const skipSeed = args.includes('--skip-seed');

function run(cmd, args, options = {}) {
  console.log(`\n> ${[cmd].concat(args).join(' ')}\n`);
  const res = spawnSync(cmd, args, { stdio: 'inherit', shell: true, ...options });
  if (res.error) {
    console.error('Failed to run command', res.error);
    process.exit(res.status || 1);
  }
  if (res.status !== 0) {
    console.error(`Command exited with code ${res.status}`);
    process.exit(res.status);
  }
}

(async function main() {
  try {
    if (!noUndo) {
      run('npx', ['sequelize-cli', 'db:migrate:undo:all']);
    } else {
      console.log('Skipping undo:all step (--no-undo)');
    }

    run('npx', ['sequelize-cli', 'db:migrate']);

    if (!skipSeed) {
      run('npx', ['sequelize-cli', 'db:seed:all']);
    } else {
      console.log('Skipping seed step (--skip-seed)');
    }

    console.log('\nDatabase migration + seeding complete.');
  } catch (err) {
    console.error('Error during db-reset:', err);
    process.exit(1);
  }
})();
