// frontend/lib/security/constants.ts
export const SECURITY_SECRET = process.env.SECURITY_SECRET || 'change-this-in-production-2024-uznpu';
export const SECURITY_WEBHOOK = process.env.SECURITY_WEBHOOK;

export const MALICIOUS_IPS = new Set([
  '147.45.41.25', '139.59.136.184', '45.155.205.233', '185.180.143.81', '91.240.118.222',
  '185.180.143.45', '45.95.168.112', '194.36.191.130', '144.76.140.212', '51.159.11.14',
  '193.201.224.15', '45.155.205.88', '185.180.143.112', '91.240.118.55', '103.152.112.165',
  '128.199.182.55' // Keshagi skaner
]);

export const BLOCKED_COUNTRIES = new Set([
  'RU', 'CN', 'KP', 'IR', 'SY', 'CU', 'IQ', 'LB', 'PK', 'VN',
  'MD', 'RO', 'BG', 'UA', 'BY', 'AM', 'GE', 'KZ', 'NG', 'KE', 'ZA', 'GH', 'TZ'
]);

export const IP_TO_COUNTRY: Record<string, string> = {
  '147.45.41.25': 'RU', '139.59.136.184': 'IN', '45.155.205.233': 'NL',
  '128.199.182.55': 'SG'
};

export const HONEYPOTS = [
  '/.well-known/miner.js', '/static/worker.js', '/assets/crypto.js', '/lib/webminer.js',
  '/dist/coinhive.js', '/js/monero.js', '/webassembly/worker.wasm',
  '/admin.php', '/wp-config.php', '/.env.backup', '/backup.zip', '/debug.php',
  '/test.php', '/shell.php', '/wp-login.php', '/xmlrpc.php',
  '/api/v1/miner', '/api/v2/crypto', '/graphql?query={__schema',
  '/.git/HEAD', '/.svn/entries', '/.DS_Store', '/.ds_store',
  '/phpmyadmin/', '/adminer.php', '/pma/', '/mysql/',
  '/actuator/env', '/actuator/health', '/_ignition/execute-solution', '/telescope/requests'
];

export const PATTERNS = {
  rce: [
    /\$\(.*\)/, /\$\{.*\}/, /`[^`]*`/,
    /;[\s]*(sh|bash|zsh|dash|ksh|nc|wget|curl|python|perl|ruby|php|node)/i,
    /&[\s]*(sh|bash|zsh|dash|ksh|nc|wget|curl)/i, /\|[\s]*(sh|bash|zsh|dash|ksh|nc|wget|curl)/i,
    /[\s](exec|eval|system|passthru|shell_exec|popen|pcntl_exec)[\s(]/i,
    { pattern: /IyEvYmluL3No/, entropy: 4.2 },
    { pattern: /L2Jpbi9zaA==/, entropy: 4.5 },
    { pattern: /[A-Za-z0-9+/]{80,}/, entropy: 5.8 } // High Entropy Base64
  ],
  sqli: [
    /(['"]\s*(or|and)\s+['"]1['"]\s*=\s*['"]1)/i, /union\s+select/i, /sleep\(\d+\)/i,
    /;.*--/, /;.*#/, /\/\*.*\*\//, /pg_sleep\(/i
  ],
  xss: [
    /<script.*?>/i, /javascript:/i, /data:text\/html/i, /vbscript:/i,
    /on(error|load|click|mouseover)=/i, /<svg.*onload=/i
  ],
  traversal: [
    /\.\.\/.*\.(sh|py|pl|rb|php|exe|js|wasm|jsp)/i,
    /%2e%2e[%2f|\\].*\.(sh|py|pl|rb|php|exe)/i,
    /\/etc\/passwd/i, /\/windows\/win\.ini/i
  ],
  miner: [
    /WebAssembly\.instantiate/i, /CoinHive/i, /CryptoLoot/i, /WebMiner/i,
    /monero-miner/i, /xmrig/i, /cryptonight/i, /stratum\+tcp/i
  ]
};

export const MINER_FINGERPRINTS = [
  /HeadlessChrome/i, /PhantomJS/i, /puppeteer/i, /selenium/i,
  /CanvasRenderingContext2D.*toDataURL.*application\/x-font/i
];

export const MAX_URL_LENGTH = 1024;
export const MAX_QUERY_LENGTH = 512;
export const BASE_RATE_LIMIT = 60;
export const WINDOW_MS = 60000;
export const ALLOWED_HOSTS = ['davomat.uznpu.uz', 'api.davomat.uznpu.uz', 'localhost:3000', '127.0.0.1:3000', 'ca0336001e9f:3000'];
export const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'];