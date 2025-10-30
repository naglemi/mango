import { spawn } from 'child_process';

console.log('Testing MCP server...');

const server = spawn('node', ['index.js'], {
  cwd: '/Users/michaelnagle/code/usability/mcp/report',
  env: {
    ...process.env,
    REPORT_BUCKET: 'mango-reports',
    AWS_REGION: 'us-east-1',
    REPORT_EMAIL_FROM: 'slurmalerts1017@gmail.com',
    REPORT_EMAIL_TO: 'slurmalerts1017@gmail.com',
    REPORT_URL_EXPIRATION: '604800'
  }
});

// Send initialization
const initMessage = {
  jsonrpc: '2.0',
  method: 'initialize',
  params: {
    protocolVersion: '1.0.0',
    capabilities: {},
    clientInfo: { name: 'test-client', version: '1.0.0' }
  },
  id: 1
};

server.stdin.write(JSON.stringify(initMessage) + '\n');

server.stdout.on('data', (data) => {
  console.log('Server response:', data.toString());
});

server.stderr.on('data', (data) => {
  console.error('Server error:', data.toString());
});

setTimeout(() => {
  server.kill();
  process.exit(0);
}, 3000);