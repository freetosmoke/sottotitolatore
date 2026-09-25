import re

def get_new_header():
    return '''  <!-- ================================================================= -->
  <!-- TOP BAR: GLOBAL PROFESSIONAL CONTROLS ONLY (REDESIGN 2026)        -->
  <!-- ================================================================= -->
  <header id="top-header" class="h-14 flex-shrink-0 border-b border-dark-700/80 bg-dark-900/90 backdrop-blur-xl px-4 flex items-center justify-between z-30 relative select-none">
    
    <!-- Left: Logo Sub Studio, Nome Progetto e Stato Discreto -->
    <div class="top-bar-left flex items-center gap-3 min-w-0">
      <div class="w-8 h-8 rounded-xl overflow-hidden shadow-lg shadow-cyan-500/20 border border-cyan-400/30 flex-shrink-0 bg-dark-950 flex items-center justify-center p-0.5">
        <img src="/app_icon.png" alt="Sub Studio Icon" class="w-full h-full object-cover rounded-[10px]">
      </div>
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <span class="text-sm font-extrabold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-cyan-300 bg-clip-text text-transparent leading-none">
            Sub Studio
          </span>
          <span class="text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded-md bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-cyan-300 border border-cyan-500/40">PRO</span>
          
          <!-- Stato Progetto Discreto (Modificato / Sincronizzato) -->
          <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-dark-800/80 border border-dark-700 text-[10px] font-mono">
            <span id="header-project-status-dot" class="project-status-dot"></span>
            <span id="header-project-status-text" class="text-slate-300 font-medium">Sincronizzato</span>
          </div>

          <!-- Autosave Badge originale (per trigger JS) -->
          <span id="autosave-badge" class="hidden text-[10px] items-center gap-1 font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span id="autosave-text">Autosalvato</span>
          </span>
        </div>
        <p class="text-[11px] text-slate-400 leading-tight truncate flex items-center gap-1.5 mt-0.5">
          <span class="text-slate-500">Video:</span>
          <span id="header-project-name" class="text-slate-300 font-medium truncate">Nessun video caricato</span>
        </p>
      </div>
    </div>

    <!-- Center: Azioni Rapide Globali (Undo / Redo / Salva) -->
    <div class="top-bar-center flex items-center gap-1.5 bg-dark-950/70 border border-dark-700/70 p-1 rounded-xl">
      <button id="btn-top-undo" type="button" class="top-btn top-btn-icon-only text-slate-300 hover:text-white" title="Annulla ultima modifica (⌘Z)">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2m-15-7l4-4m-4 4l4 4"/></svg>
      </button>
      <button id="btn-top-redo" type="button" class="top-btn top-btn-icon-only text-slate-300 hover:text-white" title="Ripristina modifica annullata (⌘⇧Z)">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a5 5 0 00-5 5v2m15-7l-4-4m4 4l-4 4"/></svg>
      </button>
      <div class="h-4 w-px bg-dark-750 mx-0.5"></div>
      <button id="btn-top-save" type="button" class="top-btn text-cyan-300 hover:text-cyan-200 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20" title="Salva modifiche progetto o preset">
        <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/></svg>
        <span>Salva</span>
      </button>
    </div>

    <!-- Right: Menus (Strumenti, Vista), Scorciatoie, Coda, Ambiente, Esporta -->
    <div class="top-bar-right flex items-center gap-2">

      <!-- Menu Strumenti Professional Dropdown -->
      <div class="relative" id="tools-menu-container">
        <button id="btn-tools-menu" type="button" class="top-btn" title="Menu strumenti video, sottotitoli e progetto">
          <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879a3 3 0 11-4.242-4.242L10.758 4.88a3 3 0 014.242 4.242L12.12 12z"/>
          </svg>
          <span>Strumenti</span>
          <svg class="w-3 h-3 text-slate-400 transition-transform" id="tools-menu-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
          </svg>
        </button>

        <!-- Dropdown Categorizzato a Sezioni -->
        <div id="tools-dropdown" class="hidden pro-dropdown-menu w-72 space-y-2">
          
          <!-- Sezione VIDEO -->
          <div>
            <div class="menu-section-header">Video</div>
            <div class="space-y-1">
              <div class="flex items-center justify-between p-2 rounded-lg bg-dark-950/70 border border-dark-750">
                <div>
                  <div class="text-xs font-semibold text-slate-200">Rimozione silenzi</div>
                  <div class="text-[10px] text-slate-400">Taglio fisico sincronizzato</div>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" id="cfg-remove-silence" class="sr-only peer">
                  <div class="w-8 h-4 bg-dark-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-dark-950 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-cyan-500 peer-checked:after:bg-dark-950"></div>
                </label>
              </div>

              <!-- Parametri Rimozione Silenzio a scomparsa -->
              <div id="silence-threshold-container" class="hidden bg-dark-950/90 border border-dark-750 rounded-xl p-2.5 space-y-2 text-xs">
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <span class="text-[10.5px] text-slate-300">Soglia Rumore:</span>
                    <span id="label-silence-noise-db" class="text-[11px] font-mono font-bold text-cyan-300">-38 dB</span>
                  </div>
                  <input type="range" id="cfg-silence-noise-db" min="-50" max="-20" step="1" value="-38" class="w-full accent-cyan-400 h-1 bg-dark-800 rounded">
                </div>
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <span class="text-[10.5px] text-slate-300">Durata Minima:</span>
                    <span id="label-silence-threshold" class="text-[11px] font-mono font-bold text-cyan-300">0.40 s</span>
                  </div>
                  <input type="range" id="cfg-silence-threshold" min="0.2" max="1.5" step="0.05" value="0.4" class="w-full accent-cyan-400 h-1 bg-dark-800 rounded">
                </div>
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <span class="text-[10.5px] text-slate-300">Margine (Padding):</span>
                    <span id="label-silence-padding" class="text-[11px] font-mono font-bold text-cyan-300">0.12 s</span>
                  </div>
                  <input type="range" id="cfg-silence-padding" min="0.05" max="0.25" step="0.01" value="0.12" class="w-full accent-cyan-400 h-1 bg-dark-800 rounded">
                </div>
                <div class="flex items-center justify-between pt-1 border-t border-dark-800">
                  <button type="button" id="btn-reset-silence-params" class="text-[10px] text-slate-400 hover:text-cyan-300 transition">Ripristina Default</button>
                  <span class="text-[9.5px] text-slate-500 font-mono">Pause &lt; 0.24s preservate</span>
                </div>
              </div>
            </div>
          </div>

          <div class="menu-divider"></div>

          <!-- Sezione SOTTOTITOLI -->
          <div>
            <div class="menu-section-header">Sottotitoli</div>
            <div class="space-y-1">
              <button type="button" onclick="window.switchInspectorTab('speaker'); document.getElementById('tools-dropdown').classList.add('hidden');" class="menu-item-btn">
                <span class="flex items-center gap-2">
                  <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"/></svg>
                  Rileva Speaker (AI)
                </span>
                <span class="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-1 rounded">AI</span>
              </button>
              <button type="button" onclick="window.switchInspectorTab('advanced'); document.getElementById('tools-dropdown').classList.add('hidden');" class="menu-item-btn">
                <span class="flex items-center gap-2">
                  <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 5v14m6-8h6m-3-4v8"/></svg>
                  Traduzione Automatica
                </span>
              </button>
            </div>
          </div>

          <div class="menu-divider"></div>

          <!-- Sezione PROGETTO -->
          <div>
            <div class="menu-section-header">Progetto</div>
            <div class="space-y-1">
              <button type="button" id="btn-reset-layout" class="menu-item-btn" title="Reimposta le finestre alle proporzioni predefinite">
                <span class="flex items-center gap-2">
                  <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                  Reimposta 4 Finestre
                </span>
                <span class="text-[10px] font-mono text-slate-400">Default</span>
              </button>
              <button type="button" id="btn-new-project" class="menu-item-btn danger" title="Chiudi il video corrente e svuota il progetto">
                <span class="flex items-center gap-2 text-rose-400">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  Nuovo Progetto (Chiudi Video)
                </span>
                <span class="text-[10px] font-mono text-rose-400 bg-rose-500/10 px-1 rounded">Svuota</span>
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- Menu Vista Dropdown -->
      <div class="relative" id="view-menu-container">
        <button id="btn-view-menu" type="button" class="top-btn" title="Gestione pannelli e visualizzazione">
          <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
          <span>Vista</span>
          <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
        </button>

        <div id="view-dropdown" class="hidden pro-dropdown-menu w-64 space-y-1">
          <div class="menu-section-header">Pannelli Workspace</div>
          <button type="button" id="btn-view-toggle-inspector" class="menu-item-btn">
            <span>Mostra / Nascondi Inspector</span>
            <span class="text-[10px] font-mono text-slate-400">⌥I</span>
          </button>
          <button type="button" id="btn-view-toggle-timeline" class="menu-item-btn">
            <span>Mostra / Nascondi Timeline</span>
            <span class="text-[10px] font-mono text-slate-400">⌥T</span>
          </button>
          <button type="button" id="btn-view-reset-layout" class="menu-item-btn">
            <span>Layout Predefinito</span>
            <span class="text-[10px] font-mono text-cyan-400">Reset</span>
          </button>
          <div class="menu-divider"></div>
          <div class="menu-section-header">Aspetto</div>
          <button type="button" id="btn-view-toggle-theme" class="menu-item-btn">
            <span>Alterna Tema Scuro / Chiaro</span>
            <span id="view-theme-indicator" class="text-xs">☀️</span>
          </button>
        </div>
      </div>

      <!-- Scorciatoie -->
      <button id="btn-open-shortcuts" type="button" class="top-btn" title="Guida scorciatoie da tastiera (Tasto ?)">
        <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
        <span class="hidden sm:inline">Scorciatoie</span>
        <span class="text-[9.5px] bg-dark-950 px-1 py-0.5 rounded text-slate-400 font-mono">?</span>
      </button>

      <!-- Coda Batch -->
      <button id="btn-open-batch" type="button" class="top-btn" title="Coda video da elaborare">
        <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
        <span class="hidden md:inline">Coda</span>
        <span id="header-batch-count" class="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-mono">0</span>
      </button>

      <!-- Ambiente / Bootstrap -->
      <button id="btn-open-bootstrap" type="button" class="top-btn top-btn-icon-only sm:w-auto sm:px-2.5" title="Stato ambiente Python e dipendenze">
        <span id="header-bootstrap-dot" class="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
        <span class="hidden sm:inline text-xs">Ambiente</span>
      </button>

      <!-- Hidden elements for JS backwards-compatibility -->
      <button id="btn-theme-toggle" type="button" class="hidden"><span id="theme-icon">☀️</span></button>
      <button id="btn-quick-upload" type="button" class="hidden"></button>
      <span id="header-preset-name" class="hidden"></span>
      <span id="preset-badge" class="hidden"></span>
      <button id="btn-lang-dropdown" type="button" class="hidden"><span id="header-lang-icon">🇮🇹</span><span id="header-lang-text">IT</span></button>
      <div id="header-lang-menu" class="hidden"></div>
      <button id="btn-open-settings" type="button" class="hidden"></button>
      <div id="dev-calib-sep" class="hidden"></div>
      <button id="btn-open-calibration" type="button" class="hidden"></button>

      <div class="h-4 w-px bg-dark-750 mx-0.5"></div>

      <!-- Export Settings (Quality & Speed - Compact) -->
      <div class="hidden lg:flex items-center gap-1.5 bg-dark-950 border border-dark-700/80 rounded-xl px-1.5 py-0.5">
        <select id="cfg-export-quality" class="bg-transparent text-cyan-300 font-semibold focus:outline-none cursor-pointer text-xs py-1" title="Qualità di rendering">
          <option value="standard" class="bg-dark-900 text-slate-200">Standard</option>
          <option value="high" selected class="bg-dark-900 text-slate-200">Alta</option>
          <option value="max" class="bg-dark-900 text-slate-200">Massima</option>
        </select>
        <span class="text-slate-600">|</span>
        <select id="cfg-export-speed" class="bg-transparent text-amber-300 font-semibold focus:outline-none cursor-pointer text-xs py-1" title="Velocità finale video esportato">
          <option value="0.5" class="bg-dark-900 text-slate-200">0.5x</option>
          <option value="0.75" class="bg-dark-900 text-slate-200">0.75x</option>
          <option value="1.0" selected class="bg-dark-900 text-slate-200">1.0x</option>
          <option value="1.25" class="bg-dark-900 text-slate-200">1.25x</option>
          <option value="1.5" class="bg-dark-900 text-slate-200">1.5x</option>
          <option value="2.0" class="bg-dark-900 text-slate-200">2.0x</option>
        </select>
      </div>

      <!-- Export Primary CTA -->
      <button id="btn-export" disabled class="btn-export-primary" title="Genera il video finale con i sottotitoli renderizzati">
        <svg class="w-3.5 h-3.5 text-slate-950" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span>Esporta Video</span>
      </button>

    </div>
  </header>'''

def get_new_inspector():
    return '''      <!-- ================================================================= -->
      <!-- PANEL 3 (RIGHT): INSPECTOR (REDESIGN 2026: TABS & CATEGORIES)      -->
      <!-- ================================================================= -->
      <div id="inspector-card" class="w-[340px] xl:w-[370px] 2xl:w-[390px] flex-shrink-0 bg-dark-900/90 rounded-2xl border border-dark-750 shadow-xl flex flex-col min-h-0 backdrop-blur-md select-none mode-basic">
        
        <!-- Collapsed Mode Vertical Bar -->
        <div class="inspector-collapsed-content hidden flex-col items-center justify-between py-3 px-1 h-full w-full">
          <button id="btn-expand-inspector" type="button" class="w-7 h-7 rounded-lg bg-dark-800 hover:bg-dark-750 text-slate-400 hover:text-white border border-dark-700 flex items-center justify-center transition cursor-pointer" title="Espandi Inspector (⌥I)">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <div class="mt-4 flex-1 flex items-center justify-center pointer-events-none select-none">
            <span class="text-[10px] uppercase font-bold tracking-widest text-slate-500 [writing-mode:vertical-rl] rotate-180 opacity-70">Inspector</span>
          </div>
        </div>

        <!-- Expanded Mode Content -->
        <div class="inspector-expanded-content flex-1 flex flex-col min-h-0">
          
          <!-- 1. Inspector Header -->
          <div class="inspector-head">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
              </svg>
              <h2 class="font-bold text-xs text-white leading-none">Inspector</h2>
              <!-- Preset Sync Status Badge -->
              <div id="preset-sync-status" class="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Sincronizzato</span>
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <!-- Switch Modalità Base / Avanzata -->
              <div class="mode-toggle-group">
                <button type="button" id="btn-mode-basic" class="mode-toggle-btn active" title="Mostra controlli essenziali">Base</button>
                <button type="button" id="btn-mode-advanced" class="mode-toggle-btn" title="Mostra tutti i parametri dettagliati">Avanzata</button>
              </div>

              <!-- Collapse Inspector Button -->
              <button id="btn-collapse-inspector" type="button" class="w-6 h-6 rounded-lg bg-dark-800 hover:bg-dark-750 text-slate-400 hover:text-white border border-dark-700 flex items-center justify-center transition cursor-pointer" title="Nascondi Inspector (⌥I)">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 2. Search Box Interna -->
          <div class="inspector-search-container relative">
            <svg class="w-3.5 h-3.5 text-slate-500 absolute left-5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input type="search" id="inspector-search-input" class="inspector-search-input" placeholder="⌕ Cerca impostazione (font, ombra, watermark...)" autocomplete="off">
          </div>

          <!-- 3. Category Tabs Navigation -->
          <div class="inspector-tabs-nav" role="tablist">
            <button type="button" id="tab-btn-text" class="inspector-tab-btn active" role="tab" aria-selected="true" title="Stile, Font, Colori, Testo">Testo</button>
            <button type="button" id="tab-btn-layout" class="inspector-tab-btn" role="tab" aria-selected="false" title="Posizione, Scala, Watermark">Layout</button>
            <button type="button" id="tab-btn-effects" class="inspector-tab-btn" role="tab" aria-selected="false" title="Filtri Video, Ombre, Highlighter">Effetti</button>
            <button type="button" id="tab-btn-audio" class="inspector-tab-btn" role="tab" aria-selected="false" title="Musica di sottofondo e Traccia">Audio</button>
            <button type="button" id="tab-btn-speaker" class="inspector-tab-btn" role="tab" aria-selected="false" title="Diarizzazione Vocale AI e Stili">Speaker</button>
            <button type="button" id="tab-btn-advanced" class="inspector-tab-btn" role="tab" aria-selected="false" title="Traduzione, Lingua, Opzioni Tecniche">Avanzate</button>
          </div>

          <!-- 4. Scrollable Tab Panes Container -->
          <div class="inspector-scroll-area">

            <!-- ========================================== -->
            <!-- TAB 1: TESTO & PRESET                      -->
            <!-- ========================================== -->
            <div id="tab-pane-text" class="tab-pane active space-y-3">
              
              <!-- Stile Preset Card -->
              <div class="studio-card">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/></svg>
                    Stile Preset
                  </span>
                  <span class="text-[10px] text-slate-500 font-mono">TextPreset</span>
                </div>
                <div>
                  <select id="select-active-preset" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2.5 py-1.5 text-slate-200 focus:border-cyan-400 focus:outline-none text-xs font-semibold cursor-pointer">
                  </select>
                </div>
                <div class="preset-toolbar-grid pt-2">
                  <button id="btn-reset-preset" type="button" class="preset-toolbar-btn bg-dark-800 hover:bg-dark-750 text-slate-400 hover:text-slate-200 cursor-pointer" title="Ripristina valori originali del preset">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    <span>Reset</span>
                  </button>
                  <button id="btn-save-as-new-preset" type="button" class="preset-toolbar-btn bg-dark-800 hover:bg-dark-750 text-slate-300 hover:text-white cursor-pointer" title="Crea un nuovo preset dai valori correnti">
                    <svg class="w-3 h-3 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    <span>Nuovo</span>
                  </button>
                  <button id="btn-save-active-preset" type="button" class="preset-toolbar-btn bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-dark-950 !border-cyan-300 font-bold shadow-sm cursor-pointer" title="Salva modifiche sul preset">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/></svg>
                    <span>Salva</span>
                  </button>
                  <button id="btn-delete-active-preset" type="button" class="preset-toolbar-btn bg-dark-800 hover:bg-rose-950/40 text-rose-400 hover:text-rose-300 cursor-pointer" title="Elimina definitivamente questo preset">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    <span>Elimina</span>
                  </button>
                </div>
              </div>

              <!-- Tipografia Card -->
              <div class="studio-card space-y-3">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"/></svg>
                    Tipografia &amp; Stili
                  </span>
                </div>

                <!-- Hidden legacy font controls for JS integrity -->
                <div class="hidden">
                  <select id="cfg-font-name"><option value="Alata">Alata</option><option value="Raleway">Raleway</option></select>
                  <select id="cfg-pattern"><option value="Bold">Bold</option><option value="Normal">Normal</option></select>
                </div>

                <!-- Testo normale -->
                <div class="space-y-1.5 p-2 rounded-xl bg-dark-950/60 border border-dark-750">
                  <div class="text-[10px] uppercase tracking-wider font-bold text-slate-400">Testo Normale</div>
                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="text-slate-500 text-[10px] block mb-0.5">Font</label>
                      <select id="cfg-normal-font" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs"></select>
                    </div>
                    <div>
                      <label class="text-slate-500 text-[10px] block mb-0.5">Variante</label>
                      <select id="cfg-normal-variant" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs">
                        <option value="Light" selected>Light</option>
                        <option value="Regular">Regular</option>
                        <option value="Medium">Medium</option>
                        <option value="SemiBold">SemiBold</option>
                        <option value="Bold">Bold</option>
                        <option value="Italic">Italic</option>
                      </select>
                    </div>
                  </div>
                  <div class="flex items-center justify-between pt-1">
                    <span class="text-[11px] text-slate-400">Colore testo</span>
                    <div class="flex items-center gap-1.5">
                      <button type="button" class="btn-open-color-picker text-[10px] px-2 py-0.5 rounded bg-dark-900 hover:bg-dark-800 text-slate-300 border border-dark-700 flex items-center gap-1 cursor-pointer" data-target="cfg-normal-color">
                        <span class="w-2.5 h-2.5 rounded-full border border-dark-600 bg-white" id="swatch-preview-cfg-normal-color"></span>
                        <span>RGB</span>
                      </button>
                      <input type="color" id="cfg-normal-color" value="#FFFFFF" class="w-6 h-5 p-0 bg-transparent border-0 rounded cursor-pointer">
                    </div>
                  </div>
                </div>

                <!-- Parola chiave -->
                <div class="space-y-1.5 p-2 rounded-xl bg-dark-950/60 border border-dark-750">
                  <div class="text-[10px] uppercase tracking-wider font-bold text-amber-400">Parola Chiave</div>
                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="text-slate-500 text-[10px] block mb-0.5">Font</label>
                      <select id="cfg-keyword-font" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs"></select>
                    </div>
                    <div>
                      <label class="text-slate-500 text-[10px] block mb-0.5">Variante</label>
                      <select id="cfg-keyword-variant" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs">
                        <option value="Light">Light</option>
                        <option value="Regular">Regular</option>
                        <option value="Medium">Medium</option>
                        <option value="SemiBold" selected>SemiBold</option>
                        <option value="Bold">Bold</option>
                        <option value="Italic">Italic</option>
                      </select>
                    </div>
                  </div>
                  <div class="flex items-center justify-between pt-1">
                    <span class="text-[11px] text-slate-400">Colore keyword</span>
                    <div class="flex items-center gap-1.5">
                      <button type="button" class="btn-open-color-picker text-[10px] px-2 py-0.5 rounded bg-dark-900 hover:bg-dark-800 text-slate-300 border border-dark-700 flex items-center gap-1 cursor-pointer" data-target="cfg-keyword-color">
                        <span class="w-2.5 h-2.5 rounded-full border border-dark-600 bg-white" id="swatch-preview-cfg-keyword-color"></span>
                        <span>RGB</span>
                      </button>
                      <input type="color" id="cfg-keyword-color" value="#FFFFFF" class="w-6 h-5 p-0 bg-transparent border-0 rounded cursor-pointer">
                    </div>
                  </div>
                </div>

                <!-- Font Actions -->
                <div class="flex items-center justify-between gap-2 pt-1">
                  <button type="button" id="btn-open-font-browser" class="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 px-2 py-1 rounded bg-dark-950 border border-dark-700">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <span>Esplora Font</span>
                  </button>
                  <input type="file" id="font-file-input" accept=".ttf,.otf,.woff2" class="hidden">
                  <button type="button" id="btn-upload-font" class="text-[11px] text-amber-400 hover:text-amber-300 flex items-center gap-1 px-2 py-1 rounded bg-dark-950 border border-dark-700">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    <span>Carica font</span>
                  </button>
                  <span id="font-upload-status" class="text-[10px] text-slate-400 font-mono"></span>
                </div>

                <!-- Evidenziazione & Animazione -->
                <div class="grid grid-cols-2 gap-2 pt-1 border-t border-dark-750">
                  <div>
                    <label class="text-slate-400 text-[10.5px] block mb-1">Evidenziazione</label>
                    <select id="cfg-keyword-mode" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs">
                      <option value="automatic" selected>Automatico</option>
                      <option value="manual">Manuale</option>
                      <option value="off">Disattivato</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-slate-400 text-[10.5px] block mb-1">Animazione</label>
                    <select id="cfg-word-animation" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs">
                      <option value="none" selected>Nessuna</option>
                      <option value="pop">💥 Pop</option>
                      <option value="scale">🔍 Scale</option>
                      <option value="fade">🎤 Fade</option>
                      <option value="slide_up">⬆️ Slide Up</option>
                      <option value="slide_down">⬇️ Slide Down</option>
                    </select>
                  </div>
                </div>

                <!-- Capitalizzazione -->
                <div class="space-y-1.5 pt-1 border-t border-dark-750">
                  <div class="flex items-center justify-between">
                    <label class="text-slate-400 text-[10.5px]">Capitalizzazione</label>
                    <input type="checkbox" id="cfg-all-caps" class="hidden">
                    <div class="flex gap-1">
                      <button type="button" id="btn-apply-caps-chunk" class="text-[10px] px-1.5 py-0.5 rounded bg-dark-800 hover:bg-dark-750 text-slate-300">Blocco</button>
                      <button type="button" id="btn-apply-caps-all" class="text-[10px] px-1.5 py-0.5 rounded bg-dark-800 hover:bg-amber-500/20 text-slate-300">Tutti</button>
                    </div>
                  </div>
                  <select id="cfg-capitalization-mode" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs">
                    <option value="original" selected>Originale (Trascrizione)</option>
                    <option value="all_caps">TUTTO MAIUSCOLO</option>
                    <option value="title_case">Iniziali Maiuscole</option>
                    <option value="all_lower">tutto minuscolo</option>
                  </select>
                </div>

                <!-- Opzioni Avanzate Testo (Spaziatura lettere & Layout righe) -->
                <div class="inspector-advanced-only space-y-2 pt-2 border-t border-dark-750/70">
                  <div class="text-[10px] uppercase font-bold tracking-wider text-cyan-400">Layout Sottotitoli Avanzato</div>
                  <div class="flex items-center justify-between">
                    <span class="text-slate-400 text-[11px]">Spaziatura lettere:</span>
                    <input type="number" id="cfg-letter-spacing" value="0" min="-5" max="20" class="w-16 bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                  </div>
                  <div class="grid grid-cols-3 gap-1.5">
                    <div>
                      <label class="text-[9.5px] text-slate-400 block">Min parole</label>
                      <input type="number" id="cfg-min-words" value="2" min="1" max="50" class="w-full bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                    </div>
                    <div>
                      <label class="text-[9.5px] text-slate-400 block">Max parole</label>
                      <input type="number" id="cfg-max-words" value="7" min="1" max="50" class="w-full bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                    </div>
                    <div>
                      <label class="text-[9.5px] text-slate-400 block">N. righe</label>
                      <input type="number" id="cfg-num-lines" value="2" min="1" max="2" class="w-full bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                    </div>
                  </div>
                </div>

              </div>

            </div>

            <!-- ========================================== -->
            <!-- TAB 2: LAYOUT & WATERMARK                  -->
            <!-- ========================================== -->
            <div id="tab-pane-layout" class="tab-pane space-y-3">
              
              <!-- Posizione & Scala Card -->
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/></svg>
                    Posizione &amp; Scala Sottotitoli
                  </span>
                </div>
                
                <div class="grid grid-cols-3 gap-2">
                  <div>
                    <label class="text-[10px] text-slate-400 block mb-0.5">Size CapCut</label>
                    <input type="number" step="0.5" id="cfg-capcut-size" value="10" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    <input type="hidden" id="cfg-fs-sub" value="55">
                  </div>
                  <div>
                    <label class="text-[10px] text-slate-400 block mb-0.5">Scala %</label>
                    <input type="number" id="cfg-sub-scale" value="100" min="10" max="500" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                  </div>
                  <div>
                    <label class="text-[10px] text-slate-400 block mb-0.5">Rotazione</label>
                    <input type="number" id="cfg-sub-rot" value="0" min="-180" max="180" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-2 pt-1 border-t border-dark-750">
                  <div>
                    <label class="text-[10px] text-slate-400 block mb-0.5">Posizione X (0 = Centro)</label>
                    <input type="number" id="cfg-sub-x" value="0" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                  </div>
                  <div>
                    <label class="text-[10px] text-slate-400 block mb-0.5">Posizione Y (Neg = Basso)</label>
                    <input type="number" id="cfg-sub-y" value="-418" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                  </div>
                </div>
              </div>

              <!-- Watermark Tag Card (Contestuale) -->
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/></svg>
                    Watermark / Overlay Canale
                  </span>
                </div>

                <!-- Empty CTA: visibile solo se non c'è watermark -->
                <div id="wm-empty-cta" class="studio-empty-state">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4"/></svg>
                  <div class="studio-empty-state-title">Nessun Watermark</div>
                  <div class="studio-empty-state-desc">Aggiungi il tuo @handle o tag canale sul video.</div>
                  <button type="button" id="btn-add-watermark" class="tl-head-btn tl-btn-primary">
                    + Aggiungi Watermark
                  </button>
                </div>

                <!-- Controlli Watermark: visibili quando attivo -->
                <div id="wm-controls-container" class="hidden space-y-2.5">
                  <div>
                    <label class="text-[10px] text-slate-400 block mb-1">Testo Watermark (es. @nomecanale)</label>
                    <input type="text" id="cfg-wm-text" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs">
                  </div>

                  <div class="grid grid-cols-3 gap-2">
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Size CapCut</label>
                      <input type="number" step="0.5" id="cfg-capcut-wm-size" value="5" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                      <input type="hidden" id="cfg-fs-wm" value="31">
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Scala %</label>
                      <input type="number" id="cfg-wm-scale" value="114" min="10" max="500" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Rotazione</label>
                      <input type="number" id="cfg-wm-rot" value="0" min="-180" max="180" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-2 pt-1 border-t border-dark-750">
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Posizione X</label>
                      <input type="number" id="cfg-wm-x" value="0" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Posizione Y</label>
                      <input type="number" id="cfg-wm-y" value="-207" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    </div>
                  </div>

                  <div class="flex justify-end pt-1">
                    <button type="button" id="btn-remove-watermark" class="text-[10.5px] text-rose-400 hover:text-rose-300 transition">
                      ✕ Rimuovi Watermark
                    </button>
                  </div>
                </div>

              </div>

            </div>

            <!-- ========================================== -->
            <!-- TAB 3: EFFETTI & FILTRI                    -->
            <!-- ========================================== -->
            <div id="tab-pane-effects" class="tab-pane space-y-3">
              
              <!-- Filtri Video 2x2 Grid -->
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/></svg>
                    Filtri Video Rapidi
                  </span>
                </div>

                <input type="checkbox" id="chk-bw-filter" class="hidden">
                <input type="hidden" id="cfg-video-filter" value="none">
                
                <div class="filter-grid-2x2" id="video-filter-cards">
                  <button type="button" class="video-filter-card active" data-filter="none" title="Colori originali non modificati">
                    <svg class="w-4 h-4 text-cyan-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/></svg>
                    <span class="text-xs font-semibold text-slate-200">Originale</span>
                    <span class="text-[9.5px] text-slate-400">Colori naturali</span>
                  </button>

                  <button type="button" class="video-filter-card" data-filter="bw_cinema" title="Bianco e nero ad alto contrasto cinematografico">
                    <svg class="w-4 h-4 text-slate-300 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
                    <span class="text-xs font-semibold text-slate-200">B&amp;W Cinema</span>
                    <span class="text-[9.5px] text-slate-400">Alto contrasto</span>
                  </button>

                  <button type="button" class="video-filter-card" data-filter="bw_vintage" title="Tono vintage e pellicola analogica">
                    <svg class="w-4 h-4 text-amber-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"/></svg>
                    <span class="text-xs font-semibold text-slate-200">B&amp;W Film</span>
                    <span class="text-[9.5px] text-slate-400">Tono vintage</span>
                  </button>

                  <button type="button" class="video-filter-card" data-filter="vibrant" title="Colori saturi ottimizzati per Reels e TikTok">
                    <svg class="w-4 h-4 text-cyan-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    <span class="text-xs font-semibold text-slate-200">Vibrant Pop</span>
                    <span class="text-[9.5px] text-slate-400">Reels saturation</span>
                  </button>
                </div>
              </div>

              <!-- Effetti Sottotitoli (Contorno & Ombra) -->
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                    Contorno &amp; Ombra Sottotitolo
                  </span>
                </div>

                <div class="space-y-2">
                  <div>
                    <div class="flex items-center justify-between text-xs mb-1">
                      <span class="text-slate-400">Contorno Nero:</span>
                      <span id="label-stroke-val" class="font-mono text-cyan-300 font-bold">0.0</span>
                    </div>
                    <input type="range" id="cfg-stroke" min="0" max="6" step="0.5" value="0" class="w-full accent-cyan-400 h-1.5 bg-dark-950 rounded">
                  </div>

                  <div>
                    <div class="flex items-center justify-between text-xs mb-1">
                      <span class="text-slate-400">Ombra Testo:</span>
                      <span id="label-shadow-val" class="font-mono text-cyan-300 font-bold">0.0</span>
                    </div>
                    <input type="range" id="cfg-shadow" min="0" max="6" step="0.5" value="0" class="w-full accent-cyan-400 h-1.5 bg-dark-950 rounded">
                  </div>
                </div>
              </div>

              <!-- Effetto Highlighter (Box Parola) -->
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                    Highlighter Box Parola
                  </span>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" id="cfg-highlighter-enabled" class="sr-only peer">
                    <div class="w-8 h-4 bg-dark-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-dark-950 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-amber-400 peer-checked:after:bg-dark-950"></div>
                  </label>
                </div>

                <!-- Palette Rapide -->
                <div>
                  <div class="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1.5">Colori Rapidi Iconici</div>
                  <div class="grid grid-cols-5 gap-1.5">
                    <button type="button" class="hl-quick-color flex flex-col items-center p-1 rounded bg-dark-950 border border-dark-700 hover:border-amber-400" data-bg="#FFE600" data-text="#000000" title="Giallo Hormozi">
                      <span class="w-3.5 h-3.5 rounded-full bg-[#FFE600]"></span>
                      <span class="text-[9px] text-slate-400 mt-0.5">Hormozi</span>
                    </button>
                    <button type="button" class="hl-quick-color flex flex-col items-center p-1 rounded bg-dark-950 border border-dark-700 hover:border-emerald-400" data-bg="#00FF66" data-text="#000000" title="Verde Toxic">
                      <span class="w-3.5 h-3.5 rounded-full bg-[#00FF66]"></span>
                      <span class="text-[9px] text-slate-400 mt-0.5">Toxic</span>
                    </button>
                    <button type="button" class="hl-quick-color flex flex-col items-center p-1 rounded bg-dark-950 border border-dark-700 hover:border-cyan-400" data-bg="#00E5FF" data-text="#000000" title="Cyan SubStudio">
                      <span class="w-3.5 h-3.5 rounded-full bg-[#00E5FF]"></span>
                      <span class="text-[9px] text-slate-400 mt-0.5">Cyan</span>
                    </button>
                    <button type="button" class="hl-quick-color flex flex-col items-center p-1 rounded bg-dark-950 border border-dark-700 hover:border-pink-400" data-bg="#FF007A" data-text="#FFFFFF" title="Pink Viral">
                      <span class="w-3.5 h-3.5 rounded-full bg-[#FF007A]"></span>
                      <span class="text-[9px] text-slate-400 mt-0.5">Pink</span>
                    </button>
                    <button type="button" class="hl-quick-color flex flex-col items-center p-1 rounded bg-dark-950 border border-dark-700 hover:border-yellow-200" data-bg="#FFF3B0" data-text="#000000" title="Pastel Soft">
                      <span class="w-3.5 h-3.5 rounded-full bg-[#FFF3B0]"></span>
                      <span class="text-[9px] text-slate-400 mt-0.5">Pastel</span>
                    </button>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-2 pt-1 border-t border-dark-750">
                  <div class="flex items-center justify-between p-1.5 rounded bg-dark-950 border border-dark-700">
                    <span class="text-[10px] text-slate-400">Box RGB</span>
                    <input type="color" id="cfg-highlighter-box-color" value="#FFE600" class="w-5 h-5 p-0 bg-transparent border-0 rounded cursor-pointer">
                  </div>
                  <div class="flex items-center justify-between p-1.5 rounded bg-dark-950 border border-dark-700">
                    <span class="text-[10px] text-slate-400">Testo RGB</span>
                    <input type="color" id="cfg-highlighter-text-color" value="#000000" class="w-5 h-5 p-0 bg-transparent border-0 rounded cursor-pointer">
                  </div>
                </div>

                <div class="inspector-advanced-only grid grid-cols-3 gap-1.5 pt-1 border-t border-dark-750/70">
                  <div>
                    <label class="text-[9.5px] text-slate-400 block">Raggio</label>
                    <input type="number" id="cfg-highlighter-radius" value="8" min="0" max="30" class="w-full bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                  </div>
                  <div>
                    <label class="text-[9.5px] text-slate-400 block">Padding X</label>
                    <input type="number" id="cfg-highlighter-pad-x" value="10" min="0" max="40" class="w-full bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                  </div>
                  <div>
                    <label class="text-[9.5px] text-slate-400 block">Padding Y</label>
                    <input type="number" id="cfg-highlighter-pad-y" value="4" min="0" max="30" class="w-full bg-dark-950 border border-dark-700 rounded px-1.5 py-0.5 text-xs font-mono text-center">
                  </div>
                  <input type="hidden" id="cfg-highlighter-stroke" value="0">
                  <input type="hidden" id="cfg-highlighter-shadow" value="0">
                </div>

              </div>

            </div>

            <!-- ========================================== -->
            <!-- TAB 4: AUDIO & MUSICA                      -->
            <!-- ========================================== -->
            <div id="tab-pane-audio" class="tab-pane space-y-3">
              
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>
                    Musica di Sottofondo (BGM)
                  </span>
                  <span id="bgm-status-pill" class="text-[9.5px] px-1.5 py-0.5 rounded font-mono font-medium text-slate-400 bg-dark-800">Nessuna</span>
                </div>

                <input type="file" id="bgm-file-input" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg" class="hidden">
                <audio id="bgm-player" preload="auto" class="hidden"></audio>

                <!-- Track info box quando caricata -->
                <div id="bgm-track-info" class="hidden p-2 rounded-xl bg-dark-950 border border-dark-750 text-xs flex items-center justify-between">
                  <div class="min-w-0 mr-2">
                    <span id="bgm-filename" class="font-medium text-slate-200 truncate block">track.mp3</span>
                    <span id="bgm-duration" class="text-[10px] text-slate-400 font-mono">00:00</span>
                  </div>
                  <div class="flex items-center gap-1.5 flex-shrink-0">
                    <button type="button" id="btn-bgm-mute" class="text-xs px-2 py-1 rounded bg-dark-800 text-slate-300 hover:text-white" title="Muto/Attivo">🔊</button>
                    <button type="button" id="btn-remove-bgm" class="text-xs px-2 py-1 rounded bg-dark-800 hover:bg-rose-950/40 text-rose-400" title="Rimuovi Traccia">✕</button>
                  </div>
                </div>

                <button type="button" id="btn-upload-bgm" class="w-full py-2 px-3 rounded-xl bg-dark-950 hover:bg-dark-800 border border-dark-700 hover:border-cyan-500/40 text-cyan-400 font-semibold text-xs flex items-center justify-center gap-2 transition cursor-pointer">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                  <span>Carica Traccia Audio</span>
                </button>

                <!-- Volume & Fades -->
                <div class="space-y-2 pt-2 border-t border-dark-750">
                  <div>
                    <div class="flex items-center justify-between text-xs mb-1">
                      <span class="text-slate-400">Volume Musica:</span>
                      <span id="label-bgm-volume" class="font-mono text-cyan-300 font-bold">20%</span>
                    </div>
                    <input type="range" id="cfg-bgm-volume" min="0" max="100" step="1" value="20" class="w-full accent-cyan-400 h-1.5 bg-dark-950 rounded">
                  </div>

                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Fade In (sec)</label>
                      <input type="number" id="cfg-bgm-fade-in" min="0" max="10" step="0.5" value="1.0" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    </div>
                    <div>
                      <label class="text-[10px] text-slate-400 block mb-0.5">Fade Out (sec)</label>
                      <input type="number" id="cfg-bgm-fade-out" min="0" max="10" step="0.5" value="1.0" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs font-mono">
                    </div>
                  </div>
                </div>

              </div>

            </div>

            <!-- ========================================== -->
            <!-- TAB 5: SPEAKER & MULTI-VOCE UNIFICATO      -->
            <!-- ========================================== -->
            <div id="tab-pane-speaker" class="tab-pane space-y-3">
              
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                    Stili Speaker (Multi-Voce)
                  </span>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" id="cfg-speaker-styles-enabled" class="sr-only peer">
                    <div class="w-8 h-4 bg-dark-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-dark-950 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-cyan-500 peer-checked:after:bg-dark-950"></div>
                  </label>
                </div>

                <div class="space-y-2">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-slate-400">Numero Interlocutori:</span>
                    <select id="cfg-diarize-num-speakers" class="bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-slate-200 text-xs">
                      <option value="auto">Auto (AI)</option>
                      <option value="2">2 Speaker</option>
                      <option value="3">3 Speaker</option>
                      <option value="4">4 Speaker</option>
                    </select>
                  </div>

                  <button type="button" id="btn-run-diarization" class="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md cursor-pointer transition">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z"/></svg>
                    <span>Rileva Speaker con AI</span>
                  </button>
                  <button type="button" id="btn-diarize-speakers" class="hidden"></button>

                  <div id="speaker-analysis-status" class="p-2 rounded-xl bg-dark-950/80 border border-dark-750 text-center">
                    <div id="speaker-status-title" class="text-xs font-semibold text-slate-300">Nessuna analisi speaker eseguita</div>
                    <div id="speaker-status-desc" class="text-[10px] text-slate-500 mt-0.5">Clicca su 'Rileva Speaker con AI' per separare automaticamente le voci.</div>
                  </div>

                  <div class="flex items-center gap-2 pt-1 border-t border-dark-750">
                    <input type="checkbox" id="chk-auto-diarize" class="rounded border-dark-700 text-cyan-500">
                    <label for="chk-auto-diarize" class="text-[10.5px] text-slate-400 cursor-pointer">Esegui diarizzazione anche durante nuove trascrizioni</label>
                  </div>

                  <!-- Container degli speaker rilevati -->
                  <div id="detected-speakers-container" class="space-y-2 pt-2"></div>
                </div>

              </div>

            </div>

            <!-- ========================================== -->
            <!-- TAB 6: AVANZATE & TRADUZIONE               -->
            <!-- ========================================== -->
            <div id="tab-pane-advanced" class="tab-pane space-y-3">
              
              <div class="studio-card space-y-2.5">
                <div class="studio-card-head">
                  <span class="studio-card-title">
                    <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 5v14m6-8h6m-3-4v8"/></svg>
                    Lingua Sorgente &amp; Traduzione
                  </span>
                  <span id="trans-status-badge" class="text-[10px] text-slate-400 font-mono">Italiano</span>
                </div>

                <div class="space-y-2 text-xs">
                  <div>
                    <label class="text-slate-400 text-[10.5px] block mb-1">Lingua Audio Sorgente:</label>
                    <select id="cfg-audio-lang" class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1.5 text-slate-200 text-xs">
                      <option value="it" selected>Italiano</option>
                      <option value="en">Inglese</option>
                      <option value="es">Spagnolo</option>
                      <option value="fr">Francese</option>
                      <option value="de">Tedesco</option>
                      <option value="auto">Rilevamento Automatico</option>
                    </select>
                  </div>

                  <div class="flex items-center gap-2 pt-1 border-t border-dark-750">
                    <input type="checkbox" id="chk-translate-it" class="rounded border-dark-700 text-cyan-500">
                    <label for="chk-translate-it" class="text-[11px] text-slate-300 font-medium cursor-pointer">Traduci sottotitoli in Italiano</label>
                  </div>

                  <div id="trans-config-box" class="hidden space-y-2 pt-1">
                    <div id="gemini-key-box" class="space-y-1">
                      <label class="text-[10px] text-slate-400 block">Chiave API Gemini (Opzionale):</label>
                      <input type="password" id="cfg-gemini-key" placeholder="AIzaSy..." class="w-full bg-dark-950 border border-dark-700 rounded-lg px-2 py-1 text-xs text-slate-200">
                    </div>
                  </div>

                  <input type="checkbox" id="modal-chk-bw-filter" class="hidden">
                </div>

              </div>

            </div>

          </div>

        </div>

      </div>'''

def get_new_timeline_header():
    return '''      <!-- Header Toolbar Timeline con Gerarchia Visiva Chiara -->
      <div class="flex items-center justify-between border-b border-dark-700/80 pb-2 flex-shrink-0 mb-2">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <h2 class="font-bold text-xs text-white leading-none">Timeline</h2>
            <span class="text-[9px] bg-dark-750 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.5 rounded font-mono">Live</span>
          </div>
          <!-- Timecode Posizione / Durata -->
          <div class="flex items-center gap-1.5 bg-dark-950 border border-dark-700/80 px-2 py-0.5 rounded-lg font-mono text-[11px] text-cyan-300">
            <span class="text-slate-500 text-[9px] uppercase">POS:</span>
            <span id="tl-pos-time">00:00.00</span>
            <span class="text-slate-600">/</span>
            <span id="tl-total-time" class="text-slate-400">00:00.00</span>
          </div>
        </div>

        <!-- Controlli Zoom & Editing Pesati Gerarchicamente -->
        <div class="flex items-center gap-2">
          
          <!-- Zoom Bar -->
          <div class="flex items-center bg-dark-950 border border-dark-700/80 rounded-lg p-0.5 text-xs">
            <button id="btn-tl-zoom-out" type="button" class="w-5 h-5 flex items-center justify-center text-slate-300 hover:text-cyan-300 rounded transition" title="Riduci Zoom">−</button>
            <span id="tl-zoom-text" class="px-1.5 font-mono text-[10px] text-slate-300 min-w-[36px] text-center select-none">100%</span>
            <button id="btn-tl-zoom-in" type="button" class="w-5 h-5 flex items-center justify-center text-slate-300 hover:text-cyan-300 rounded transition" title="Aumenta Zoom">+</button>
            <button id="btn-tl-zoom-fit" type="button" class="px-1.5 h-5 flex items-center justify-center text-[10px] font-medium text-slate-300 hover:text-cyan-300 rounded transition" title="Adatta intera durata">Adatta</button>
          </div>

          <div class="h-4 w-px bg-dark-750"></div>

          <!-- Azione Primaria Timeline: Dividi / Split -->
          <button id="btn-split-playhead" type="button" class="tl-head-btn tl-btn-primary" title="Dividi sottotitolo al punto corrente del cursore (⌘B o tasto S)">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z"/></svg>
            <span>Dividi (Split)</span>
            <span class="text-[9px] bg-dark-900 px-1 py-0.5 rounded font-mono">⌘B</span>
          </button>

          <!-- Azione Secondaria: Elimina -->
          <button id="btn-delete-selected-chunk" type="button" class="tl-head-btn tl-btn-danger" title="Elimina il sottotitolo selezionato (Delete / Backspace)">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            <span>Elimina</span>
            <span class="text-[9px] bg-dark-900 px-1 py-0.5 rounded font-mono">Canc</span>
          </button>

          <!-- Azioni Discrete: Undo / Redo / Centra / Scorciatoie -->
          <button id="btn-tl-undo" type="button" class="tl-head-btn tl-btn-secondary" title="Annulla ultima modifica (⌘Z)">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2m-15-7l4-4m-4 4l4 4"/></svg>
            <span class="text-[9px] font-mono">⌘Z</span>
          </button>
          <button id="btn-tl-redo" type="button" class="tl-head-btn tl-btn-secondary" title="Ripristina modifica annullata (⌘⇧Z)">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a5 5 0 00-5 5v2m15-7l-4-4m4 4l-4 4"/></svg>
            <span class="text-[9px] font-mono">⌘⇧Z</span>
          </button>
          <button id="btn-tl-center" type="button" class="tl-head-btn tl-btn-secondary" title="Centra la timeline sulla testina (C)">
            <svg class="w-3 h-3 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
            <span>Centra</span>
          </button>
          <button id="btn-tl-shortcuts" type="button" class="tl-head-btn tl-btn-secondary" title="Guida scorciatoie da tastiera (?)">
            <span class="text-[10px] font-mono">?</span>
          </button>
        </div>
      </div>'''

def apply_clean():
    with open('web_static/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Stile CSS nell'head
    if 'redesign_studio.css' not in content:
        content = content.replace('</head>', '  <link rel="stylesheet" href="/redesign_studio.css">\n</head>')

    # 2. Script JS prima di </body>
    if 'redesign_studio.js' not in content:
        content = content.replace('</body>', '  <script src="/redesign_studio.js"></script>\n</body>')

    # 3. Sostituzione Header precisa tramite indici
    h_start = content.find('<header class="h-14')
    h_end = content.find('</header>') + len('</header>')
    if h_start != -1 and h_end > h_start:
        content = content[:h_start] + get_new_header() + content[h_end:]
        print("Header successfully replaced via exact string indexes.")

    # 4. Sostituzione Inspector Card precisa tramite indici
    insp_start = content.find('<div id="inspector-card"')
    btm_row_comment = content.find('<!-- Bottom Row: Docked Audio Timeline')
    if insp_start != -1 and btm_row_comment != -1:
        # Troviamo la fine esatta di inspector-card prima del commento
        sub_chunk = content[insp_start:btm_row_comment]
        last_div_idx = sub_chunk.rfind('</div>\n        </div>\n      </div>')
        if last_div_idx != -1:
            insp_end = insp_start + last_div_idx + len('</div>\n        </div>\n      </div>')
            content = content[:insp_start] + get_new_inspector() + content[insp_end:]
            print("Inspector Card successfully replaced via exact string indexes.")
        else:
            print("Could not find exact closing divs for inspector card!")

    # 5. Sostituzione Timeline Header
    tl_head_start = content.find('<!-- Header Toolbar Timeline -->')
    tl_scroll_start = content.find('<!-- Area Scrollabile della Timeline -->')
    if tl_head_start != -1 and tl_scroll_start != -1:
        content = content[:tl_head_start] + get_new_timeline_header() + '\n\n      ' + content[tl_scroll_start:]
        print("Timeline Header successfully replaced via exact string indexes.")

    with open('web_static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Clean refactoring completed successfully.")

if __name__ == '__main__':
    apply_clean()
