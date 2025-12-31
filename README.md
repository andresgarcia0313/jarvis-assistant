# JARVIS - Asistente de Voz para Kubuntu

Asistente de voz inspirado en JARVIS de Iron Man, con procesamiento de voz 100% local y Claude como cerebro.

**Repositorio:** https://devops.ingeniumcodex.com/devops/jarvis

## Características

### Core
- **Wake Word**: Activación por voz ("Alexa" por defecto, configurable)
- **STT Local**: Transcripción offline con Vosk
- **TTS Local**: Síntesis de voz con Piper
- **Claude CLI**: Respuestas inteligentes vía Claude
- **Barge-in**: Interrumpe a JARVIS mientras habla

### Personalidad
- Tono profesional con toques de humor británico
- Frases icónicas de JARVIS/Iron Man
- Modo sarcástico configurable
- Respuestas en español

### Memoria
- Memoria persistente entre sesiones
- Contexto de conversaciones anteriores
- Preferencias del usuario
- Base de datos SQLite

### Monitoreo del Sistema
- CPU, RAM, disco, red
- Temperaturas de componentes
- Alertas automáticas
- "Jarvis, estado del sistema"

### Control del Sistema
- Volumen y brillo
- Control de música (Spotify, Rhythmbox)
- Capturas de pantalla
- Aplicaciones del sistema
- "Jarvis, sube el volumen"

### Recordatorios y Calendario
- Recordatorios con tiempo natural
- Integración con calendario ICS
- Persistencia entre sesiones
- "Jarvis, recuérdame en 10 minutos..."

### Herramientas de Desarrollador
- Estado de git del proyecto
- Dependencias NPM/pip
- Verificación de puertos
- "Jarvis, estado del proyecto"

### Visión de Pantalla
- Análisis de contenido en pantalla
- Lectura de texto visible
- Detección de errores
- "Jarvis, qué hay en pantalla"

### Visión de Cámara
- Captura con privacidad (siempre notifica)
- Análisis visual del entorno
- Fotos se eliminan inmediatamente
- "Jarvis, qué ves con la cámara"

### Control de Input
- Control de mouse y teclado
- Confirmación antes de ejecutar
- Palabras de seguridad ("alto", "para")
- Modo demo sin ejecución real

### Automatización Visual
- Tareas multi-paso
- Planificación con IA
- Ejecución supervisada
- "Jarvis, abre el navegador y busca..."

### Interfaz
- Widget de estado (PyQt5, opcional)
- Efectos de sonido
- Indicadores de estado
- Bandeja del sistema

## Requisitos

- Kubuntu 24.04+ (o Ubuntu/Debian compatible)
- Python 3.10+
- Micrófono funcional
- Claude CLI instalado y configurado

## Instalación

```bash
# Clonar o navegar al directorio
cd ~/Desarrollo/JarvisIronMan

# Instalación básica
chmod +x install.sh
./install.sh

# Con servicio systemd (auto-inicio)
./install.sh --systemd

# Con herramientas de desarrollo
./install.sh --dev
```

El script instalará:
- Dependencias del sistema (portaudio, espeak, ffmpeg, xdotool)
- Entorno virtual Python
- Paquetes Python
- Modelos de voz (Vosk español, Piper español)

## Uso

### Ejecución Manual
```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar JARVIS
python jarvis.py

# Con logs detallados
python jarvis.py -v
```

### Como Servicio
```bash
# Iniciar
sudo systemctl start jarvis

# Detener
sudo systemctl stop jarvis

# Ver estado
sudo systemctl status jarvis

# Ver logs
journalctl -u jarvis -f
```

### Comandos de Voz

| Comando | Acción |
|---------|--------|
| "Alexa" | Activar JARVIS |
| "Apágate" | Cerrar JARVIS |
| "Estado del sistema" | Ver CPU, RAM, etc. |
| "Sube el volumen" | Aumentar volumen |
| "Qué hay en pantalla" | Analizar pantalla |
| "Recuérdame en 10 minutos..." | Crear recordatorio |
| "Estado del proyecto" | Git y dependencias |
| "Abre Firefox" | Ejecutar aplicación |

## Estructura del Proyecto

```
Jarvis/
├── jarvis.py              # Orquestador CLI
├── jarvis_gui.py          # Punto de entrada GUI
├── config.yaml            # Configuración
├── requirements.txt       # Dependencias Python
├── install.sh             # Script de instalación
├── build_deb.sh           # Construcción paquete .deb
│
├── modules/               # Lógica de negocio
│   ├── stt.py             # Speech-to-Text (Vosk)
│   ├── tts.py             # Text-to-Speech (Piper)
│   ├── wake_word.py       # Detección wake word
│   ├── cli_bridge.py      # Integración Claude CLI
│   ├── personality.py     # Personalidad JARVIS
│   ├── memory.py          # Memoria persistente
│   ├── system_monitor.py  # Monitoreo del sistema
│   ├── system_control.py  # Control del sistema
│   ├── reminders.py       # Recordatorios
│   ├── calendar_tools.py  # Calendario ICS
│   ├── dev_tools.py       # Herramientas dev
│   ├── screen_vision.py   # Visión de pantalla
│   ├── camera_vision.py   # Visión de cámara
│   ├── input_control.py   # Control mouse/teclado
│   └── visual_automation.py
│
├── ui/                    # Interfaz gráfica (arquitectura Vue-style)
│   ├── hud_gui.py         # GUI principal
│   ├── hud_style.py       # Compatibilidad legacy
│   ├── live_listener.py   # Thread de audio
│   ├── jarvis_brain.py    # Lógica de procesamiento
│   ├── config_dialog.py   # Diálogo configuración
│   ├── tts_engine.py      # Motor TTS
│   ├── audio_devices.py   # Gestión dispositivos
│   ├── audio_processor.py # Procesamiento audio
│   ├── vad_detector.py    # Voice Activity Detection
│   ├── beamformer.py      # Beamforming
│   ├── logger_config.py   # Config logs
│   ├── diagnostics.py     # Diagnósticos
│   └── components/        # Componentes autocontenidos
│       ├── theme.py       # Paleta de colores
│       ├── header.py      # Título + CONFIG + STANDBY
│       ├── audio_bar.py   # Barra nivel audio
│       ├── text_panels.py # Paneles de texto
│       ├── controls.py    # Botones ACTIVATE/CLEAR
│       ├── diagnostics_screen.py
│       └── main_screen.py # Composición principal
│
├── sounds/                # Efectos de sonido
├── tests/                 # Tests unitarios
├── models/                # Modelos Vosk/Piper (gitignore)
├── memory/                # SQLite (gitignore)
├── logs/                  # Logs (gitignore)
├── assets/                # Iconos
├── docs/                  # Documentación
└── packaging/             # Archivos .deb
```

### Arquitectura UI (Vue-style)

Los componentes UI siguen principios de Vue.js:
- **Autocontenidos**: Cada componente tiene sus estilos inline
- **Testeables**: Cada uno tiene `if __name__ == "__main__":` para pruebas
- **Composición**: `MainScreen` compone todos los demás componentes

```bash
# Probar componente individual
python -m ui.components.header
python -m ui.components.audio_bar
python -m ui.components.main_screen
```

## Configuración

Edita `config.yaml`:

```yaml
# Personalidad
personality:
  sarcasm_level: 0.3    # 0.0 a 1.0
  formal_mode: false
  use_sir: true         # Usar "Señor"

# Wake word
wake_word:
  threshold: 0.5        # Sensibilidad

# Sistema
system_monitor:
  check_interval: 30    # Segundos
  temp_warning: 80      # °C

# Sonidos
sounds:
  enabled: true
  volume: 0.5

# Widget
widget:
  enabled: true
```

## Tecnologías

| Componente | Tecnología |
|------------|------------|
| Wake Word | OpenWakeWord |
| STT | Vosk |
| TTS | Piper |
| IA | Claude CLI |
| Base de datos | SQLite |
| Control input | xdotool |
| Capturas | spectacle/scrot |
| Cámara | ffmpeg/v4l2 |
| Widget | PyQt5 |

## Tests

```bash
# Activar entorno
source venv/bin/activate

# Ejecutar todos los tests
python -m pytest tests/ -v

# Tests específicos
python -m pytest tests/test_memory.py -v

# Con cobertura
python -m pytest tests/ --cov=modules
```

## Troubleshooting

### "Claude CLI not found"
```bash
npm install -g @anthropic-ai/claude-cli
```

### "No audio devices"
```bash
arecord -l
sudo apt install pulseaudio pavucontrol
```

### Cámara no detectada
```bash
ls /dev/video*
sudo apt install v4l-utils
v4l2-ctl --list-devices
```

### xdotool no funciona
```bash
# Solo funciona en X11, no Wayland
echo $XDG_SESSION_TYPE
# Si es wayland, cerrar sesión e iniciar con X11
```

### Widget no aparece
```bash
pip install PyQt5
```

## Seguridad

- **Cámara**: Siempre notifica antes de capturar, fotos eliminadas inmediatamente
- **Input control**: Requiere confirmación explícita
- **Palabras de seguridad**: "alto", "para", "stop" cancelan operaciones
- **Modo demo**: Ejecutar sin acciones reales para probar

## Licencia

Proyecto personal - uso libre

## Créditos

- Claude (Anthropic) como motor de IA
- Vosk para reconocimiento de voz offline
- Piper para síntesis de voz
- OpenWakeWord para detección de palabra clave
