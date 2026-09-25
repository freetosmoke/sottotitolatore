import re

def get_sidebar_markup():
    return '''  <div class="app-workspace-body">
    
    <!-- ================================================================= -->
    <!-- DESKTOP NLE SIDEBAR (COLLAPSIBLE 210px / 58px)                    -->
    <!-- ================================================================= -->
    <aside id="sidebar-desktop" class="sidebar-desktop select-none">
      
      <!-- Top Section of Sidebar: Brand & Collapse Toggle -->
      <div class="sidebar-header">
        <div class="flex items-center gap-2 sidebar-header-title min-w-0">
          <div class="w-6 h-6 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-xs">
            ◆
          </div>
          <span class="text-xs font-bold text-slate-200 truncate">Sub Studio</span>
        </div>
        <button id="btn-toggle-sidebar" type="button" class="sidebar-toggle-btn" title="Espandi / Riduci Sidebar">
          <svg id="sidebar-toggle-icon" class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
          </svg>
        </button>
      </div>

      <!-- Navigation Workspaces List -->
      <div class="flex-1 overflow-y-auto overflow-x-hidden">
        
        <!-- WORKSPACES -->
        <div class="sidebar-group-title">Workspace</div>
        <div class="sidebar-nav-list">
          
          <!-- Progetto -->
          <button type="button" id="nav-ws-project" class="sidebar-nav-item" title="Panoramica Progetto e Video Attivo">
            <span class="sidebar-icon text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
            </span>
            <span class="sidebar-item-label">Progetto</span>
          </button>

          <!-- Sottotitoli (Default) -->
          <button type="button" id="nav-ws-subtitles" class="sidebar-nav-item active" title="Editor Sottotitoli &amp; Sincronizzazione Live">
            <span class="sidebar-icon text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
            </span>
            <span class="sidebar-item-label">Sottotitoli</span>
          </button>

          <!-- Stile & Tipografia -->
          <button type="button" id="nav-ws-style" class="sidebar-nav-item" title="Preset, Tipografia, Colori e Posizione">
            <span class="sidebar-icon text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"/></svg>
            </span>
            <span class="sidebar-item-label">Stile &amp; Preset</span>
          </button>

          <!-- Audio & Musica -->
          <button type="button" id="nav-ws-audio" class="sidebar-nav-item" title="Musica di sottofondo, Waveform e Silenzi">
            <span class="sidebar-icon text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>
            </span>
            <span class="sidebar-item-label">Audio &amp; Musica</span>
          </button>

          <!-- Speaker Diarization -->
          <button type="button" id="nav-ws-speaker" class="sidebar-nav-item" title="Riconoscimento Vocale Interlocutori (Diarizzazione)">
            <span class="sidebar-icon text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
            </span>
            <span class="sidebar-item-label">Speaker (Voci)</span>
          </button>

          <!-- Strumenti AI -->
          <button type="button" id="nav-ws-ai" class="sidebar-nav-item" title="Suite AI: Trascrizione Whisper, Traduzione, Silenzi">
            <span class="sidebar-icon text-amber-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            </span>
            <span class="sidebar-item-label">Strumenti AI</span>
          </button>

        </div>

        <!-- PRODUZIONE -->
        <div class="sidebar-group-title">Produzione</div>
        <div class="sidebar-nav-list">
          
          <button type="button" id="nav-ws-timeline" class="sidebar-nav-item" title="Focus Timeline &amp; Navigazione Traccia">
            <span class="sidebar-icon text-slate-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z"/></svg>
            </span>
            <span class="sidebar-item-label">Timeline</span>
          </button>

          <button type="button" id="nav-ws-export" class="sidebar-nav-item" title="Esporta Video Finale &amp; Coda di Rendering">
            <span class="sidebar-icon text-emerald-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            </span>
            <span class="sidebar-item-label">Esporta Video</span>
          </button>

        </div>

      </div>

      <!-- Footer: Setup & Ambiente -->
      <div class="sidebar-footer">
        <button type="button" id="nav-ws-setup" class="sidebar-nav-item" title="Stato Runtime, FFmpeg, Whisper e Sistema">
          <span class="sidebar-icon text-slate-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          </span>
          <span class="sidebar-item-label">Setup Sistema</span>
        </button>
      </div>

    </aside>

    <!-- WORKSPACE STAGE AREA (ADAPTIVE DESKTOP CANVAS) -->
    <div id="workspace-stage">'''

def apply():
    with open('web_static/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Trova fine di header e inizio di main
    main_start = content.find('<!-- Main Workspace')
    if main_start == -1:
        main_start = content.find('<main')

    # Sostituisci il tag <main ...> con la sidebar e il contenitore workspace
    main_tag_start = content.find('<main', main_start)
    main_tag_end = content.find('>', main_tag_start) + 1

    content = content[:main_start] + get_sidebar_markup() + '\n\n    <!-- Main Row of Workspace -->' + content[main_tag_end:]

    # 2. Chiudi la struttura prima di </main> o della chiusura del main
    main_close = content.find('</main>')
    if main_close != -1:
        content = content[:main_close] + '    </div>\n  </div>\n\n  <!-- Hidden Legacy Elements for 100% JS API Safety -->\n  <div class="hidden">\n    <button id="btn-close-settings"></button>\n    <button id="btn-load-default"></button>\n    <button id="btn-save-settings"></button>\n    <input type="checkbox" id="chk-dont-show-preset-startup">\n    <div id="modal-settings"></div>\n    <input id="new-preset-capcut-size">\n    <input id="new-preset-capcut-wm-size">\n    <input id="new-preset-fs-sub">\n    <input id="new-preset-fs-wm">\n    <div id="presets-list-container"></div>\n  </div>\n' + content[main_close + len('</main>'):]

    with open('web_static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Phase 1 Shell and Sidebar applied successfully.")

if __name__ == '__main__':
    apply()
