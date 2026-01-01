"""OPM Flow integration tests.

These tests require Docker and a built OPM Flow image.
Run with: pytest tests/integration/test_opm_flow.py -v

Skip in CI without Docker: pytest -m "not docker"
"""

import pytest
import subprocess
from pathlib import Path

# Mark all tests in this module as requiring Docker
pytestmark = pytest.mark.docker


def docker_available() -> bool:
    """Check if Docker daemon is running."""
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def opm_image_exists() -> bool:
    """Check if opm-flow:latest image is available."""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "opm-flow:latest"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return len(result.stdout.strip()) > 0
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture
def opm_adapter():
    """Create OPMFlowAdapter instance."""
    from clarissa.simulators.opm import OPMFlowAdapter
    return OPMFlowAdapter(timeout=300)


@pytest.fixture
def sample_deck(tmp_path) -> Path:
    """Create a minimal test deck."""
    # SPE1 is a standard test case - in real tests, download or include it
    deck_content = """-- Minimal test deck
RUNSPEC
TITLE
Test Case

DIMENS
10 10 3 /

OIL
WATER
GAS
DISGAS

METRIC

START
1 'JAN' 2020 /

WELLDIMS
2 10 2 2 /

TABDIMS
1 1 20 20 1 20 /

GRID
-- Minimal grid definition would go here

END
"""
    deck_file = tmp_path / "TEST.DATA"
    deck_file.write_text(deck_content)
    return deck_file


@pytest.mark.skipif(not docker_available(), reason="Docker not available")
@pytest.mark.skipif(not opm_image_exists(), reason="opm-flow:latest image not built")
class TestOPMFlowAdapter:
    """Integration tests for OPMFlowAdapter."""
    
    def test_adapter_creation(self, opm_adapter):
        """Adapter can be instantiated."""
        assert opm_adapter is not None
        assert "OPMFlow" in opm_adapter.name
    
    def test_docker_check(self, opm_adapter):
        """Adapter correctly detects Docker availability."""
        assert opm_adapter._docker_available() is True
    
    def test_missing_deck_raises_error(self, opm_adapter):
        """SimulatorError raised for missing deck file."""
        from clarissa.simulators import SimulatorError
        
        with pytest.raises(SimulatorError, match="not found"):
            opm_adapter.run("/nonexistent/path/to/deck.DATA")
    
    def test_run_returns_valid_result(self, opm_adapter, sample_deck):
        """run() returns contract-compliant result structure."""
        result = opm_adapter.run(str(sample_deck))
        
        assert isinstance(result, dict)
        assert "converged" in result
        assert "errors" in result
        assert isinstance(result["converged"], bool)
        assert isinstance(result["errors"], list)


@pytest.mark.skipif(not docker_available(), reason="Docker not available")
class TestOPMDockerSetup:
    """Tests for Docker infrastructure."""
    
    def test_dockerfile_exists(self):
        """Dockerfile is present in the opm module."""
        from clarissa.simulators import opm
        import importlib.resources as resources
        
        # Check that Dockerfile exists alongside the module
        opm_path = Path(opm.__file__).parent
        dockerfile = opm_path / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"
    
    def test_docker_compose_exists(self):
        """docker-compose.yml is present in the opm module."""
        from clarissa.simulators import opm
        
        opm_path = Path(opm.__file__).parent
        compose = opm_path / "docker-compose.yml"
        assert compose.exists(), f"docker-compose.yml not found at {compose}"
