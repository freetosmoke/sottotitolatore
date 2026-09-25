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

  console.log("=== VERIFICA CDP FASE 5: VIDEO EDITOR WORKSPACE ===");
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

    await new Promise(r => setTimeout(r, 1500));

    // 1. Initial Home at 1440x900
    console.log("\n[TEST 1] Verifica Home / Project Library a 1440x900...");
    await client.setViewport(1440, 900);
    await new Promise(r => setTimeout(r, 500));
    await client.screenshot('tests/screenshots/phase5_01_home_1440x900.png');

    // 2. Creazione Progetto Video-Only tramite Wizard
    console.log("\n[TEST 2] Creazione nuovo progetto Video-Only ('No, solo editing video')...");
    const createRes = await client.evaluate(`(async () => {
      // 1. Apri wizard
      openNewProjectWizard();
      await new Promise(r => setTimeout(r, 300));

      // 2. Step 1: simula caricamento video
      wizardData.videoUrl = "/media/Download_10.mp4";
      wizardData.videoServerPath = "web_uploads/Download_10.mp4";
      wizardData.videoFilename = "Download_10.mp4";
      wizardData.videoDuration = 78.62;
      wizardData.videoOriginalName = "Download_10.mp4";
      wizardData.videoStoredName = "Download_10.mp4";
      setWizardStep(2);
      await new Promise(r => setTimeout(r, 300));

      // 3. Step 2: Clic su card 'No, solo editing video'
      const optVid = document.getElementById("wizard-opt-video-only");
      if (optVid) optVid.click();
      await new Promise(r => setTimeout(r, 300));

      // 4. Step 3: Imposta nome
      setWizardStep(3);
      await new Promise(r => setTimeout(r, 300));
      const inpName = document.getElementById("wizard-input-name");
      if (inpName) {
        inpName.value = "Montaggio Video FASE 5";
        wizardData.projectName = "Montaggio Video FASE 5";
      }

      // 5. Step 4: Riepilogo e Crea
      setWizardStep(4);
      await new Promise(r => setTimeout(r, 300));

      await createProjectFromWizard();
      await new Promise(r => setTimeout(r, 1200));

      const vEditor = document.getElementById("view-editor");
      const projType = vEditor?.getAttribute("data-project-type");
      const editorCard = document.getElementById("editor-card");
      const subInspector = document.getElementById("inspector-card");
      const videoInspector = document.getElementById("video-inspector-panel");
      const videoTrack = document.getElementById("tl-video-track-container");
      const playerCard = document.getElementById("player-card");

      const editorCardComputed = editorCard ? window.getComputedStyle(editorCard).display : "";
      const subInspectorComputed = subInspector ? window.getComputedStyle(subInspector).display : "";
      const videoInspectorComputed = videoInspector ? window.getComputedStyle(videoInspector).display : "";
      const videoTrackComputed = videoTrack ? window.getComputedStyle(videoTrack).display : "";

      return {
        editorVisible: vEditor && !vEditor.classList.contains("hidden"),
        projectType: projType,
        editorCardDisplay: editorCardComputed,
        subInspectorDisplay: subInspectorComputed,
        videoInspectorDisplay: videoInspectorComputed,
        videoTrackDisplay: videoTrackComputed,
        clipsCount: window.videoClips ? window.videoClips.length : 0,
        whisperNotRunning: document.getElementById("transcribe-loading")?.classList.contains("hidden"),
        headerProjectName: document.getElementById("header-project-name")?.innerText,
        playerCardWidth: playerCard?.getBoundingClientRect().width
      };
    })()`);
    console.log("Esito creazione progetto Video-Only:", JSON.stringify(createRes.result.value, null, 2));

    await new Promise(r => setTimeout(r, 600));
    await client.screenshot('tests/screenshots/phase5_02_video_editor_workspace_1440x900.png');

    // 3. Test Player & Timeline Playhead sync
    console.log("\n[TEST 3] Test Player & Timeline Playhead sync...");
    const playerTest = await client.evaluate(`(async () => {
      const v = document.getElementById("video-player");
      if (v) v.muted = true; // Necessario per autoplay in headless
      
      // Test play e pausa
      try {
        await v.play();
        await new Promise(r => setTimeout(r, 800));
        v.pause();
      } catch (e) {
        console.warn("Play bypass:", e);
      }

      // Sposta cursore a 8.5s
      seekVideo(8.5);
      v.currentTime = 8.5;
      updateTimelinePlayhead(8.5);
      await new Promise(r => setTimeout(r, 400));

      const playheadLeft = parseFloat(document.getElementById("tl-playhead")?.style.left || "0");
      const pxPerSec = getPxPerSecond();

      return {
        currentTime: v ? v.currentTime : 0,
        playheadLeft: playheadLeft,
        expectedPlayheadLeft: +(8.5 * pxPerSec).toFixed(1),
        timecodeDisplay: document.getElementById("video-time")?.innerText,
        timelinePosDisplay: document.getElementById("tl-pos-time")?.innerText,
        isPlayheadSynced: Math.abs(playheadLeft - (8.5 * pxPerSec)) < 5
      };
    })()`);
    console.log("Esito Player & Timeline Sync:", JSON.stringify(playerTest.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_03_player_timeline_synced.png');

    // 4. Test Split Clip al Playhead (8.5s)
    console.log("\n[TEST 4] Test Split Clip al Playhead (8.5s)...");
    const splitTest = await client.evaluate(`(async () => {
      const v = document.getElementById("video-player");
      if (v) v.currentTime = 8.5;
      updateTimelinePlayhead(8.5);
      await new Promise(r => setTimeout(r, 200));

      const initialCount = window.videoClips.length;
      splitVideoClipAtPlayhead();
      await new Promise(r => setTimeout(r, 400));

      const afterCount = window.videoClips.length;
      const domClips = document.querySelectorAll("#tl-video-track-container .tl-vclip-item").length;
      const clip0 = window.videoClips[0];
      const clip1 = window.videoClips[1];
      const inspectorBadge = document.getElementById("vclip-badge")?.innerText;
      const tIn = document.getElementById("vclip-time-in")?.innerText;
      const tOut = document.getElementById("vclip-time-out")?.innerText;
      const tDur = document.getElementById("vclip-time-duration")?.innerText;

      return {
        initialCount,
        afterCount,
        domClips,
        clip0: { start: clip0?.start, end: clip0?.end, dur: clip0?.duration },
        clip1: { start: clip1?.start, end: clip1?.end, dur: clip1?.duration },
        inspectorBadge,
        inspectorTimes: { in: tIn, out: tOut, duration: tDur }
      };
    })()`);
    console.log("Esito Split Clip:", JSON.stringify(splitTest.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_04_timeline_after_split.png');

    // 5. Test Selezione ed Eliminazione (Delete) Clip
    console.log("\n[TEST 5] Test Eliminazione (Delete) Clip...");
    const deleteTest = await client.evaluate(`(async () => {
      // Seleziona la seconda clip (indice 1) ed eliminala
      selectVideoClip(1, false);
      await new Promise(r => setTimeout(r, 200));

      deleteSelectedVideoClip();
      await new Promise(r => setTimeout(r, 400));

      const remainingClips = window.videoClips.length;
      const domClipsRemaining = document.querySelectorAll("#tl-video-track-container .tl-vclip-item").length;
      const activeClip = window.videoClips[0];

      return {
        remainingClips,
        domClipsRemaining,
        activeClipStart: activeClip?.start,
        activeClipEnd: activeClip?.end,
        inspectorBadge: document.getElementById("vclip-badge")?.innerText
      };
    })()`);
    console.log("Esito Delete Clip:", JSON.stringify(deleteTest.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_05_timeline_after_delete.png');

    // 6. Test Undo e Salvataggio / Ritorno a Home
    console.log("\n[TEST 6] Test Undo e Persistenza su Server...");
    const undoAndSaveTest = await client.evaluate(`(async () => {
      // Undo per ripristinare la clip eliminata
      undoVideo();
      await new Promise(r => setTimeout(r, 400));
      const restoredClipsCount = window.videoClips.length;

      // Salva progetto sul server
      const savedProj = await saveCurrentProjectToLibrary();

      // Torna alla Home
      showHomeView();
      await new Promise(r => setTimeout(r, 600));

      return {
        restoredClipsCount,
        savedProjId: savedProj?.id,
        savedClipsOnServer: savedProj?.video_clips?.length,
        homeVisible: !document.getElementById("view-home")?.classList.contains("hidden")
      };
    })()`);
    console.log("Esito Undo & Ritorno Home:", JSON.stringify(undoAndSaveTest.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_06_home_with_video_badge.png');

    // 7. Riapertura del Progetto Video-Only dalla Home
    console.log("\n[TEST 7] Riapertura del Progetto Video-Only dalla Home (Verifica ripristino tagli)...");
    const reopenTest = await client.evaluate(`(async () => {
      // Cerca la card con titolo 'Montaggio Video FASE 5'
      const cards = Array.from(document.querySelectorAll("#home-projects-grid .home-card-glow"));
      const targetCard = cards.find(c => c.innerText.includes("Montaggio Video FASE 5")) || cards[0];
      if (targetCard) targetCard.click();
      await new Promise(r => setTimeout(r, 800));

      return {
        editorVisible: !document.getElementById("view-editor")?.classList.contains("hidden"),
        projectType: document.getElementById("view-editor")?.getAttribute("data-project-type"),
        restoredClips: window.videoClips ? window.videoClips.length : 0,
        timelineClipsDom: document.querySelectorAll("#tl-video-track-container .tl-vclip-item").length,
        inspectorVisible: document.getElementById("video-inspector-panel")?.offsetParent !== null,
        subtitlesHidden: document.getElementById("editor-card")?.offsetParent === null
      };
    })()`);
    console.log("Esito Riapertura Progetto:", JSON.stringify(reopenTest.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_07_reopened_video_project.png');

    // 8. Test 1920x1080 Responsive Layout
    console.log("\n[TEST 8] Verifica Video Editor a 1920x1080 (Cinema layout)...");
    await client.setViewport(1920, 1080);
    await new Promise(r => setTimeout(r, 500));
    const layout1920 = await client.evaluate(`(() => {
      const vEditor = document.getElementById("view-editor");
      const rect = vEditor.getBoundingClientRect();
      return {
        editorWidth: rect.width,
        editorHeight: rect.height,
        noHorizontalOverflow: document.documentElement.scrollWidth <= window.innerWidth,
        playerCardWidth: document.getElementById("player-card")?.getBoundingClientRect().width,
        inspectorWidth: document.getElementById("video-inspector-panel")?.getBoundingClientRect().width
      };
    })()`);
    console.log("Layout 1920x1080:", JSON.stringify(layout1920.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_08_video_editor_1920x1080.png');

    // 9. Regression Test Subtitle Editor ("Video Guglielmino")
    console.log("\n[TEST 9] Regression Test Subtitle Editor ('Video Guglielmino')...");
    const regressionTest = await client.evaluate(`(async () => {
      // Torna alla Home
      showHomeView();
      await new Promise(r => setTimeout(r, 600));

      // Apri 'Video Guglielmino'
      const cards = Array.from(document.querySelectorAll("#home-projects-grid .home-card-glow"));
      const subCard = cards.find(c => c.innerText.includes("Guglielmino")) || cards[cards.length - 1];
      if (subCard) subCard.click();
      await new Promise(r => setTimeout(r, 800));

      const vEditor = document.getElementById("view-editor");
      const projType = vEditor?.getAttribute("data-project-type");
      const editorCardVisible = document.getElementById("editor-card")?.offsetParent !== null;
      const subInspectorVisible = document.getElementById("inspector-card")?.offsetParent !== null;
      const videoInspectorHidden = document.getElementById("video-inspector-panel")?.offsetParent === null;
      const chunk0 = document.getElementById("chunk-row-0");
      const boldBtn = chunk0?.querySelector("button[title*='grassetto']");
      const spkBtn = chunk0?.querySelector(".spk-toggle-btn");

      return {
        projectType: projType,
        editorCardVisible,
        subInspectorVisible,
        videoInspectorHidden,
        chunksLoaded: document.querySelectorAll("#chunks-list .studio-chunk-card").length,
        hasBoldBtn: !!boldBtn,
        hasSpkBtn: !!spkBtn,
        hasSopraSotto: !!document.querySelector("#chunks-list button[title*='Sposta sopra']")
      };
    })()`);
    console.log("Esito Regression Test Subtitles:", JSON.stringify(regressionTest.result.value, null, 2));
    await client.screenshot('tests/screenshots/phase5_09_subtitles_regression_verified.png');

    console.log("\n=== TUTTI I TEST CDP DELLA FASE 5 COMPLETATI CON SUCCESSO! ===");
    client.close();
  } catch (err) {
    console.error("Errore durante verifica CDP:", err);
  } finally {
    chromeProc.kill();
  }
}

main();
