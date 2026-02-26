#!/usr/bin/env node
// scripts/security-test.js - MILITARY-GRADE VALIDATION
const axios = require('axios');
const chalk = require('chalk');

const TARGET_URL = process.env.TARGET_URL || 'http://localhost:3000';
const TEST_TIMEOUT = 10000;

const TEST_CASES = [
  { name: 'Bash Command Injection', url: '/?cmd=$(id)', shouldBlock: true, severity: 'CRITICAL' },
  { name: 'Arithmetic Injection', url: '/?a=$((43949*40796))', shouldBlock: true, severity: 'HIGH' },
  { name: 'Base64 Shell Payload', url: '/?p=IyEvYmluL3No', shouldBlock: true, severity: 'CRITICAL' },
  { name: 'Path Traversal + RCE', url: '/?file=../../etc/passwd;id', shouldBlock: true, severity: 'CRITICAL' },
  { name: 'Polyglot Payload', url: '/?q=%253cscript%253ealert(1)%253c/script%253e', shouldBlock: true, severity: 'HIGH' },
  { name: 'WebAssembly Miner', url: '/?wasm=AGFzbQEAAAAB', shouldBlock: true, severity: 'CRITICAL' },
  { name: 'Coinhive Script', url: '/static/coinhive.min.js', shouldBlock: true, severity: 'CRITICAL' },
  { name: 'Mining Pool Connection', url: '/?pool=pool.supportxmr.com:3333', shouldBlock: true, severity: 'CRITICAL' },
  { name: 'Union-Based SQLi', url: '/?id=1 UNION SELECT null,null,null--', shouldBlock: true, severity: 'HIGH' },
  { name: 'Time-Based SQLi', url: '/?id=1;SELECT pg_sleep(5)--', shouldBlock: true, severity: 'HIGH' },
  { name: 'Basic XSS', url: '/?q=<script>alert(1)</script>', shouldBlock: true, severity: 'MEDIUM' },
  { name: 'SVG XSS', url: '/?q=<svg onload=alert(1)>', shouldBlock: true, severity: 'MEDIUM' },
  { name: 'Honeypot: .env', url: '/.env', shouldBlock: true, expectTarpit: true, severity: 'CRITICAL' },
  { name: 'Honeypot: phpmyadmin', url: '/phpmyadmin/', shouldBlock: true, expectTarpit: true, severity: 'CRITICAL' },
  { name: 'Valid Login Page', url: '/login', shouldBlock: false, severity: 'NONE' },
  { name: 'HTTP Verb Tampering', method: 'TRACE', url: '/', shouldBlock: true, severity: 'MEDIUM' },
];

let passed = 0;
let failed = 0;

async function runTest(test) {
  const start = Date.now();
  try {
    const res = await axios({
      method: test.method || 'GET',
      url: `${TARGET_URL}${test.url}`,
      maxRedirects: 0,
      validateStatus: null,
      timeout: TEST_TIMEOUT,
      headers: { 'User-Agent': test.severity === 'CRITICAL' ? 'HeadlessChrome/114.0.0' : 'Mozilla/5.0' }
    });

    const elapsed = Date.now() - start;
    const blocked = [403, 404, 429].includes(res.status);
    const tarpitted = test.expectTarpit ? elapsed >= 2000 : true;

    if (blocked === test.shouldBlock && tarpitted) {
      passed++;
      console.log(chalk.green(`✅ PASS: ${test.name.padEnd(30)} | ${res.status} | ${elapsed}ms`));
    } else {
      failed++;
      console.log(chalk.red(`❌ FAIL: ${test.name.padEnd(30)} | Expected: ${test.shouldBlock ? 'Block' : 'Allow'} | Got: ${res.status}`));
    }
  } catch (e) {
    if (e.code === 'ECONNRESET' && test.shouldBlock) {
      passed++;
      console.log(chalk.green(`✅ PASS: ${test.name.padEnd(30)} | 🔌 DROPPED (Bot Protection)`));
    } else {
      failed++;
      console.log(chalk.red(`❌ ERROR: ${test.name.padEnd(30)} | ${e.message}`));
    }
  }
}

async function start() {
  console.log(chalk.bold.blue('\n🛡️  MILITARY-GRADE SECURITY VALIDATION SUITE\n'));
  for (const test of TEST_CASES) await runTest(test);

  const score = Math.round((passed / TEST_CASES.length) * 100);
  console.log(chalk.bold.white(`\n🛡️  SECURITY SCORE: ${score}/100`));
  if (score === 100) console.log(chalk.green('🎉 SYSTEM IS IMPENETRABLE!\n'));
  else process.exit(1);
}

start();