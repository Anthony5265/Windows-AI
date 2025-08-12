const fs = require('fs');
const path = require('path');
const arg = process.argv[2] || '';
const out = arg === 'agent' ? 'windows-ai-agent/dist' : 'windows-ai-tray/dist';
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'README.txt'), 'Build artifacts will live here.');
console.log('Created', out);
