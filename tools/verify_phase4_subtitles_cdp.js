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
    console.log(`✓ Screenshot salvato: ${filename}`);
  }

  close() {
    this.ws.close();
  }
}

async function main() {
  fs.mkdirSync('tests/screenshots', { recursive: true });

  console.log("=== VERIFICA CDP FASE 4: SUBTITLE EDITOR & WORD-BY-WORD ENGINE ===");
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

    // Attesa caricamento Home
    await new Promise(r => setTimeout(r, 1500));

    // 1. Apertura progetto da Home a 1440x900
    console.log("\n[TEST 1] Apertura progetto 'Video Guglielmino' con sottotitoli da Home a 1440x900...");
    await client.setViewport(1440, 900);
    await new Promise(r => setTimeout(r, 400));

    const openProjRes = await client.evaluate(`(async () => {
      // Clic sulla prima card progetto
      const firstCard = document.querySelector("#home-projects-grid .home-card-glow");
      if (firstCard) {
        firstCard.click();
      } else {
        // Fallback: chiama openProjectById con primo progetto
        const res = await fetch("/api/projects");
        const d = await res.json();
        if (d.projects && d.projects[0]) {
          await openProjectById(d.projects[0].id);
        }
      }

      // Attesa rendering editor
      for (let i = 0; i < 30; i++) {
        await new Promise(r => setTimeout(r, 200));
        const vEditor = document.getElementById("view-editor");
        const chunk0 = document.getElementById("chunk-row-0");
        if (vEditor && !vEditor.classList.contains("hidden") && chunk0) {
          return {
            success: true,
            editorVisible: true,
            headerTitle: document.getElementById("header-project-name")?.innerText,
            chunksCount: document.querySelectorAll("#chunks-list .studio-chunk-card").length,
            timelineBlocks: document.querySelectorAll("#timeline-blocks-layer > div").length,
            videoSrc: document.getElementById("video-player")?.src,
            statsBadge: document.getElementById("editor-stats-badge")?.innerText
          };
        }
      }
      return { success: false };
    })()`);
    console.log("Stato apertura progetto:", JSON.stringify(openProjRes.result.value, null, 2));

    await new Promise(r => setTimeout(r, 500));
    await client.screenshot('tests/screenshots/phase4_subtitles_editor_1440x900.png');

    // 2. Verifica rendering a 1920x1080 (zero clipping, perfetta leggibilità)
    console.log("\n[TEST 2] Verifica Subtitle Editor a 1920x1080...");
    await client.setViewport(1920, 1080);
    await new Promise(r => setTimeout(r, 500));

    const check1920 = await client.evaluate(`(() => {
      const vEditor = document.getElementById("view-editor");
      const rect = vEditor.getBoundingClientRect();
      const chunks = document.querySelectorAll("#chunks-list .studio-chunk-card");
      return {
        editorWidth: rect.width,
        editorHeight: rect.height,
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight,
        chunksRendered: chunks.length,
        noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth
      };
    })()`);
    console.log("Layout 1920x1080:", JSON.stringify(check1920.result.value));
    await client.screenshot('tests/screenshots/phase4_subtitles_editor_1920x1080.png');

    // 3. Test Interazione Parola-per-Parola (Grassetto ★, Speaker, Ascolta)
    console.log("\n[TEST 3] Test interazioni Parola-per-Parola (Grassetto ★, Speaker toggle)...");
    const wordTestRes = await client.evaluate(`(async () => {
      // 3.1 Clic su una parola del Chunk 0 per alternare grassetto ★
      const chunk0 = document.getElementById("chunk-row-0");
      const wordBtns = chunk0.querySelectorAll("button[title*='grassetto']");
      const firstWordBtn = wordBtns[0]; // "Benvenuti"
      const initialBold = firstWordBtn.innerText.includes("★") || firstWordBtn.classList.contains("bg-amber-500");
      firstWordBtn.click();
      await new Promise(r => setTimeout(r, 200));
      const afterBold = firstWordBtn.innerText.includes("★") || firstWordBtn.classList.contains("bg-amber-500");

      // 3.2 Clic sullo Speaker toggle
      const spkBtn = chunk0.querySelector(".spk-toggle-btn");
      const initialSpkText = spkBtn?.innerText.trim();
      spkBtn.click();
      await new Promise(r => setTimeout(r, 200));
      const afterSpkBtn = document.getElementById("chunk-row-0")?.querySelector(".spk-toggle-btn");
      const afterSpkText = afterSpkBtn?.innerText.trim();

      // 3.3 Presenza controlli SOPRA / SOTTO
      const upBtns = document.querySelectorAll("#chunks-list button[title*='Sposta sopra']");
      const prevBtns = document.querySelectorAll("#chunks-list button[title*='precedente']");

      return {
        firstWord: firstWordBtn.innerText.trim(),
        boldToggled: initialBold !== afterBold,
        afterBoldState: afterBold,
        initialSpkText,
        afterSpkText,
        spkSwitched: initialSpkText !== afterSpkText,
        moveUpBtnsCount: upBtns.length,
        movePrevBtnsCount: prevBtns.length
      };
    })()`);
    console.log("Risultato Test Parola-per-Parola:", JSON.stringify(wordTestRes.result.value, null, 2));

    await new Promise(r => setTimeout(r, 300));
    await client.screenshot('tests/screenshots/phase4_subtitles_word_interaction.png');

    // 4. Test Ritorno alla Home tramite [ Home ] Header Button con autosave
    console.log("\n[TEST 4] Test ritorno alla Home tramite pulsante [ Home ]...");
    const homeReturnRes = await client.evaluate(`(async () => {
      const btnHome = document.getElementById("btn-header-home");
      if (btnHome) btnHome.click();
      await new Promise(r => setTimeout(r, 600));

      const vHome = document.getElementById("view-home");
      const vEditor = document.getElementById("view-editor");
      return {
        vHomeVisible: vHome && !vHome.classList.contains("hidden"),
        vEditorHidden: vEditor && vEditor.classList.contains("hidden")
      };
    })()`);
    console.log("Stato ritorno a Home:", JSON.stringify(homeReturnRes.result.value));

    await new Promise(r => setTimeout(r, 400));
    await client.screenshot('tests/screenshots/phase4_subtitles_return_home.png');

    client.close();
  } catch (err) {
    console.error("Errore durante test CDP:", err);
  } finally {
    chromeProc.kill('SIGTERM');
    console.log("Test CDP completati e Chrome terminato.");
  }
}

main();
