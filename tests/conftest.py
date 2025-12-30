"""
Pytest configuration and shared fixtures for JARVIS tests.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test configuration
TEST_SAMPLE_RATE = 16000
TEST_AUDIO_CHUNK = bytes([0] * 1024)


@pytest.fixture
def project_root():
    """Return project root path."""
    return PROJECT_ROOT


@pytest.fixture
def models_dir(project_root):
    """Return models directory path."""
    return project_root / "models"


@pytest.fixture
def config_path(project_root):
    """Return config file path."""
    return project_root / "config.yaml"


@pytest.fixture
def mock_audio_stream():
    """Mock audio input stream."""
    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    return mock_stream


@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing."""
    import numpy as np
    # Generate 1 second of silence at 16kHz
    return np.zeros(16000, dtype=np.int16)


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for CLI tests."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Test response from Claude",
            stderr=""
        )
        yield mock_run
