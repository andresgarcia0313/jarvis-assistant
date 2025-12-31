# JARVIS - Contexto para Claude

> Asistente de voz estilo Iron Man para Kubuntu. Claude CLI como cerebro, voz 100% local.

## Estado Actual (2025-12-31)

**Fases Completadas:** 1-13 (Core completo + GUI)
**Fase Actual:** Mejoras y optimizaciones
**Repositorio:** https://devops.ingeniumcodex.com/devops/jarvis

### Lo que funciona:
- Wake word detection (OpenWakeWord)
- STT local (Vosk) - español
- TTS local (Piper) - voz davefx español
- Integración Claude CLI
- Memoria persistente SQLite
- Monitoreo del sistema
- Control de volumen/brillo
- Recordatorios y calendario
- Visión de pantalla y cámara
- Control de mouse/teclado
- GUI PyQt5 estilo Iron Man HUD

---

## Arquitectura de Componentes UI (Vue-style)

La UI usa arquitectura de componentes autocontenidos similar a Vue.js.

### Estructura

```
ui/
├── __init__.py
├── hud_gui.py           # GUI principal (usa MainScreen)
├── hud_style.py         # Compatibilidad legacy (30 lineas)
├── live_listener.py     # Thread de audio
├── jarvis_brain.py      # Logica de procesamiento
├── config_dialog.py     # Dialogo de configuracion
├── tts_engine.py        # Motor TTS
├── audio_devices.py     # Gestion de dispositivos
├── audio_processor.py   # Procesamiento de audio
├── vad_detector.py      # Voice Activity Detection
├── beamformer.py        # Beamforming de audio
├── logger_config.py     # Configuracion de logs
├── diagnostics.py       # Diagnosticos del sistema
└── components/
    ├── __init__.py      # Exports publicos
    ├── theme.py         # Constantes de color (14 lineas)
    ├── header.py        # Titulo + CONFIG + STANDBY (60 lineas)
    ├── audio_bar.py     # Barra nivel audio (59 lineas)
    ├── text_panels.py   # VoiceInput, AIResponse, SystemLog (139 lineas)
    ├── controls.py      # ACTIVATE/CLEAR buttons (76 lineas)
    ├── diagnostics_screen.py  # Pantalla diagnosticos (107 lineas)
    └── main_screen.py   # Composicion de todo (108 lineas)
```

### Principios de Componentes

1. **Autocontenidos**: Cada componente tiene estilos inline
2. **Testeables**: Cada componente tiene `if __name__ == "__main__":`
3. **Minimal**: Codigo minimo necesario
4. **Composicion**: MainScreen compone los demas componentes

### Paleta de Colores (theme.py)

```python
CYAN = "#00d4ff"      # Principal
GREEN = "#00ff88"     # Exito/Activo
YELLOW = "#ffaa00"    # Advertencia
RED = "#ff4444"       # Error
BG = "#050a0e"        # Fondo oscuro
BORDER = "#1a3a4a"    # Bordes
TEXT = "#e0f7ff"      # Texto principal
TEXT_DIM = "#4a6a7a"  # Texto secundario
```

### Probar Componente Individual

```bash
cd /home/andres/Desarrollo/IA/Jarvis
source venv/bin/activate
python -m ui.components.header      # Probar header
python -m ui.components.audio_bar   # Probar barra audio
python -m ui.components.main_screen # Probar pantalla completa
```

---

## Comandos Frecuentes

### Ejecutar

```bash
cd /home/andres/Desarrollo/IA/Jarvis
source venv/bin/activate

# GUI completa
python jarvis_gui.py

# Solo voz (sin GUI)
python jarvis.py

# Tests
python -m pytest tests/ -v
```

### Git

```bash
git status
git add -A
git commit -m "feat(scope): descripcion"
git push origin main
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
├── jarvis_gui.py          # Punto de entrada GUI
├── config.yaml            # Configuracion
├── requirements.txt       # Dependencias Python
├── install.sh             # Instalador
├── build_deb.sh           # Construccion .deb
│
├── modules/               # Logica de negocio
│   ├── stt.py             # Speech-to-Text (Vosk)
│   ├── tts.py             # Text-to-Speech (Piper)
│   ├── wake_word.py       # Wake word (OpenWakeWord)
│   ├── cli_bridge.py      # Puente a Claude CLI
│   ├── personality.py     # Personalidad JARVIS
│   ├── memory.py          # Memoria SQLite
│   ├── system_monitor.py  # CPU, RAM, temp
│   ├── system_control.py  # Volumen, brillo
│   ├── reminders.py       # Recordatorios
│   ├── calendar_tools.py  # Calendario ICS
│   ├── dev_tools.py       # Git, Docker
│   ├── screen_vision.py   # Captura pantalla
│   ├── camera_vision.py   # Captura camara
│   ├── input_control.py   # Mouse/teclado
│   └── visual_automation.py
│
├── ui/                    # Interfaz grafica
│   ├── components/        # Componentes Vue-style
│   └── ...
│
├── sounds/                # Efectos de sonido
├── tests/                 # Tests unitarios
├── models/                # Modelos Vosk/Piper (gitignore)
├── memory/                # SQLite (gitignore)
├── logs/                  # Logs (gitignore)
├── assets/                # Iconos
├── docs/                  # Documentacion
└── packaging/             # Archivos .deb
```

---

## Dependencias Clave

| Componente | Libreria | Notas |
|------------|----------|-------|
| GUI | PyQt5 | Widgets y layouts |
| STT | vosk | Modelo small-es |
| TTS | piper-tts | Voz es_ES-davefx |
| Wake Word | openwakeword | "Alexa" por defecto |
| Audio | pyaudio, sounddevice | Captura mic |
| Vision | Pillow, spectacle | Screenshots |
| Input | xdotool | Solo X11 |
| DB | sqlite3 | Memoria persistente |

---

## Repositorio Git

- **URL:** https://devops.ingeniumcodex.com/devops/jarvis
- **Branch:** main
- **Credenciales:** devops / asde71.4

### Push cambios

```bash
git add -A
git commit -m "tipo(scope): descripcion"
git push origin main
```

---

## Notas de Desarrollo

### Al modificar UI
1. Editar componente en `ui/components/`
2. Probar individualmente: `python -m ui.components.NOMBRE`
3. Probar integracion: `python jarvis_gui.py`
4. Actualizar `build_deb.sh` si hay nuevos archivos

### Al agregar modulo
1. Crear en `modules/`
2. Agregar test en `tests/`
3. Integrar en `jarvis.py` o `jarvis_gui.py`

### Convenciones
- Commits: `tipo(scope): descripcion`
- Tipos: feat, fix, refactor, docs, test, chore
- Codigo en ingles, comentarios en espanol si es necesario

---

## Problemas Conocidos

1. **xdotool** solo funciona en X11, no Wayland
2. **Modelos** deben descargarse via `install.sh` (~200MB)
3. **RAM** objetivo < 250MB en reposo

---

## Proximos Pasos (ROADMAP.md)

- Fase 14: Integracion Web (email, clima)
- Fase 15: Proactividad (sugerencias automaticas)
- Fase 16: Voz natural (XTTS)
- Fase 17: Home Assistant

---

*Ultima actualizacion: 2025-12-31*
