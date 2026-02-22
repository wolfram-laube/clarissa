"""
Tests for CLARISSA Whisper Transcription Module

Issue: #68 - Whisper API Integration
"""

import pytest
import io
import os
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from clarissa.voice.transcribe import (
    WhisperTranscriber,
    LocalWhisperTranscriber,
    TranscriberFactory,
    TranscriptionResult,
    TranscriptionMetrics,
    TranscriptionError,
    RateLimitError,
    TranscriptionTimeout,
    DOMAIN_VOCABULARY,
    WHISPER_COST_PER_MINUTE,
)


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_default_values(self):
        result = TranscriptionResult(text="Hello world")
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.confidence == 1.0
        assert result.cost_usd == 0.0

    def test_all_fields(self):
        result = TranscriptionResult(
            text="Test",
            language="de",
            confidence=0.95,
            duration_ms=5000,
            latency_ms=1500,
            cost_usd=0.0005,
            model="whisper-1",
        )
        assert result.duration_ms == 5000
        assert result.latency_ms == 1500


class TestTranscriptionMetrics:
    """Tests for TranscriptionMetrics."""

    def test_initial_values(self):
        metrics = TranscriptionMetrics()
        assert metrics.total_requests == 0
        assert metrics.total_cost_usd == 0.0

    def test_avg_latency(self):
        metrics = TranscriptionMetrics(
            total_requests=10,
            total_latency_ms=15000
        )
        assert metrics.avg_latency_ms == 1500.0

    def test_avg_latency_zero_requests(self):
        metrics = TranscriptionMetrics()
        assert metrics.avg_latency_ms == 0.0


class TestWhisperTranscriber:
    """Tests for WhisperTranscriber."""

    def test_init_with_api_key(self):
        transcriber = WhisperTranscriber(api_key="test-key")
        assert transcriber.api_key == "test-key"
        assert transcriber.model == "whisper-1"

    def test_init_from_env(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            transcriber = WhisperTranscriber()
            assert transcriber.api_key == "env-key"

    def test_init_no_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY if present
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
                WhisperTranscriber()

    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        """Test successful transcription with mocked API."""
        transcriber = WhisperTranscriber(api_key="test-key")
        
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "Hello, this is a test."}
        
        # Create fake audio data (WAV-like header + silence)
        audio_data = b'RIFF' + b'\x00' * 44 + b'\x00' * 32000  # ~1 second
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            result = await transcriber.transcribe(audio_data)
        
        assert result.text == "Hello, this is a test."
        assert result.latency_ms >= 0
        assert transcriber.metrics.total_requests == 1

    @pytest.mark.asyncio
    async def test_transcribe_rate_limit(self):
        """Test rate limit handling."""
        transcriber = WhisperTranscriber(api_key="test-key")
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}
        
        audio_data = b'RIFF' + b'\x00' * 1000
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            with pytest.raises(RateLimitError) as exc_info:
                # Disable retry for this test
                transcriber.max_retries = 0
                await transcriber.transcribe.__wrapped__(transcriber, audio_data)
        
        assert exc_info.value.retry_after == 30.0

    def test_metrics_tracking(self):
        transcriber = WhisperTranscriber(api_key="test-key")
        
        # Manually update metrics to test
        transcriber.metrics.total_requests = 5
        transcriber.metrics.total_cost_usd = 0.03
        transcriber.metrics.total_latency_ms = 7500
        
        metrics = transcriber.get_metrics()
        assert metrics.total_requests == 5
        assert metrics.avg_latency_ms == 1500.0

    def test_reset_metrics(self):
        transcriber = WhisperTranscriber(api_key="test-key")
        transcriber.metrics.total_requests = 10
        
        transcriber.reset_metrics()
        
        assert transcriber.metrics.total_requests == 0


class TestLocalWhisperTranscriber:
    """Tests for LocalWhisperTranscriber."""

    def test_init(self):
        transcriber = LocalWhisperTranscriber(model_size="small")
        assert transcriber.model_size == "small"
        assert transcriber._model is None

    def test_model_lazy_loading(self):
        """Test that model is not loaded until needed."""
        transcriber = LocalWhisperTranscriber()
        assert transcriber._model is None

    @pytest.mark.asyncio
    async def test_transcribe_without_faster_whisper(self):
        """Test graceful error when faster-whisper not installed."""
        transcriber = LocalWhisperTranscriber()
        
        with patch.dict('sys.modules', {'faster_whisper': None}):
            # This should raise ImportError
            with pytest.raises(ImportError, match="faster-whisper not installed"):
                transcriber._load_model()


class TestTranscriberFactory:
    """Tests for TranscriberFactory."""

    def test_create_with_api_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            transcriber = TranscriberFactory.create()
            assert isinstance(transcriber, WhisperTranscriber)

    def test_create_prefer_local(self):
        transcriber = TranscriberFactory.create(prefer_local=True)
        assert isinstance(transcriber, LocalWhisperTranscriber)

    def test_create_no_key_uses_local(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            transcriber = TranscriberFactory.create()
            assert isinstance(transcriber, LocalWhisperTranscriber)


class TestDomainVocabulary:
    """Tests for domain vocabulary."""

    def test_vocabulary_contains_key_terms(self):
        key_terms = [
            "permeability",
            "porosity",
            "BHP",
            "OOIP",
            "waterflood",
            "FOPR",
            "FWCT",
            "millidarcy",
            "ECLIPSE",
            "OPM Flow",
        ]
        for term in key_terms:
            assert term in DOMAIN_VOCABULARY, f"Missing term: {term}"

    def test_vocabulary_is_not_empty(self):
        assert len(DOMAIN_VOCABULARY) > 100


class TestCostCalculation:
    """Tests for cost calculation."""

    def test_cost_per_minute(self):
        # Current rate is $0.006/minute
        assert WHISPER_COST_PER_MINUTE == 0.006

    def test_cost_calculation_one_minute(self):
        # 1 minute should cost $0.006
        duration_s = 60
        cost = (duration_s / 60) * WHISPER_COST_PER_MINUTE
        assert cost == pytest.approx(0.006)

    def test_cost_calculation_30_seconds(self):
        # 30 seconds should cost $0.003
        duration_s = 30
        cost = (duration_s / 60) * WHISPER_COST_PER_MINUTE
        assert cost == pytest.approx(0.003)


class TestIntegration:
    """Integration tests (require API key or skip)."""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_transcription(self):
        """Test with real API (requires key)."""
        # Create a simple test audio (silence)
        # In real tests, use actual audio file
        import wave
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            # 1 second of silence
            wav.writeframes(b'\x00' * 32000)
        
        buffer.seek(0)
        
        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(buffer.read())
        
        assert isinstance(result.text, str)
        assert result.latency_ms >= 0
        assert result.cost_usd > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
