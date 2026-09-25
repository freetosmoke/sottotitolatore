import re

def get_workspace_panels_markup():
    return '''      <!-- =============================================================== -->
      <!-- WORKSPACE VIEWS CONTAINER (DYNAMIC NLE CONTEXTS)                  -->
      <!-- =============================================================== -->

      <!-- WORKSPACE: PROGETTO (Info Video, Nuovo Progetto, Asset) -->
      <div id="ws-view-project" class="workspace-view hidden flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        <div class="max-w-3xl mx-auto space-y-4">
          <div class="flex items-center justify-between border-b border-dark-700/80 pb-3">
            <div>
              <h2 class="text-base font-bold text-white flex items-center gap-2">
                <span class="text-cyan-400">▣</span>
                <span>Panoramica Progetto</span>
              </h2>
              <p class="text-xs text-slate-400 mt-0.5">Dettagli del video caricato, metadati e azioni di progetto</p>
            </div>
            <div class="flex gap-2">
              <button type="button" onclick="document.getElementById('video-input').click();" class="tl-head-btn tl-btn-primary">
                + Carica Altro Video
              </button>
              <button type="button" onclick="document.getElementById('btn-new-project').click();" class="tl-head-btn tl-btn-danger">
                Nuovo Progetto (Chiudi)
              </button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="studio-card space-y-2">
              <div class="studio-card-title text-cyan-400">Video Attivo</div>
              <div class="space-y-1.5 text-xs">
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Nome file:</span>
                  <span id="proj-card-filename" class="font-medium text-slate-200 truncate max-w-[220px]">Nessun video</span>
                </div>
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Durata:</span>
                  <span id="proj-card-duration" class="font-mono text-cyan-300">00:00.00</span>
                </div>
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Formato:</span>
                  <span class="font-mono text-slate-400">9:16 Verticale</span>
                </div>
              </div>
            </div>

            <div class="studio-card space-y-2">
              <div class="studio-card-title text-cyan-400">Stato Trascrizione</div>
              <div class="space-y-1.5 text-xs">
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Sottotitoli creati:</span>
                  <span id="proj-card-chunks-count" class="font-mono text-cyan-300">0 blocchi</span>
                </div>
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Preset stile:</span>
                  <span id="proj-card-preset-name" class="font-medium text-slate-200">Guglielmino</span>
                </div>
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Salvataggio:</span>
                  <span class="text-emerald-400 font-medium">Automatico attivo</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- WORKSPACE: STRUMENTI AI (Hub Unificato Trascrizione, Diarizzazione, Traduzione, Silenzi) -->
      <div id="ws-view-ai" class="workspace-view hidden flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        <div class="max-w-3xl mx-auto space-y-4">
          <div class="border-b border-dark-700/80 pb-3">
            <h2 class="text-base font-bold text-white flex items-center gap-2">
              <span class="text-amber-400">🪄</span>
              <span>Hub Strumenti Intelligenti (AI Suite)</span>
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">Modelli locali di intelligenza artificiale per trascrizione, rimozione pause e diarizzazione</p>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <!-- 1. Trascrizione Whisper -->
            <div class="studio-card space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="studio-card-title text-white flex items-center gap-2">
                  <span class="text-amber-400">✦</span>
                  <span>Trascrizione Whisper</span>
                </div>
                <span class="text-[9.5px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">Locale HW</span>
              </div>
              <p class="text-xs text-slate-400">Riconoscimento vocale ultra-accurato con timecode per ogni singola parola.</p>
              <button type="button" onclick="window.switchWorkspace('subtitles');" class="tl-head-btn tl-btn-primary w-full justify-center">
                Apri Editor Sottotitoli
              </button>
            </div>

            <!-- 2. Rimozione Silenzi -->
            <div class="studio-card space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="studio-card-title text-white flex items-center gap-2">
                  <span class="text-cyan-400">✂</span>
                  <span>Rimozione Silenzi Fisica</span>
                </div>
                <span class="text-[9.5px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">Fisico Sync</span>
              </div>
              <p class="text-xs text-slate-400">Rileva e taglia fisicamente le pause morte del parlato mantenendo la sincronizzazione perfetta.</p>
              <button type="button" onclick="window.switchWorkspace('audio');" class="tl-head-btn tl-btn-secondary w-full justify-center">
                Configura Soglie &amp; Pause
              </button>
            </div>

            <!-- 3. Diarizzazione Voci (Speaker Detection) -->
            <div class="studio-card space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="studio-card-title text-white flex items-center gap-2">
                  <span class="text-cyan-400">♙</span>
                  <span>Speaker Diarization</span>
                </div>
                <span class="text-[9.5px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">Multi-Voice</span>
              </div>
              <p class="text-xs text-slate-400">Distingue gli interlocutori (Interlocutore 1 vs Interlocutore 2) assegnando stili e colori dedicati.</p>
              <button type="button" onclick="window.switchWorkspace('speaker');" class="tl-head-btn tl-btn-primary w-full justify-center">
                Avvia Analisi Speaker
              </button>
            </div>

            <!-- 4. Traduzione Automatica -->
            <div class="studio-card space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="studio-card-title text-white flex items-center gap-2">
                  <span class="text-cyan-400">🌍</span>
                  <span>Traduzione Multilingua</span>
                </div>
                <span class="text-[9.5px] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">Google Gemini</span>
              </div>
              <p class="text-xs text-slate-400">Traduce automaticamente i sottotitoli in italiano o in altre lingue preservando il timing.</p>
              <button type="button" onclick="window.switchWorkspace('subtitles'); window.switchInspectorTab('advanced');" class="tl-head-btn tl-btn-secondary w-full justify-center">
                Configura Traduzione
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- WORKSPACE: EXPORT STUDIO (Rendering, Formato, Burn-in, SRT, Queue) -->
      <div id="ws-view-export" class="workspace-view hidden flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        <div class="max-w-3xl mx-auto space-y-4">
          <div class="border-b border-dark-700/80 pb-3">
            <h2 class="text-base font-bold text-white flex items-center gap-2">
              <span class="text-emerald-400">⇧</span>
              <span>Esporta Video &amp; Rendering Studio</span>
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">Configura il formato di uscita, l'accelerazione hardware e genera il video finale</p>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="studio-card space-y-3">
              <div class="studio-card-title text-white">Specifiche di Rendering</div>
              <div class="space-y-2 text-xs">
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Risoluzione Output:</span>
                  <span class="font-mono text-cyan-300 font-bold">1080 × 1920 (9:16)</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Codec Accelerato:</span>
                  <span class="font-mono text-emerald-300">Apple Silicon VideoToolbox</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Filtro Video Applicato:</span>
                  <span id="export-card-filter-name" class="font-medium text-slate-300">Originale</span>
                </div>
              </div>
            </div>

            <div class="studio-card space-y-3">
              <div class="studio-card-title text-white">Sottotitoli &amp; Tracce</div>
              <div class="space-y-2 text-xs">
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Burn-in Permanente:</span>
                  <span class="text-emerald-400 font-bold">Attivo (Hardsub)</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Download .SRT:</span>
                  <button type="button" onclick="document.getElementById('btn-export-srt').click();" class="text-cyan-400 hover:text-cyan-300 underline font-medium">
                    Scarica File .SRT
                  </button>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-slate-400">Musica di sottofondo:</span>
                  <span id="export-card-bgm-status" class="text-slate-400 font-mono">Nessuna</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Pulsante Primario Gigante di Esportazione -->
          <div class="p-4 rounded-2xl bg-dark-900 border border-dark-750 flex flex-col items-center justify-center gap-3">
            <button type="button" onclick="document.getElementById('btn-export').click();" class="px-8 py-3.5 bg-gradient-to-r from-cyan-400 via-sky-500 to-blue-600 hover:from-cyan-300 hover:via-sky-400 hover:to-blue-500 text-slate-950 font-extrabold rounded-xl shadow-lg shadow-cyan-500/30 text-sm transition transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer flex items-center gap-3">
              <svg class="w-5 h-5 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>AVVIA RENDERING VIDEO FINALE</span>
            </button>
            <p class="text-[11px] text-slate-500 font-mono">Accelerazione GPU Apple Silicon a 60fps · Anteprima in tempo reale</p>
          </div>
        </div>
      </div>'''

def apply():
    with open('web_static/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Inserisci i pannelli di workspace dentro #workspace-stage prima del row dei 3 pannelli
    anchor = '<!-- Main Row of Workspace -->'
    if anchor in content and 'ws-view-project' not in content:
        content = content.replace(anchor, get_workspace_panels_markup() + '\n\n    ' + anchor)
        print("Workspace panels injected successfully into index.html.")

    with open('web_static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    apply()
