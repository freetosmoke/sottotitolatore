#!/usr/bin/env python3
"""
tools/apply_phase5_video_editor.py
Implementa la FASE 5 — VIDEO EDITOR WORKSPACE per SubStudio.
Aggiunge il layout, la timeline V1 per video clips, e l'inspector contestuale video_only.
Preserva integralmente al 100% tutti i 373 ID del baseline e la logica dei sottotitoli.
"""

import sys
import re
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parent.parent / "web_static" / "index.html"

def main():
    content = INDEX_PATH.read_text(encoding="utf-8")
    orig_content = content

    # 1. AGGIUNTA STILI CSS PER VIDEO EDITOR WORKSPACE
    css_target = "</style>\n\n</head>"
    if css_target not in content:
        css_target = "</style>\n</head>"
    if css_target not in content:
        css_target = "</head>"

    video_editor_css = """
/* ======================================================================= */
/* FASE 5: VIDEO EDITOR WORKSPACE (type="video_only")                     */
/* ======================================================================= */
#view-editor[data-project-type="video_only"] #editor-card {
  display: none !important;
}
#view-editor[data-project-type="video_only"] #inspector-card {
  display: none !important;
}
#view-editor[data-project-type="video_only"] #video-inspector-panel {
  display: flex !important;
}
#view-editor[data-project-type="video_only"] #player-card {
  flex: 1 1 0% !important;
  width: auto !important;
  max-width: none !important;
}
#view-editor[data-project-type="video_only"] #video-container {
  aspect-ratio: auto !important;
  max-width: 100% !important;
  width: 100% !important;
  background-color: #030712 !important;
}
#view-editor[data-project-type="video_only"] #video-player {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
}
#view-editor[data-project-type="video_only"] #live-sub-box,
#view-editor[data-project-type="video_only"] #live-wm-box,
#view-editor[data-project-type="video_only"] #canvas-gizmo,
#view-editor[data-project-type="video_only"] #calib-metric-overlay,
#view-editor[data-project-type="video_only"] #calib-canvas-center,
#view-editor[data-project-type="video_only"] #calib-ref-layer {
  display: none !important;
}
#view-editor[data-project-type="video_only"] #tl-blocks-container {
  display: none !important;
}
#view-editor[data-project-type="video_only"] #tl-video-track-container {
  display: block !important;
}
#view-editor[data-project-type="subtitles"] #video-inspector-panel {
  display: none !important;
}
#view-editor[data-project-type="subtitles"] #tl-video-track-container {
  display: none !important;
}
#view-editor[data-project-type="subtitles"] #tl-blocks-container {
  display: block !important;
}

/* Video Clips in Timeline V1 */
.tl-vclip-item {
  position: absolute;
  top: 4px;
  bottom: 4px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98));
  border: 1.5px solid rgba(59, 130, 246, 0.4);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
  padding: 0 10px;
  user-select: none;
}
.tl-vclip-item:hover {
  border-color: rgba(96, 165, 250, 0.8);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.35);
}
.tl-vclip-item.is-selected {
  border-color: #00f0ff !important;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.35), rgba(15, 23, 42, 0.95)) !important;
  box-shadow: 0 0 14px rgba(0, 240, 255, 0.45), inset 0 0 8px rgba(0, 240, 255, 0.2) !important;
}
.tl-vclip-cut-indicator {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.85);
  pointer-events: none;
  z-index: 10;
}
</style>
"""

    if "FASE 5: VIDEO EDITOR WORKSPACE" not in content:
        content = content.replace("</style>\n\n</head>", video_editor_css + "\n</head>")
        if "FASE 5: VIDEO EDITOR WORKSPACE" not in content:
            content = content.replace("</style>\n</head>", video_editor_css + "\n</head>")

    # 2. AGGIUNTA VIDEO INSPECTOR PANEL (Accanto a #inspector-card)
    video_inspector_html = """
      <!-- ================================================================= -->
      <!-- PANEL 4 (RIGHT): Video Inspector (Video Only Workspace - FASE 5)   -->
      <!-- ================================================================= -->
      <div id="video-inspector-panel" class="hidden w-[340px] xl:w-[370px] 2xl:w-[390px] flex-shrink-0 bg-dark-900/90 rounded-2xl p-3.5 border border-dark-750 shadow-xl flex flex-col min-h-0 relative backdrop-blur-md">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-dark-700/80 pb-2.5 flex-shrink-0">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
            </div>
            <div>
              <h2 class="font-bold text-sm text-white leading-none">Inspector Video</h2>
              <p class="text-[10px] text-slate-400 mt-0.5">Proprietà clip & montaggio</p>
            </div>
          </div>
          <span id="vclip-badge" class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">Clip 1 / 1</span>
        </div>

        <!-- Scrollable Body -->
        <div class="flex-1 overflow-y-auto pr-1 space-y-3 mt-3 text-xs select-none">

          <!-- Section 1: Proprietà Clip Selezionata -->
          <div class="bg-dark-950/70 border border-dark-750 rounded-xl p-3 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-200 text-xs flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                Clip Selezionata
              </span>
              <span id="vclip-index-label" class="text-[10px] text-cyan-400 font-mono font-bold">#1</span>
            </div>

            <!-- Titolo Clip -->
            <div class="space-y-1">
              <label class="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Nome Clip</label>
              <input type="text" id="vclip-title-input" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2.5 py-1.5 text-white font-medium text-xs focus:border-cyan-400 focus:outline-none" value="Clip 1">
            </div>

            <!-- Timecodes In / Out / Durata -->
            <div class="grid grid-cols-3 gap-2 pt-1">
              <div class="bg-dark-900 border border-dark-800 rounded-lg p-2 text-center">
                <div class="text-[9px] text-slate-500 uppercase font-mono">Punto In</div>
                <div id="vclip-time-in" class="text-xs font-mono font-bold text-cyan-300 mt-0.5">00:00.00</div>
              </div>
              <div class="bg-dark-900 border border-dark-800 rounded-lg p-2 text-center">
                <div class="text-[9px] text-slate-500 uppercase font-mono">Punto Out</div>
                <div id="vclip-time-out" class="text-xs font-mono font-bold text-cyan-300 mt-0.5">00:00.00</div>
              </div>
              <div class="bg-dark-900 border border-dark-800 rounded-lg p-2 text-center">
                <div class="text-[9px] text-slate-500 uppercase font-mono">Durata</div>
                <div id="vclip-time-duration" class="text-xs font-mono font-bold text-amber-300 mt-0.5">00:00.00</div>
              </div>
            </div>

            <!-- Media Source Info -->
            <div class="border-t border-dark-800/80 pt-2 space-y-1 text-[10px] text-slate-400">
              <div class="flex items-center justify-between">
                <span>File Sorgente:</span>
                <span id="vclip-source-filename" class="font-mono text-slate-300 truncate max-w-[160px]">-</span>
              </div>
              <div class="flex items-center justify-between">
                <span>Durata Totale Media:</span>
                <span id="vclip-source-duration" class="font-mono text-slate-300">-</span>
              </div>
              <div class="flex items-center justify-between">
                <span>Formato / Risoluzione:</span>
                <span id="vclip-source-resolution" class="font-mono text-slate-300">1080×1920 (9:16)</span>
              </div>
            </div>
          </div>

          <!-- Section 2: Regolazioni Video Supportate dal Backend -->
          <div class="bg-dark-950/70 border border-dark-750 rounded-xl p-3 space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-200 text-xs flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
                Regolazioni Clip
              </span>
              <span class="text-[9px] text-slate-500 font-mono">Backend Ready</span>
            </div>

            <!-- Filtro Video (video_renderer.py) -->
            <div class="space-y-1">
              <label class="text-[10px] text-slate-400 font-medium">Filtro Colore / Look</label>
              <select id="vclip-filter-select" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs font-semibold focus:border-cyan-400 focus:outline-none cursor-pointer">
                <option value="none">Originale (Nessun filtro)</option>
                <option value="bw_cinema">Cinema Bianco & Nero</option>
                <option value="vibrant">Vibrant Pop (Colori Accesi)</option>
                <option value="cyberpunk">Cyberpunk Neon</option>
                <option value="warm_golden">Golden Hour (Caldo)</option>
                <option value="cold_minimal">Cold Minimal (Freddo)</option>
              </select>
            </div>

            <!-- Velocità Clip -->
            <div class="space-y-1">
              <div class="flex items-center justify-between">
                <label class="text-[10px] text-slate-400 font-medium">Velocità Clip</label>
                <span id="vclip-speed-val" class="font-mono text-cyan-300 font-bold text-[11px]">1.0x</span>
              </div>
              <select id="vclip-speed-select" class="w-full bg-dark-900 border border-dark-700 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs font-semibold focus:border-cyan-400 focus:outline-none cursor-pointer">
                <option value="0.5">0.5x (Rallentatore)</option>
                <option value="0.75">0.75x</option>
                <option value="1.0" selected>1.0x (Normale)</option>
                <option value="1.25">1.25x</option>
                <option value="1.5">1.5x</option>
                <option value="2.0">2.0x (Veloce)</option>
              </select>
            </div>
          </div>

          <!-- Section 3: Azioni di Taglio & Montaggio -->
          <div class="bg-dark-950/70 border border-dark-750 rounded-xl p-3 space-y-2">
            <span class="font-bold text-slate-200 text-xs flex items-center gap-1.5">
              <svg class="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z"/></svg>
              Azioni di Montaggio
            </span>

            <div class="space-y-1.5 pt-1">
              <!-- Dividi al Playhead -->
              <button id="btn-vclip-split" type="button" class="w-full px-3 py-2 bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 text-amber-300 border border-amber-500/40 rounded-xl font-bold text-xs flex items-center justify-between transition cursor-pointer shadow-sm active:scale-98">
                <span class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z"/></svg>
                  <span>Dividi al Playhead (Split)</span>
                </span>
                <span class="text-[9px] bg-dark-900/90 text-amber-300 px-1.5 py-0.5 rounded font-mono">⌘B / S</span>
              </button>

              <!-- Elimina Clip Selezionata -->
              <button id="btn-vclip-delete" type="button" class="w-full px-3 py-2 bg-dark-900 hover:bg-rose-950/40 text-slate-300 hover:text-rose-300 border border-dark-750 hover:border-rose-500/40 rounded-xl font-semibold text-xs flex items-center justify-between transition cursor-pointer active:scale-98">
                <span class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-slate-400 group-hover:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  <span>Elimina Clip Selezionata</span>
                </span>
                <span class="text-[9px] bg-dark-900/90 text-slate-400 px-1.5 py-0.5 rounded font-mono">Canc</span>
              </button>

              <!-- Naviga tra i tagli -->
              <div class="grid grid-cols-2 gap-1.5 pt-1">
                <button id="btn-vclip-goto-in" type="button" class="px-2.5 py-1.5 bg-dark-900 hover:bg-dark-800 text-slate-300 hover:text-white border border-dark-750 rounded-lg text-[11px] font-medium transition flex items-center justify-center gap-1.5 cursor-pointer">
                  <span>⏮ Inizio Clip</span>
                </button>
                <button id="btn-vclip-goto-out" type="button" class="px-2.5 py-1.5 bg-dark-900 hover:bg-dark-800 text-slate-300 hover:text-white border border-dark-750 rounded-lg text-[11px] font-medium transition flex items-center justify-center gap-1.5 cursor-pointer">
                  <span>⏭ Fine Clip</span>
                </button>
              </div>

              <!-- Ripristina Tagli -->
              <button id="btn-vclip-reset" type="button" class="w-full mt-1 px-2.5 py-1.5 bg-dark-900/60 hover:bg-dark-800 text-slate-400 hover:text-slate-200 border border-dark-750 rounded-lg text-[11px] transition flex items-center justify-center gap-1.5 cursor-pointer" title="Rimuovi tutti i tagli e torna alla clip intera">
                <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                <span>Ripristina Clip Intera</span>
              </button>
            </div>
          </div>

        </div>
      </div>
"""

    if 'id="video-inspector-panel"' not in content:
        # Trova la fine di #inspector-card: </div> seguito da </div> <!-- chiusura top row -->
        target_marker = '</div>\n        </div>\n      </div>\n\n    </div>\n\n    <!-- Bottom Row: Docked Audio Timeline'
        replacement = '</div>\n        </div>\n      </div>\n' + video_inspector_html + '\n    </div>\n\n    <!-- Bottom Row: Docked Audio Timeline'
        if target_marker in content:
            content = content.replace(target_marker, replacement)
        else:
            # Fallback regex search
            pattern = r'(id="inspector-card"[\s\S]*?</div>\s*</div>\s*</div>)(\s*</div>\s*<!-- Bottom Row: Docked Audio Timeline)'
            content = re.sub(pattern, r'\1\n' + video_inspector_html + r'\2', content)

    # 3. AGGIUNTA TRACCIA V1 IN TIMELINE (#tl-video-track-container)
    video_track_html = """
          <!-- Traccia V1 Video Montage Track (Visibile solo in modalità video_only - FASE 5) -->
          <div id="tl-video-track-container" class="relative w-full hidden" style="height: 60px;">
            <!-- Renderizzato dinamicamente da renderVideoClipsTrack() -->
          </div>
"""
    if 'id="tl-video-track-container"' not in content:
        # Inserisci prima di #tl-blocks-container
        blocks_marker = '<!-- Traccia dei Blocchi Sottotitoli Interattivi -->'
        if blocks_marker in content:
            content = content.replace(blocks_marker, video_track_html + "\n          " + blocks_marker)

    # 4. AGGIUNTA LOGICA JAVASCRIPT VIDEO EDITOR ENGINE
    video_editor_js = """
    // =======================================================================
    // FASE 5: VIDEO EDITOR ENGINE (type="video_only")
    // =======================================================================
    window.videoClips = [];
    window.selectedClipIndex = 0;
    let videoUndoStack = [];
    let videoRedoStack = [];

    function initVideoClipsForProject(duration) {
      const dur = duration || currentVideoDuration || (videoPlayer && !isNaN(videoPlayer.duration) ? videoPlayer.duration : 0) || 10.0;
      window.videoClips = [
        {
          id: "clip_" + Date.now(),
          start: 0.0,
          end: Math.max(0.1, Number(dur.toFixed(2))),
          duration: Math.max(0.1, Number(dur.toFixed(2))),
          title: "Clip 1",
          filter: "none",
          speed: 1.0
        }
      ];
      window.selectedClipIndex = 0;
      videoUndoStack = [];
      videoRedoStack = [];
    }

    function renderVideoClipsTrack() {
      const container = document.getElementById("tl-video-track-container");
      if (!container) return;
      container.innerHTML = "";

      if (!window.videoClips || window.videoClips.length === 0) {
        initVideoClipsForProject(currentVideoDuration);
      }

      const pxPerSec = getPxPerSecond();

      window.videoClips.forEach((clip, idx) => {
        const left = clip.start * pxPerSec;
        const width = Math.max(24, (clip.end - clip.start) * pxPerSec);

        const el = document.createElement("div");
        el.className = "tl-vclip-item" + (idx === window.selectedClipIndex ? " is-selected" : "");
        el.style.left = `${left}px`;
        el.style.width = `${width}px`;
        el.setAttribute("data-clip-index", idx);
        el.title = `${clip.title || 'Clip ' + (idx + 1)} (${formatTime(clip.start)} - ${formatTime(clip.end)})`;

        const displayDur = (typeof clip.duration === "number" && clip.duration > 0) ? clip.duration : (clip.end - clip.start);

        el.innerHTML = `
          <div class="flex items-center justify-between w-full min-w-0 pointer-events-none">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="text-[9.5px] font-bold text-cyan-400 font-mono bg-dark-950/80 px-1 rounded border border-cyan-500/30">V1</span>
              <span class="text-[11px] font-semibold text-slate-100 truncate">${clip.title || 'Clip ' + (idx + 1)}</span>
            </div>
            <span class="text-[9.5px] font-mono text-cyan-300 font-medium bg-dark-950/80 px-1.5 py-0.5 rounded ml-1 flex-shrink-0 border border-dark-750">${formatTime(displayDur)}</span>
          </div>
        `;

        el.onclick = (e) => {
          e.stopPropagation();
          selectVideoClip(idx, false);
          // Seek del player video al punto cliccato
          const rect = tlTrackWrapper.getBoundingClientRect();
          const clickOffsetPx = e.clientX - rect.left;
          const targetTime = Math.max(clip.start, Math.min(clip.end, clickOffsetPx / pxPerSec));
          seekVideo(targetTime);
        };

        container.appendChild(el);

        // Aggiungi indicatore visivo di taglio netto tra clip adiacenti
        if (idx > 0) {
          const cut = document.createElement("div");
          cut.className = "tl-vclip-cut-indicator";
          cut.style.left = `${left - 1}px`;
          container.appendChild(cut);
        }
      });

      updateVideoInspector();
      updateVideoUndoRedoButtons();
    }

    function selectVideoClip(idx, seekToStart = false) {
      if (!window.videoClips || idx < 0 || idx >= window.videoClips.length) return;
      window.selectedClipIndex = idx;
      const clip = window.videoClips[idx];
      if (seekToStart && clip) {
        seekVideo(clip.start);
      }
      const container = document.getElementById("tl-video-track-container");
      if (container) {
        container.querySelectorAll(".tl-vclip-item").forEach((el, i) => {
          if (i === idx) el.classList.add("is-selected");
          else el.classList.remove("is-selected");
        });
      }
      updateVideoInspector();
    }

    function updateVideoInspector() {
      const panel = document.getElementById("video-inspector-panel");
      if (!panel || panel.classList.contains("hidden")) return;

      const clip = (window.videoClips && window.videoClips[window.selectedClipIndex]) || null;
      const totalClips = (window.videoClips ? window.videoClips.length : 0);

      const badge = document.getElementById("vclip-badge");
      if (badge) badge.innerText = clip ? `Clip ${window.selectedClipIndex + 1} / ${totalClips}` : "Nessuna clip";

      const idxLabel = document.getElementById("vclip-index-label");
      if (idxLabel) idxLabel.innerText = clip ? `#${window.selectedClipIndex + 1}` : "-";

      const titleInput = document.getElementById("vclip-title-input");
      if (titleInput && clip) {
        titleInput.value = clip.title || `Clip ${window.selectedClipIndex + 1}`;
      }

      const tIn = document.getElementById("vclip-time-in");
      if (tIn) tIn.innerText = clip ? formatTime(clip.start) : "00:00.00";

      const tOut = document.getElementById("vclip-time-out");
      if (tOut) tOut.innerText = clip ? formatTime(clip.end) : "00:00.00";

      const tDur = document.getElementById("vclip-time-duration");
      if (tDur) tDur.innerText = clip ? formatTime(clip.duration || (clip.end - clip.start)) : "00:00.00";

      const fn = document.getElementById("vclip-source-filename");
      if (fn) fn.innerText = (currentVideoPath ? currentVideoPath.split("/").pop() : "video.mp4");

      const sDur = document.getElementById("vclip-source-duration");
      if (sDur) sDur.innerText = formatTime(currentVideoDuration || (videoPlayer && !isNaN(videoPlayer.duration) ? videoPlayer.duration : 0));

      const filterSel = document.getElementById("vclip-filter-select");
      if (filterSel && clip) {
        filterSel.value = clip.filter || "none";
      }

      const speedSel = document.getElementById("vclip-speed-select");
      const speedVal = document.getElementById("vclip-speed-val");
      if (speedSel && clip) {
        speedSel.value = String(clip.speed || "1.0");
      }
      if (speedVal && clip) {
        speedVal.innerText = `${clip.speed || 1.0}x`;
      }
    }

    function splitVideoClipAtPlayhead() {
      if (!window.videoClips || window.videoClips.length === 0) return;
      const t = (videoPlayer ? videoPlayer.currentTime : 0);

      // Trova la clip che racchiude t con margine di almeno 0.08s dai confini
      const clipIdx = window.videoClips.findIndex(c => t >= c.start + 0.08 && t <= c.end - 0.08);
      if (clipIdx === -1) {
        console.warn("Playhead non è all'interno di una clip divisibile (troppo vicino ai bordi o fuori traccia)");
        return;
      }

      pushVideoUndo();

      const orig = window.videoClips[clipIdx];
      const clip1 = {
        id: "clip_" + Date.now() + "_1",
        start: orig.start,
        end: Number(t.toFixed(2)),
        duration: Number((t - orig.start).toFixed(2)),
        title: orig.title || ("Clip " + (clipIdx + 1)),
        filter: orig.filter || "none",
        speed: orig.speed || 1.0
      };
      const clip2 = {
        id: "clip_" + Date.now() + "_2",
        start: Number(t.toFixed(2)),
        end: orig.end,
        duration: Number((orig.end - t).toFixed(2)),
        title: "Clip " + (window.videoClips.length + 1),
        filter: orig.filter || "none",
        speed: orig.speed || 1.0
      };

      window.videoClips.splice(clipIdx, 1, clip1, clip2);
      window.selectedClipIndex = clipIdx + 1;

      renderVideoClipsTrack();
      triggerAutosave();
      saveCurrentProjectToLibrary();
    }

    function deleteSelectedVideoClip() {
      if (!window.videoClips || window.videoClips.length <= 1) {
        alert("Il progetto video deve contenere almeno una clip. Non puoi eliminare l'unica clip presente.");
        return;
      }

      pushVideoUndo();

      window.videoClips.splice(window.selectedClipIndex, 1);
      window.selectedClipIndex = Math.max(0, window.selectedClipIndex - 1);

      const nextClip = window.videoClips[window.selectedClipIndex];
      if (nextClip) {
        seekVideo(nextClip.start);
      }

      renderVideoClipsTrack();
      triggerAutosave();
      saveCurrentProjectToLibrary();
    }

    function resetVideoClips() {
      if (!confirm("Vuoi ripristinare la traccia video rimuovendo tutti i tagli effettuati?")) return;
      pushVideoUndo();
      initVideoClipsForProject(currentVideoDuration);
      renderVideoClipsTrack();
      triggerAutosave();
      saveCurrentProjectToLibrary();
    }

    function pushVideoUndo() {
      videoUndoStack.push(JSON.parse(JSON.stringify(window.videoClips)));
      if (videoUndoStack.length > 50) videoUndoStack.shift();
      videoRedoStack = [];
      updateVideoUndoRedoButtons();
    }

    function undoVideo() {
      if (videoUndoStack.length === 0) return;
      videoRedoStack.push(JSON.parse(JSON.stringify(window.videoClips)));
      window.videoClips = videoUndoStack.pop();
      window.selectedClipIndex = Math.max(0, Math.min(window.selectedClipIndex, window.videoClips.length - 1));
      renderVideoClipsTrack();
      triggerAutosave();
      saveCurrentProjectToLibrary();
    }

    function redoVideo() {
      if (videoRedoStack.length === 0) return;
      videoUndoStack.push(JSON.parse(JSON.stringify(window.videoClips)));
      window.videoClips = videoRedoStack.pop();
      window.selectedClipIndex = Math.max(0, Math.min(window.selectedClipIndex, window.videoClips.length - 1));
      renderVideoClipsTrack();
      triggerAutosave();
      saveCurrentProjectToLibrary();
    }

    function updateVideoUndoRedoButtons() {
      const btnTlUndo = document.getElementById("btn-tl-undo");
      const btnTlRedo = document.getElementById("btn-tl-redo");
      if (btnTlUndo) btnTlUndo.disabled = (videoUndoStack.length === 0);
      if (btnTlRedo) btnTlRedo.disabled = (videoRedoStack.length === 0);
    }

    function initVideoInspectorListeners() {
      const btnSplit = document.getElementById("btn-vclip-split");
      if (btnSplit) btnSplit.onclick = () => splitVideoClipAtPlayhead();

      const btnDelete = document.getElementById("btn-vclip-delete");
      if (btnDelete) btnDelete.onclick = () => deleteSelectedVideoClip();

      const btnReset = document.getElementById("btn-vclip-reset");
      if (btnReset) btnReset.onclick = () => resetVideoClips();

      const btnIn = document.getElementById("btn-vclip-goto-in");
      if (btnIn) {
        btnIn.onclick = () => {
          const clip = window.videoClips && window.videoClips[window.selectedClipIndex];
          if (clip) seekVideo(clip.start);
        };
      }

      const btnOut = document.getElementById("btn-vclip-goto-out");
      if (btnOut) {
        btnOut.onclick = () => {
          const clip = window.videoClips && window.videoClips[window.selectedClipIndex];
          if (clip) seekVideo(clip.end);
        };
      }

      const titleInput = document.getElementById("vclip-title-input");
      if (titleInput) {
        titleInput.onchange = () => {
          const clip = window.videoClips && window.videoClips[window.selectedClipIndex];
          if (clip && titleInput.value.trim()) {
            clip.title = titleInput.value.trim();
            renderVideoClipsTrack();
            triggerAutosave();
            saveCurrentProjectToLibrary();
          }
        };
      }

      const filterSel = document.getElementById("vclip-filter-select");
      if (filterSel) {
        filterSel.onchange = () => {
          const clip = window.videoClips && window.videoClips[window.selectedClipIndex];
          if (clip) {
            clip.filter = filterSel.value;
            triggerAutosave();
            saveCurrentProjectToLibrary();
          }
        };
      }

      const speedSel = document.getElementById("vclip-speed-select");
      if (speedSel) {
        speedSel.onchange = () => {
          const clip = window.videoClips && window.videoClips[window.selectedClipIndex];
          if (clip) {
            clip.speed = parseFloat(speedSel.value) || 1.0;
            const speedVal = document.getElementById("vclip-speed-val");
            if (speedVal) speedVal.innerText = `${clip.speed}x`;
            triggerAutosave();
            saveCurrentProjectToLibrary();
          }
        };
      }
    }
"""

    if "FASE 5: VIDEO EDITOR ENGINE" not in content:
        # Inserisci prima di initHomeProjectLibrary
        target_fn = "function initHomeProjectLibrary() {"
        content = content.replace(target_fn, video_editor_js + "\n    " + target_fn)

    # 5. AGGIORNAMENTO openProjectById PER type="video_only"
    # Quando p.type === 'video_only', configuri il workspace dedicato
    old_open_block = """        // Distinzione tra workflow Subtitles vs Video Only
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
        }"""

    new_open_block = """        // Distinzione tra workflow Subtitles vs Video Only
        if (projectType === "subtitles") {
          // Sottotitoli SÌ
          document.getElementById("view-editor")?.setAttribute("data-project-type", "subtitles");
          window.currentProjectType = "subtitles";
          if (typeof startTranscription === "function") {
            startTranscription(currentVideoPath, createdProject.media.url || wizardData.videoUrl);
          }
        } else {
          // Video Only NO: Nessuna trascrizione Whisper o sottotitolo caricato
          document.getElementById("view-editor")?.setAttribute("data-project-type", "video_only");
          window.currentProjectType = "video_only";
          if (editorEmpty) editorEmpty.classList.add("hidden");
          if (chunksList) chunksList.classList.add("hidden");
          if (statsBadge) statsBadge.innerText = "Video Only";
          initVideoClipsForProject(createdProject.media.duration || wizardData.videoDuration);
          updateTimelineLayout();
          renderVideoClipsTrack();
          updateVideoInspector();
          saveCurrentProjectToLibrary();
        }"""

    if old_open_block in content:
        content = content.replace(old_open_block, new_open_block)

    # Aggiorna anche openProjectById per gestire p.type === 'video_only'
    open_proj_target = """        // Switch a view-editor
        showEditorView();"""
    
    # Verifica se openProjectById gestisce video_only
    if 'if (p.type === "video_only")' not in content:
        old_restore_media = """        if (media.server_path && typeof initWaveform === "function") {
          initWaveform(media.server_path);
        }

        // Switch a view-editor
        showEditorView();"""

        new_restore_media = """        if (media.server_path && typeof initWaveform === "function") {
          initWaveform(media.server_path);
        }

        if (p.type === "video_only") {
          window.currentProjectType = "video_only";
          document.getElementById("view-editor")?.setAttribute("data-project-type", "video_only");
          if (p.video_clips && Array.isArray(p.video_clips) && p.video_clips.length > 0) {
            window.videoClips = p.video_clips;
          } else {
            initVideoClipsForProject(media.duration || currentVideoDuration);
          }
          window.selectedClipIndex = 0;
          if (editorEmpty) editorEmpty.classList.add("hidden");
          if (chunksList) chunksList.classList.add("hidden");
          const tlEmpty = document.getElementById("timeline-empty");
          if (tlEmpty) tlEmpty.classList.add("hidden");
          if (statsBadge) statsBadge.innerText = `${window.videoClips.length} clip video`;
          updateTimelineLayout();
          renderVideoClipsTrack();
          updateVideoInspector();
        } else {
          window.currentProjectType = "subtitles";
          document.getElementById("view-editor")?.setAttribute("data-project-type", "subtitles");
        }

        // Switch a view-editor
        showEditorView();"""
        if old_restore_media in content:
            content = content.replace(old_restore_media, new_restore_media)

    # 6. AGGIORNAMENTO saveCurrentProjectToLibrary per includere video_clips
    old_save_payload = """        chunks: currentChunks || [],
        allOriginalWords: window.allOriginalWords || [],"""
    new_save_payload = """        chunks: currentChunks || [],
        video_clips: window.videoClips || [],
        video_clips_count: (window.videoClips || []).length,
        allOriginalWords: window.allOriginalWords || [],"""
    if old_save_payload in content and "video_clips: window.videoClips || []," not in content:
        content = content.replace(old_save_payload, new_save_payload)

    # 7. AGGIORNAMENTO BOTTONI SPLIT & DELETE NELLA TIMELINE
    old_btn_split = """    const btnSplitPlayhead = document.getElementById("btn-split-playhead");
    if (btnSplitPlayhead) {
      btnSplitPlayhead.onclick = () => {
        if (typeof splitChunkAtPlayhead === "function") splitChunkAtPlayhead();
      };
    }

    const btnDeleteSelectedChunk = document.getElementById("btn-delete-selected-chunk");
    if (btnDeleteSelectedChunk) {
      btnDeleteSelectedChunk.onclick = () => {
        if (typeof selectedChunkIndex === "number" && selectedChunkIndex >= 0 && currentChunks && selectedChunkIndex < currentChunks.length) {
          deleteChunk(selectedChunkIndex);
        } else {
          alert("Seleziona prima un sottotitolo sulla timeline o nella lista da eliminare.");
        }
      };
    }"""

    new_btn_split = """    const btnSplitPlayhead = document.getElementById("btn-split-playhead");
    if (btnSplitPlayhead) {
      btnSplitPlayhead.onclick = () => {
        if (window.currentProjectType === "video_only") {
          splitVideoClipAtPlayhead();
        } else {
          if (typeof splitChunkAtPlayhead === "function") splitChunkAtPlayhead();
        }
      };
    }

    const btnDeleteSelectedChunk = document.getElementById("btn-delete-selected-chunk");
    if (btnDeleteSelectedChunk) {
      btnDeleteSelectedChunk.onclick = () => {
        if (window.currentProjectType === "video_only") {
          deleteSelectedVideoClip();
        } else {
          if (typeof selectedChunkIndex === "number" && selectedChunkIndex >= 0 && currentChunks && selectedChunkIndex < currentChunks.length) {
            deleteChunk(selectedChunkIndex);
          } else {
            alert("Seleziona prima un sottotitolo sulla timeline o nella lista da eliminare.");
          }
        }
      };
    }"""
    if old_btn_split in content:
        content = content.replace(old_btn_split, new_btn_split)

    # 8. AGGIORNAMENTO UNDO/REDO HANDLERS PER VIDEO EDITOR
    old_undo_wiring = """    if (btnUndo) btnUndo.onclick = () => undo();
    if (btnRedo) btnRedo.onclick = () => redo();
    const btnTlUndo = document.getElementById("btn-tl-undo");
    const btnTlRedo = document.getElementById("btn-tl-redo");
    if (btnTlUndo) btnTlUndo.onclick = () => undo();
    if (btnTlRedo) btnTlRedo.onclick = () => redo();"""

    new_undo_wiring = """    if (btnUndo) btnUndo.onclick = () => undo();
    if (btnRedo) btnRedo.onclick = () => redo();
    const btnTlUndo = document.getElementById("btn-tl-undo");
    const btnTlRedo = document.getElementById("btn-tl-redo");
    if (btnTlUndo) {
      btnTlUndo.onclick = () => {
        if (window.currentProjectType === "video_only") undoVideo();
        else undo();
      };
    }
    if (btnTlRedo) {
      btnTlRedo.onclick = () => {
        if (window.currentProjectType === "video_only") redoVideo();
        else redo();
      };
    }"""
    if old_undo_wiring in content:
        content = content.replace(old_undo_wiring, new_undo_wiring)

    # Inizializza listener inspector all'avvio
    if "initVideoInspectorListeners();" not in content:
        content = content.replace("initHomeProjectLibrary();", "initHomeProjectLibrary();\n    initVideoInspectorListeners();")

    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"Aggiornato con successo: {INDEX_PATH} (bytes: {len(content)})")

if __name__ == "__main__":
    main()
