# 🗺️ SUB STUDIO — ROADMAP UFFICIALE DI SVILUPPO

Documento strategico di riferimento per l'evoluzione dell'applicazione **Sub Studio** (ex Sottotitolatore).  
Questo file unisce lo storico dei traguardi completati con i nuovi sviluppi pianificati per trasformare Sub Studio in una suite creativa professionale di livello internazionale per video verticali 9:16, creator, agenzie e montatori video.

---

## 📊 STATO ATTUALE DEL PROGETTO (Riepilogo Generale)

| Area | Stato | Note |
| :--- | :---: | :--- |
| **Motore di Trascrizione** | 🟢 Completato | faster-whisper (CPU/MPS/CUDA), segmentazione DP intelligente |
| **Calibrazione Coordinate** | 🟢 Completato | Proporzioni grafiche CapCut, Snap Guides, Gizmo di trasformazione |
| **Coda Batch & Multi-Video** | 🟢 Completato | Upload multiplo, code batch, rendering sequenziale, ZIP export |
| **Timeline & Waveform** | 🟢 Completato | Forma d'onda audio interattiva, drag & resize blocchi, playhead |
| **Rimozione Silenzi** | 🟢 Completato | Taglio fisico video con FFmpeg, compattamento live preview |
| **Traduzione AI** | 🟢 Completato | Integrazione Google Gemini API + fallback web |
| **Brand Identity & UI Rebrand** | 🟢 Completato | Nuovo brand Sub Studio, palette Obsidian/Cyan/Indigo, 4 finestre fluide |
| **Effetto Highlighter Parola** | 🟢 Completato | Box dinamico karaoke virale parola per parola con rendering GPU/Pillow |
| **Diarizzazione & Speaker AI** | 🟢 Completato | Auto-detect professionale monologo/dialogo, silenziamento live/render e taglio video timeline |
| **Bilanciamento Visivo a 2 Righe** | 🟢 Completato | Ottimizzazione visiva proporzionale larghezza righe, anti-dangling e vincolo max 2 righe |
| **Intelligenza Apostrofi & Elisioni** | 🟢 Completato | Unificazione token Whisper (es. l'energia), protezione assoluta anti-split |
| **Editing Veloce & Blade Tool** | 🟡 Pianificato | Fase 1 |
| **Nuovi Preset & Kinetic FX** | 🟡 Pianificato | Fase 2 |
| **Export NLE (ProRes Alpha, CapCut)** | 🟡 Pianificato | Fase 4 |
| **Desktop App macOS Standalone** | 🟢 Completato | Pacchetto DMG Apple Silicon con Whisper offline e launcher Cocoa nativo |

---

## ✅ TRAGUARDI COMPLETATI (Milestone Storiche)

### 🟢 Milestone 1: Motore Core & Calibrazione Visiva CapCut
- [x] Integrazione motore `faster-whisper` con modelli `tiny`, `base`, `small`, `medium`, `large-v3`.
- [x] Algoritmo di segmentazione dinamica DP (*Dynamic Programming*) per il raggruppamento intelligente delle parole e bilanciamento della lunghezza delle frasi.
- [x] Riconoscimento automatico delle parole chiave (*keyword extraction*) con accento grassetto.
- [x] Calibrazione matematica delle coordinate su base standard 9:16 (1080x1920) coerente con CapCut.
- [x] Gizmo di trasformazione interattivo sul canvas (bounding box, maniglie di ridimensionamento, maniglia di rotazione a gambo).
- [x] Guide magnetiche di snap (linea verticale e orizzontale centrale con aggancio automatico a 540x960).

### 🟢 Milestone 2: Coda Batch & Dashboard di Elaborazione Multi-Video
- [x] Modale e pannello di gestione della coda batch (`modal-batch`).
- [x] Caricamento multi-file con drag & drop aggregato.
- [x] Trascrizione cumulativa sequenziale in background.
- [x] Rendering batch con barra di avanzamento percentuale e report di stato per ciascun video.
- [x] Esportazione massiva in archivio compresso `.ZIP` contenente tutti i video finalizzati.

### 🟢 Milestone 3: Timeline Audio & Waveform Interattiva
- [x] Estrazione dei picchi audio (*audio waveform peaks*) a 16kHz e rendering su canvas dinamico.
- [x] Controlli di zoom timeline (50%, 100%, 150%, 200%, pulsante Adatta / Centra).
- [x] Blocchi sottotitolo interattivi sulla timeline con maniglie sinistra/destra per allungare, accorciare o trascinare i timestamp.
- [x] Cursore playhead con scrubbing in tempo reale e sincronizzazione bidirezionale con il player video.

### 🟢 Milestone 4: Taglio Automatico Silenzi (*Silence Removal*)
- [x] Rilevamento automatico delle pause con filtro FFmpeg `silencedetect`.
- [x] Soglia di silenzio regolabile (da 0.1s a 0.5s).
- [x] Compattazione fisica della traccia video e audio senza desincronizzazione dei sottotitoli.
- [x] Mappatura del tempo virtuale (*virtual-to-real timestamp mapping*) per preview fluida.

### 🟢 Milestone 5: Traduzione AI & Multi-Lingua
- [x] Traduzione automatica di tutti i sottotitoli tramite Google Gemini API (chiave API memorizzabile localmente).
- [x] Modalità fallback gratuita per traduzione web senza API key.
- [x] Ricalcolo automatico della sincronizzazione temporale delle parole tradotte.

### 🟢 Milestone 6: Rebranding "Sub Studio" & Architettura UI Professionale
- [x] Nuovo nome e identità internazionale: **Sub Studio**.
- [x] Iconografia master 3D glassmorphic e icone multi-piattaforma (`AppIcon.icns`, `AppIcon.png`, `favicon.ico`).
- [x] Design system professionale ispirato alle creative suite (Obsidian Navy `#050711`, Cyan `#00f0ff`, Indigo `#6366f1`, Magenta `#d946ef`).
- [x] Gestione fluida delle 4 finestre di lavoro (Anteprima 9:16, Sottotitoli, Inspector, Timeline) con doppio clic di ripristino e nessun movimento involontario al passaggio del mouse.
- [x] Sistema di gestione progetti con Autosave continuo e pulsante dedicato `Chiudi video / Nuovo Progetto`.

### 🟢 Milestone 7: Bilanciamento Visivo Intelligente a 2 Righe & Analisi Linguistica Apostrofi
- [x] **Algoritmo di Bilanciamento Visivo Proporzionale a 2 Righe**:
  - Calcolo dinamico dell'ingombro visivo (in pixel stimati e peso caratteri) per evitare asimmetrie sgradevoli ("sopra enorme, sotto minuscolo").
  - Spostamento automatico delle parole lunghe per massimizzare l'equilibrio estetico (`|w1 - w2|`).
  - Penalizzazione graduata del dangling per evitare preposizioni e articoli orfani a fine riga.
- [x] **Intelligenza e Riconoscimento Linguistico delle Parole con Apostrofo & Elisioni**:
  - Unificazione automatica dei token separati generati da faster-whisper (es. `l'energia.`, `d'accordo`, `c'è`, `un'altra`, `dell'arte`).
  - Regola inviolabile anti-split: divieto assoluto di separare parole legate da apostrofi su righe diverse, preservando coesione sintattica e prosodica.
  - Normalizzazione istantanea degli spazi post-apostrofo nell'input testuale dell'editor.
  - Se un chunk contiene solo la parola apostrofata, rimane su un'unica riga elegante senza creare righe vuote.
- [x] **Perfezionamento Effetto Highlighter & Preset**:
  - Supporto completo e persistenza su `presets.json` delle proprietà highlighter (colore box, padding X/Y, raggio bordi, ombra e contorno).
  - Micro-animazione fluida e morbida senza scatti e senza ingrandimento involontario della parola attiva.
  - Fallback a contorno e ombra globali per la massima leggibilità su sfondi chiari.
  - Vincolo a massimo 2 righe per chunk.
- [x] **Diarizzazione Speaker & Rilevamento Automatico**:
  - Rimozione della selezione forzata manuale degli interlocutori (1, 2, 3 speaker) e passaggio esclusivo alla modalità di analisi spettrale e clustering automatico.

---

## 🚀 NUOVA ROADMAP DI SVILUPPO (Prossime Fasi)

```
[FASE 1: WORKFLOW & TIMELINE] ──> [FASE 2: STILI & KINETIC FX] ──> [FASE 3: AI & INTELLIGENCE] ──> [FASE 4: EXPORT NLE & PRO] ──> [FASE 5: STANDALONE APP]
```

---

### 🎯 FASE 1: Workflow di Editing Avanzato & Precisione Timeline
*Obiettivo: Ottimizzare la produttività del montatore, consentendo revisioni e tagli ultrarapidi via tastiera.*

1. **Taglio Veloce da Tastiera (Blade Tool / Split al Playhead - Tasto `C` o `S`):**
   - Suddivisione istantanea del blocco di sottotitolo attivo esattamente dove si trova il cursore playhead.
   - Ricalcolo automatico dei millisecondi e distribuzione proporzionale delle parole tra i due nuovi blocchi.
2. **Unione Rapida Blocchi (Merge Tool - Scorciatoia `Cmd + J`):**
   - Fusione con un clic di due blocchi adiacenti selezionati nella timeline o nella lista editor.
3. **Trova & Sostituisci Globale (Search & Replace - Scorciatoia `Cmd + F`):**
   - Pannello rapido per cercare una parola o frase in tutto il video e sostituirla su tutti i chunk contemporaneamente (es. correzione di un cognome o brand errato).
4. **Glossario / Dizionario Personalizzato Anti-Allucinazioni:**
   - Database locale di parole chiave, acronimi e nomi propri ricorrenti.
   - Sostituzione automatica post-trascrizione Whisper prima dell'impaginazione dei sottotitoli.
5. **Snapping Magnetico Intelligente sulla Timeline:**
   - Aggancio magnetico automatico tra i bordi dei blocchi vicini (evita buchi neri di pochi fotogrammi tra una frase e la successiva).
6. **Playback a Velocità Variabile (1.25x, 1.5x, 2x):**
   - Scrubbing e ascolto accelerato con pitch vocale corretto (*audio pitch preservation*) per revisionare video lunghi in metà tempo.

---

### 🎨 FASE 2: Stili Visivi, Preset Creator & Kinetic FX
*Obiettivo: Fornire l'estetica virale dei top creator mondiali (Alex Hormozi, MrBeast, Iman Gadzhi, Ali Abdaal).*

1. **Nuova Collezione di Preset Iconici:**
   - **Hormozi Kinetic:** Caratteri bold compatti, parole chiave evidenziate con box giallo/verde fluo ad alto contrasto.
   - **Luxe Minimalist:** Tipografia elegante (Syne, Montserrat, Inter), tracciamento allargato, sfumatura sottile.
   - **Beast Impact:** Animazione pop-up con micro-rotazione 3D e bordo sagomato per la parola attiva.
   - **Ali Abdaal Clean:** Look editoriale con evidenziatore color pastello a scorrimento orizzontale.
2. **Effetto "Highlighter" (Box Dinamico Parola per Parola) [COMPLETATO]:**
   - [x] Rettangolo colorato stondato che segue o illumina la parola pronunciata in stile karaoke avanzato.
   - [x] Integrazione rendering video millisecondo per millisecondo con Pillow e FFmpeg.
   - [x] Controlli completi nell'Inspector: colori rapidi virali (Hormozi, Toxic, Cyan, Pink, Pastel), raggio bordi, padding e colore testo contrasto.
   - [x] Nuovo preset ufficiale "Hormozi Kinetic Highlighter".
3. **Auto-Emoji Contestuali:**
   - Mappatura semantica di keyword (es. "soldi" 💸, "tempo" ⏱️, "fuoco" 🔥, "risultato" 🎯) con rendering automatico dell'emoji posizionata sopra o a lato del testo.
4. **Motore di Animazione Parola (*Word Kinetic Animations*):**
   - Opzioni selezionabili: *Pop / Bounce, Slide Up, Typewriter, Smooth Fade-In*.

---

### 🧠 FASE 3: Funzionalità AI Avanzate
*Obiettivo: Automatizzare le operazioni ripetitive e la gestione audio/video tramite intelligenza artificiale.*

1. **Diarizzazione e Riconoscimento Speaker (Multi-Interlocutore) [COMPLETATO]:**
   - [x] Modulo nativo `speaker_diarizer.py` con analisi spettrale avanzata (12 MFCC, varianze timbriche, dinamica delta formanti, stima pitch F0 in ottave e armonicità HNR).
   - [x] Riconoscimento professionale senza falsi positivi: clustering sferico su coordinate acustiche assolute e calcolo del differenziale di pitch mediano, garantendo l'identificazione certa del singolo speaker (monologo) senza frammentazioni fittizie.
   - [x] Riconoscimento automatico e bilanciato delle diverse voci (Speaker 1 vs Speaker 2) per podcast, interviste e dialoghi multi-voce.
   - [x] Personalizzazione visiva avanzata (colori testo ed evidenziatore box dedicati per ciascun interlocutore).
   - [x] **Silenzia Audio Speaker**: pulsante rapido `Muta Audio` per ciascuno speaker con muting live istantaneo nel player e applicazione filtro volume FFmpeg nell'esportazione finale.
   - [x] **Rimozione dalla Timeline**:
     - `🗑️ Rimuovi Sottotitoli`: rimozione con un clic di tutti i sottotitoli dello speaker scelto dalla timeline.
     - `✂️ Taglia Video dello Speaker`: endpoint dedicato `/api/cut_speaker` per tagliare fisicamente ed eliminare video e audio dello speaker, ricompattando la timeline senza interruzioni.
   - [x] Badge interattivo rapido su ogni blocco sottotitoli per alternare l'oratore (Speaker 1 ⇄ Speaker 2) con indicatore `🔇 Muto`.
2. **Auto-Censura & Audio Bleep:**
   - Riconoscimento di parolacce o termini sensibili da lista configurabile.
   - Opzione per mascheramento visivo nei sottotitoli (es. `f***`) e inserimento opzionale del bip audio con attenuazione voce.
3. **AI Hook & Viral Title Generator (via Gemini API):**
   - Estrazione automatica dei 3 secondi più accattivanti del video per l'inquadratura iniziale (Hook).
   - Generazione di 5 idee di titoli virali e didascalia ottimizzata per Instagram Reels, TikTok e YouTube Shorts.

---

### 🎬 FASE 4: Esportazione Professionale & Integrazione NLE
*Obiettivo: Consentire ai professionisti del montaggio di integrare Sub Studio direttamente in Premiere Pro, DaVinci Resolve e Final Cut.*

1. **Esportazione Trasparenza Apple ProRes 4444 (Alpha Channel):**
   - Esportazione QuickTime `.mov` dei soli sottotitoli animati su sfondo 100% trasparente.
   - Permette di sovrapporre i sottotitoli direttamente sulla timeline di Premiere o DaVinci sul girato master originale in 4K/HDR senza ri-comprimere il video.
2. **Esportazione Sequenze NLE (XML / FCPXML / DaVinci EDL):**
   - File di scambio per importare i titoli direttamente come tracce testo native nei principali software di montaggio.
3. **Esportazione Progetto CapCut (Draft JSON):**
   - Generazione della struttura di progetto CapCut Desktop (`draft_content.json`) con testi e animazioni pre-impostate.
4. **Esportazione Multi-Formato Sottotitoli:**
   - Esportazione simultanea in: `.SRT` standard, `.VTT` (compatibile web e YouTube con stili), `.ASS` (Advanced SubStation Alpha per karaoke preciso) e `.JSON`.

---

### 💻 FASE 5: Desktop App macOS Nativa & Performance Hardware
*Obiettivo: Pacchettizzazione autonoma, robusta e ottimizzata per i chip Apple Silicon.*

1. **Installer DMG Professionale con Drag-to-Applications:**
   - Script di packaging aggiornato con la nuova icona 3D di Sub Studio, sfondo personalizzato e link simbolico alla cartella `/Applications`.
2. **Accelerazione Hardware Completa (Apple Silicon M1-M4):**
   - Sfruttamento della Neural Engine via Apple MLX o MPS per velocizzare la trascrizione Whisper.
   - Encoding video con accelerazione hardware `h264_videotoolbox` / `hevc_videotoolbox`.
3. **Notifiche Native di Sistema:**
   - Notifica banner macOS al termine della trascrizione o del rendering finale di video pesanti in background.

---

## 📋 TABELLA DELLE PRIORITÀ DI IMPLEMENTAZIONE

| Ordine | ID | Funzionalità | Fase | Impatto | Complessità |
| :---: | :---: | :--- | :---: | :---: | :---: |
| **1** | `F1.1` | **Taglio rapido timeline (Blade Tool al playhead con tasto `C`/`S`)** | Fase 1 | 🔥 Altissimo | Bassa |
| **2** | `F1.2` | **Trova & Sostituisci globale (`Cmd + F`) per correzioni veloci** | Fase 1 | 🔥 Altissimo | Bassa |
| **3** | `F4.1` | **Esportazione ProRes 4444 con Canale Alpha (Sottotitoli Trasparenti)** | Fase 4 | 🔥 Altissimo | Media |
| **4** | `F2.1` | **Nuovi Preset Visivi (Hormozi, Minimalist, Beast) con Box Highlighter** | Fase 2 | 🚀 Molto Alto | Media |
| **5** | `F4.3` | **Esportazione CapCut Draft (`draft_content.json`)** | Fase 4 | 🚀 Molto Alto | Media |
| **6** | `F1.3` | **Glossario / Dizionario parole ricorrenti anti-allucinazione** | Fase 1 | 💡 Alto | Media |
| **7** | `F3.1` | **Diarizzazione Speaker (riconoscimento voci e colori diversi)** | Fase 3 | 💡 Alto | Alta |
| **8** | `F4.2` | **Esportazione FCPXML / Premiere XML** | Fase 4 | 💡 Alto | Media |
| **9** | `F5.1` | **Pacchetto DMG definitivo con installatore grafico** | Fase 5 | 📦 Essenziale | Bassa |
