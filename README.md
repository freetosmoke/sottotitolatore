# Sottotitolatore

A macOS-focused subtitle and video processing tool for creating styled subtitles for vertical 9:16 video content.

Sottotitolatore combines automatic speech transcription, subtitle chunking, visual subtitle rendering, video preview and final video export in a single local workflow.

The project provides both a command-line interface and a local Web UI.

---

## Features

- Automatic speech transcription with `faster-whisper`
- Italian transcription by default
- Configurable transcription language
- Support for multiple Whisper model sizes
- Automatic word grouping and subtitle chunking
- Keyword highlighting
- Styled subtitle rendering
- Multiple subtitle presets
- Custom font support
- Watermark rendering
- Local Web UI
- Video upload and preview
- Synchronized video playback
- Subtitle correction workflow
- Audio waveform visualization
- Batch video processing from the CLI
- Apple Silicon hardware-accelerated video encoding
- Software encoding fallback through `libx264`
- macOS application and DMG build scripts

---

## How It Works

The main processing pipeline is:

```text
Video
  │
  ▼
Audio extraction
  │
  ▼
Speech transcription
  │
  ▼
Word grouping / chunking
  │
  ▼
Subtitle rendering
  │
  ▼
Video burn-in
  │
  ▼
Final subtitled video
```

The CLI pipeline uses:

- `faster-whisper` for speech transcription
- Pillow for subtitle image rendering
- FFmpeg for video processing and final rendering

---

## User Interface

Sottotitolatore includes a local Web UI designed for working with vertical video subtitles.

The Web UI provides:

- Video upload
- Video frame preview
- Synchronized video playback
- Subtitle preview
- Audio waveform visualization
- Subtitle correction
- Multiple highlighted words within the same subtitle line
- Preset selection
- Final video rendering

The Web UI runs locally on the user's Mac.

---

## Subtitle Presets

The project includes several predefined subtitle styles.

### La Voce del Successo

The default preset.

It uses the Raleway font and includes a watermark.

### MC

A preset using the Alata font without a watermark.

### Minimal Modern

A compact Raleway-based preset with subtitle outline/shadow and watermark support.

Presets are stored in:

```text
presets.json
```

The application can load and save preset configurations from the configured data directory.

---

## Project Structure

```text
sottotitolatore/
│
├── main.py
├── web_app.py
│
├── transcriber.py
├── translator.py
├── audio_extractor.py
├── keyword_selector.py
├── subtitle_renderer.py
├── ass_generator.py
├── video_renderer.py
├── silence_remover.py
│
├── presets.json
├── requirements.txt
│
├── web_static/
│   └── index.html
│
├── fonts/
│   ├── Alata-Regular.ttf
│   ├── Raleway-Light.ttf
│   └── Raleway-SemiBold.ttf
│
├── build_app.sh
├── build_dmg.sh
├── build_silicon_dmg.sh
├── package_dmg.py
├── create_icon.py
├── launcher.m
│
├── AppIcon.icns
└── LICENSE
```

---

## Requirements

- macOS
- Python 3.10 or newer
- FFmpeg

Apple Silicon is recommended when using hardware-accelerated video encoding.

---

## Installing FFmpeg

The easiest way to install FFmpeg on macOS is through Homebrew:

```bash
brew install ffmpeg
```

Verify the installation:

```bash
ffmpeg -version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/freetosmoke/sottotitolatore.git
cd sottotitolatore
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The main Python dependencies are:

```text
faster-whisper
typer
rich
Pillow
```

---

# CLI

Sottotitolatore can be used directly from the command line.

## Process a Video

```bash
python main.py --input video.mp4
```

If no output path is specified, the application creates an output file using the `_subtitled` suffix.

For example:

```text
video.mp4
```

becomes:

```text
video_subtitled.mp4
```

---

## Specify an Output File

```bash
python main.py \
  --input video.mp4 \
  --output output.mp4
```

---

## Select a Whisper Model

The default model is `small`.

Example:

```bash
python main.py \
  --input video.mp4 \
  --model medium
```

The available model names depend on the models supported by the installed `faster-whisper` version.

---

## Select the Language

Italian is the default language:

```bash
python main.py \
  --input video.mp4 \
  --language it
```

A different language can be specified using its language code:

```bash
python main.py \
  --input video.mp4 \
  --language en
```

---

## Batch Processing

The CLI can process all supported videos in a directory:

```bash
python main.py \
  --input ./videos \
  --batch
```

Supported video extensions include:

```text
.mp4
.mov
.mkv
.avi
.webm
.m4v
```

---

## Keep Temporary Files

By default, temporary processing files are removed after rendering.

To keep them:

```bash
python main.py \
  --input video.mp4 \
  --keep-temp
```

This can be useful when debugging the processing pipeline.

---

## Hardware Encoding

On compatible Apple Silicon systems, hardware video encoding can be enabled explicitly:

```bash
python main.py \
  --input video.mp4 \
  --hw
```

To explicitly disable hardware encoding:

```bash
python main.py \
  --input video.mp4 \
  --no-hw
```

When hardware encoding is not used, the project can fall back to software encoding through `libx264`.

---

## CLI Options

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | Required | Input video or directory |
| `--output`, `-o` | `<input>_subtitled` | Output video path |
| `--batch`, `-b` | `False` | Process videos in a directory |
| `--model`, `-m` | `small` | Whisper model |
| `--compute-type` | `float16` | Whisper computation type |
| `--language`, `-l` | `it` | Transcription language |
| `--keep-temp` | `False` | Keep temporary processing files |
| `--hw` / `--no-hw` | Automatic | Enable or disable hardware video encoding |

---

# Web UI

The project also includes a local Web UI implemented in:

```text
web_app.py
```

The application uses a local HTTP server and can be configured through environment variables.

Start it with:

```bash
python web_app.py
```

The default port is:

```text
8501
```

The Web UI can therefore be accessed locally through:

```text
http://localhost:8501
```

---

## Custom Port

The port can be changed using:

```bash
SOTTOTITOLATORE_PORT=9000 python web_app.py
```

---

## Custom Data Directory

The application supports a custom data directory:

```bash
SOTTOTITOLATORE_DATA_DIR=/path/to/data python web_app.py
```

The application uses this directory for its runtime upload/output data and preset storage.

---

# Fonts

The repository includes the following fonts:

- Raleway Light
- Raleway SemiBold
- Alata Regular

They are used by the included subtitle presets.

Font files are stored in:

```text
fonts/
```

---

# Video Rendering

FFmpeg is used for the final video rendering stage.

On Apple Silicon, the project can use:

```text
h264_videotoolbox
```

for hardware-accelerated H.264 encoding.

A software encoding path using:

```text
libx264
```

is also supported.

---

# macOS Builds

The repository includes scripts for building the macOS application and DMG packages.

Available scripts include:

```text
build_app.sh
build_dmg.sh
build_silicon_dmg.sh
```

The project also includes:

```text
package_dmg.py
create_icon.py
launcher.m
```

for the application packaging workflow.

The Apple Silicon build is intended for compatible Apple Silicon Macs.

---

# Development

After installing the dependencies, the CLI can be run directly from the project directory:

```bash
python main.py --input video.mp4
```

The local Web UI can be started with:

```bash
python web_app.py
```

For development, changes should ideally be tested against the workflow they affect before being committed.

---

# Contributing

Contributions, bug reports and improvements are welcome.

When contributing:

1. Keep changes focused.
2. Avoid committing generated files or local runtime data.
3. Test the affected workflow before submitting changes.
4. Document new user-facing functionality.
5. Keep dependencies and configuration changes explicit.

---

# Project Status

Sottotitolatore is a macOS-oriented subtitle and video processing project currently under development.

The repository contains both:

- a command-line processing pipeline
- a local Web UI for subtitle and video workflows

The project is primarily designed around vertical 9:16 video content and customizable subtitle styles.

---

# License

Sottotitolatore is released under the MIT License.

See [`LICENSE`](LICENSE) for the complete license text.

---

# Repository

GitHub:

https://github.com/freetosmoke/sottotitolatore
