const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

async function getCDPTarget() {
  return new Promise((resolve, reject) => {
    http.get('http://127.0.0.1:9222/json', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          const page = json.find(t => t.type === 'page');
          if (page) resolve(page.webSocketDebuggerUrl);
          else reject(new Error('No page target found'));
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 1;
    this.callbacks = new Map();
    this.ready = new Promise((resolve) => {
      this.ws.onopen = resolve;
    });
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.callbacks.has(msg.id)) {
        const { resolve, reject } = this.callbacks.get(msg.id);
        this.callbacks.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      }
    };
  }

  async send(method, params = {}) {
    await this.ready;
    const reqId = this.id++;
    return new Promise((resolve, reject) => {
      this.callbacks.set(reqId, { resolve, reject });
      this.ws.send(JSON.stringify({ id: reqId, method, params }));
    });
  }

  async evaluate(expression) {
    return this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true
    });
  }

  async setViewport(width, height) {
    return this.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: false
    });
  }

  async screenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(filename, Buffer.from(res.data, 'base64'));
    console.log(`Saved screenshot: ${filename}`);
  }

  close() {
    this.ws.close();
  }
}

async function main() {
  const chromeProc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new',
    '--disable-gpu',
    '--remote-debugging-port=9222',
    '--no-first-run',
    '--no-default-browser-check',
    'http://localhost:8501'
  ]);

  await new Promise(r => setTimeout(r, 2000));

  try {
    const wsUrl = await getCDPTarget();
    const client = new CDPClient(wsUrl);
    await client.ready;

    await client.send('Page.enable');
    await client.send('Runtime.enable');
    await new Promise(r => setTimeout(r, 800));

    // 1. Editor Base 1440x900 (con Drawer Chiuso)
    await client.setViewport(1440, 900);
    await client.evaluate('window.switchWorkspace("subtitles"); window.closeInspectorDrawer();');
    await new Promise(r => setTimeout(r, 500));
    await client.screenshot('tests/screenshots/screen_refined_1440x900.png');

    // 2. Editor Base 1920x1080 (con Drawer Chiuso)
    await client.setViewport(1920, 1080);
    await new Promise(r => setTimeout(r, 500));
    await client.screenshot('tests/screenshots/screen_refined_1920x1080.png');

    // 3. Editor con Drawer APERTO a 1440x900
    await client.setViewport(1440, 900);
    await client.evaluate('window.openInspectorDrawer("text", "Chunk #1");');
    await new Promise(r => setTimeout(r, 600));
    await client.screenshot('tests/screenshots/screen_refined_drawer_1440.png');

    // 4. Workspace PROGETTO (1440x900) - Timeline deve essere nascosta!
    await client.evaluate('window.switchWorkspace("project");');
    await new Promise(r => setTimeout(r, 600));
    await client.screenshot('tests/screenshots/screen_refined_ws_project.png');

    // 5. Workspace AI HUB (1440x900)
    await client.evaluate('window.switchWorkspace("ai");');
    await new Promise(r => setTimeout(r, 600));
    await client.screenshot('tests/screenshots/screen_refined_ws_ai.png');

    // 6. Workspace EXPORT (1440x900)
    await client.evaluate('window.switchWorkspace("export");');
    await new Promise(r => setTimeout(r, 600));
    await client.screenshot('tests/screenshots/screen_refined_ws_export.png');

    // 7. Sidebar COLLASSATA (1440x900)
    await client.evaluate('window.switchWorkspace("subtitles"); window.toggleSidebar(true); window.closeInspectorDrawer();');
    await new Promise(r => setTimeout(r, 600));
    await client.screenshot('tests/screenshots/screen_refined_sidebar_collapsed.png');

    client.close();
  } finally {
    chromeProc.kill();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
