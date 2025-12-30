 
claude

Desarrolla un asistente de voz JARVIS completo para Kubuntu, inspirado en el de Iron Man. Usa Claude CLI como cerebro y procesamiento de voz local.

IMPORTANTE: Este proyecto se desarrolla en FASES ITERATIVAS. Completa cada fase por completo, pruébala, y confirma conmigo antes de avanzar a la siguiente. No saltes fases.

---

## FASE 1: NÚCLEO BÁSICO (MVP)
Objetivo: Un asistente de voz funcional mínimo

### Entregables Fase 1:
- Wake word detection ("Jarvis") funcionando
- STT local transcribiendo voz a texto
- Integración básica con claude CLI (enviar texto, recibir respuesta)
- TTS local reproduciendo respuestas
- Capacidad de interrupción (barge-in)
- Comando "apágate" para cerrar

### Estructura inicial:
~/jarvis/
├── jarvis.py
├── config.yaml
├── modules/
│   ├── stt.py
│   ├── tts.py
│   └── cli_bridge.py
├── install_phase1.sh
└── README.md

### Criterios de aceptación Fase 1:
- Puedo decir "Jarvis", esperar respuesta, hacer pregunta, escuchar respuesta
- RAM en reposo < 250MB
- Puedo interrumpir mientras habla
- Latencia aceptable (< 3 segundos hasta inicio de respuesta)

DETENTE AL COMPLETAR FASE 1 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 2: PERSONALIDAD JARVIS
Objetivo: Que se sienta como el JARVIS real

### Entregables Fase 2:
- System prompt completo con personalidad JARVIS
- Tono británico elegante, humor sutil
- Usa "señor" naturalmente (no en cada frase)
- Frases icónicas: "A su servicio", "Me temo que...", "Si me permite sugerir..."
- Adapta saludos según hora del día
- Muestra preocupación por bienestar del usuario
- Ligeramente sarcástico ante ideas arriesgadas
- Conciso normalmente, detallado cuando amerita

### Archivo nuevo:
├── personality.py    # Gestión de personalidad y prompts

### Criterios de aceptación Fase 2:
- Conversación se siente natural y "jarvisesca"
- Diferentes respuestas según contexto
- Personalidad consistente

DETENTE AL COMPLETAR FASE 2 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 3: MEMORIA Y CONTEXTO
Objetivo: JARVIS recuerda y aprende

### Entregables Fase 3:
- Memoria persistente entre sesiones (SQLite o JSON)
- Recuerda nombre del usuario y preferencias
- Historial de conversaciones
- Contexto de conversación actual (multi-turno)
- Aprende información que el usuario comparte
- "Jarvis, recuerda que mi cliente principal es RSM"

### Estructura nueva:
├── memory/
│   ├── database.py
│   ├── preferences.json
│   └── history/

### Criterios de aceptación Fase 3:
- Reinicio el sistema y JARVIS recuerda info anterior
- Mantiene contexto en conversación larga
- Puedo pedirle que recuerde cosas específicas

DETENTE AL COMPLETAR FASE 3 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 4: MONITOREO DEL SISTEMA
Objetivo: JARVIS conoce el estado de la máquina

### Entregables Fase 4:
- Monitoreo de CPU, RAM, disco, temperatura
- Estado de conexión a internet
- Procesos activos y consumo
- Alertas proactivas si algo está fuera de rango
- Respuestas a: "¿Cómo está el sistema?", "¿Cuánta RAM libre tengo?"
- Notificación: "Señor, el CPU lleva 10 minutos al 95%"

### Módulo nuevo:
│   ├── system_monitor.py

### Criterios de aceptación Fase 4:
- Pregunto por el sistema y da información precisa
- Alerta proactivamente si hay problemas
- No consume recursos significativos el monitoreo

DETENTE AL COMPLETAR FASE 4 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 5: CONTROL BÁSICO DEL SISTEMA
Objetivo: JARVIS ejecuta acciones en el sistema

### Entregables Fase 5:
- Abrir aplicaciones por voz: "Jarvis, abre Firefox"
- Cerrar aplicaciones: "Cierra el reproductor"
- Control de volumen: "Sube el volumen", "Silencia"
- Control de brillo (si aplica)
- Ejecutar comandos de terminal cuando se solicite
- Confirmación antes de acciones destructivas
- Log de acciones ejecutadas

### Módulo nuevo:
│   ├── system_control.py

### Seguridad:
- Lista de comandos permitidos sin confirmación
- Lista de comandos que requieren confirmación
- Lista de comandos prohibidos
- "¿Está seguro, señor?" antes de eliminar archivos

### Criterios de aceptación Fase 5:
- Puedo abrir/cerrar apps por voz
- Control de volumen funciona
- Pide confirmación para acciones peligrosas
- Log registra todo

DETENTE AL COMPLETAR FASE 5 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 6: CONCIENCIA TEMPORAL Y PROACTIVIDAD
Objetivo: JARVIS anticipa y recuerda eventos

### Entregables Fase 6:
- Recordatorios: "Recuérdame en 30 minutos revisar el correo"
- Alertas temporales: "Señor, lleva 3 horas trabajando"
- Integración con calendario (local o Google Calendar)
- Aviso de próximas reuniones
- Sugerencias según hora: "Buenos días, señor. Hoy tiene 3 reuniones programadas"
- Notas de voz guardadas como archivos

### Módulo nuevo:
│   ├── calendar.py
│   ├── reminders.py

### Criterios de aceptación Fase 6:
- Recordatorios funcionan y suenan a la hora indicada
- Avisa de reuniones próximas
- Saludos adaptados a hora del día

DETENTE AL COMPLETAR FASE 6 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 7: MODO DESARROLLADOR
Objetivo: JARVIS ayuda con tareas de programación

### Entregables Fase 7:
- Comandos git por voz: "¿Qué cambios tengo sin commitear?"
- Estado de Docker containers: "¿Cómo están los contenedores?"
- Estado de servicios K8s (si aplica)
- "Ejecuta los tests del proyecto actual"
- "¿Qué errores hay en el log?"
- Lectura de archivos: "Lee el archivo config.yaml"

### Módulo nuevo:
│   ├── dev_tools.py

### Criterios de aceptación Fase 7:
- Comandos git funcionan por voz
- Estado de Docker/containers accesible
- Puede leer archivos y reportar contenido

DETENTE AL COMPLETAR FASE 7 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 8: VISIÓN - CAPTURA DE PANTALLA
Objetivo: JARVIS puede "ver" la pantalla cuando se necesite

### Entregables Fase 8:
- Captura de pantalla bajo demanda: "Jarvis, ¿qué hay en mi pantalla?"
- Análisis del contenido visible mediante Claude CLI (enviar imagen)
- "¿Qué aplicación tengo abierta?"
- "Lee el texto que está en pantalla"
- "¿Hay algún error visible?"
- Captura de región específica si es posible
- Las capturas son temporales, se eliminan después de analizar

### Módulo nuevo:
│   ├── screen_vision.py

### Consideraciones:
- Solo captura cuando el usuario lo solicita explícitamente
- Informar al usuario cuando se toma captura
- No almacenar capturas más de lo necesario
- Usar herramientas nativas de Kubuntu (spectacle, scrot, o similar)

### Criterios de aceptación Fase 8:
- "¿Qué hay en pantalla?" funciona y describe contenido
- Puede leer texto visible
- Capturas se eliminan después de usar
- Usuario sabe cuándo se captura

DETENTE AL COMPLETAR FASE 8 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 9: VISIÓN - CÁMARA WEB
Objetivo: JARVIS puede ver a través de la cámara

### Entregables Fase 9:
- Captura de cámara bajo demanda: "Jarvis, ¿qué ves?"
- Análisis visual mediante Claude CLI
- "¿Hay alguien detrás de mí?"
- "¿Cómo me veo?" (descripción general)
- "¿Qué objeto tengo en la mano?"
- Detección básica de presencia (opcional)
- Fotos temporales, se eliminan después de analizar

### Módulo nuevo:
│   ├── camera_vision.py

### Seguridad y privacidad:
- SOLO activa cámara con comando explícito del usuario
- Indicador visible/audible cuando cámara está activa
- "Señor, activando cámara" antes de capturar
- Nunca graba video, solo fotos puntuales
- Fotos se eliminan inmediatamente después del análisis

### Criterios de aceptación Fase 9:
- Puede describir lo que ve la cámara
- Usuario siempre sabe cuando cámara está activa
- Fotos no persisten

DETENTE AL COMPLETAR FASE 9 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 10: CONTROL DE MOUSE Y TECLADO
Objetivo: JARVIS puede operar el computador

### Entregables Fase 10:
- Mover mouse a posición: "Mueve el mouse arriba a la derecha"
- Clicks: "Haz click", "Click derecho", "Doble click"
- Escribir texto: "Escribe: Hola mundo"
- Atajos de teclado: "Presiona Control Alt T"
- Scroll: "Baja la página", "Sube"
- Combinación con visión: "Haz click en el botón que dice Guardar"

### Módulo nuevo:
│   ├── input_control.py

### Modos de operación:
1. Modo guiado: Usuario da instrucciones paso a paso
2. Modo asistido: JARVIS sugiere acciones basadas en visión
3. Modo autónomo: JARVIS ejecuta secuencia completa (con confirmación)

### Seguridad CRÍTICA:
- Confirmación verbal antes de cualquier acción de input
- "Voy a hacer click en [ubicación], ¿procedo señor?"
- Palabra de seguridad para detener todo: "Alto" o "Para"
- Límite de acciones por secuencia
- Log detallado de toda acción de input
- Modo de solo demostración (muestra qué haría sin hacerlo)

### Criterios de aceptación Fase 10:
- Puede mover mouse y hacer clicks por voz
- Puede escribir texto dictado
- Confirmaciones funcionan
- "Alto" detiene cualquier acción inmediatamente
- Log completo de acciones

DETENTE AL COMPLETAR FASE 10 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 11: AUTOMATIZACIÓN VISUAL INTELIGENTE
Objetivo: Combinar visión + control para tareas complejas

### Entregables Fase 11:
- Tareas compuestas: "Jarvis, abre Chrome y busca el clima en Bogotá"
- Navegación visual: "Busca el botón de descargar y haz click"
- Llenado de formularios simples por voz
- Captura pantalla → Analiza → Decide acción → Ejecuta → Verifica
- Recuperación de errores: Si algo falla, intenta alternativa

### Módulo nuevo:
│   ├── visual_automation.py

### Flujo de automatización:
1. Usuario da tarea
2. JARVIS captura pantalla
3. Analiza estado actual
4. Planifica pasos necesarios
5. Pide confirmación del plan
6. Ejecuta paso a paso
7. Verifica resultado de cada paso
8. Reporta resultado final

### Criterios de aceptación Fase 11:
- Puede completar tareas de múltiples pasos
- Verifica cada paso antes de continuar
- Se recupera de errores simples
- Usuario puede cancelar en cualquier momento

DETENTE AL COMPLETAR FASE 11 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 12: INTERFAZ VISUAL Y SONIDOS
Objetivo: Feedback visual y auditivo estilo Stark Industries

### Entregables Fase 12:
- Sonidos de confirmación elegantes (beeps sutiles)
- Sonidos diferentes para: escuchando, procesando, completado, error
- Widget minimalista opcional mostrando:
  - Estado actual (reposo/escuchando/procesando)
  - Últimos comandos
  - Estado del sistema resumido
- Indicador visual de wake word detectado
- Animación sutil cuando habla

### Estructura nueva:
├── sounds/
│   ├── listening.wav
│   ├── processing.wav
│   ├── complete.wav
│   ├── error.wav
│   └── startup.wav
├── ui/
│   ├── widget.py

### Criterios de aceptación Fase 12:
- Sonidos funcionan y son agradables
- Widget muestra estado correctamente
- Se puede desactivar widget si se prefiere solo voz

DETENTE AL COMPLETAR FASE 12 Y ESPERA MI CONFIRMACIÓN.

---

## FASE 13: PULIDO Y OPTIMIZACIÓN FINAL
Objetivo: Experiencia refinada y estable

### Entregables Fase 13:
- Optimización de RAM y CPU
- Manejo robusto de errores en todos los módulos
- Documentación completa
- Script de instalación unificado
- Servicio systemd para inicio automático
- Configuración de niveles de logging
- Backup y restauración de memoria/preferencias
- Tests básicos de cada módulo

### Estructura final:
~/jarvis/
├── jarvis.py
├── config.yaml
├── personality.py
├── requirements.txt
├── modules/
│   ├── stt.py
│   ├── tts.py
│   ├── cli_bridge.py
│   ├── system_monitor.py
│   ├── system_control.py
│   ├── calendar.py
│   ├── reminders.py
│   ├── dev_tools.py
│   ├── screen_vision.py
│   ├── camera_vision.py
│   ├── input_control.py
│   └── visual_automation.py
├── memory/
├── sounds/
├── ui/
├── logs/
├── tests/
├── install.sh
├── jarvis.service
└── README.md

---

## REQUISITOS TÉCNICOS GLOBALES (todas las fases)

- RAM máxima: 250MB en reposo
- Python 3
- Compatible Kubuntu 24.04
- STT y TTS 100% local (no nube)
- Modular y extensible
- Logs para debugging
- Configuración externalizada

---

## COMANDOS DE SEGURIDAD GLOBALES

Estos funcionan en cualquier fase desde la 5:
- "Alto" / "Para" → Detiene cualquier acción inmediatamente
- "Cancela" → Cancela operación en progreso
- "Modo seguro" → Desactiva control de input/visión
- "Apágate" → Cierra JARVIS limpiamente

---

COMIENZA CON LA FASE 1. Investiga las mejores herramientas actuales para STT y TTS local en Linux, diseña la arquitectura del MVP, e implementa. Cuando termines, muéstrame cómo probar y espera mi confirmación para continuar.
