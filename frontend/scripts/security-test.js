#!/usr/bin/env node
// frontend/scripts/security-test.js
// ════════════════════════════════════════════════════════════════════════════════
// MILITARY-GRADE SECURITY VALIDATION SUITE v3.0
// ════════════════════════════════════════════════════════════════════════════════

const axios = require('axios');
const chalk = require('chalk');
const { createWriteStream } = require('fs');

const TARGET_URL = process.env.TARGET_URL || 'http://localhost:3000';
const TEST_TIMEOUT = 10000;
const LOG_FILE = 'security-test.log';
const logStream = createWriteStream(LOG_FILE, { flags: 'a' });

const TEST_CASES = [
  { name: 'Bash Command Injection', url: '/?cmd=$(id)', shouldBlock: true, severity: 'CRITICAL', category: 'RCE' },
  { name: 'Arithmetic Injection', url: '/?a=$((43949*40796))', shouldBlock: true, severity: 'HIGH', category: 'RCE' },
  { name: 'Base64 Shell Payload', url: '/?p=IyEvYmluL3No', shouldBlock: true, severity: 'CRITICAL', category: 'RCE' },
  { name: 'Path Traversal + RCE', url: '/?file=../../etc/passwd;id', shouldBlock: true, severity: 'CRITICAL', category: 'RCE' },
  { name: 'Polyglot Payload', url: '/?q=%253cscript%253ealert(1)%253c/script%253e', shouldBlock: true, severity: 'HIGH', category: 'RCE' },
  { name: 'Obfuscated Command', url: '/?c=$%7B7*7%7D', shouldBlock: true, severity: 'HIGH', category: 'RCE' },
  { name: 'WebAssembly Miner', url: '/?wasm=AGFzbQEAAAAB', shouldBlock: true, severity: 'CRITICAL', category: 'CRYPTO', expectTarpit: true },
  { name: 'Coinhive Script', url: '/static/coinhive.min.js', shouldBlock: true, severity: 'CRITICAL', category: 'CRYPTO', expectTarpit: true },
  { name: 'WebWorker Miner', url: '/worker.js', shouldBlock: true, severity: 'CRITICAL', category: 'CRYPTO', expectTarpit: true },
  { name: 'Mining Pool Connection', url: '/?pool=pool.supportxmr.com:3333', shouldBlock: true, severity: 'CRITICAL', category: 'CRYPTO' },
  { name: 'XMRig Payload', url: '/?payload=44hdm7jN3TcBt2J6ZsQcGx6rQxH6Qq6J6X6X6X6X6X6', shouldBlock: true, severity: 'CRITICAL', category: 'CRYPTO' },
  { name: 'Union-Based SQLi', url: '/?id=1 UNION SELECT null,null,null--', shouldBlock: true, severity: 'HIGH', category: 'SQLI' },
  { name: 'Time-Based SQLi', url: '/?id=1;SELECT pg_sleep(5)--', shouldBlock: true, severity: 'HIGH', category: 'SQLI' },
  { name: 'Boolean-Based SQLi', url: '/?id=1\' AND \'1\'=\'1', shouldBlock: true, severity: 'MEDIUM', category: 'SQLI' },
  { name: 'Basic XSS', url: '/?q=<script>alert(1)</script>', shouldBlock: true, severity: 'MEDIUM', category: 'XSS' },
  { name: 'SVG XSS', url: '/?q=<svg onload=alert(1)>', shouldBlock: true, severity: 'MEDIUM', category: 'XSS' },
  { name: 'DOM XSS', url: '/#<img src=x onerror=alert(1)>', shouldBlock: true, severity: 'MEDIUM', category: 'XSS' },
  { name: 'Encoded XSS', url: '/?q=%3Cscript%3Ealert(1)%3C/script%3E', shouldBlock: true, severity: 'MEDIUM', category: 'XSS' },
  { name: 'Honeypot: .env', url: '/.env', shouldBlock: true, severity: 'CRITICAL', category: 'HONEYPOT', expectTarpit: true },
  { name: 'Honeypot: phpmyadmin', url: '/phpmyadmin/', shouldBlock: true, severity: 'CRITICAL', category: 'HONEYPOT', expectTarpit: true },
  { name: 'Honeypot: admin.php', url: '/admin.php', shouldBlock: true, severity: 'CRITICAL', category: 'HONEYPOT', expectTarpit: true },
  { name: 'Honeypot: actuator/env', url: '/actuator/env', shouldBlock: true, severity: 'CRITICAL', category: 'HONEYPOT', expectTarpit: true },
  { name: 'Basic Path Traversal', url: '/?file=../../etc/passwd', shouldBlock: true, severity: 'HIGH', category: 'TRAVERSAL' },
  { name: 'URL-Encoded Traversal', url: '/?f=%2e%2e%2f%2e%2e%2fetc%2fpasswd', shouldBlock: true, severity: 'HIGH', category: 'TRAVERSAL' },
  { name: 'Valid Login Page', url: '/login', shouldBlock: false, severity: 'NONE', category: 'VALID' },
  { name: 'Valid API Endpoint', url: '/api/health', shouldBlock: false, severity: 'NONE', category: 'VALID' },
  { name: 'Static Asset', url: '/_next/static/chunks/main.js', shouldBlock: false, severity: 'NONE', category: 'VALID' },
  { name: 'HTTP Verb Tampering', method: 'TRACE', url: '/', shouldBlock: true, severity: 'MEDIUM', category: 'MISC' },
  { name: 'Mass Assignment', url: '/?admin=true&role=admin', shouldBlock: true, severity: 'HIGH', category: 'MISC' },
  { name: 'SSRF Attempt', url: '/?url=http://169.254.169.254/latest/meta-data', shouldBlock: true, severity: 'CRITICAL', category: 'MISC' },
  { name: 'High Entropy Payload', url: '/?p=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', shouldBlock: true, severity: 'CRITICAL', category: 'MISC' },
];

let passed = 0;
let failed = 0;
let errors = 0;
const startTime = Date.now();

async function runSecurityTests() {
  console.log(chalk.bold.blue('\n🛡️  MILITARY-GRADE SECURITY VALIDATION SUITE v3.0'));

  try {
    await axios.get(`${TARGET_URL}/login`, {
      timeout: TEST_TIMEOUT,
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    console.log(chalk.green('✅ Server warm-up successful\n'));
  } catch (e) {
    console.log(chalk.red('❌ Server unavailable. Is it running?'));
    process.exit(1);
  }

  for (let i = 0; i < TEST_CASES.length; i++) {
    const test = TEST_CASES[i];
    await runTest(test);
  }

  const duration = Date.now() - startTime;
  const score = Math.round((passed / TEST_CASES.length) * 100);

  console.log(chalk.bold.blue('\n' + '='.repeat(70)));
  console.log(chalk.bold.white(`🛡️  SECURITY VALIDATION REPORT - SCORE: ${score}/100`));
  console.log(chalk.bold.blue('='.repeat(70)));
  console.log(chalk.green(`✅ PASSED:  ${passed}/${TEST_CASES.length}`));
  console.log(chalk.red(`❌ FAILED:  ${failed}/${TEST_CASES.length}`));

  if (score >= 98) console.log(chalk.green('\n🎉 EXCELLENT: System is immune to all tested attacks!'));
  else process.exit(1);
}

async function runTest(test) {
  const start = Date.now();
  let status = 'UNKNOWN';
  let blocked = false;
  let tarpitted = false;

  try {
    const res = await axios({
      method: test.method || 'GET', url: `${TARGET_URL}${test.url}`, maxRedirects: 0, validateStatus: null, timeout: TEST_TIMEOUT,
      headers: { 'User-Agent': test.severity === 'CRITICAL' ? 'HeadlessChrome/114.0.0.0' : 'Mozilla/5.0' }
    });

    blocked = [403, 404, 429, 444].includes(res.status);
    tarpitted = test.expectTarpit ? (Date.now() - start) >= 2000 : true;

    if (blocked === test.shouldBlock && tarpitted) { status = 'PASS'; passed++; }
    else { status = 'FAIL'; failed++; }
  } catch (e) {
    if (e.code === 'ECONNRESET' && test.shouldBlock) { status = 'PASS'; passed++; }
    else { status = 'ERROR'; errors++; }
  }

  const color = status === 'PASS' ? chalk.green : chalk.red;
  console.log(color(`${status === 'PASS' ? '✅' : '❌'} ${test.name.padEnd(35)} | ${status}`));
}

runSecurityTests().catch(() => process.exit(1));