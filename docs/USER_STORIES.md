# Historias de Usuario - JARVIS Voice Assistant

## Índice
1. [Core - Sistema Base](#core---sistema-base)
2. [UI - Interfaz de Usuario](#ui---interfaz-de-usuario)
3. [STT - Speech to Text](#stt---speech-to-text)
4. [TTS - Text to Speech](#tts---text-to-speech)
5. [Brain - Integración con IA](#brain---integración-con-ia)
6. [Diagnóstico - Sistema de Verificación](#diagnóstico---sistema-de-verificación)

---

## Core - Sistema Base

### US-001: Instalación via paquete .deb
**Como** usuario de Kubuntu
**Quiero** instalar JARVIS con un solo comando
**Para** tener el asistente funcionando sin configuración manual

**Criterios de aceptación:**
- [x] Paquete .deb se construye con `./build_deb.sh`
- [x] Instalación con `sudo dpkg -i jarvis-assistant_*.deb`
- [x] Crea entorno virtual Python automáticamente
- [x] Instala dependencias: vosk, sounddevice, PyYAML, pyaudio, numpy, PyQt5
- [x] Descarga modelo de voz Vosk automáticamente
- [x] Crea comando `jarvis-gui` en el sistema
- [x] Registra aplicación en menú del sistema

**Archivos:** `build_deb.sh`, `packaging/deb/DEBIAN/*`

---

### US-002: Ejecución del asistente
**Como** usuario
**Quiero** iniciar JARVIS desde terminal o menú
**Para** comenzar a usar el asistente de voz

**Criterios de aceptación:**
- [x] Comando `jarvis-gui` inicia la aplicación
- [x] Icono disponible en menú de aplicaciones
- [x] Aplicación se abre con interfaz gráfica
- [x] Mensaje de bienvenida por voz al iniciar

**Archivos:** `jarvis_gui.py`, `packaging/deb/usr/bin/jarvis-gui`

---

## UI - Interfaz de Usuario

### US-003: Interfaz estilo Iron Man HUD
**Como** usuario
**Quiero** una interfaz visual similar al HUD de JARVIS en Iron Man
**Para** tener una experiencia inmersiva y futurista

**Criterios de aceptación:**
- [x] Fondo oscuro (#050a0e)
- [x] Colores cyan brillante (#00d4ff) para acentos
- [x] Título "J.A.R.V.I.S." con espaciado de letras
- [x] Etiquetas en mayúsculas (VOICE INPUT, AI RESPONSE, etc.)
- [x] Botones con bordes brillantes
- [x] Barra de audio con gradiente cyan

**Archivos:** `ui/hud_style.py`

---

### US-004: Panel de entrada de voz
**Como** usuario
**Quiero** ver lo que JARVIS está escuchando en tiempo real
**Para** verificar que mi voz se está detectando correctamente

**Criterios de aceptación:**
- [x] Panel "VOICE INPUT" visible
- [x] Transcripción en tiempo real mientras hablo
- [x] Texto en color verde (#00ff88)
- [x] Borde izquierdo verde como indicador visual

**Archivos:** `ui/components/text_panels.py`

---

### US-005: Panel de respuesta de IA
**Como** usuario
**Quiero** ver las respuestas de JARVIS en pantalla
**Para** leer la información además de escucharla

**Criterios de aceptación:**
- [x] Panel "AI RESPONSE" expandible
- [x] Respuestas en color cyan (#00d4ff)
- [x] Borde izquierdo cyan como indicador
- [x] Scroll automático al agregar texto

**Archivos:** `ui/components/text_panels.py`

---

### US-006: Panel de log del sistema
**Como** usuario
**Quiero** ver los eventos del sistema
**Para** depurar problemas y entender qué está pasando

**Criterios de aceptación:**
- [x] Panel "SYSTEM LOG" colapsable
- [x] Botón HIDE/SHOW para alternar visibilidad
- [x] Eventos con timestamp y tipo
- [x] Iconos por tipo: [i] info, [+] ok, [!] warn, [x] error

**Archivos:** `ui/components/text_panels.py`

---

### US-007: Barra de nivel de audio
**Como** usuario
**Quiero** ver el nivel de mi micrófono en tiempo real
**Para** saber si JARVIS me está escuchando

**Criterios de aceptación:**
- [x] Barra de progreso de 0-100%
- [x] Actualización cada 100ms
- [x] Color según nivel: verde (alto), cyan (medio), amarillo (bajo)
- [x] Porcentaje numérico visible

**Archivos:** `ui/components/audio_bar.py`

---

### US-008: Controles principales
**Como** usuario
**Quiero** botones claros para activar/desactivar el micrófono
**Para** controlar cuándo JARVIS me escucha

**Criterios de aceptación:**
- [x] Botón ACTIVATE/DEACTIVATE grande y visible
- [x] Cambio de color al activar (cyan → rojo)
- [x] Botón CLEAR para limpiar pantalla
- [x] Indicador de estado en header (STANDBY/LISTENING)

**Archivos:** `ui/components/controls.py`, `ui/components/header.py`

---

### US-009: Configuración del sistema
**Como** usuario
**Quiero** acceder a opciones de configuración
**Para** personalizar el comportamiento de JARVIS

**Criterios de aceptación:**
- [x] Botón CONFIG en header
- [x] Diálogo de configuración modal
- [x] Selección de dispositivo de audio
- [x] Opción de activar/desactivar TTS
- [x] Modo de operación (REPL/API)

**Archivos:** `ui/config_dialog.py`

---

### US-010: Arquitectura de componentes modular
**Como** desarrollador
**Quiero** componentes UI separados y reutilizables
**Para** mantener el código organizado y fácil de modificar

**Criterios de aceptación:**
- [x] Carpeta `ui/components/` con componentes aislados
- [x] HeaderComponent - título y estado
- [x] AudioBarComponent - barra de nivel
- [x] TextPanelComponent - paneles de texto genéricos
- [x] ControlsComponent - botones de control
- [x] DiagnosticsScreen - pantalla de diagnóstico
- [x] MainScreen - pantalla principal integrada

**Archivos:** `ui/components/*.py`

---

## STT - Speech to Text

### US-011: Reconocimiento de voz local
**Como** usuario
**Quiero** que mi voz se procese localmente
**Para** mantener mi privacidad sin enviar audio a la nube

**Criterios de aceptación:**
- [x] Modelo Vosk ejecutándose localmente
- [x] Modelo español (vosk-model-small-es-0.42)
- [x] Transcripción en tiempo real
- [x] Soporte para resultados parciales y finales

**Archivos:** `ui/live_listener.py`

---

### US-012: Wake word "Jarvis"
**Como** usuario
**Quiero** activar JARVIS diciendo su nombre
**Para** dar comandos de forma natural

**Criterios de aceptación:**
- [x] Detecta "Jarvis" como wake word
- [x] Variantes aceptadas: jarvis, jarvi, jarby, harvey, chavis, chaves
- [x] Extrae comando después del wake word
- [x] Responde "A sus órdenes" si solo se dice el nombre

**Archivos:** `ui/hud_gui.py`

---

### US-013: Procesamiento de audio multi-canal
**Como** usuario
**Quiero** que JARVIS funcione con diferentes micrófonos
**Para** usar el hardware que tengo disponible

**Criterios de aceptación:**
- [x] Detección automática de dispositivos de audio
- [x] Soporte para micrófonos mono y estéreo
- [x] Beamforming para arrays de micrófonos
- [x] Selección de dispositivo en configuración

**Archivos:** `ui/audio_devices.py`, `ui/audio_processor.py`, `ui/beamformer.py`

---

## TTS - Text to Speech

### US-014: Síntesis de voz local
**Como** usuario
**Quiero** que JARVIS hable usando síntesis local
**Para** escuchar respuestas sin depender de internet

**Criterios de aceptación:**
- [x] Motor espeak-ng funcionando
- [x] Voz en español
- [x] Velocidad ajustada (150 wpm)
- [x] Opción para desactivar TTS

**Archivos:** `ui/tts_engine.py`

---

### US-015: Interrupción de voz (Barge-in)
**Como** usuario
**Quiero** interrumpir a JARVIS mientras habla
**Para** corregir o dar un nuevo comando rápidamente

**Criterios de aceptación:**
- [x] Detecta wake word mientras TTS está activo
- [x] Detiene reproducción inmediatamente
- [x] Log "Interrumpido por usuario"
- [x] Procesa nuevo comando

**Archivos:** `ui/hud_gui.py`, `ui/tts_engine.py`

---

## Brain - Integración con IA

### US-016: Integración con Claude CLI
**Como** usuario
**Quiero** que JARVIS use Claude como cerebro
**Para** obtener respuestas inteligentes a mis preguntas

**Criterios de aceptación:**
- [x] Detecta Claude CLI en múltiples ubicaciones
- [x] Ejecuta comandos con `-p` (modo print)
- [x] Incluye system prompt con personalidad JARVIS
- [x] Timeout de 60 segundos
- [x] Manejo de errores

**Archivos:** `ui/jarvis_brain.py`

---

### US-017: Personalidad JARVIS
**Como** usuario
**Quiero** que JARVIS responda con personalidad de mayordomo británico
**Para** tener la experiencia auténtica de Iron Man

**Criterios de aceptación:**
- [x] System prompt con personalidad definida
- [x] Usa "señor" naturalmente
- [x] Tono elegante y profesional
- [x] Respuestas concisas

**Archivos:** `ui/jarvis_brain.py`

---

## Diagnóstico - Sistema de Verificación

### US-018: Pantalla de diagnóstico al inicio
**Como** usuario
**Quiero** ver el estado de todos los componentes al iniciar
**Para** saber si el sistema está funcionando correctamente

**Criterios de aceptación:**
- [x] Pantalla de diagnóstico antes de UI principal
- [x] Verifica: Modelo STT, Motor TTS, Claude CLI, Audio, Dependencias, Permisos
- [x] Indicadores visuales: [OK] verde, [!] amarillo, [X] rojo
- [x] Barra de progreso durante verificación
- [x] Mensaje final: "TODOS LOS SISTEMAS OPERATIVOS" o "SE DETECTARON PROBLEMAS"
- [x] Botón para continuar

**Archivos:** `ui/diagnostics.py`, `ui/components/diagnostics_screen.py`

---

### US-019: Logging detallado
**Como** desarrollador
**Quiero** logs detallados de cada módulo
**Para** depurar problemas y monitorear el sistema

**Criterios de aceptación:**
- [x] Logger centralizado en `logger_config.py`
- [x] Logs por módulo: UI, STT, TTS, BRAIN, AUDIO
- [x] Archivos en `~/.local/share/jarvis/logs/`
- [x] Rotación diaria de archivos
- [x] Salida coloreada en consola

**Archivos:** `ui/logger_config.py`

---

### US-020: Captura de pantalla desde código
**Como** desarrollador
**Quiero** capturar la pantalla sin depender de herramientas del SO
**Para** pruebas E2E multiplataforma

**Criterios de aceptación:**
- [x] Método `capture_screenshot()` usando PyQt5
- [x] Guarda en `tests/screenshots/`
- [x] Soporta señal SIGUSR1 para capturas externas
- [x] Modo `--test` para capturas automáticas

**Archivos:** `ui/hud_gui.py`

---

## Resumen de Implementación

| Categoría | Historias | Implementadas |
|-----------|-----------|---------------|
| Core | 2 | 2 |
| UI | 8 | 8 |
| STT | 3 | 3 |
| TTS | 2 | 2 |
| Brain | 2 | 2 |
| Diagnóstico | 3 | 3 |
| **Total** | **20** | **20** |

---

## Próximas Historias (Backlog)

### US-021: Memoria persistente
Guardar historial de conversaciones y preferencias del usuario.

### US-022: Comandos de sistema
Controlar volumen, abrir aplicaciones, ejecutar comandos.

### US-023: Integración con calendario
Recordatorios y eventos programados.

### US-024: Modo silencioso
Respuestas solo en pantalla sin TTS.

### US-025: Temas de color personalizables
Permitir al usuario elegir colores de la interfaz.
