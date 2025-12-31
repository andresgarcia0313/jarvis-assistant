# JARVIS - Roadmap de Mejoras

Mejoras priorizadas para perfil de Ingeniero de Sistemas / Gestión de Proyectos.

---

## Fase 14: Integración Web y Productividad
**Objetivo:** JARVIS conectado con el mundo exterior para trabajo diario.

### Entregables
- [ ] Consultas de clima, noticias, tráfico
- [ ] Lectura de emails (IMAP) con resumen
- [ ] Envío de emails por voz
- [ ] Integración Telegram/WhatsApp (notificaciones)
- [ ] Búsquedas web con respuesta hablada
- [ ] "Jarvis, ¿cómo está el tráfico hacia la oficina?"
- [ ] "Lee mis correos no leídos"

### Módulos
```
modules/
├── web_services.py      # Clima, noticias, tráfico
├── email_handler.py     # IMAP/SMTP
└── messaging.py         # Telegram bot
```

### Criterios de Aceptación
- Consulta clima/tráfico funciona
- Lee resumen de emails no leídos
- Puede enviar email dictado
- Notificaciones de Telegram llegan a JARVIS

---

## Fase 15: Proactividad Inteligente
**Objetivo:** JARVIS anticipa necesidades sin que se le pida.

### Entregables
- [ ] Análisis de patrones de uso (horas de trabajo, breaks)
- [ ] Sugerencias basadas en calendario
- [ ] Alertas contextuales ("Debería salir en 15 min para su reunión")
- [ ] Recordatorios de bienestar ("Lleva 3 horas sin descanso")
- [ ] Resumen matutino automático al detectar actividad
- [ ] Detección de contexto (hora, día, apps abiertas)

### Módulos
```
modules/
├── proactive_engine.py  # Motor de sugerencias
├── pattern_analyzer.py  # Análisis de patrones
└── context_awareness.py # Detección de contexto
```

### Criterios de Aceptación
- Resumen matutino automático al iniciar día
- Sugiere breaks después de trabajo prolongado
- Avisa de reuniones con tiempo suficiente
- No interrumpe en momentos inapropiados

---

## Fase 16: Voz Natural (XTTS/StyleTTS2)
**Objetivo:** Voz expresiva y natural, no robótica.

### Entregables
- [ ] Reemplazar Piper con Coqui XTTS o StyleTTS2
- [ ] Clonación de voz estilo Paul Bettany (opcional)
- [ ] Prosodia natural según contexto emocional
- [ ] Énfasis en palabras importantes
- [ ] Velocidad adaptativa según contenido

### Módulos
```
modules/
└── tts_advanced.py      # Wrapper para XTTS/StyleTTS2
models/
└── voice_model/         # Modelo de voz personalizado
```

### Criterios de Aceptación
- Voz claramente más natural que Piper
- Latencia aceptable (< 2s para iniciar)
- Expresividad según contexto (urgencia, calma, humor)

---

## Fase 17: Home Assistant / Domótica
**Objetivo:** Control del entorno físico por voz.

### Entregables
- [ ] Integración con Home Assistant API
- [ ] Control de luces (encender, apagar, atenuar, colores)
- [ ] Control de clima (temperatura, modo)
- [ ] Control de persianas/cortinas
- [ ] Escenas predefinidas ("Modo trabajo", "Modo cine")
- [ ] Estado de dispositivos IoT
- [ ] "Jarvis, enciende las luces del estudio"

### Módulos
```
modules/
└── home_assistant.py    # Integración HA API
config.yaml:
  home_assistant:
    url: "http://homeassistant.local:8123"
    token: "..."
```

### Criterios de Aceptación
- Controla luces por voz
- Controla clima por voz
- Ejecuta escenas predefinidas
- Reporta estado de dispositivos

---

## Fase 18: Contexto Conversacional Profundo
**Objetivo:** Memoria de largo plazo y referencias complejas.

### Entregables
- [ ] Embedding de conversaciones históricas (vector DB)
- [ ] Búsqueda semántica en historial
- [ ] Referencias a conversaciones pasadas ("lo que hablamos ayer")
- [ ] Contexto multi-tema simultáneo
- [ ] Resumen de proyectos/temas recurrentes
- [ ] "¿Qué decidimos sobre el proyecto X?"

### Módulos
```
modules/
├── semantic_memory.py   # Vector embeddings
└── conversation_search.py
memory/
└── vectors.db           # ChromaDB o similar
```

### Criterios de Aceptación
- Encuentra conversaciones por tema
- Entiende referencias temporales ("la semana pasada")
- Mantiene contexto de múltiples hilos

---

## Fase 19: Multi-Room / Multi-Dispositivo
**Objetivo:** JARVIS omnipresente en el hogar/oficina.

### Entregables
- [ ] Arquitectura cliente-servidor
- [ ] Servidor central con el cerebro
- [ ] Clientes ligeros (Raspberry Pi) en cada habitación
- [ ] Detección de habitación activa
- [ ] Respuesta desde altavoz más cercano
- [ ] Sincronización de estado entre clientes

### Arquitectura
```
jarvis-server/           # Servidor central
├── server.py
└── api/

jarvis-client/           # Cliente ligero
├── client.py
├── wake_word.py
└── audio_stream.py
```

### Criterios de Aceptación
- Funciona desde múltiples habitaciones
- Responde desde el dispositivo correcto
- Estado sincronizado entre clientes

---

## Fase 20: Video en Tiempo Real
**Objetivo:** Visión continua, no solo capturas puntuales.

### Entregables
- [ ] Streaming de cámara con análisis
- [ ] Detección de presencia/movimiento
- [ ] Reconocimiento facial básico (familia)
- [ ] Alertas de seguridad ("Alguien en la puerta")
- [ ] Tracking de objetos
- [ ] "Jarvis, vigila la entrada"

### Módulos
```
modules/
├── video_stream.py      # Streaming + análisis
├── motion_detection.py
└── face_recognition.py
```

### Criterios de Aceptación
- Detecta movimiento y alerta
- Reconoce personas conocidas
- No consume recursos excesivos en reposo

---

## Fase 21: Interfaz HUD Avanzada
**Objetivo:** Dashboard visual estilo Stark Industries.

### Entregables
- [ ] Dashboard fullscreen opcional
- [ ] Visualización de estado del sistema
- [ ] Timeline de actividad
- [ ] Animación de ondas al hablar
- [ ] Widgets configurables
- [ ] Modo transparente/overlay

### Módulos
```
ui/
├── hud_dashboard.py     # Dashboard principal
├── visualizations.py    # Gráficos y animaciones
└── themes/
    └── stark.qss        # Tema Stark Industries
```

### Criterios de Aceptación
- Dashboard funcional y atractivo
- Animaciones fluidas
- Configurable (widgets, posición)

---

## Fase 22: Seguridad por Voz
**Objetivo:** Solo usuarios autorizados pueden dar comandos.

### Entregables
- [ ] Huella vocal del usuario principal
- [ ] Verificación de speaker antes de comandos sensibles
- [ ] Usuarios con diferentes niveles de acceso
- [ ] Log de intentos no autorizados
- [ ] "Jarvis, registra la voz de [nombre]"

### Módulos
```
modules/
├── voice_auth.py        # Autenticación por voz
└── access_control.py    # Niveles de acceso
```

### Criterios de Aceptación
- Distingue voces de diferentes personas
- Bloquea comandos sensibles de desconocidos
- Registra intentos fallidos

---

## Matriz de Prioridad

| Fase | Nombre | Valor Productividad | Complejidad | Prioridad |
|------|--------|---------------------|-------------|-----------|
| 14 | Integración Web | ★★★★★ | ★★☆☆☆ | **P0** |
| 15 | Proactividad | ★★★★★ | ★★★☆☆ | **P0** |
| 16 | Voz Natural | ★★★★☆ | ★★★☆☆ | **P1** |
| 17 | Home Assistant | ★★★☆☆ | ★★☆☆☆ | **P1** |
| 18 | Contexto Profundo | ★★★★☆ | ★★★★☆ | **P2** |
| 19 | Multi-Room | ★★★☆☆ | ★★★★☆ | **P2** |
| 20 | Video Real-time | ★★☆☆☆ | ★★★★☆ | **P3** |
| 21 | HUD Avanzado | ★★☆☆☆ | ★★★☆☆ | **P3** |
| 22 | Seguridad Voz | ★★☆☆☆ | ★★★★★ | **P3** |

---

## Progreso

- [x] Fase 1-13: Core completo
- [x] Refactor UI: Arquitectura Vue-style (componentes autocontenidos)
- [x] Repositorios: GitHub + Gitea
- [ ] Fase 14: Integración Web
- [ ] Fase 15: Proactividad
- [ ] Fase 16: Voz Natural
- [ ] Fase 17: Home Assistant
- [ ] Fase 18: Contexto Profundo
- [ ] Fase 19: Multi-Room
- [ ] Fase 20: Video Real-time
- [ ] Fase 21: HUD Avanzado
- [ ] Fase 22: Seguridad Voz

---

## Notas de Implementación

### Arquitectura UI Vue-style (2025-12-31)

Componentes en `ui/components/`:
- `theme.py` - Constantes de color compartidas
- `header.py` - Título + botones CONFIG/STANDBY
- `audio_bar.py` - Barra de nivel de audio
- `text_panels.py` - VoiceInput, AIResponse, SystemLog
- `controls.py` - Botones ACTIVATE/CLEAR
- `diagnostics_screen.py` - Pantalla de diagnósticos
- `main_screen.py` - Composición de todos los componentes

Cada componente:
- Es autocontenido con estilos inline
- Tiene bloque `if __name__ == "__main__":` para testing
- Sigue principio de mínimo código necesario

---

*Última actualización: 2025-12-31*
