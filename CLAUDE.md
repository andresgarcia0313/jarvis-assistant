# JARVIS - Contexto para Claude

> Asistente de voz estilo Iron Man para Kubuntu. Claude CLI como cerebro, voz 100% local.

## Repositorios

| Remote | URL | Propósito |
|--------|-----|-----------|
| `github` | https://github.com/andresgarcia0313/jarvis-assistant | Público |
| `origin` | https://devops.ingeniumcodex.com/devops/jarvis | Privado (CI/CD) |

---

## Estado Actual

**Fases Completadas:** 1-13 (Core + GUI)
**Historias Implementadas:** 20/20
**Última actualización:** 2025-12-31

### Funcionalidades Activas

- Wake word detection (OpenWakeWord)
- STT local (Whisper/Vosk) - español, alta precisión
- TTS local (Piper) - voz davefx
- Integración Claude CLI
- Memoria persistente SQLite
- Monitoreo del sistema
- Control volumen/brillo
- Recordatorios y calendario
- Visión pantalla/cámara
- Control mouse/teclado
- GUI PyQt5 estilo Iron Man HUD

---

## Arquitectura UI (Vue-style)

Componentes autocontenidos en `ui/components/`:

```
ui/
├── hud_gui.py           # GUI principal
├── live_listener.py     # Thread de audio
├── jarvis_brain.py      # Lógica de procesamiento
├── config_dialog.py     # Diálogo configuración
├── tts_engine.py        # Motor TTS
├── audio_devices.py     # Gestión dispositivos
├── audio_processor.py   # Procesamiento audio
├── vad_detector.py      # Voice Activity Detection
├── beamformer.py        # Beamforming
├── diagnostics.py       # Diagnósticos
└── components/
    ├── theme.py         # Paleta de colores
    ├── header.py        # Título + CONFIG + STANDBY
    ├── audio_bar.py     # Barra nivel audio
    ├── text_panels.py   # VoiceInput, AIResponse, SystemLog
    ├── controls.py      # ACTIVATE/CLEAR
    ├── diagnostics_screen.py
    └── main_screen.py   # Composición principal
```

### Paleta de Colores

```python
CYAN = "#00d4ff"      # Principal
GREEN = "#00ff88"     # Éxito/Activo
YELLOW = "#ffaa00"    # Advertencia
RED = "#ff4444"       # Error
BG = "#050a0e"        # Fondo
BORDER = "#1a3a4a"    # Bordes
TEXT = "#e0f7ff"      # Texto principal
TEXT_DIM = "#4a6a7a"  # Texto secundario
```

---

## Comandos

### Ejecutar

```bash
cd /home/andres/Desarrollo/IA/Jarvis
source venv/bin/activate

python jarvis_gui.py      # GUI completa
python jarvis.py          # Solo voz
python -m pytest tests/   # Tests
```

### Probar Componentes

```bash
python -m ui.components.header
python -m ui.components.audio_bar
python -m ui.components.main_screen
```

### Git

```bash
git add -A && git commit -m "tipo(scope): descripción"
git push github main && git push origin main
```

### Build .deb

```bash
./build_deb.sh
# Resultado: jarvis-assistant_1.9.0_amd64.deb
```

---

## Estructura del Proyecto

```
Jarvis/
├── jarvis.py              # Orquestador CLI
├── jarvis_gui.py          # Entrada GUI
├── config.yaml            # Configuración
├── requirements.txt       # Dependencias
├── install.sh             # Instalador
├── build_deb.sh           # Build .deb
│
├── modules/               # Lógica de negocio
│   ├── stt.py             # Speech-to-Text
│   ├── tts.py             # Text-to-Speech
│   ├── wake_word.py       # Wake word
│   ├── cli_bridge.py      # Puente Claude CLI
│   ├── personality.py     # Personalidad
│   ├── memory.py          # SQLite
│   ├── system_monitor.py  # CPU, RAM, temp
│   ├── system_control.py  # Volumen, brillo
│   ├── reminders.py       # Recordatorios
│   ├── calendar_tools.py  # Calendario ICS
│   ├── dev_tools.py       # Git, Docker
│   ├── screen_vision.py   # Captura pantalla
│   ├── camera_vision.py   # Captura cámara
│   └── input_control.py   # Mouse/teclado
│
├── ui/                    # Interfaz gráfica
├── sounds/                # Efectos
├── tests/                 # Tests
├── models/                # Vosk/Piper (gitignore)
├── memory/                # SQLite (gitignore)
├── logs/                  # Logs (gitignore)
├── assets/                # Iconos
└── packaging/             # Archivos .deb
```

---

## Dependencias

| Componente | Librería |
|------------|----------|
| GUI | PyQt5 |
| STT | faster-whisper, vosk |
| TTS | piper-tts |
| Wake Word | openwakeword |
| Audio | pyaudio, sounddevice |
| Vision | Pillow, spectacle |
| Input | xdotool (solo X11) |
| DB | sqlite3 |

---

## Arquitectura STT (Speech-to-Text)

Sistema modular con soporte para múltiples motores:

```
modules/
├── stt_whisper.py      # faster-whisper (alta precisión)
├── stt_vosk_adapter.py # Vosk (bajo consumo)
└── stt_factory.py      # Factory para crear motor

ui/
├── listener_whisper.py # Listener optimizado para Whisper
├── listener_factory.py # Factory para crear listener
└── live_listener.py    # Listener Vosk (legacy)
```

### Configuración (config.yaml)

```yaml
stt:
  engine: "whisper"  # o "vosk"
  whisper:
    model_size: "tiny"  # tiny, base, small
  vosk:
    model_path: "models/vosk-model-small-es-0.42"
```

### Comparación

| Motor | Precisión | RAM | Latencia |
|-------|-----------|-----|----------|
| Whisper tiny | ★★★★★ | ~150MB | ~1s |
| Vosk small-es | ★★☆☆☆ | ~50MB | Real-time |

---

## Roadmap

### Fase 14: Integración Web (P0)
- [ ] Clima, noticias, tráfico
- [ ] Lectura emails (IMAP)
- [ ] Envío emails por voz
- [ ] Telegram/WhatsApp
- [ ] Búsquedas web

### Fase 15: Proactividad (P0)
- [ ] Análisis de patrones
- [ ] Sugerencias por calendario
- [ ] Alertas contextuales
- [ ] Recordatorios bienestar
- [ ] Resumen matutino

### Fase 16: Voz Natural (P1)
- [ ] XTTS o StyleTTS2
- [ ] Prosodia natural
- [ ] Velocidad adaptativa

### Fase 17: Home Assistant (P1)
- [ ] Control luces
- [ ] Control clima
- [ ] Escenas predefinidas

### Fases Futuras
- 18: Contexto conversacional profundo (vector DB)
- 19: Multi-room / Multi-dispositivo
- 20: Video en tiempo real
- 21: HUD avanzado (dashboard)
- 22: Seguridad por voz

---

## Problemas Conocidos

1. **xdotool** solo funciona en X11, no Wayland
2. **Modelos** deben descargarse via `install.sh` (~200MB)
3. **RAM** objetivo < 250MB en reposo

---

## Convenciones

- **Commits:** `tipo(scope): descripción`
- **Tipos:** feat, fix, refactor, docs, test, chore
- **Código:** inglés
- **Archivos:** < 100 líneas (refactorizar si excede)

---

*Última actualización: 2025-12-31*
