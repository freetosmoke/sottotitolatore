with open('web_static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. TOP BAR LABELS COLLAPSE
html = html.replace(
    '<span class="hidden sm:inline">Scorciatoie</span>',
    '<span class="top-btn-label-collapse hidden sm:inline">Scorciatoie</span>'
)
html = html.replace(
    '<span class="hidden md:inline">Coda</span>',
    '<span class="top-btn-label-collapse hidden md:inline">Coda</span>'
)
html = html.replace(
    '<span class="hidden sm:inline text-xs">Ambiente</span>',
    '<span class="top-btn-label-collapse hidden sm:inline text-xs">Ambiente</span>'
)

# 2. INSPECTOR HEADER 2-ROWS
old_head = '''          <!-- 1. Inspector Header (Drawer Contestuale Desktop) -->
          <div class="inspector-head">
            <div class="flex items-center gap-2 min-w-0">
              <svg class="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
              </svg>
              <h2 class="font-bold text-xs text-white leading-none tracking-tight flex-shrink-0">Proprietà</h2>
              <!-- Dynamic Context Badge -->
              <span id="drawer-context-badge" class="drawer-context-badge truncate">Globale</span>
              <!-- Preset Sync Status Badge -->
              <div id="preset-sync-status" class="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex-shrink-0">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Sincronizzato</span>
              </div>
            </div>
            
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <!-- Switch Modalità Base / Avanzata -->
              <div class="mode-toggle-group">
                <button type="button" id="btn-mode-basic" class="mode-toggle-btn active" title="Mostra controlli essenziali">Base</button>
                <button type="button" id="btn-mode-advanced" class="mode-toggle-btn" title="Mostra tutti i parametri dettagliati">Avanzata</button>
              </div>

              <!-- Close Contextual Drawer Button -->
              <button id="btn-collapse-inspector" type="button" class="w-6 h-6 rounded-lg bg-dark-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 border border-dark-700 hover:border-rose-500/40 flex items-center justify-center transition cursor-pointer" title="Chiudi Drawer Contestuale (Esc o ⌥I)">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>'''

new_head = '''          <!-- 1. Inspector Header (Drawer Contestuale Desktop a 2 Righe) -->
          <div class="inspector-head">
            <!-- Riga 1: Titolo, Badge Contestuale e Chiusura Desktop -->
            <div class="inspector-head-top">
              <div class="flex items-center gap-2 min-w-0">
                <svg class="w-3.5 h-3.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
                </svg>
                <h2 class="font-bold text-xs text-white uppercase tracking-wider">Proprietà</h2>
                <span id="drawer-context-badge" class="drawer-context-badge truncate">Globale</span>
              </div>
              <button id="btn-collapse-inspector" type="button" class="w-6 h-6 rounded-lg bg-dark-800 hover:bg-dark-700 text-slate-400 hover:text-white border border-dark-700 flex items-center justify-center transition cursor-pointer" title="Chiudi Drawer Contestuale (Esc o ⌥I)">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <!-- Riga 2: Switch Modalità Base / Avanzata e Stato Sincronizzazione -->
            <div class="inspector-head-sub">
              <div class="mode-toggle-group">
                <button type="button" id="btn-mode-basic" class="mode-toggle-btn active" title="Mostra controlli essenziali">Base</button>
                <button type="button" id="btn-mode-advanced" class="mode-toggle-btn" title="Mostra tutti i parametri dettagliati">Avanzata</button>
              </div>
              <div id="preset-sync-status" class="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Sincronizzato</span>
              </div>
            </div>
          </div>'''

if old_head in html:
    html = html.replace(old_head, new_head)
    print('Inspector header aggiornato a 2 righe ordinate')
else:
    print('Warning: old_head non trovato')

# 3. EMPTY STATE RAFFINATO
old_empty = '''        <!-- Professional Empty State -->
        <div id="editor-empty" class="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-3">
          <div class="w-12 h-12 rounded-2xl bg-dark-800 border border-dark-700 flex items-center justify-center text-cyan-400 shadow-inner">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"></path></svg>
          </div>
          <p class="text-sm font-semibold text-slate-300">Nessun sottotitolo presente</p>
          <p class="text-xs text-slate-500 max-w-sm">Trascina un video nell'anteprima o premi <b>Carica Video</b> in alto per avviare la trascrizione automatica.</p>
        </div>'''

new_empty = '''        <!-- Professional Empty State -->
        <div id="editor-empty" class="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-3">
          <div class="empty-state-card">
            <div class="empty-state-icon-box">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
            </div>
            <h3 class="text-sm font-bold text-white tracking-wide">Nessun Video nel Progetto</h3>
            <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
              Trascina un file video (MP4 o MOV) nell'anteprima oppure usa il pulsante sottostante per importarlo e avviare la sincronizzazione automatica.
            </p>
            <div class="mt-4 pt-2 w-full flex flex-col gap-2">
              <button type="button" onclick="document.getElementById('video-input').click();" class="w-full py-2 px-4 bg-dark-800 hover:bg-dark-750 text-slate-200 hover:text-white border border-dark-650 hover:border-cyan-500/40 font-semibold rounded-xl text-xs transition flex items-center justify-center gap-2 cursor-pointer shadow-sm">
                <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
                <span>Importa Video dal Computer</span>
              </button>
            </div>
            <div class="mt-4 grid grid-cols-3 gap-2 w-full pt-3 border-t border-dark-800 text-[10px] text-slate-400 font-medium">
              <div class="flex flex-col items-center gap-1">
                <span class="w-4 h-4 rounded-full bg-dark-800 border border-dark-700 flex items-center justify-center text-slate-300 font-bold text-[9px]">1</span>
                <span>Carica Video</span>
              </div>
              <div class="flex flex-col items-center gap-1">
                <span class="w-4 h-4 rounded-full bg-dark-800 border border-dark-700 flex items-center justify-center text-slate-300 font-bold text-[9px]">2</span>
                <span>Whisper AI</span>
              </div>
              <div class="flex flex-col items-center gap-1">
                <span class="w-4 h-4 rounded-full bg-dark-800 border border-dark-700 flex items-center justify-center text-slate-300 font-bold text-[9px]">3</span>
                <span>Stile &amp; Export</span>
              </div>
            </div>
          </div>
        </div>'''

if old_empty in html:
    html = html.replace(old_empty, new_empty)
    print('Empty state aggiornato')
else:
    print('Warning: old_empty non trovato')

# 4. WORKSPACE VIEWS CENTRATE E A TUTTA ALTEZZA
html = html.replace(
    '<div id="ws-view-project" class="workspace-view hidden flex-1 min-h-0 overflow-y-auto p-4 space-y-4">',
    '<div id="ws-view-project" class="workspace-view hidden flex-1 h-full min-h-0 overflow-y-auto">'
)
html = html.replace(
    '<div class="max-w-3xl mx-auto space-y-4">',
    '<div class="workspace-fullscreen-pane">'
)

html = html.replace(
    '<div id="ws-view-ai" class="workspace-view hidden flex-1 min-h-0 overflow-y-auto p-4 space-y-4">',
    '<div id="ws-view-ai" class="workspace-view hidden flex-1 h-full min-h-0 overflow-y-auto">'
)

html = html.replace(
    '<div id="ws-view-export" class="workspace-view hidden flex-1 min-h-0 overflow-y-auto p-4 space-y-4">',
    '<div id="ws-view-export" class="workspace-view hidden flex-1 h-full min-h-0 overflow-y-auto">'
)

with open('web_static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Aggiornamento completato con successo!')
