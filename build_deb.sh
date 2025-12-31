#!/bin/bash
# Script para construir el paquete .deb de JARVIS

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$PROJECT_DIR/packaging/deb"
VERSION="1.9.0"

echo "=== Construyendo JARVIS .deb v$VERSION ==="

# Limpiar build anterior
rm -rf "$PKG_DIR/usr/share/jarvis"
mkdir -p "$PKG_DIR/usr/share/jarvis/ui"
mkdir -p "$PKG_DIR/usr/share/jarvis/ui/components"
mkdir -p "$PKG_DIR/usr/share/jarvis/models"
mkdir -p "$PKG_DIR/usr/share/jarvis/docs"

# Copiar archivos de la aplicación
echo "Copiando archivos..."
cp "$PROJECT_DIR/jarvis_gui.py" "$PKG_DIR/usr/share/jarvis/"

# Copiar todos los módulos de ui
cp "$PROJECT_DIR/ui/hud_gui.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/hud_style.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/live_listener.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/jarvis_brain.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/config_dialog.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/tts_engine.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/audio_devices.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/audio_processor.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/vad_detector.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/beamformer.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/logger_config.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/diagnostics.py" "$PKG_DIR/usr/share/jarvis/ui/"
cp "$PROJECT_DIR/ui/__init__.py" "$PKG_DIR/usr/share/jarvis/ui/" 2>/dev/null || touch "$PKG_DIR/usr/share/jarvis/ui/__init__.py"

# Copiar componentes UI
echo "Copiando componentes UI..."
cp "$PROJECT_DIR/ui/components/__init__.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/theme.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/header.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/audio_bar.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/text_panels.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/controls.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/diagnostics_screen.py" "$PKG_DIR/usr/share/jarvis/ui/components/"
cp "$PROJECT_DIR/ui/components/main_screen.py" "$PKG_DIR/usr/share/jarvis/ui/components/"

# Copiar documentación
echo "Copiando documentación..."
cp "$PROJECT_DIR/docs/USER_STORIES.md" "$PKG_DIR/usr/share/jarvis/docs/" 2>/dev/null || true

# Copiar icono
echo "Copiando icono..."
mkdir -p "$PROJECT_DIR/assets"
cp "$PROJECT_DIR/assets/jarvis-icon.svg" \
   "$PKG_DIR/usr/share/icons/hicolor/scalable/apps/jarvis.svg" 2>/dev/null || echo "Icono no encontrado, usando existente"

# Establecer permisos
echo "Configurando permisos..."
chmod 755 "$PKG_DIR/DEBIAN/postinst"
chmod 755 "$PKG_DIR/DEBIAN/postrm"
chmod 755 "$PKG_DIR/usr/bin/jarvis-gui"
chmod 644 "$PKG_DIR/usr/share/applications/jarvis.desktop"

# Eliminar paquete anterior
rm -f "$PROJECT_DIR/jarvis-assistant_"*.deb

# Construir .deb
echo "Construyendo paquete..."
dpkg-deb --build "$PKG_DIR" "$PROJECT_DIR/jarvis-assistant_${VERSION}_amd64.deb"

echo ""
echo "=== Paquete creado: jarvis-assistant_${VERSION}_amd64.deb ==="
echo ""
echo "Para instalar:"
echo "  sudo dpkg -i jarvis-assistant_${VERSION}_amd64.deb"
echo "  sudo apt-get install -f"
