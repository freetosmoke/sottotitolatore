# 🎬 Sottotitolatore CLI

Pipeline automatica per generare sottotitoli verticali **9:16** per video podcast su **macOS (Apple Silicon)**.

---

## Architettura dei moduli

```
sottotitolatore/
├── main.py              # CLI entry point (typer)
├── audio_extractor.py   # Estrazione WAV 16kHz mono via ffmpeg
├── transcriber.py       # Trascrizione faster-whisper + chunking
├── keyword_selector.py  # Selezione keyword euristica + tag ASS
├── ass_generator.py     # Generazione file .ass con stili e watermark
├── video_renderer.py    # Burn-in ffmpeg (HW Apple Silicon o libx264)
├── requirements.txt
└── fonts/               # (opzionale) Inserisci qui Raleway-Light.ttf ecc.
```

---

## Prerequisiti

### 1. Homebrew + ffmpeg con libass

```bash
brew install ffmpeg
```

> **Nota:** il ffmpeg di Homebrew include già `libass` per il render dei sottotitoli ASS.

### 2. Python 3.10+

```bash
brew install python@3.12
```

### 3. Font Raleway (opzionale ma consigliato)

Scarica i file `.ttf` da [Google Fonts](https://fonts.google.com/specimen/Raleway) e:
- **Opzione A**: Installali nel sistema (doppio clic → Installa font)
- **Opzione B**: Copia i file in `./fonts/` nella cartella del progetto

Se Raleway non è disponibile, lo script usa automaticamente `Arial` come fallback.

---

## Installazione

```bash
# Clona / entra nella cartella del progetto
cd sottotitolatore

# Crea e attiva un virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt
```

> La prima esecuzione scaricherà il modello Whisper (~150MB per `small`, ~300MB per `medium`).

---

## Utilizzo

### Singolo file

```bash
python main.py --input podcast_episodio1.mp4
```

Produce: `podcast_episodio1_subtitled.mp4` nella stessa cartella.

### Output personalizzato

```bash
python main.py --input input.mp4 --output output_finale.mp4
```

### Modello più accurato (consigliato per podcast lunghi)

```bash
python main.py --input video.mp4 --model medium
```

### Modalità batch (intera cartella)

```bash
python main.py --input ./video/ --batch
```

Elabora tutti i `.mp4 .mov .mkv .avi .webm .m4v` nella cartella.

### Conserva i file temporanei (per debug)

```bash
python main.py --input video.mp4 --keep-temp
```

Mantiene il file `.wav` e il file `.ass` nella cartella temp per ispezione.

### Forza/disabilita accelerazione hardware

```bash
# Forza Apple Silicon hardware encoder
python main.py --input video.mp4 --hw

# Forza libx264 software
python main.py --input video.mp4 --no-hw
```

---

## Tutte le opzioni

| Opzione | Default | Descrizione |
|---|---|---|
| `--input / -i` | — | Percorso video o cartella (obbligatorio) |
| `--output / -o` | `*_subtitled.mp4` | Percorso output (solo senza --batch) |
| `--batch / -b` | `False` | Modalità batch su cartella |
| `--model / -m` | `small` | Modello Whisper: tiny, base, **small**, medium, large-v3 |
| `--compute-type` | `float16` | Tipo calcolo: float16, int8, float32 |
| `--language / -l` | `it` | Codice lingua ISO 639-1 |
| `--keep-temp` | `False` | Non eliminare file WAV e .ass temporanei |
| `--hw / --no-hw` | auto | Forza/disabilita h264_videotoolbox |

---

## Dettagli tecnici

### Stile sottotitoli
- **Font**: Raleway Light (`\b300`), size 62, bianco, bordo nero 2px
- **Posizione**: Centro schermo (Alignment 5, `\pos(540,1040)`)
- **Keyword**: Parola più significativa del chunk in Raleway SemiBold (`\b600`)
- **Chunking**: 3–4 parole per riga, max ~26 caratteri, pausa > 500ms forza split

### Watermark
- **Testo**: `@lavocedelsuccesso`  
- **Font**: Raleway SemiBold (`\b600`), size 36, bianco
- **Posizione**: 70px sotto i sottotitoli (`\pos(540,1110)`)
- **Durata**: Tutta la timeline

### Codec output
- **Apple Silicon**: `h264_videotoolbox` (accelerazione hardware, `-q:v 60`)
- **Fallback**: `libx264 -crf 18 -preset fast`
- **Audio**: AAC 192kbps, copiato dal sorgente

---

## Soluzione problemi

### `ModuleNotFoundError: No module named 'faster_whisper'`
```bash
source .venv/bin/activate  # riattiva il venv
pip install -r requirements.txt
```

### `ffmpeg: command not found`
```bash
brew install ffmpeg
```

### I sottotitoli appaiono con font sbagliato
Installa Raleway dal sistema o copia i `.ttf` in `./fonts/`.

### Audio non rilevato / trascrizione vuota
Verifica che il video abbia una traccia audio:
```bash
ffprobe -v error -select_streams a -show_entries stream=codec_name -of default=noprint_wrappers=1 video.mp4
```

### Errore `compute_type=float16` non supportato
Usa il fallback manuale:
```bash
python main.py --input video.mp4 --compute-type int8
```
