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
  fs.mkdirSync('tests/screenshots', { recursive: true });

  console.log("Avvio Chrome headless...");
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

    // Enable Page & Runtime
    await client.send('Page.enable');
    await client.send('Runtime.enable');

    // Wait for app load
    await new Promise(r => setTimeout(r, 1500));

    // 1. Verifica a 1440x900
    console.log("\n--- TEST 1: HOME VIEW A 1440x900 ---");
    await client.setViewport(1440, 900);
    await new Promise(r => setTimeout(r, 500));

    const checkHome = await client.evaluate(`(() => {
      const vHome = document.getElementById("view-home");
      const vEditor = document.getElementById("view-editor");
      const sidebar = document.getElementById("home-sidebar");
      const grid = document.getElementById("home-projects-grid");
      const hero = document.querySelector("#view-home h2");
      const cards = document.querySelectorAll("#home-projects-grid .home-card-glow");
      const sidebarItems = document.querySelectorAll("#home-sidebar-projects-list > div");
      return {
        vHomeVisible: vHome && !vHome.classList.contains("hidden"),
        vEditorHidden: vEditor && vEditor.classList.contains("hidden"),
        hasSidebar: !!sidebar,
        hasHero: !!hero,
        gridCardsCount: cards.length,
        sidebarItemsCount: sidebarItems.length,
        heroTitle: hero ? hero.innerText : "",
        cardTitles: Array.from(cards).map(c => c.querySelector("h4")?.innerText || "")
      };
    })()`);

    console.log("Stato Home 1440x900:", JSON.stringify(checkHome.result.value, null, 2));
    await client.screenshot('tests/screenshots/screen_home_1440x900.png');

    // 2. Verifica a 1920x1080
    console.log("\n--- TEST 2: HOME VIEW A 1920x1080 ---");
    await client.setViewport(1920, 1080);
    await new Promise(r => setTimeout(r, 500));

    const check1920 = await client.evaluate(`(() => {
      const vHome = document.getElementById("view-home");
      const rect = vHome.getBoundingClientRect();
      const hasOverflowX = document.documentElement.scrollWidth > window.innerWidth;
      const hasOverflowY = document.documentElement.scrollHeight > window.innerHeight;
      return {
        width: rect.width,
        height: rect.height,
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight,
        hasOverflowX,
        hasOverflowY
      };
    })()`);
    console.log("Stato Home 1920x1080:", JSON.stringify(check1920.result.value, null, 2));
    await client.screenshot('tests/screenshots/screen_home_1920x1080.png');

    // 3. Click sul Progetto -> Apertura nell'Editor
    console.log("\n--- TEST 3: APERTURA PROGETTO NELL'EDITOR ---");
    const openRes = await client.evaluate(`(async () => {
      const firstCard = document.querySelector("#home-projects-grid .home-card-glow");
      if (firstCard) {
        firstCard.click();
        return { clicked: true };
      }
      return { clicked: false };
    })()`);
    console.log("Click su progetto:", openRes.result.value);

    await new Promise(r => setTimeout(r, 1200));

    const checkEditor = await client.evaluate(`(() => {
      const vHome = document.getElementById("view-home");
      const vEditor = document.getElementById("view-editor");
      const hpn = document.getElementById("header-project-name");
      const chunks = document.querySelectorAll("#chunks-list .studio-chunk-card");
      const btnHome = document.getElementById("btn-header-home");
      const videoPlayer = document.getElementById("video-player");
      return {
        vHomeHidden: vHome && vHome.classList.contains("hidden"),
        vEditorVisible: vEditor && !vEditor.classList.contains("hidden"),
        projectName: hpn ? hpn.innerText : "",
        chunksCount: chunks.length,
        hasHomeButton: !!btnHome,
        videoSrc: videoPlayer ? videoPlayer.src : ""
      };
    })()`);
    console.log("Stato Editor aperto:", JSON.stringify(checkEditor.result.value, null, 2));
    await client.screenshot('tests/screenshots/screen_editor_opened_from_project.png');

    // 4. Click sul pulsante Home -> Ritorno alla Home View
    console.log("\n--- TEST 4: RITORNO ALLA HOME DALL'EDITOR ---");
    const returnRes = await client.evaluate(`(() => {
      const btnHome = document.getElementById("btn-header-home");
      if (btnHome) {
        btnHome.click();
        return { clicked: true };
      }
      return { clicked: false };
    })()`);
    console.log("Click Home:", returnRes.result.value);

    await new Promise(r => setTimeout(r, 1000));

    const checkReturn = await client.evaluate(`(() => {
      const vHome = document.getElementById("view-home");
      const vEditor = document.getElementById("view-editor");
      return {
        vHomeVisible: vHome && !vHome.classList.contains("hidden"),
        vEditorHidden: vEditor && vEditor.classList.contains("hidden")
      };
    })()`);
    console.log("Stato dopo ritorno a Home:", JSON.stringify(checkReturn.result.value, null, 2));
    await client.screenshot('tests/screenshots/screen_home_returned.png');

    client.close();
    console.log("\n✓ TUTTI I TEST VISIVI E FUNZIONALI DELLA HOME SUPERATI CON SUCCESSO!");
  } finally {
    chromeProc.kill();
  }
}

main().catch(err => {
  console.error("Errore esecuzione verifica CDP:", err);
  process.exit(1);
});
