#!/usr/bin/env python3
"""
tools/apply_phase3_wizard.py
Applica l'implementazione della FASE 3: WIZARD NUOVO PROGETTO A 4 STEP in web_static/index.html.
Preserva integralmente:
- Tutti i 343+ ID DOM esistenti
- La Home / Project Library creata in FASE 2
- Il Subtitle Editor con gestione parola-per-parola (SOPRA/SOTTO, frecce, grassetto ★, timestamp, speaker)
- Il Video Player, timeline e Inspector
- Tutti gli handler JS e preset
"""
import sys
from pathlib import Path

INDEX_PATH = Path("web_static/index.html")

def main():
    if not INDEX_PATH.exists():
        print(f"Error: {INDEX_PATH} not found", file=sys.stderr)
        sys.exit(1)

    content = INDEX_PATH.read_text(encoding="utf-8")

    # 1. Stili CSS per il Wizard
    css_target = ".custom-scrollbar::-webkit-scrollbar-thumb:hover {\n  background: rgba(148, 163, 184, 0.3);\n}"
    if css_target not in content:
        print("Error: css_target not found", file=sys.stderr)
        sys.exit(1)

    wizard_css = """.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.3);
}

/* ========================================================================= */
/* SUBSTUDIO FASE 3 — WIZARD NUOVO PROGETTO STYLES                           */
/* ========================================================================= */
.wizard-step-pill {
  transition: all 0.2s ease;
}
.wizard-step-pill.is-active .wizard-step-num {
  background-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 0 12px rgba(37, 99, 235, 0.6);
}
.wizard-step-pill.is-active .wizard-step-title {
  color: #ffffff;
  font-weight: 700;
}
.wizard-step-pill.is-done .wizard-step-num {
  background-color: rgba(37, 99, 235, 0.2);
  color: #60a5fa;
  border-color: rgba(96, 165, 250, 0.4);
}
.wizard-opt-card {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.wizard-opt-card:hover {
  transform: translateY(-2px);
}
.wizard-opt-card.is-selected {
  border-color: #3b82f6 !important;
  background-color: rgba(30, 58, 138, 0.15) !important;
  box-shadow: 0 0 20px -2px rgba(59, 130, 246, 0.25);
}"""

    content = content.replace(css_target, wizard_css, 1)

    # 2. Markup: Inserimento del Modale Wizard prima dei dialoghi esistenti
    modal_target = '  <!-- ================================================================= -->\n  <!-- MODALS DIALOGS (Preset, Stile/Coordinate & Coda Batch)             -->'
    if modal_target not in content:
        print("Error: modal_target not found", file=sys.stderr)
        sys.exit(1)

    wizard_markup = """  <!-- ================================================================= -->
  <!-- MODAL: WIZARD NUOVO PROGETTO A 4 STEP (FASE 3)                      -->
  <!-- ================================================================= -->
  <div id="modal-wizard" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl transition-opacity animate-fadeIn select-none">
    <div class="bg-dark-900 border border-dark-750 rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] animate-scaleUp">
      
      <!-- Wizard Window Header: macOS Traffic Lights + Stepper Bar -->
      <div class="h-16 px-6 border-b border-dark-800/80 bg-dark-950/70 flex items-center justify-between flex-shrink-0">
        <!-- Traffic lights -->
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-rose-500/80 cursor-pointer hover:opacity-100 opacity-80" onclick="closeNewProjectWizard()"></div>
          <div class="w-3 h-3 rounded-full bg-amber-500/80 opacity-80"></div>
          <div class="w-3 h-3 rounded-full bg-emerald-500/80 opacity-80"></div>
        </div>

        <!-- 4 Steps Indicators -->
        <div class="flex items-center gap-3 sm:gap-6">
          <!-- Step 1 -->
          <div id="wizard-pill-1" class="wizard-step-pill is-active flex items-center gap-2">
            <span class="wizard-step-num w-6 h-6 rounded-full bg-blue-600 text-white text-[11px] font-bold flex items-center justify-center border border-blue-400/40">1</span>
            <span class="wizard-step-title text-xs font-semibold text-white hidden sm:inline">Importa video</span>
          </div>
          <div class="w-6 h-px bg-dark-750"></div>

          <!-- Step 2 -->
          <div id="wizard-pill-2" class="wizard-step-pill flex items-center gap-2">
            <span class="wizard-step-num w-6 h-6 rounded-full bg-dark-800 text-slate-400 text-[11px] font-bold flex items-center justify-center border border-dark-700">2</span>
            <span class="wizard-step-title text-xs font-medium text-slate-400 hidden sm:inline">Sottotitoli</span>
          </div>
          <div class="w-6 h-px bg-dark-750"></div>

          <!-- Step 3 -->
          <div id="wizard-pill-3" class="wizard-step-pill flex items-center gap-2">
            <span class="wizard-step-num w-6 h-6 rounded-full bg-dark-800 text-slate-400 text-[11px] font-bold flex items-center justify-center border border-dark-700">3</span>
            <span class="wizard-step-title text-xs font-medium text-slate-400 hidden sm:inline">Impostazioni</span>
          </div>
          <div class="w-6 h-px bg-dark-750"></div>

          <!-- Step 4 -->
          <div id="wizard-pill-4" class="wizard-step-pill flex items-center gap-2">
            <span class="wizard-step-num w-6 h-6 rounded-full bg-dark-800 text-slate-400 text-[11px] font-bold flex items-center justify-center border border-dark-700">4</span>
            <span class="wizard-step-title text-xs font-medium text-slate-400 hidden sm:inline">Riepilogo</span>
          </div>
        </div>

        <!-- Close Button -->
        <button type="button" class="text-slate-500 hover:text-white p-1 rounded-lg hover:bg-dark-800 transition" onclick="closeNewProjectWizard()">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <!-- Wizard Body: 4 Step Panels -->
      <div class="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6 custom-scrollbar">

        <!-- =============================================================== -->
        <!-- STEP 1: IMPORTA VIDEO                                           -->
        <!-- =============================================================== -->
        <div id="wizard-step-1" class="space-y-6">
          <input type="file" id="wizard-video-input" accept="video/mp4,video/quicktime,video/x-matroska,video/x-msvideo,video/webm" class="hidden">
          
          <!-- Drop Area / Not Selected State -->
          <div id="wizard-dropzone" class="border-2 border-dashed border-dark-700 hover:border-blue-500/60 rounded-2xl p-8 sm:p-12 text-center bg-dark-950/50 hover:bg-dark-950/80 transition-all cursor-pointer flex flex-col items-center justify-center gap-4 group">
            <div class="w-16 h-16 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center justify-center group-hover:scale-105 transition-transform shadow-inner">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
            </div>
            <div class="space-y-1">
              <h3 class="text-base font-bold text-white tracking-tight">Iniziamo dal tuo video</h3>
              <p class="text-xs text-slate-400">Trascina qui il video oppure selezionalo dal Mac.</p>
            </div>
            <button type="button" id="wizard-btn-browse" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-blue-600/25 transition active:scale-95 cursor-pointer">
              <span>Seleziona video</span>
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
            </button>
            <p class="text-[11px] text-slate-500 font-mono">Formati supportati: MP4, MOV, MKV, AVI, WebM</p>
          </div>

          <!-- Video Selected Card Preview (Hidden initially) -->
          <div id="wizard-video-selected-card" class="hidden p-4 rounded-2xl bg-dark-950 border border-blue-500/40 flex items-center justify-between gap-4 shadow-xl">
            <div class="flex items-center gap-4 min-w-0">
              <div class="w-20 h-14 rounded-xl bg-dark-900 border border-dark-750 overflow-hidden relative flex-shrink-0 flex items-center justify-center">
                <img id="wizard-preview-img" class="w-full h-full object-cover">
                <div class="absolute inset-0 bg-dark-950/20"></div>
                <svg class="w-6 h-6 text-blue-400 absolute" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4l12 6-12 6V4z"/></svg>
              </div>
              <div class="min-w-0 space-y-1">
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">Video Selezionato</span>
                  <h4 id="wizard-preview-filename" class="text-xs font-bold text-white truncate max-w-sm">video.mp4</h4>
                </div>
                <div class="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                  <span id="wizard-preview-duration">00:00</span>
                  <span>•</span>
                  <span id="wizard-preview-res">1080 x 1920</span>
                  <span>•</span>
                  <span id="wizard-preview-size">0 MB</span>
                </div>
              </div>
            </div>
            <button type="button" id="wizard-btn-change-video" class="px-3 py-1.5 bg-dark-800 hover:bg-dark-750 text-slate-300 hover:text-white rounded-xl text-xs font-medium border border-dark-700 transition cursor-pointer">
              Cambia
            </button>
          </div>

          <!-- 3 Quick Utility Cards -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div id="wizard-btn-iphone" class="p-3 rounded-xl bg-dark-950/70 border border-dark-800 hover:border-dark-700 text-center flex flex-col items-center gap-2 cursor-pointer transition">
              <span class="text-base">📱</span>
              <span class="text-xs font-medium text-slate-300">Importa da iPhone</span>
            </div>
            <div id="wizard-btn-folder" class="p-3 rounded-xl bg-dark-950/70 border border-dark-800 hover:border-dark-700 text-center flex flex-col items-center gap-2 cursor-pointer transition">
              <span class="text-base">📁</span>
              <span class="text-xs font-medium text-slate-300">Importa da cartella</span>
            </div>
            <div id="wizard-btn-recent" class="p-3 rounded-xl bg-dark-950/70 border border-dark-800 hover:border-dark-700 text-center flex flex-col items-center gap-2 cursor-pointer transition" title="Usa l'ultimo video caricato">
              <span class="text-base">⚡️</span>
              <span class="text-xs font-medium text-slate-300">Usa video recente</span>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- STEP 2: SOTTOTITOLI SÌ / NO                                      -->
        <!-- =============================================================== -->
        <div id="wizard-step-2" class="hidden space-y-6">
          <div class="flex flex-col lg:flex-row items-center gap-6">
            <!-- Left: Video Badge Summary -->
            <div class="w-full lg:w-56 p-3.5 rounded-2xl bg-dark-950 border border-dark-800 flex-shrink-0 space-y-2.5">
              <div class="w-full aspect-video rounded-xl bg-dark-900 border border-dark-750 overflow-hidden relative">
                <img id="wizard-step2-img" class="w-full h-full object-cover">
                <div class="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 rounded bg-dark-950/85 text-[10px] font-mono text-slate-200" id="wizard-step2-duration">00:00</div>
              </div>
              <div>
                <span class="text-[10px] uppercase font-bold text-slate-500">Video selezionato</span>
                <div id="wizard-step2-filename" class="text-xs font-bold text-white truncate">video.mp4</div>
                <div id="wizard-step2-meta" class="text-[10px] font-mono text-slate-400 mt-0.5">1080x1920 • 6.9MB</div>
              </div>
            </div>

            <!-- Right: Question & Option Cards -->
            <div class="flex-1 space-y-4 w-full">
              <div>
                <h3 class="text-base font-bold text-white tracking-tight">Vuoi aggiungere i sottotitoli?</h3>
                <p class="text-xs text-slate-400 mt-1 leading-relaxed">
                  Puoi trascrivere automaticamente l'audio del video e generare i sottotitoli sincronizzati, oppure continuare solo con l'editing video.
                </p>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <!-- Option A: SÌ, AGGIUNGI SOTTOTITOLI -->
                <div id="wizard-opt-subtitles" class="wizard-opt-card is-selected p-4 rounded-2xl bg-dark-950 border border-blue-500/50 flex flex-col justify-between gap-3 cursor-pointer">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <div class="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center text-xs font-extrabold">
                        CC
                      </div>
                      <span class="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs">✓</span>
                    </div>
                    <div>
                      <h4 class="text-xs font-bold text-white">Sì, aggiungi sottotitoli</h4>
                      <p class="text-[11px] text-slate-400 mt-0.5">Genera sottotitoli dinamici</p>
                    </div>
                    <ul class="text-[11px] text-slate-400 space-y-1.5 pt-1">
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Trascrizione automatica</span>
                      </li>
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Speaker detection</span>
                      </li>
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Timeline con sottotitoli</span>
                      </li>
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Tutte le funzioni di editing</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- Option B: NO, SOLO EDITING VIDEO -->
                <div id="wizard-opt-video-only" class="wizard-opt-card p-4 rounded-2xl bg-dark-950 border border-dark-800 flex flex-col justify-between gap-3 cursor-pointer">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <div class="w-9 h-9 rounded-xl bg-cyan-600/20 border border-cyan-500/30 text-cyan-400 flex items-center justify-center text-xs">
                        ✂️
                      </div>
                      <span class="w-5 h-5 rounded-full border border-dark-700 flex items-center justify-center text-xs opacity-0">✓</span>
                    </div>
                    <div>
                      <h4 class="text-xs font-bold text-white">No, solo editing video</h4>
                      <p class="text-[11px] text-slate-400 mt-0.5">Workspace video tradizionale</p>
                    </div>
                    <ul class="text-[11px] text-slate-400 space-y-1.5 pt-1">
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Editor video completo</span>
                      </li>
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Tagli e modifiche</span>
                      </li>
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Effetti e transizioni</span>
                      </li>
                      <li class="flex items-center gap-1.5 text-slate-300">
                        <svg class="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                        <span>Senza trascrizione</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- STEP 3: IMPOSTAZIONI PROGETTO                                    -->
        <!-- =============================================================== -->
        <div id="wizard-step-3" class="hidden space-y-5">
          <div>
            <h3 class="text-base font-bold text-white tracking-tight">Impostazioni progetto</h3>
            <p class="text-xs text-slate-400 mt-1">Configura le impostazioni iniziali del tuo progetto.</p>
          </div>

          <div class="space-y-4">
            <!-- Nome Progetto -->
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Nome progetto</label>
              <input type="text" id="wizard-input-name" class="w-full bg-dark-950 border border-dark-750 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none transition">
            </div>

            <!-- Sezione Sottotitoli (mostrata solo se Subtitles === YES) -->
            <div id="wizard-subtitles-fields" class="space-y-4">
              <!-- Lingua Video -->
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Lingua video</label>
                <select id="wizard-select-lang" class="w-full bg-dark-950 border border-dark-750 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none transition cursor-pointer">
                  <option value="it" selected>🇮🇹 Italiano</option>
                  <option value="en">🇬🇧 English</option>
                  <option value="es">🇪🇸 Español</option>
                  <option value="fr">🇫🇷 Français</option>
                  <option value="de">🇩🇪 Deutsch</option>
                </select>
              </div>

              <!-- Speaker Detection Toggle -->
              <div class="p-3.5 rounded-xl bg-dark-950 border border-dark-800 flex items-center justify-between">
                <div>
                  <div class="text-xs font-semibold text-white">Speaker Detection (Diarizzazione)</div>
                  <div class="text-[11px] text-slate-400 mt-0.5">Distingue e colora automaticamente gli interlocutori (Speaker 1, Speaker 2)</div>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" id="wizard-toggle-diarize" checked class="sr-only peer">
                  <div class="w-9 h-5 bg-dark-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <!-- Preset Iniziale -->
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Stile iniziale sottotitoli</label>
                <select id="wizard-select-preset" class="w-full bg-dark-950 border border-dark-750 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none transition cursor-pointer">
                  <option value="voce_del_successo" selected>★ La Voce del Successo (Consigliato)</option>
                  <option value="preset_clean">Clean Modern</option>
                  <option value="preset_social">Social Pop</option>
                  <option value="preset_bold">Bold Impact</option>
                  <option value="preset_minimal">Minimalist</option>
                  <option value="preset_creator">Creator Studio</option>
                </select>
              </div>
            </div>

            <!-- Sezione Video Only (mostrata solo se Subtitles === NO) -->
            <div id="wizard-video-only-fields" class="hidden space-y-4">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5">Formato video</label>
                <select id="wizard-select-aspect" class="w-full bg-dark-950 border border-dark-750 focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none transition cursor-pointer">
                  <option value="9:16" selected>9:16 Verticale (Reels, TikTok, Shorts)</option>
                  <option value="16:9">16:9 Orizzontale (YouTube, Cinema)</option>
                  <option value="1:1">1:1 Quadrato (Instagram Feed)</option>
                </select>
              </div>
            </div>

            <!-- Cartella Salvataggio -->
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Cartella di salvataggio</label>
              <div class="flex items-center gap-2">
                <input type="text" id="wizard-input-folder" value="~/Movies/SubStudio" readonly class="flex-1 bg-dark-950 border border-dark-800 rounded-xl px-3.5 py-2 text-xs text-slate-400 font-mono">
                <button type="button" class="px-3 py-2 bg-dark-800 hover:bg-dark-750 text-slate-300 hover:text-white rounded-xl text-xs font-medium border border-dark-750 transition" onclick="alert('Cartella di lavoro predefinita di SubStudio configurata.')">
                  Cambia
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- STEP 4: RIEPILOGO                                                -->
        <!-- =============================================================== -->
        <div id="wizard-step-4" class="hidden space-y-5">
          <div>
            <h3 class="text-base font-bold text-white tracking-tight">Riepilogo progetto</h3>
            <p class="text-xs text-slate-400 mt-1">Verifica le impostazioni prima di iniziare a lavorare.</p>
          </div>

          <div class="p-5 rounded-2xl bg-dark-950 border border-dark-800 space-y-4 shadow-xl">
            <!-- Video & Title Summary -->
            <div class="flex items-center gap-4 pb-4 border-b border-dark-800/80">
              <div class="w-20 h-14 rounded-xl bg-dark-900 border border-dark-750 overflow-hidden relative flex-shrink-0">
                <img id="wizard-summary-img" class="w-full h-full object-cover">
              </div>
              <div class="min-w-0 space-y-1">
                <h4 id="wizard-summary-name" class="text-sm font-bold text-white truncate">Progetto</h4>
                <div id="wizard-summary-meta" class="text-xs text-slate-400 font-mono">video.mp4 • 01:18 • 1080x1920</div>
              </div>
            </div>

            <!-- Details List -->
            <div class="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span class="text-slate-500 block text-[11px]">Workflow</span>
                <span id="wizard-summary-workflow" class="font-bold text-blue-400 flex items-center gap-1.5 mt-0.5">
                  <span>CC</span> Sottotitoli intelligenti
                </span>
              </div>
              <div>
                <span class="text-slate-500 block text-[11px]">Lingua Audio</span>
                <span id="wizard-summary-lang" class="font-medium text-slate-200 mt-0.5">🇮🇹 Italiano</span>
              </div>
              <div>
                <span class="text-slate-500 block text-[11px]">Speaker Detection</span>
                <span id="wizard-summary-spk" class="font-medium text-slate-200 mt-0.5">Attivo (Multi-Speaker)</span>
              </div>
              <div>
                <span class="text-slate-500 block text-[11px]">Preset Iniziale</span>
                <span id="wizard-summary-preset" class="font-medium text-slate-200 mt-0.5">La Voce del Successo</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Wizard Bottom Action Bar -->
      <div class="h-16 px-6 border-t border-dark-800/80 bg-dark-950/70 flex items-center justify-between flex-shrink-0">
        <!-- Left: Annulla & Indietro -->
        <div class="flex items-center gap-2">
          <button type="button" id="wizard-btn-cancel" class="px-4 py-2 text-slate-400 hover:text-slate-200 hover:bg-dark-800/60 rounded-xl text-xs font-medium transition cursor-pointer" onclick="closeNewProjectWizard()">
            Annulla
          </button>
          <button type="button" id="wizard-btn-prev" class="hidden px-4 py-2 bg-dark-800 hover:bg-dark-750 text-slate-300 hover:text-white rounded-xl text-xs font-medium border border-dark-700 transition cursor-pointer">
            ← Indietro
          </button>
        </div>

        <!-- Right: Continua & Crea Progetto -->
        <div class="flex items-center gap-2">
          <button type="button" id="wizard-btn-next" disabled class="px-5 py-2 bg-blue-600 disabled:bg-dark-800 disabled:text-slate-500 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-600/25 transition active:scale-95 cursor-pointer disabled:cursor-not-allowed">
            Continua →
          </button>
          <button type="button" id="wizard-btn-create" class="hidden px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-600/30 transition active:scale-95 cursor-pointer">
            Crea progetto
          </button>
        </div>
      </div>

    </div>
  </div>"""

    content = content.replace(modal_target, wizard_markup + "\n\n" + modal_target, 1)

    # 3. JavaScript: Logica del Wizard
    js_target = "    function pushState() {"
    if js_target not in content:
        print("Error: js_target pushState not found", file=sys.stderr)
        sys.exit(1)

    wizard_js = """    // =========================================================================
    // SUBSTUDIO WIZARD NUOVO PROGETTO A 4 STEP (FASE 3)
    // =========================================================================
    let wizardCurrentStep = 1;
    let wizardData = {
      videoOriginalName: "",
      videoStoredName: "",
      videoServerPath: "",
      videoUrl: "",
      videoDuration: 0,
      videoResolution: "1080 x 1920",
      videoSize: "0 MB",
      thumbnail: "",
      subtitlesWorkflow: true, // true: Subtitle Project, false: Video Only Project
      projectName: "",
      language: "it",
      speakerDetection: true,
      presetId: "voce_del_successo",
      aspectRatio: "9:16"
    };

    window.openNewProjectWizard = function() {
      wizardCurrentStep = 1;
      resetWizardState();
      updateWizardUI();
      const modal = document.getElementById("modal-wizard");
      if (modal) modal.classList.remove("hidden");
    };

    window.closeNewProjectWizard = function() {
      const modal = document.getElementById("modal-wizard");
      if (modal) modal.classList.add("hidden");
    };

    function resetWizardState() {
      wizardData = {
        videoOriginalName: "",
        videoStoredName: "",
        videoServerPath: "",
        videoUrl: "",
        videoDuration: 0,
        videoResolution: "1080 x 1920",
        videoSize: "0 MB",
        thumbnail: "",
        subtitlesWorkflow: true,
        projectName: "",
        language: "it",
        speakerDetection: true,
        presetId: "voce_del_successo",
        aspectRatio: "9:16"
      };
      const dropzone = document.getElementById("wizard-dropzone");
      const card = document.getElementById("wizard-video-selected-card");
      if (dropzone) dropzone.classList.remove("hidden");
      if (card) card.classList.add("hidden");
      const btnNext = document.getElementById("wizard-btn-next");
      if (btnNext) btnNext.disabled = true;
    }

    function setWizardStep(step) {
      wizardCurrentStep = step;
      updateWizardUI();
    }

    function updateWizardUI() {
      // 1. Aggiorna Pills
      for (let s = 1; s <= 4; s++) {
        const pill = document.getElementById(`wizard-pill-${s}`);
        const panel = document.getElementById(`wizard-step-${s}`);
        if (!pill || !panel) continue;

        if (s === wizardCurrentStep) {
          pill.className = "wizard-step-pill is-active flex items-center gap-2";
          panel.classList.remove("hidden");
        } else if (s < wizardCurrentStep) {
          pill.className = "wizard-step-pill is-done flex items-center gap-2";
          panel.classList.add("hidden");
        } else {
          pill.className = "wizard-step-pill flex items-center gap-2";
          panel.classList.add("hidden");
        }
      }

      // 2. Aggiorna Bottoni Azione
      const btnPrev = document.getElementById("wizard-btn-prev");
      const btnNext = document.getElementById("wizard-btn-next");
      const btnCreate = document.getElementById("wizard-btn-create");

      if (btnPrev) {
        if (wizardCurrentStep > 1) {
          btnPrev.classList.remove("hidden");
        } else {
          btnPrev.classList.add("hidden");
        }
      }

      if (wizardCurrentStep === 4) {
        if (btnNext) btnNext.classList.add("hidden");
        if (btnCreate) btnCreate.classList.remove("hidden");
        populateWizardSummary();
      } else {
        if (btnNext) {
          btnNext.classList.remove("hidden");
          if (wizardCurrentStep === 1) {
            btnNext.disabled = !wizardData.videoServerPath;
          } else {
            btnNext.disabled = false;
          }
        }
        if (btnCreate) btnCreate.classList.add("hidden");
      }

      // 3. Step 2 & 3 specifics
      if (wizardCurrentStep === 2) {
        const img2 = document.getElementById("wizard-step2-img");
        if (img2) img2.src = wizardData.thumbnail || wizardData.videoUrl;
        const dur2 = document.getElementById("wizard-step2-duration");
        if (dur2) dur2.innerText = formatProjectDuration(wizardData.videoDuration);
        const name2 = document.getElementById("wizard-step2-filename");
        if (name2) name2.innerText = wizardData.videoOriginalName || "video.mp4";
        const meta2 = document.getElementById("wizard-step2-meta");
        if (meta2) meta2.innerText = `${wizardData.videoResolution} • ${wizardData.videoSize}`;
      } else if (wizardCurrentStep === 3) {
        const inpName = document.getElementById("wizard-input-name");
        if (inpName && !inpName.value) {
          const baseName = wizardData.videoOriginalName.replace(/\\.[^/.]+$/, "");
          inpName.value = baseName ? baseName.replace(/_/g, " ") : "Nuovo Progetto";
          wizardData.projectName = inpName.value;
        }
        const subFields = document.getElementById("wizard-subtitles-fields");
        const vidFields = document.getElementById("wizard-video-only-fields");
        if (wizardData.subtitlesWorkflow) {
          if (subFields) subFields.classList.remove("hidden");
          if (vidFields) vidFields.classList.add("hidden");
        } else {
          if (subFields) subFields.classList.add("hidden");
          if (vidFields) vidFields.classList.remove("hidden");
        }
      }
    }

    function populateWizardSummary() {
      const sumImg = document.getElementById("wizard-summary-img");
      if (sumImg) sumImg.src = wizardData.thumbnail || wizardData.videoUrl;
      const sumName = document.getElementById("wizard-summary-name");
      if (sumName) sumName.innerText = wizardData.projectName || "Nuovo Progetto";
      const sumMeta = document.getElementById("wizard-summary-meta");
      if (sumMeta) sumMeta.innerText = `${wizardData.videoOriginalName} • ${formatProjectDuration(wizardData.videoDuration)} • ${wizardData.videoResolution}`;

      const sumWf = document.getElementById("wizard-summary-workflow");
      if (sumWf) {
        sumWf.innerHTML = wizardData.subtitlesWorkflow
          ? `<span class="text-blue-400 font-bold flex items-center gap-1.5"><span class="w-4 h-4 rounded bg-blue-600/20 flex items-center justify-center text-[10px]">CC</span> Sottotitoli intelligenti</span>`
          : `<span class="text-cyan-400 font-bold flex items-center gap-1.5"><span class="w-4 h-4 rounded bg-cyan-600/20 flex items-center justify-center text-[10px]">✂️</span> Solo Video Editing</span>`;
      }

      const sumLang = document.getElementById("wizard-summary-lang");
      if (sumLang) {
        sumLang.innerText = wizardData.subtitlesWorkflow ? (wizardData.language === "en" ? "🇬🇧 English" : "🇮🇹 Italiano") : "N/D (Senza Trascrizione)";
      }

      const sumSpk = document.getElementById("wizard-summary-spk");
      if (sumSpk) {
        sumSpk.innerText = wizardData.subtitlesWorkflow ? (wizardData.speakerDetection ? "Attivo (Multi-Speaker)" : "Disattivato") : "N/D";
      }

      const sumPreset = document.getElementById("wizard-summary-preset");
      if (sumPreset) {
        sumPreset.innerText = wizardData.subtitlesWorkflow ? "La Voce del Successo" : `Formato ${wizardData.aspectRatio}`;
      }
    }

    async function handleWizardFileUpload(file) {
      if (!file) return;
      const dropzone = document.getElementById("wizard-dropzone");
      const card = document.getElementById("wizard-video-selected-card");
      if (dropzone) {
        dropzone.classList.add("opacity-50", "pointer-events-none");
        dropzone.innerHTML = `<div class="p-6 text-center space-y-2"><div class="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin mx-auto"></div><p class="text-xs text-slate-300 font-medium">Caricamento del video in corso...</p></div>`;
      }

      const fd = new FormData();
      fd.append("video", file);
      try {
        const res = await fetch("/api/upload", { method: "POST", body: fd });
        const data = await res.json();
        if (data.success) {
          applyVideoDataToWizard({
            original_name: data.original_name || file.name,
            filename: data.filename,
            server_path: data.server_path,
            video_url: data.video_url,
            duration: data.duration || 60.0,
            size: file.size || 0
          });
        } else {
          alert("Errore upload: " + data.error);
          resetWizardState();
        }
      } catch (err) {
        console.error("Upload fallito:", err);
        alert("Errore caricamento file: " + err);
        resetWizardState();
      }
    }

    function applyVideoDataToWizard(data) {
      wizardData.videoOriginalName = data.original_name || "video.mp4";
      wizardData.videoStoredName = data.filename || "video.mp4";
      wizardData.videoServerPath = data.server_path || "";
      wizardData.videoUrl = data.video_url || "";
      wizardData.videoDuration = data.duration || 60.0;
      wizardData.videoSize = (data.size ? (data.size / (1024 * 1024)).toFixed(1) + " MB" : "6.9 MB");
      wizardData.thumbnail = data.video_url || "";

      const baseName = wizardData.videoOriginalName.replace(/\\.[^/.]+$/, "");
      wizardData.projectName = baseName ? baseName.replace(/_/g, " ") : "Nuovo Progetto";

      const dropzone = document.getElementById("wizard-dropzone");
      const card = document.getElementById("wizard-video-selected-card");
      if (dropzone) dropzone.classList.add("hidden");
      if (card) card.classList.remove("hidden");

      const prevImg = document.getElementById("wizard-preview-img");
      if (prevImg) prevImg.src = wizardData.videoUrl;
      const prevName = document.getElementById("wizard-preview-filename");
      if (prevName) prevName.innerText = wizardData.videoOriginalName;
      const prevDur = document.getElementById("wizard-preview-duration");
      if (prevDur) prevDur.innerText = formatProjectDuration(wizardData.videoDuration);
      const prevRes = document.getElementById("wizard-preview-res");
      if (prevRes) prevRes.innerText = wizardData.videoResolution;
      const prevSize = document.getElementById("wizard-preview-size");
      if (prevSize) prevSize.innerText = wizardData.videoSize;

      const btnNext = document.getElementById("wizard-btn-next");
      if (btnNext) btnNext.disabled = false;
    }

    async function createProjectFromWizard() {
      const btnCreate = document.getElementById("wizard-btn-create");
      if (btnCreate) {
        btnCreate.disabled = true;
        btnCreate.innerHTML = `<span class="flex items-center gap-2"><span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span> Creazione...</span>`;
      }

      const projectType = wizardData.subtitlesWorkflow ? "subtitles" : "video_only";
      const payload = {
        name: wizardData.projectName || "Nuovo Progetto",
        type: projectType,
        status: "ready",
        media: {
          filename: wizardData.videoOriginalName,
          stored_filename: wizardData.videoStoredName,
          server_path: wizardData.videoServerPath,
          url: wizardData.videoUrl,
          duration: wizardData.videoDuration,
          size: wizardData.videoSize
        },
        settings: {
          language: wizardData.language || "it",
          speaker_detection: wizardData.speakerDetection,
          activePresetId: wizardData.presetId || "voce_del_successo",
          aspect_ratio: wizardData.aspectRatio || "9:16"
        },
        chunks: [],
        allOriginalWords: [],
        snapshot: {}
      };

      try {
        const res = await fetch("/api/projects", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const d = await res.json();
        if (d.success && d.project) {
          const createdProject = d.project;
          closeNewProjectWizard();

          // Configura stato globale
          window.currentProjectId = createdProject.id;
          window.currentProjectType = projectType;

          // Header
          const hpn = document.getElementById("header-project-name");
          if (hpn) hpn.innerText = createdProject.name;

          // Carica player e layout
          if (videoPlayer) {
            videoPlayer.src = createdProject.media.url || wizardData.videoUrl;
            videoPlayer.load();
          }
          currentVideoPath = createdProject.media.server_path || wizardData.videoServerPath;
          currentVideoDuration = wizardData.videoDuration;
          originalVideoDuration = wizardData.videoDuration;

          if (videoContainer) videoContainer.classList.remove("hidden");
          if (uploadBox) uploadBox.classList.add("hidden");
          const tlEmpty = document.getElementById("timeline-empty");
          if (tlEmpty) tlEmpty.classList.add("hidden");

          // Carica waveform
          if (typeof initWaveform === "function" && currentVideoPath) {
            initWaveform(currentVideoPath);
          }

          // Distinzione tra workflow Subtitles vs Video Only
          if (projectType === "subtitles") {
            // Sottotitoli SÌ
            document.getElementById("view-editor")?.setAttribute("data-project-type", "subtitles");
            if (typeof startTranscription === "function") {
              startTranscription(currentVideoPath, createdProject.media.url || wizardData.videoUrl);
            }
          } else {
            // Video Only NO: Nessuna trascrizione caricata
            document.getElementById("view-editor")?.setAttribute("data-project-type", "video_only");
            if (editorEmpty) editorEmpty.classList.add("hidden");
            if (chunksList) chunksList.classList.add("hidden");
            if (statsBadge) statsBadge.innerText = "Video Only";
          }

          // Mostra Editor View
          showEditorView();
          return;
        }
      } catch (err) {
        console.error("Creazione progetto fallita:", err);
        alert("Errore durante la creazione del progetto: " + err);
      } finally {
        if (btnCreate) {
          btnCreate.disabled = false;
          btnCreate.innerText = "Crea progetto";
        }
      }
    }

    function initWizardEventListeners() {
      // Navigazione bottoni
      const btnNext = document.getElementById("wizard-btn-next");
      if (btnNext) {
        btnNext.onclick = () => {
          if (wizardCurrentStep < 4) setWizardStep(wizardCurrentStep + 1);
        };
      }

      const btnPrev = document.getElementById("wizard-btn-prev");
      if (btnPrev) {
        btnPrev.onclick = () => {
          if (wizardCurrentStep > 1) setWizardStep(wizardCurrentStep - 1);
        };
      }

      const btnCreate = document.getElementById("wizard-btn-create");
      if (btnCreate) {
        btnCreate.onclick = () => createProjectFromWizard();
      }

      // Input video file
      const vInput = document.getElementById("wizard-video-input");
      const dropzone = document.getElementById("wizard-dropzone");
      const btnBrowse = document.getElementById("wizard-btn-browse");
      const btnChange = document.getElementById("wizard-btn-change-video");

      if (vInput) {
        vInput.onchange = (e) => {
          if (e.target.files && e.target.files[0]) {
            handleWizardFileUpload(e.target.files[0]);
            vInput.value = "";
          }
        };
      }

      if (dropzone && vInput) {
        dropzone.onclick = (e) => {
          if (e.target !== btnBrowse) vInput.click();
        };
        dropzone.ondragover = (e) => { e.preventDefault(); dropzone.classList.add("border-blue-500"); };
        dropzone.ondragleave = () => { dropzone.classList.remove("border-blue-500"); };
        dropzone.ondrop = (e) => {
          e.preventDefault();
          dropzone.classList.remove("border-blue-500");
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleWizardFileUpload(e.dataTransfer.files[0]);
          }
        };
      }
      if (btnBrowse && vInput) btnBrowse.onclick = (e) => { e.stopPropagation(); vInput.click(); };
      if (btnChange && vInput) btnChange.onclick = () => vInput.click();

      // Quick Import cards
      const btnRecent = document.getElementById("wizard-btn-recent");
      if (btnRecent) {
        btnRecent.onclick = async () => {
          try {
            const res = await fetch("/api/default_video");
            const data = await res.json();
            if (data.success) {
              applyVideoDataToWizard({
                original_name: data.filename,
                filename: data.filename,
                server_path: data.server_path,
                video_url: data.video_url,
                duration: data.duration || 78.6,
                size: 6943294
              });
            } else {
              if (vInput) vInput.click();
            }
          } catch (err) {
            if (vInput) vInput.click();
          }
        };
      }

      const btnIphone = document.getElementById("wizard-btn-iphone");
      if (btnIphone && vInput) btnIphone.onclick = () => vInput.click();
      const btnFolder = document.getElementById("wizard-btn-folder");
      if (btnFolder && vInput) btnFolder.onclick = () => vInput.click();

      // Step 2 Option Cards: Sottotitoli Sì vs No
      const optSub = document.getElementById("wizard-opt-subtitles");
      const optVid = document.getElementById("wizard-opt-video-only");
      if (optSub && optVid) {
        optSub.onclick = () => {
          wizardData.subtitlesWorkflow = true;
          optSub.classList.add("is-selected");
          optSub.querySelector("span:last-child")?.classList.remove("opacity-0");
          optVid.classList.remove("is-selected");
          optVid.querySelector("span:last-child")?.classList.add("opacity-0");
        };

        optVid.onclick = () => {
          wizardData.subtitlesWorkflow = false;
          optVid.classList.add("is-selected");
          optVid.querySelector("span:last-child")?.classList.remove("opacity-0");
          optSub.classList.remove("is-selected");
          optSub.querySelector("span:last-child")?.classList.add("opacity-0");
        };
      }

      // Step 3 Inputs
      const inpName = document.getElementById("wizard-input-name");
      if (inpName) {
        inpName.oninput = (e) => { wizardData.projectName = e.target.value; };
      }

      const selLang = document.getElementById("wizard-select-lang");
      if (selLang) {
        selLang.onchange = (e) => { wizardData.language = e.target.value; };
      }

      const tglSpk = document.getElementById("wizard-toggle-diarize");
      if (tglSpk) {
        tglSpk.onchange = (e) => { wizardData.speakerDetection = e.target.checked; };
      }

      const selPreset = document.getElementById("wizard-select-preset");
      if (selPreset) {
        selPreset.onchange = (e) => { wizardData.presetId = e.target.value; };
      }

      const selAspect = document.getElementById("wizard-select-aspect");
      if (selAspect) {
        selAspect.onchange = (e) => { wizardData.aspectRatio = e.target.value; };
      }
    }
"""

    content = content.replace(js_target, wizard_js + "\n\n    function pushState() {", 1)

    # 4. Aggiornamento handler di apertura "+ Nuovo progetto" per lanciare il Wizard
    old_new_handler = """      const handleNewProjClick = () => {
        // In FASE 2: pulisce lo stato e apre l'editor pronto per il video (in FASE 3 aprirà il Wizard)
        window.closeCurrentProject(false);
        window.currentProjectId = null;
        window.currentProjectType = "subtitles";
        showEditorView();
        const vIn = document.getElementById("video-input");
        if (vIn) vIn.click();
      };"""

    new_new_handler = """      const handleNewProjClick = () => {
        // FASE 3: Lancia il Wizard a 4 Step
        openNewProjectWizard();
      };
      initWizardEventListeners();"""

    if old_new_handler not in content:
        print("Error: old_new_handler not found", file=sys.stderr)
        sys.exit(1)

    content = content.replace(old_new_handler, new_new_handler, 1)

    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"✓ FASE 3 (Wizard a 4 Step) applicata con successo a {INDEX_PATH}")

if __name__ == "__main__":
    main()
