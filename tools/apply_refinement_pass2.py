with open('web_static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Timeline badge e icone sobrie
html = html.replace(
    '<span class="text-[9px] bg-dark-750 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.5 rounded font-mono">Live</span>',
    '<span class="text-[9px] bg-dark-800 text-slate-400 border border-dark-700 px-1.5 py-0.5 rounded font-mono uppercase tracking-wider">Timeline</span>'
)
html = html.replace(
    '<svg class="w-3 h-3 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>',
    '<svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>'
)

# 2. Arricchimento Workspace PROGETTO (Card Azioni Rapide sotto)
old_proj_end = '''            <div class="studio-card space-y-2">
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
      </div>'''

new_proj_end = '''            <div class="studio-card space-y-2">
              <div class="studio-card-title text-slate-200">Stato Trascrizione</div>
              <div class="space-y-1.5 text-xs">
                <div class="flex justify-between text-slate-300">
                  <span class="text-slate-400">Sottotitoli creati:</span>
                  <span id="proj-card-chunks-count" class="font-mono text-slate-200">0 blocchi</span>
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

          <!-- Card Azioni Rapide Workflow -->
          <div class="studio-card space-y-3">
            <div class="studio-card-title text-slate-200">Flusso di Lavoro &amp; Accesso Rapido</div>
            <div class="grid grid-cols-4 gap-2 text-xs">
              <button type="button" onclick="window.switchWorkspace('subtitles');" class="p-3 rounded-xl bg-dark-950/70 border border-dark-700 hover:border-cyan-500/40 text-left transition flex flex-col gap-1.5 group cursor-pointer">
                <span class="text-cyan-400 font-bold group-hover:underline">1. Editor Sottotitoli</span>
                <span class="text-[11px] text-slate-400">Visualizza testo, forme d'onda e sincronizzazione live</span>
              </button>
              <button type="button" onclick="window.switchWorkspace('style');" class="p-3 rounded-xl bg-dark-950/70 border border-dark-700 hover:border-cyan-500/40 text-left transition flex flex-col gap-1.5 group cursor-pointer">
                <span class="text-slate-200 font-bold group-hover:text-cyan-300">2. Stile &amp; Preset</span>
                <span class="text-[11px] text-slate-400">Personalizza font, animazioni CapCut, ombre e colori</span>
              </button>
              <button type="button" onclick="window.switchWorkspace('ai');" class="p-3 rounded-xl bg-dark-950/70 border border-dark-700 hover:border-cyan-500/40 text-left transition flex flex-col gap-1.5 group cursor-pointer">
                <span class="text-slate-200 font-bold group-hover:text-cyan-300">3. Strumenti AI</span>
                <span class="text-[11px] text-slate-400">Whisper, taglio silenzi e diarizzazione speaker</span>
              </button>
              <button type="button" onclick="window.switchWorkspace('export');" class="p-3 rounded-xl bg-dark-950/70 border border-dark-700 hover:border-cyan-500/40 text-left transition flex flex-col gap-1.5 group cursor-pointer">
                <span class="text-slate-200 font-bold group-hover:text-cyan-300">4. Esportazione</span>
                <span class="text-[11px] text-slate-400">Rendering finale GPU e download tracce SRT</span>
              </button>
            </div>
          </div>

        </div>
      </div>'''

if old_proj_end in html:
    html = html.replace(old_proj_end, new_proj_end)
    print('Workspace Progetto arricchito con flow card')
else:
    print('Warning: old_proj_end non trovato')

# 3. Arricchimento Workspace AI SUITE (Sezione HW Info sotto)
old_ai_end = '''              <p class="text-xs text-slate-400">Traduce automaticamente i sottotitoli in italiano o in altre lingue preservando il timing.</p>
              <button type="button" onclick="window.switchWorkspace('subtitles'); document.getElementById('btn-translate-all').click();" class="tl-head-btn tl-btn-secondary w-full justify-center">
                Configura Traduzione
              </button>
            </div>
          </div>
        </div>
      </div>'''

new_ai_end = '''              <p class="text-xs text-slate-400">Traduce automaticamente i sottotitoli in italiano o in altre lingue preservando il timing.</p>
              <button type="button" onclick="window.switchWorkspace('subtitles'); document.getElementById('btn-translate-all').click();" class="tl-head-btn tl-btn-secondary w-full justify-center">
                Configura Traduzione
              </button>
            </div>
          </div>

          <!-- Specifiche Modelli AI & Privacy Locale -->
          <div class="studio-card p-4 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-200 uppercase tracking-wider">Architettura Locale &amp; Privacy</span>
              <span class="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Zero Cloud Upload</span>
            </div>
            <p class="text-xs text-slate-400 leading-relaxed">
              Tutti i modelli Whisper e gli algoritmi di diarizzazione vocale vengono eseguiti interamente sul tuo chip Apple Silicon tramite accelerazione hardware locale. Nessun video, traccia audio o dato sensibile viene mai trasmesso all'esterno.
            </p>
          </div>

        </div>
      </div>'''

if old_ai_end in html:
    html = html.replace(old_ai_end, new_ai_end)
    print('Workspace AI arricchito con privacy card')
else:
    print('Warning: old_ai_end non trovato')

# 4. Arricchimento Workspace EXPORT (Dettagli Hardware sotto)
old_exp_end = '''            <p class="text-[11px] text-slate-500 font-mono">Accelerazione GPU Apple Silicon a 60fps · Anteprima in tempo reale</p>
          </div>
        </div>
      </div>'''

new_exp_end = '''            <p class="text-[11px] text-slate-500 font-mono">Accelerazione GPU Apple Silicon a 60fps · Anteprima in tempo reale</p>
          </div>

          <!-- Scheda Dettagli Encoder & Profilo Colore -->
          <div class="grid grid-cols-3 gap-3 text-xs">
            <div class="studio-card space-y-1">
              <span class="text-slate-400 text-[11px]">Motore Grafico:</span>
              <p class="font-semibold text-slate-200">VideoToolbox HW</p>
              <p class="text-[10.5px] text-slate-500">60 FPS fissi a zero dropped frames</p>
            </div>
            <div class="studio-card space-y-1">
              <span class="text-slate-400 text-[11px]">Sottotitoli Integrati:</span>
              <p class="font-semibold text-slate-200">Hardsub ASS Ultra-AA</p>
              <p class="text-[10.5px] text-slate-500">Rendering font vettoriale nativo</p>
            </div>
            <div class="studio-card space-y-1">
              <span class="text-slate-400 text-[11px]">Traccia Audio:</span>
              <p class="font-semibold text-slate-200">AAC 48kHz Stereo</p>
              <p class="text-[10.5px] text-slate-500">Normalizzazione volume e ducking</p>
            </div>
          </div>

        </div>
      </div>'''

if old_exp_end in html:
    html = html.replace(old_exp_end, new_exp_end)
    print('Workspace Export arricchito con encoder specs card')
else:
    print('Warning: old_exp_end non trovato')

with open('web_static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Pass 2 completato con successo!')
