def get_new_shortcuts_modal():
    return '''  <div id="modal-shortcuts-cheatsheet" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl transition-opacity animate-fadeIn">
    <div class="bg-dark-900 border border-dark-750 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col animate-scaleUp">
      <div class="px-6 py-4 border-b border-dark-700 flex items-center justify-between bg-dark-950/60">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono text-sm font-bold">⌨️</div>
          <div>
            <h3 class="font-bold text-sm text-white">Scorciatoie da Tastiera Pro</h3>
            <p class="text-xs text-slate-400 mt-0.5">Workflow professionale ispirato ai migliori software NLE</p>
          </div>
        </div>
        <button type="button" id="btn-shortcuts-close" class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-dark-800 transition cursor-pointer">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="p-6 space-y-4 overflow-y-auto max-h-[75vh] text-xs">
        
        <!-- 1. RIPRODUZIONE -->
        <div class="space-y-2">
          <div class="text-[10.5px] uppercase font-bold text-cyan-400 tracking-wider">Riproduzione</div>
          <div class="space-y-1">
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Riproduci / Metti in Pausa</span>
              <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">Space</kbd>
            </div>
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Fotogramma Prec. / Succ. (±0.05s)</span>
              <div class="flex gap-1">
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">←</kbd>
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">→</kbd>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. EDITING -->
        <div class="space-y-2 border-t border-dark-750 pt-3">
          <div class="text-[10.5px] uppercase font-bold text-cyan-400 tracking-wider">Editing</div>
          <div class="space-y-1">
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <div>
                <span class="block text-slate-200 font-semibold">Dividi blocco alla testina (Split)</span>
                <span class="text-[10px] text-slate-400">Taglia il sottotitolo al fotogramma esatto</span>
              </div>
              <div class="flex gap-1">
                <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-amber-300 font-mono font-bold">⌘B</kbd>
                <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-amber-300 font-mono font-bold">S</kbd>
              </div>
            </div>
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-200 font-semibold">Elimina blocco selezionato</span>
              <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-rose-300 font-mono font-bold">⌫ Canc / Del</kbd>
            </div>
          </div>
        </div>

        <!-- 3. TIMELINE -->
        <div class="space-y-2 border-t border-dark-750 pt-3">
          <div class="text-[10.5px] uppercase font-bold text-cyan-400 tracking-wider">Timeline</div>
          <div class="space-y-1">
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Centra timeline sul playhead</span>
              <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">C</kbd>
            </div>
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Zoom In / Zoom Out</span>
              <div class="flex gap-1">
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">+</kbd>
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">−</kbd>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. NAVIGAZIONE -->
        <div class="space-y-2 border-t border-dark-750 pt-3">
          <div class="text-[10.5px] uppercase font-bold text-cyan-400 tracking-wider">Navigazione</div>
          <div class="space-y-1">
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Salto temporale rapido (±1 secondo)</span>
              <div class="flex gap-1">
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">⇧ ←</kbd>
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">⇧ →</kbd>
              </div>
            </div>
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Controlli Jog Shuttle (Rewind / Stop / Forward)</span>
              <div class="flex gap-1">
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">J</kbd>
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">K</kbd>
                <kbd class="px-2 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">L</kbd>
              </div>
            </div>
          </div>
        </div>

        <!-- 5. GENERALE -->
        <div class="space-y-2 border-t border-dark-750 pt-3">
          <div class="text-[10.5px] uppercase font-bold text-cyan-400 tracking-wider">Generale</div>
          <div class="space-y-1">
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Annulla modifica (Undo)</span>
              <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">⌘Z</kbd>
            </div>
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Ripristina modifica (Redo)</span>
              <div class="flex gap-1">
                <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">⌘⇧Z</kbd>
                <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">⌘Y</kbd>
              </div>
            </div>
            <div class="flex items-center justify-between p-2 rounded-xl bg-dark-950 border border-dark-750">
              <span class="text-slate-300">Mostra / Nascondi questa Guida</span>
              <kbd class="px-2.5 py-1 rounded bg-dark-800 border border-dark-700 text-slate-200 font-mono font-bold">?</kbd>
            </div>
          </div>
        </div>

      </div>

      <div class="px-6 py-3 bg-dark-950/80 border-t border-dark-750 flex justify-end">
        <button type="button" id="btn-shortcuts-ok" class="px-4 py-1.5 rounded-xl bg-dark-800 hover:bg-dark-750 border border-dark-700 text-slate-200 font-bold text-xs transition cursor-pointer">
          Ho capito
        </button>
      </div>
    </div>
  </div>'''

def apply():
    with open('web_static/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    pos = content.find('<div id="modal-shortcuts-cheatsheet"')
    end_pos = content.find('<!-- Modal 2: Dashboard Coda Video -->')
    if pos != -1 and end_pos != -1:
        content = content[:pos] + get_new_shortcuts_modal() + '\n\n  ' + content[end_pos:]
        print("Shortcuts modal successfully updated!")

    with open('web_static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    apply()
