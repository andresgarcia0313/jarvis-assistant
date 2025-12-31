"""
Tests E2E para el módulo Beamformer.
Prueba Delay-and-Sum beamforming para 2 micrófonos.
"""

import pytest
import numpy as np
import sys
sys.path.insert(0, '/home/andres/Desarrollo/IA/Jarvis')

from ui.beamformer import Beamformer


class TestBeamformerInit:
    """Tests de inicialización del Beamformer."""

    def test_init_default(self):
        """Test inicialización con valores por defecto."""
        bf = Beamformer()
        assert bf.sample_rate == 16000
        assert bf.mic_distance == 0.1
        assert bf.direction_angle == 0.0
        assert not bf.is_enabled()

    def test_init_custom(self):
        """Test inicialización con valores personalizados."""
        bf = Beamformer(sample_rate=48000, mic_distance=0.15, direction_angle=30.0)
        assert bf.sample_rate == 48000
        assert bf.mic_distance == 0.15
        assert bf.direction_angle == 30.0


class TestBeamformerDelay:
    """Tests de cálculo de delay."""

    def test_delay_center(self):
        """Test delay con ángulo 0 (frente)."""
        bf = Beamformer(direction_angle=0.0)
        # Con ángulo 0, sin(0) = 0, delay debe ser 0
        assert bf._delay_samples == 0

    def test_delay_left(self):
        """Test delay con ángulo negativo (izquierda)."""
        bf = Beamformer(direction_angle=-45.0, mic_distance=0.1)
        # Con ángulo -45, debe haber delay positivo
        assert bf._delay_samples > 0

    def test_delay_right(self):
        """Test delay con ángulo positivo (derecha)."""
        bf = Beamformer(direction_angle=45.0, mic_distance=0.1)
        # Con ángulo 45, debe haber delay positivo
        assert bf._delay_samples > 0


class TestBeamformerProcess:
    """Tests de procesamiento de audio."""

    def test_process_mono_passthrough(self):
        """Test que audio mono pasa sin cambios."""
        bf = Beamformer()
        mono = np.random.randint(-1000, 1000, size=1000, dtype=np.int16)
        result = bf.process(mono)
        np.testing.assert_array_equal(result, mono)

    def test_process_stereo_to_mono(self):
        """Test conversión estéreo a mono."""
        bf = Beamformer(direction_angle=0.0)
        bf.enable(True)

        # Audio estéreo sintético
        stereo = np.random.randint(-1000, 1000, size=(1000, 2), dtype=np.int16)
        result = bf.process(stereo)

        # Resultado debe ser mono
        assert len(result.shape) == 1
        assert result.shape[0] == stereo.shape[0]

    def test_process_stereo_identical_channels(self):
        """Test con canales idénticos produce promedio."""
        bf = Beamformer(direction_angle=0.0)
        bf.enable(True)

        # Crear audio estéreo con canales idénticos
        mono_data = np.array([100, 200, 300, 400, 500], dtype=np.int16)
        stereo = np.column_stack([mono_data, mono_data])

        result = bf.process(stereo)

        # El resultado debe ser aproximadamente igual a cada canal
        np.testing.assert_array_almost_equal(result, mono_data, decimal=0)

    def test_process_enhances_target_direction(self):
        """Test que el beamforming mejora la señal desde la dirección objetivo."""
        bf = Beamformer(direction_angle=0.0, mic_distance=0.1)
        bf.enable(True)

        # Crear señal sintética (onda sinusoidal)
        t = np.linspace(0, 0.1, 1600)  # 100ms a 16kHz
        freq = 1000  # 1kHz
        signal = (np.sin(2 * np.pi * freq * t) * 10000).astype(np.int16)

        # Canales idénticos (señal desde el frente)
        stereo = np.column_stack([signal, signal])
        result = bf.process(stereo)

        # La potencia del resultado debe ser similar a la original
        power_in = np.mean(signal.astype(np.float32) ** 2)
        power_out = np.mean(result.astype(np.float32) ** 2)

        # La relación de potencias debe ser cercana a 1
        ratio = power_out / power_in
        assert 0.8 < ratio < 1.2


class TestBeamformerDirection:
    """Tests de cambio de dirección."""

    def test_set_direction_valid(self):
        """Test cambio de dirección válido."""
        bf = Beamformer()
        bf.set_direction(45.0)
        assert bf.direction_angle == 45.0

    def test_set_direction_clamp_max(self):
        """Test límite máximo de dirección."""
        bf = Beamformer()
        bf.set_direction(120.0)
        assert bf.direction_angle == 90.0

    def test_set_direction_clamp_min(self):
        """Test límite mínimo de dirección."""
        bf = Beamformer()
        bf.set_direction(-120.0)
        assert bf.direction_angle == -90.0


class TestBeamformerMicDistance:
    """Tests de distancia entre micrófonos."""

    def test_set_mic_distance_valid(self):
        """Test cambio de distancia válido."""
        bf = Beamformer()
        bf.set_mic_distance(0.15)
        assert bf.mic_distance == 0.15

    def test_set_mic_distance_clamp_min(self):
        """Test límite mínimo de distancia."""
        bf = Beamformer()
        bf.set_mic_distance(0.001)
        assert bf.mic_distance == 0.01

    def test_set_mic_distance_clamp_max(self):
        """Test límite máximo de distancia."""
        bf = Beamformer()
        bf.set_mic_distance(2.0)
        assert bf.mic_distance == 1.0


class TestBeamformerEstimateDirection:
    """Tests de estimación de dirección."""

    def test_estimate_direction_mono_returns_zero(self):
        """Test que audio mono retorna 0."""
        bf = Beamformer()
        mono = np.random.randint(-1000, 1000, size=1000, dtype=np.int16)
        result = bf.estimate_direction(mono)
        assert result == 0.0

    def test_estimate_direction_centered_signal(self):
        """Test estimación con señal centrada (canales idénticos)."""
        bf = Beamformer()

        # Señal idéntica en ambos canales = fuente al frente
        signal = np.sin(np.linspace(0, 10, 1000)) * 10000
        signal = signal.astype(np.int16)
        stereo = np.column_stack([signal, signal])

        angle = bf.estimate_direction(stereo)
        # La señal centrada debe dar un ángulo cercano a 0
        assert abs(angle) < 10.0


class TestBeamformerSeparateChannels:
    """Tests de procesamiento con canales separados."""

    def test_process_separate_channels(self):
        """Test procesamiento con canales separados."""
        bf = Beamformer(direction_angle=0.0)

        left = np.random.randint(-1000, 1000, size=1000, dtype=np.int16)
        right = np.random.randint(-1000, 1000, size=1000, dtype=np.int16)

        result = bf.process_separate_channels(left, right)

        # Resultado debe ser mono
        assert len(result.shape) == 1
        assert result.shape[0] == 1000


class TestBeamformerState:
    """Tests de estado del beamformer."""

    def test_enable_disable(self):
        """Test habilitar/deshabilitar."""
        bf = Beamformer()
        assert not bf.is_enabled()

        bf.enable(True)
        assert bf.is_enabled()

        bf.enable(False)
        assert not bf.is_enabled()

    def test_get_info(self):
        """Test obtener información."""
        bf = Beamformer(mic_distance=0.12, direction_angle=30.0)
        bf.enable(True)

        info = bf.get_info()

        assert info["enabled"] == True
        assert info["mic_distance_cm"] == 12.0
        assert info["direction_angle"] == 30.0
        assert "delay_samples" in info


class TestBeamformerIntegration:
    """Tests de integración con LiveListener."""

    def test_beamformer_import(self):
        """Test que el módulo se importa correctamente."""
        from ui.beamformer import Beamformer
        assert Beamformer is not None

    def test_live_listener_has_beamformer(self):
        """Test que LiveListener tiene beamformer integrado."""
        # Este test verifica la integración pero no requiere hardware
        try:
            from ui.live_listener import LiveListener

            # Verificar que LiveListener tiene los métodos de beamforming
            assert hasattr(LiveListener, 'set_beamforming')
            assert hasattr(LiveListener, 'set_beamformer_direction')
            assert hasattr(LiveListener, 'is_beamforming_available')
            assert hasattr(LiveListener, 'is_beamforming_enabled')
            assert hasattr(LiveListener, 'get_beamformer_info')
        except ImportError as e:
            # Si sounddevice no está disponible, verificar al menos el código fuente
            pytest.skip(f"Dependencia no disponible: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
