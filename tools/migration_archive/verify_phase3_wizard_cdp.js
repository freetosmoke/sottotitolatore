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

  console.log("=== VERIFICA CDP FASE 3: WIZARD NUOVO PROGETTO A 4 STEP ===");
  console.log("Avvio Chrome headless con debugging port 9222...");
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

    // Attendi caricamento app
    await new Promise(r => setTimeout(r, 1500));

    // =========================================================================
    // STEP 1: VERIFICA APERTURA WIZARD A 1440x900
    // =========================================================================
    console.log("\n[TEST 1] Apertura Wizard da Home a 1440x900...");
    await client.setViewport(1440, 900);
    await new Promise(r => setTimeout(r, 400));

    // Clic su "+ Nuovo progetto"
    const openRes = await client.evaluate(`(() => {
      const btn = document.getElementById("home-btn-new-project");
      if (btn) btn.click();
      else if (window.openNewProjectWizard) window.openNewProjectWizard();
      const modal = document.getElementById("modal-wizard");
      const step1 = document.getElementById("wizard-step-1");
      const btnNext = document.getElementById("wizard-btn-next");
      return {
        modalOpened: modal && !modal.classList.contains("hidden"),
        step1Visible: step1 && !step1.classList.contains("hidden"),
        btnNextDisabled: btnNext ? btnNext.disabled : null
      };
    })()`);
    console.log("Stato apertura:", JSON.stringify(openRes.result.value));

    await new Promise(r => setTimeout(r, 500));
    await client.screenshot('tests/screenshots/wizard_step1_empty_1440x900.png');

    // =========================================================================
    // STEP 1: CARICAMENTO VIDEO (SIMULAZIONE VIDEO RECENTE)
    // =========================================================================
    console.log("\n[TEST 2] Caricamento video da video recente...");
    const loadVideoRes = await client.evaluate(`(async () => {
      const btnRecent = document.getElementById("wizard-btn-recent");
      if (btnRecent) {
        btnRecent.click();
        // attendi fetch
        await new Promise(r => setTimeout(r, 1000));
      }
      const card = document.getElementById("wizard-video-selected-card");
      const filename = document.getElementById("wizard-preview-filename")?.innerText;
      const duration = document.getElementById("wizard-preview-duration")?.innerText;
      const btnNext = document.getElementById("wizard-btn-next");
      return {
        cardVisible: card && !card.classList.contains("hidden"),
        filename,
        duration,
        btnNextEnabled: btnNext ? !btnNext.disabled : false
      };
    })()`);
    console.log("Stato video caricato:", JSON.stringify(loadVideoRes.result.value));

    await new Promise(r => setTimeout(r, 400));
    await client.screenshot('tests/screenshots/wizard_step1_loaded_1440x900.png');

    // =========================================================================
    // STEP 2: SOTTOTITOLI SÌ / NO (DEFAULT: SÌ)
    // =========================================================================
    console.log("\n[TEST 3] Avanzamento a Step 2 (Sottotitoli Sì/No)...");
    const step2Res = await client.evaluate(`(() => {
      const btnNext = document.getElementById("wizard-btn-next");
      if (btnNext) btnNext.click();
      const step2 = document.getElementById("wizard-step-2");
      const optSub = document.getElementById("wizard-opt-subtitles");
      const optVid = document.getElementById("wizard-opt-video-only");
      return {
        step2Visible: step2 && !step2.classList.contains("hidden"),
        optSubSelected: optSub?.classList.contains("is-selected"),
        optVidSelected: optVid?.classList.contains("is-selected")
      };
    })()`);
    console.log("Stato Step 2:", JSON.stringify(step2Res.result.value));

    await new Promise(r => setTimeout(r, 400));
    await client.screenshot('tests/screenshots/wizard_step2_subtitles_1440x900.png');

    // =========================================================================
    // STEP 2: TEST SELEZIONE "NO, SOLO EDITING VIDEO"
    // =========================================================================
    console.log("\n[TEST 4] Selezione opzione 'No, solo editing video'...");
    await client.evaluate(`(() => {
      const optVid = document.getElementById("wizard-opt-video-only");
      if (optVid) optVid.click();
    })()`);
    await new Promise(r => setTimeout(r, 300));
    await client.screenshot('tests/screenshots/wizard_step2_video_only_1440x900.png');

    // Riporta a SÌ per testare il flusso completo Sottotitoli
    await client.evaluate(`(() => {
      const optSub = document.getElementById("wizard-opt-subtitles");
      if (optSub) optSub.click();
    })()`);
    await new Promise(r => setTimeout(r, 300));

    // =========================================================================
    // STEP 3: IMPOSTAZIONI PROGETTO (CON SOTTOTITOLI)
    // =========================================================================
    console.log("\n[TEST 5] Avanzamento a Step 3 (Impostazioni Progetto)...");
    const step3Res = await client.evaluate(`(() => {
      const btnNext = document.getElementById("wizard-btn-next");
      if (btnNext) btnNext.click();
      const step3 = document.getElementById("wizard-step-3");
      const subFields = document.getElementById("wizard-subtitles-fields");
      const vidFields = document.getElementById("wizard-video-only-fields");
      const projName = document.getElementById("wizard-input-name")?.value;
      const lang = document.getElementById("wizard-select-lang")?.value;
      const diarize = document.getElementById("wizard-toggle-diarize")?.checked;
      const preset = document.getElementById("wizard-select-preset")?.value;
      return {
        step3Visible: step3 && !step3.classList.contains("hidden"),
        subFieldsVisible: subFields && !subFields.classList.contains("hidden"),
        vidFieldsHidden: vidFields && vidFields.classList.contains("hidden"),
        projName,
        lang,
        diarize,
        preset
      };
    })()`);
    console.log("Stato Step 3:", JSON.stringify(step3Res.result.value));

    await new Promise(r => setTimeout(r, 400));
    await client.screenshot('tests/screenshots/wizard_step3_settings_1440x900.png');

    // =========================================================================
    // STEP 4: RIEPILOGO PROGETTO (CON SOTTOTITOLI)
    // =========================================================================
    console.log("\n[TEST 6] Avanzamento a Step 4 (Riepilogo Progetto)...");
    const step4Res = await client.evaluate(`(() => {
      const btnNext = document.getElementById("wizard-btn-next");
      if (btnNext) btnNext.click();
      const step4 = document.getElementById("wizard-step-4");
      const btnCreate = document.getElementById("wizard-btn-create");
      const summaryName = document.getElementById("wizard-summary-name")?.innerText;
      const summaryWf = document.getElementById("wizard-summary-workflow")?.innerText;
      const summaryLang = document.getElementById("wizard-summary-lang")?.innerText;
      const summaryPreset = document.getElementById("wizard-summary-preset")?.innerText;
      return {
        step4Visible: step4 && !step4.classList.contains("hidden"),
        btnCreateVisible: btnCreate && !btnCreate.classList.contains("hidden"),
        summaryName,
        summaryWf,
        summaryLang,
        summaryPreset
      };
    })()`);
    console.log("Stato Step 4:", JSON.stringify(step4Res.result.value));

    await new Promise(r => setTimeout(r, 400));
    await client.screenshot('tests/screenshots/wizard_step4_summary_1440x900.png');

    // =========================================================================
    // VERIFICA A 1920x1080 (RESPONSIVITÀ, ZERO CLIPPING)
    // =========================================================================
    console.log("\n[TEST 7] Verifica Responsiva a 1920x1080...");
    await client.setViewport(1920, 1080);
    await new Promise(r => setTimeout(r, 500));

    const check1920 = await client.evaluate(`(() => {
      const modal = document.querySelector("#modal-wizard > div");
      const rect = modal ? modal.getBoundingClientRect() : null;
      return {
        modalWidth: rect ? rect.width : 0,
        modalHeight: rect ? rect.height : 0,
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight,
        centeredX: rect ? Math.abs((window.innerWidth - rect.width) / 2 - rect.left) < 5 : false,
        noOverflowY: rect ? rect.bottom <= window.innerHeight : true
      };
    })()`);
    console.log("Layout 1920x1080:", JSON.stringify(check1920.result.value));
    await client.screenshot('tests/screenshots/wizard_step4_summary_1920x1080.png');

    // =========================================================================
    // TEST WORKFLOW B: WIZARD CON "NO, SOLO EDITING VIDEO"
    // =========================================================================
    console.log("\n[TEST 8] Verifica Workflow Video Only (Senza Trascrizione)...");
    const testVideoOnly = await client.evaluate(`(async () => {
      // Torna allo Step 2
      document.getElementById("wizard-btn-prev").click(); // Step 3
      document.getElementById("wizard-btn-prev").click(); // Step 2
      
      // Seleziona Video Only
      document.getElementById("wizard-opt-video-only").click();
      
      // Avanza a Step 3
      document.getElementById("wizard-btn-next").click();
      const subFields = document.getElementById("wizard-subtitles-fields");
      const vidFields = document.getElementById("wizard-video-only-fields");
      const vidFieldsVisible = vidFields && !vidFields.classList.contains("hidden");
      const subFieldsHidden = subFields && subFields.classList.contains("hidden");

      // Avanza a Step 4
      document.getElementById("wizard-btn-next").click();
      const wfText = document.getElementById("wizard-summary-workflow")?.innerText;

      return {
        vidFieldsVisible,
        subFieldsHidden,
        summaryWorkflowText: wfText
      };
    })()`);
    console.log("Stato Workflow Video Only:", JSON.stringify(testVideoOnly.result.value));
    await new Promise(r => setTimeout(r, 400));
    await client.screenshot('tests/screenshots/wizard_step4_video_only_1920x1080.png');

    // =========================================================================
    // TEST CREAZIONE PROGETTO: TRANSIZIONE REALE ALL'EDITOR
    // =========================================================================
    console.log("\n[TEST 9] Clic su 'Crea progetto' e verifica transizione ad Editor...");
    const createRes = await client.evaluate(`(async () => {
      const btnCreate = document.getElementById("wizard-btn-create");
      btnCreate.click();
      // Attendi che la chiamata fetch /api/projects termini e l'editor sia mostrato
      for (let i = 0; i < 30; i++) {
        await new Promise(r => setTimeout(r, 200));
        const vEditor = document.getElementById("view-editor");
        const modal = document.getElementById("modal-wizard");
        if (vEditor && !vEditor.classList.contains("hidden") && modal && modal.classList.contains("hidden")) {
          return {
            success: true,
            editorVisible: true,
            modalClosed: true,
            projectId: window.currentProjectId,
            projectType: window.currentProjectType,
            headerTitle: document.getElementById("header-project-name")?.innerText,
            videoSrc: document.getElementById("video-player")?.src
          };
        }
      }
      return { success: false };
    })()`);
    console.log("Risultato Creazione Progetto:", JSON.stringify(createRes.result.value, null, 2));

    await new Promise(r => setTimeout(r, 1000));
    await client.screenshot('tests/screenshots/editor_transition_from_wizard_1920x1080.png');

    client.close();
  } catch (err) {
    console.error("Errore durante test CDP:", err);
  } finally {
    chromeProc.kill('SIGTERM');
    console.log("Test CDP completati e Chrome terminato.");
  }
}

main();
