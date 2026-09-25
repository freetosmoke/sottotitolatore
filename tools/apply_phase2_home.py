#!/usr/bin/env python3
"""
tools/apply_phase2_home.py
Applica l'implementazione della FASE 2: HOME / PROJECT LIBRARY in web_static/index.html.
Preserva integralmente:
- Tutti i 343 ID DOM esistenti
- Il Subtitle Editor con la gestione parola-per-parola (SOPRA/SOTTO, frecce, grassetto ★, timestamp, speaker)
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

    # 1. Aggiunta Stili CSS dedicati per la Home
    css_target = "</style>\n\n</head>"
    if css_target not in content:
        print("Error: CSS target not found", file=sys.stderr)
        sys.exit(1)

    home_css = """
/* ========================================================================= */
/* SUBSTUDIO FASE 2 — HOME & PROJECT LIBRARY STYLES                          */
/* ========================================================================= */
.home-card-glow {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.home-card-glow:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px -8px rgba(0, 0, 0, 0.6), 0 0 20px -2px rgba(59, 130, 246, 0.2);
}
.home-thumb-container {
  aspect-ratio: 16 / 9;
  background-color: #0b0f17;
  position: relative;
  overflow: hidden;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.15);
  border-radius: 9999px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.3);
}
</style>

</head>"""
    content = content.replace(css_target, home_css, 1)

    # 2. Markup: Inserimento di #view-home e apertura di #view-editor
    body_target = '<body class="bg-dark-950 text-slate-100 h-screen flex flex-col antialiased overflow-hidden select-none">\n\n  <!-- Header -->'
    if body_target not in content:
        print("Error: body_target not found", file=sys.stderr)
        sys.exit(1)

    home_markup = """<body class="bg-dark-950 text-slate-100 h-screen flex flex-col antialiased overflow-hidden select-none">

  <!-- ======================================================================= -->
  <!-- VIEW 1: HOME / PROJECT LIBRARY (FASE 2)                                 -->
  <!-- ======================================================================= -->
  <div id="view-home" class="flex-1 flex min-h-0 overflow-hidden w-full h-full bg-dark-950 select-none">
    
    <!-- LEFT SIDEBAR (ChatGPT Style) -->
    <aside id="home-sidebar" class="w-64 xl:w-72 bg-dark-900 border-r border-dark-800 flex flex-col h-full flex-shrink-0 z-20">
      <!-- Brand Header -->
      <div class="h-16 px-5 border-b border-dark-800/80 flex items-center justify-between flex-shrink-0">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl overflow-hidden shadow-md shadow-blue-500/25 border border-blue-400/30 flex-shrink-0 bg-dark-950 flex items-center justify-center p-0.5">
            <img src="/app_icon.png" alt="SubStudio Icon" class="w-full h-full object-cover select-none rounded-[8px]">
          </div>
          <div>
            <div class="flex items-center gap-1.5 leading-none">
              <span class="text-sm font-extrabold tracking-tight text-white">SubStudio</span>
              <span class="text-[9px] uppercase tracking-wider font-extrabold px-1 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40">PRO</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation & Primary Action -->
      <div class="p-3.5 space-y-2 border-b border-dark-800/60 flex-shrink-0">
        <!-- Home Active Tab -->
        <button id="btn-home-nav-home" type="button" class="w-full px-3 py-2 bg-dark-800/90 text-white font-medium rounded-xl text-xs flex items-center gap-2.5 shadow-sm border border-dark-700/60 transition cursor-default">
          <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
          <span>Home</span>
        </button>

        <!-- Nuovo Progetto Primary CTA Button -->
        <button id="btn-home-new-project" type="button" class="w-full px-3 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25 transition active:scale-95 cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
          </svg>
          <span>Nuovo progetto</span>
        </button>
      </div>

      <!-- Progetti Recenti List (ChatGPT Style) -->
      <div class="flex-1 flex flex-col min-h-0 px-3 py-3 overflow-hidden">
        <div class="flex items-center justify-between px-2 pb-2 flex-shrink-0">
          <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Progetti</span>
          <span id="home-sidebar-count" class="text-[10px] font-mono text-slate-500 bg-dark-850 px-1.5 py-0.5 rounded border border-dark-800">0</span>
        </div>
        <div id="home-sidebar-projects-list" class="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
          <!-- Rendered dynamically -->
        </div>
      </div>

      <!-- Bottom Settings & Help Footer -->
      <div class="p-3 border-t border-dark-800/80 space-y-1 flex-shrink-0">
        <button id="btn-home-settings" type="button" class="w-full px-3 py-2 text-slate-400 hover:text-slate-200 hover:bg-dark-800/60 rounded-xl text-xs flex items-center gap-2.5 transition cursor-pointer">
          <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <span>Impostazioni</span>
        </button>
        <button id="btn-home-help" type="button" class="w-full px-3 py-2 text-slate-400 hover:text-slate-200 hover:bg-dark-800/60 rounded-xl text-xs flex items-center gap-2.5 transition cursor-pointer">
          <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <span>Aiuto & Scorciatoie</span>
        </button>
      </div>
    </aside>

    <!-- MAIN HOME STAGE -->
    <main class="flex-1 flex flex-col min-h-0 overflow-y-auto bg-dark-950 p-6 xl:p-8 space-y-7 custom-scrollbar">
      
      <!-- Top Search & User Bar -->
      <div class="flex items-center justify-between gap-4 flex-shrink-0">
        <div class="relative w-80 max-w-full">
          <svg class="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input id="home-search-input" type="text" placeholder="Cerca nei progetti..." class="w-full bg-dark-900 border border-dark-800 hover:border-dark-750 focus:border-blue-500/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none transition shadow-inner">
        </div>
        <div class="flex items-center gap-3">
          <button id="btn-home-shortcuts-trigger" type="button" class="w-8 h-8 rounded-xl bg-dark-900 border border-dark-800 text-slate-400 hover:text-white flex items-center justify-center transition cursor-pointer" title="Scorciatoie">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
            </svg>
          </button>
          <div class="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-300 font-bold text-xs flex items-center justify-center shadow-inner">
            S
          </div>
        </div>
      </div>

      <!-- Hero Banner -->
      <div class="relative bg-gradient-to-r from-dark-900 via-dark-850 to-dark-900 border border-dark-800/90 rounded-2xl p-6 xl:p-8 overflow-hidden shadow-2xl flex items-center justify-between gap-6 flex-shrink-0">
        <div class="space-y-3 z-10 max-w-xl">
          <h2 class="text-2xl xl:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Crea, edita, dai vita alle tue <span class="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">idee.</span>
          </h2>
          <p class="text-xs xl:text-sm text-slate-400 leading-relaxed">
            SubStudio è il tuo ambiente di lavoro per l'editing video, i sottotitoli e la post-produzione, tutto in un unico posto.
          </p>
        </div>

        <!-- Preview Mockup Image in Hero -->
        <div class="hidden lg:flex items-center gap-6 z-10">
          <div class="w-64 h-36 rounded-xl bg-dark-950 border border-dark-750 shadow-2xl overflow-hidden relative flex items-center justify-center group cursor-pointer" onclick="document.getElementById('btn-home-new-project').click()">
            <div class="absolute inset-0 bg-cover bg-center opacity-70 group-hover:scale-105 transition-transform duration-500" style="background-image: url('/app_icon.png'); background-size: contain; background-repeat: no-repeat; background-position: center;"></div>
            <div class="absolute inset-0 bg-dark-950/40 backdrop-blur-[2px]"></div>
            <div class="w-10 h-10 rounded-full bg-blue-600/90 border border-blue-400 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
              <svg class="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4l12 6-12 6V4z"/></svg>
            </div>
          </div>

          <div class="space-y-2.5 text-xs text-slate-300 font-medium">
            <div class="flex items-center gap-2">
              <span class="w-5 h-5 rounded-md bg-blue-500/15 text-blue-400 flex items-center justify-center text-[10px] font-bold">CC</span>
              <span>Sottotitoli intelligenti</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-5 h-5 rounded-md bg-cyan-500/15 text-cyan-400 flex items-center justify-center text-[10px]">✂️</span>
              <span>Editing video avanzato</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-5 h-5 rounded-md bg-indigo-500/15 text-indigo-400 flex items-center justify-center text-[10px]">⚡️</span>
              <span>Esportazione in alta qualità</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Progetti Recenti Section -->
      <div class="space-y-3.5">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            <span>Progetti recenti</span>
            <span id="home-grid-count-badge" class="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-dark-800 text-slate-400 border border-dark-750">0</span>
          </h3>
          <button id="btn-home-refresh-projects" type="button" class="text-xs text-blue-400 hover:text-blue-300 font-medium transition cursor-pointer flex items-center gap-1">
            <span>Aggiorna</span>
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          </button>
        </div>

        <!-- Grid of Projects -->
        <div id="home-projects-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
          <!-- Rendered dynamically -->
        </div>
      </div>

      <!-- Inizia da qui Section -->
      <div class="space-y-3 pt-2">
        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider">Inizia da qui</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Card 1: Nuovo progetto -->
          <div id="btn-home-quick-new" class="group p-4 rounded-2xl bg-dark-900 border border-dark-800 hover:border-blue-500/40 hover:bg-dark-850/80 transition-all cursor-pointer flex items-center justify-between shadow-lg">
            <div class="flex items-center gap-3.5">
              <div class="w-10 h-10 rounded-xl bg-blue-600/15 border border-blue-500/30 text-blue-400 flex items-center justify-center group-hover:scale-105 transition-transform flex-shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              </div>
              <div>
                <h4 class="text-xs font-bold text-white group-hover:text-blue-300 transition-colors">Nuovo progetto</h4>
                <p class="text-[11px] text-slate-400 mt-0.5">Importa un video e inizia a creare il tuo progetto.</p>
              </div>
            </div>
            <svg class="w-4 h-4 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </div>

          <!-- Card 2: Guida rapida -->
          <div id="btn-home-quick-guide" class="group p-4 rounded-2xl bg-dark-900 border border-dark-800 hover:border-blue-500/40 hover:bg-dark-850/80 transition-all cursor-pointer flex items-center justify-between shadow-lg">
            <div class="flex items-center gap-3.5">
              <div class="w-10 h-10 rounded-xl bg-indigo-600/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center group-hover:scale-105 transition-transform flex-shrink-0">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
              </div>
              <div>
                <h4 class="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors">Guida rapida</h4>
                <p class="text-[11px] text-slate-400 mt-0.5">Scopri come usare SubStudio in pochi passaggi.</p>
              </div>
            </div>
            <svg class="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </div>
        </div>
      </div>

    </main>
  </div> <!-- /#view-home -->

  <!-- ======================================================================= -->
  <!-- VIEW 2: EDITOR WORKSPACE (Con e Senza Sottotitoli)                       -->
  <!-- ======================================================================= -->
  <div id="view-editor" class="flex-1 flex flex-col min-h-0 overflow-hidden hidden w-full h-full">

  <!-- Header -->"""
    content = content.replace(body_target, home_markup, 1)

    # 3. Aggiunta pulsante "Home" nell'header dell'editor
    header_brand_target = """    <!-- Left: Studio Logo, Brand & Active Video Badge -->
    <div class="flex items-center space-x-3.5">
      <div class="w-9 h-9 rounded-xl overflow-hidden shadow-lg shadow-cyan-500/25 border border-cyan-400/30 flex-shrink-0 bg-dark-950 flex items-center justify-center p-0.5">
        <img src="/app_icon.png" alt="Sub Studio Icon" class="w-full h-full object-cover select-none rounded-[10px]">
      </div>"""

    header_brand_replacement = """    <!-- Left: Studio Logo, Brand & Active Video Badge -->
    <div class="flex items-center space-x-2.5">
      <!-- Pulsante Torna alla Home -->
      <button id="btn-header-home" type="button" class="group px-2.5 py-1.5 bg-dark-950/80 hover:bg-dark-800 text-slate-300 hover:text-white border border-dark-750 hover:border-blue-500/50 rounded-xl text-xs font-medium flex items-center gap-1.5 transition active:scale-95 cursor-pointer shadow-sm" title="Torna alla Home / Project Library">
        <svg class="w-3.5 h-3.5 text-blue-400 group-hover:text-blue-300 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        <span>Home</span>
      </button>
      <div class="w-9 h-9 rounded-xl overflow-hidden shadow-lg shadow-cyan-500/25 border border-cyan-400/30 flex-shrink-0 bg-dark-950 flex items-center justify-center p-0.5">
        <img src="/app_icon.png" alt="Sub Studio Icon" class="w-full h-full object-cover select-none rounded-[10px]">
      </div>"""

    if header_brand_target not in content:
        print("Error: header_brand_target not found", file=sys.stderr)
        sys.exit(1)

    content = content.replace(header_brand_target, header_brand_replacement, 1)

    # 4. Chiusura di #view-editor dopo </main>
    main_close_target = """        </div>
      </div>

    </div>

  </main>"""

    main_close_replacement = """        </div>
      </div>

    </div>

  </main>
  </div> <!-- /#view-editor -->"""

    if main_close_target not in content:
        print("Error: main_close_target not found", file=sys.stderr)
        sys.exit(1)

    content = content.replace(main_close_target, main_close_replacement, 1)

    # 5. Aggiunta motore JavaScript Project Library prima di pushState()
    js_target = "    window.clearProjectAutosave = window.closeCurrentProject;\n\n    function pushState() {"
    if js_target not in content:
        print("Error: js_target not found", file=sys.stderr)
        sys.exit(1)

    project_library_js = """    window.clearProjectAutosave = window.closeCurrentProject;

    // =========================================================================
    // SUBSTUDIO PROJECT LIBRARY & HOME ENGINE (FASE 2)
    // =========================================================================
    let cachedProjectsList = [];
    window.currentProjectId = null;
    window.currentProjectType = "subtitles";
    window.activeView = "home";

    function formatProjectDuration(secs) {
      if (!secs || isNaN(secs) || secs <= 0) return "00:00";
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }

    function formatProjectDate(isoStr) {
      if (!isoStr) return "Recente";
      try {
        const d = new Date(isoStr);
        const now = new Date();
        const isToday = d.toDateString() === now.toDateString();
        const timeStr = d.getHours().toString().padStart(2, "0") + ":" + d.getMinutes().toString().padStart(2, "0");
        if (isToday) return `Oggi · ${timeStr}`;
        const months = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"];
        return `${d.getDate()} ${months[d.getMonth()]} · ${timeStr}`;
      } catch (e) {
        return "Recente";
      }
    }

    window.showHomeView = function() {
      window.activeView = "home";
      const vHome = document.getElementById("view-home");
      const vEditor = document.getElementById("view-editor");
      if (vHome) vHome.classList.remove("hidden");
      if (vEditor) vEditor.classList.add("hidden");
      if (videoPlayer) {
        videoPlayer.pause();
      }
      loadProjectLibrary();
    };

    window.showEditorView = function() {
      window.activeView = "editor";
      const vHome = document.getElementById("view-home");
      const vEditor = document.getElementById("view-editor");
      if (vHome) vHome.classList.add("hidden");
      if (vEditor) vEditor.classList.remove("hidden");
      if (typeof updateTimelineLayout === "function") {
        setTimeout(updateTimelineLayout, 60);
      }
    };

    async function loadProjectLibrary() {
      try {
        const res = await fetch("/api/projects");
        const data = await res.json();
        if (data.success && Array.isArray(data.projects)) {
          cachedProjectsList = data.projects;
          renderHomeSidebarProjects(cachedProjectsList);
          renderHomeGridProjects(cachedProjectsList);
        }
      } catch (err) {
        console.warn("Caricamento Project Library fallito:", err);
      }
    }

    function renderHomeSidebarProjects(projects) {
      const container = document.getElementById("home-sidebar-projects-list");
      const countEl = document.getElementById("home-sidebar-count");
      if (countEl) countEl.innerText = projects.length;
      if (!container) return;

      container.innerHTML = "";
      if (projects.length === 0) {
        container.innerHTML = `<div class="p-3 text-center text-xs text-slate-500 italic">Nessun progetto</div>`;
        return;
      }

      projects.forEach((p) => {
        const item = document.createElement("div");
        const isCurrent = (p.id === window.currentProjectId);
        item.className = `group flex items-center justify-between p-2 rounded-xl transition cursor-pointer border ${
          isCurrent ? "bg-dark-800/90 border-blue-500/40 text-white" : "hover:bg-dark-800/60 border-transparent text-slate-300 hover:text-white"
        }`;
        
        const thumbHtml = p.thumbnail 
          ? `<img src="${p.thumbnail}" class="w-full h-full object-cover">`
          : `<div class="w-full h-full bg-dark-800 flex items-center justify-center text-[10px] text-slate-500 font-bold">▶</div>`;

        item.innerHTML = `
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            <div class="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0 border border-dark-750 bg-dark-950">
              ${thumbHtml}
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-xs font-semibold truncate group-hover:text-blue-300 transition-colors">${p.name || 'Progetto'}</div>
              <div class="text-[10px] text-slate-400 truncate">${formatProjectDate(p.updated_at)} · ${formatProjectDuration(p.duration)}</div>
            </div>
          </div>
          <button type="button" class="btn-sidebar-opts p-1 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition rounded-md hover:bg-dark-700" title="Opzioni">
            •••
          </button>
        `;

        item.onclick = () => openProjectById(p.id);

        const btnOpts = item.querySelector(".btn-sidebar-opts");
        if (btnOpts) {
          btnOpts.onclick = (e) => {
            e.stopPropagation();
            showProjectOptionsMenu(e, p);
          };
        }

        container.appendChild(item);
      });
    }

    function renderHomeGridProjects(projects) {
      const container = document.getElementById("home-projects-grid");
      const badgeCount = document.getElementById("home-grid-count-badge");
      if (badgeCount) badgeCount.innerText = projects.length;
      if (!container) return;

      container.innerHTML = "";
      if (projects.length === 0) {
        container.innerHTML = `
          <div class="col-span-full p-12 text-center bg-dark-900/60 rounded-2xl border border-dark-800 space-y-3">
            <div class="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 mx-auto flex items-center justify-center">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
            </div>
            <h4 class="text-sm font-bold text-white">Nessun progetto trovato</h4>
            <p class="text-xs text-slate-400 max-w-sm mx-auto">Non hai ancora nessun progetto salvato. Clicca su "Nuovo progetto" per importare il tuo primo video.</p>
            <button type="button" onclick="document.getElementById('btn-home-new-project').click()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition active:scale-95 cursor-pointer shadow-md shadow-blue-600/20">
              + Crea il tuo primo progetto
            </button>
          </div>
        `;
        return;
      }

      projects.forEach((p) => {
        const card = document.createElement("div");
        card.className = "home-card-glow group rounded-2xl bg-dark-900 border border-dark-800 hover:border-blue-500/50 overflow-hidden flex flex-col cursor-pointer transition-all";

        const isSubtitles = (p.type !== "video_only");
        const typeBadge = isSubtitles
          ? `<span class="text-[9.5px] font-bold text-blue-400 bg-blue-500/15 border border-blue-500/30 px-1.5 py-0.5 rounded flex items-center gap-1"><span>CC</span> Sottotitoli</span>`
          : `<span class="text-[9.5px] font-bold text-cyan-400 bg-cyan-500/15 border border-cyan-500/30 px-1.5 py-0.5 rounded flex items-center gap-1"><span>✂️</span> Video</span>`;

        const thumbContent = p.thumbnail
          ? `<img src="${p.thumbnail}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">`
          : `<div class="w-full h-full bg-dark-950 flex flex-col items-center justify-center text-slate-600 gap-1.5">
               <svg class="w-8 h-8 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
               <span class="text-[10px]">Video Media</span>
             </div>`;

        card.innerHTML = `
          <!-- Thumbnail Container -->
          <div class="home-thumb-container w-full relative">
            ${thumbContent}
            <div class="absolute inset-0 bg-gradient-to-t from-dark-950/80 via-transparent to-transparent opacity-60"></div>
            <!-- Duration Badge -->
            <div class="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-dark-950/85 backdrop-blur-md border border-dark-750 text-[10px] font-mono font-medium text-slate-200 shadow-sm">
              ${formatProjectDuration(p.duration)}
            </div>
            ${p.media && p.media.missing ? `<div class="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-rose-500/90 text-white text-[9px] font-bold shadow">Media mancante</div>` : ''}
          </div>

          <!-- Card Info -->
          <div class="p-3.5 flex flex-col justify-between flex-1 gap-2.5">
            <div>
              <h4 class="text-xs font-bold text-white group-hover:text-blue-300 transition-colors truncate" title="${p.name}">${p.name || 'Progetto senza titolo'}</h4>
              <p class="text-[10px] text-slate-400 mt-0.5">${formatProjectDate(p.updated_at)}</p>
            </div>
            
            <div class="flex items-center justify-between pt-1 border-t border-dark-800/80">
              ${typeBadge}
              <button type="button" class="btn-card-opts text-slate-400 hover:text-white p-1 rounded-lg hover:bg-dark-800 transition" title="Opzioni progetto">
                •••
              </button>
            </div>
          </div>
        `;

        card.onclick = () => openProjectById(p.id);

        const btnOpts = card.querySelector(".btn-card-opts");
        if (btnOpts) {
          btnOpts.onclick = (e) => {
            e.stopPropagation();
            showProjectOptionsMenu(e, p);
          };
        }

        container.appendChild(card);
      });
    }

    function showProjectOptionsMenu(e, p) {
      const existing = document.getElementById("project-context-menu");
      if (existing) existing.remove();

      const menu = document.createElement("div");
      menu.id = "project-context-menu";
      menu.className = "fixed z-50 bg-dark-900 border border-dark-750 rounded-xl shadow-2xl p-1.5 w-44 space-y-1 text-xs backdrop-blur-xl animate-scaleUp";
      menu.style.left = `${Math.min(window.innerWidth - 190, e.clientX)}px`;
      menu.style.top = `${Math.min(window.innerHeight - 150, e.clientY)}px`;

      menu.innerHTML = `
        <button type="button" class="btn-opt-open w-full px-2.5 py-1.5 rounded-lg text-left text-slate-200 hover:bg-dark-800 hover:text-white flex items-center gap-2 cursor-pointer transition">
          <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span>Apri progetto</span>
        </button>
        <button type="button" class="btn-opt-dup w-full px-2.5 py-1.5 rounded-lg text-left text-slate-200 hover:bg-dark-800 hover:text-white flex items-center gap-2 cursor-pointer transition">
          <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
          <span>Duplica</span>
        </button>
        <button type="button" class="btn-opt-rename w-full px-2.5 py-1.5 rounded-lg text-left text-slate-200 hover:bg-dark-800 hover:text-white flex items-center gap-2 cursor-pointer transition">
          <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
          <span>Rinomina</span>
        </button>
        <div class="h-px bg-dark-800 my-1"></div>
        <button type="button" class="btn-opt-del w-full px-2.5 py-1.5 rounded-lg text-left text-rose-400 hover:bg-rose-950/40 hover:text-rose-300 flex items-center gap-2 cursor-pointer transition">
          <svg class="w-3.5 h-3.5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          <span>Elimina</span>
        </button>
      `;

      menu.querySelector(".btn-opt-open").onclick = () => {
        menu.remove();
        openProjectById(p.id);
      };

      menu.querySelector(".btn-opt-dup").onclick = async () => {
        menu.remove();
        try {
          const res = await fetch(`/api/projects/${p.id}/duplicate`, { method: "POST" });
          const d = await res.json();
          if (d.success) loadProjectLibrary();
        } catch (err) {
          console.error("Duplicazione fallita:", err);
        }
      };

      menu.querySelector(".btn-opt-rename").onclick = async () => {
        menu.remove();
        const newName = prompt("Nuovo nome per il progetto:", p.name);
        if (!newName || newName.trim() === "" || newName.trim() === p.name) return;
        try {
          const res = await fetch("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: p.id, name: newName.trim() })
          });
          const d = await res.json();
          if (d.success) loadProjectLibrary();
        } catch (err) {
          console.error("Rinomina fallita:", err);
        }
      };

      menu.querySelector(".btn-opt-del").onclick = async () => {
        menu.remove();
        if (!confirm(`Sei sicuro di voler eliminare il progetto "${p.name}"?`)) return;
        try {
          const res = await fetch(`/api/projects/${p.id}`, { method: "DELETE" });
          const d = await res.json();
          if (d.success) {
            if (window.currentProjectId === p.id) {
              window.currentProjectId = null;
            }
            loadProjectLibrary();
          }
        } catch (err) {
          console.error("Eliminazione fallita:", err);
        }
      };

      document.body.appendChild(menu);
      const closeMenu = (evt) => {
        if (!menu.contains(evt.target)) {
          menu.remove();
          document.removeEventListener("pointerdown", closeMenu);
        }
      };
      setTimeout(() => document.addEventListener("pointerdown", closeMenu), 50);
    }

    async function openProjectById(projectId) {
      try {
        const res = await fetch(`/api/projects/${projectId}`);
        const data = await res.json();
        if (!data.success || !data.project) {
          alert("Impossibile caricare il progetto selezionato");
          return;
        }
        const p = data.project;
        window.currentProjectId = p.id;
        window.currentProjectType = p.type || "subtitles";

        // Ripristina nome progetto
        const hpn = document.getElementById("header-project-name");
        if (hpn) hpn.innerText = p.name || "Progetto";

        // Ripristina video
        const media = p.media || {};
        if (media.server_path) currentVideoPath = media.server_path;
        if (media.url && videoPlayer) {
          videoPlayer.src = media.url;
          if (videoContainer) videoContainer.classList.remove("hidden");
          if (uploadBox) uploadBox.classList.add("hidden");
        }
        if (media.duration) {
          currentVideoDuration = media.duration;
          originalVideoDuration = media.duration;
        }

        // Ripristina chunks
        if (p.chunks && Array.isArray(p.chunks)) {
          currentChunks = sanitizeChunks(p.chunks);
        } else {
          currentChunks = [];
        }
        if (p.allOriginalWords && Array.isArray(p.allOriginalWords)) {
          window.allOriginalWords = p.allOriginalWords;
        }

        // Ripristina snapshot o preset
        if (p.snapshot && typeof applyFullEditorSnapshot === "function") {
          applyFullEditorSnapshot(p.snapshot);
        } else if (p.activePresetId && typeof applyPresetById === "function") {
          applyPresetById(p.activePresetId);
        }

        // Renderizza chunks e timeline
        renderChunksList();
        renderTimelineBlocks();
        updateLiveSubtitleAtCurrentTime();
        if (statsBadge) statsBadge.innerText = `${currentChunks.length} chunk`;

        // Switch a view-editor
        showEditorView();

        const badge = document.getElementById("autosave-badge");
        const badgeText = document.getElementById("autosave-text");
        if (badge && badgeText) {
          badgeText.innerText = "Caricato";
          badge.classList.remove("hidden");
          badge.classList.add("flex");
        }
        if (typeof updatePreviewUploadButton === "function") {
          updatePreviewUploadButton();
        }
      } catch (err) {
        console.error("Errore apertura progetto:", err);
        alert("Errore durante l'apertura del progetto");
      }
    }

    async function saveCurrentProjectToLibrary() {
      if (!currentVideoPath && (!currentChunks || currentChunks.length === 0)) return null;
      const hpn = document.getElementById("header-project-name");
      const projName = hpn ? hpn.innerText : "Progetto";

      const payload = {
        id: window.currentProjectId || undefined,
        name: projName,
        type: window.currentProjectType || "subtitles",
        media: {
          filename: (currentVideoPath ? currentVideoPath.split("/").pop() : "video.mp4"),
          stored_filename: (currentVideoPath ? currentVideoPath.split("/").pop() : "video.mp4"),
          server_path: currentVideoPath || "",
          url: (videoPlayer && videoPlayer.src) ? videoPlayer.src : "",
          duration: currentVideoDuration || 0
        },
        chunks: currentChunks || [],
        allOriginalWords: window.allOriginalWords || [],
        activePresetId: activePresetId,
        snapshot: typeof getFullEditorSnapshot === "function" ? getFullEditorSnapshot() : {}
      };

      try {
        const res = await fetch("/api/projects", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success && data.project) {
          window.currentProjectId = data.project.id;
          return data.project;
        }
      } catch (err) {
        console.warn("Salvataggio su server fallito:", err);
      }
      return null;
    }

    function initHomeProjectLibrary() {
      // Setup listeners Home
      const btnHome = document.getElementById("btn-header-home");
      if (btnHome) {
        btnHome.onclick = async () => {
          await saveCurrentProjectToLibrary();
          showHomeView();
        };
      }

      const btnNewProj = document.getElementById("btn-home-new-project");
      const btnQuickNew = document.getElementById("btn-home-quick-new");
      const handleNewProjClick = () => {
        // In FASE 2: pulisce lo stato e apre l'editor pronto per il video (in FASE 3 aprirà il Wizard)
        window.closeCurrentProject(false);
        window.currentProjectId = null;
        window.currentProjectType = "subtitles";
        showEditorView();
        const vIn = document.getElementById("video-input");
        if (vIn) vIn.click();
      };
      if (btnNewProj) btnNewProj.onclick = handleNewProjClick;
      if (btnQuickNew) btnQuickNew.onclick = handleNewProjClick;

      const btnQuickGuide = document.getElementById("btn-home-quick-guide");
      const btnHelp = document.getElementById("btn-home-help");
      const btnShortcuts = document.getElementById("btn-home-shortcuts-trigger");
      const handleHelpClick = () => {
        const modal = document.getElementById("modal-shortcuts");
        if (modal) modal.classList.remove("hidden");
      };
      if (btnQuickGuide) btnQuickGuide.onclick = handleHelpClick;
      if (btnHelp) btnHelp.onclick = handleHelpClick;
      if (btnShortcuts) btnShortcuts.onclick = handleHelpClick;

      const btnRefresh = document.getElementById("btn-home-refresh-projects");
      if (btnRefresh) {
        btnRefresh.onclick = () => loadProjectLibrary();
      }

      const searchInput = document.getElementById("home-search-input");
      if (searchInput) {
        searchInput.oninput = (e) => {
          const q = (e.target.value || "").trim().toLowerCase();
          const filtered = cachedProjectsList.filter(p => (p.name || "").toLowerCase().includes(q));
          renderHomeSidebarProjects(filtered);
          renderHomeGridProjects(filtered);
        };
      }

      // Default: visualizza Home View all'avvio
      showHomeView();
    }

    function pushState() {"""

    content = content.replace(js_target, project_library_js, 1)

    # 6. Chiamata di initHomeProjectLibrary() al termine del loadPresetsFromApi
    init_target = """    loadPresetsFromApi(false).then(() => {
      checkAndRestoreAutosave();
    });"""

    init_replacement = """    loadPresetsFromApi(false).then(() => {
      checkAndRestoreAutosave();
      initHomeProjectLibrary();
    });"""

    if init_target not in content:
        print("Error: init_target not found", file=sys.stderr)
        sys.exit(1)

    content = content.replace(init_target, init_replacement, 1)

    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"✓ FASE 2 applicata con successo a {INDEX_PATH}")

if __name__ == "__main__":
    main()
