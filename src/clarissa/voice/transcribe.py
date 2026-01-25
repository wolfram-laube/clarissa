"""
Speech-to-Text Module - Integrates with OpenAI Whisper API.

Features:
- OpenAI Whisper API integration with domain vocabulary
- Local Whisper support for air-gapped deployments
- Error handling (rate limits, timeouts, retries)
- Latency and cost tracking
- Async and sync interfaces

ADR-028 Reference: Section 2 - Speech-to-Text (STT/ASR)
Issue: #68 - Whisper API Integration
"""

import os
import io
import time
import logging
from typing import Optional, BinaryIO, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass


class RateLimitError(TranscriptionError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, retry_after: float = 60.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")


class TranscriptionTimeout(TranscriptionError):
    """Raised when transcription takes too long."""
    pass


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    text: str
    language: str = "en"
    confidence: float = 1.0
    duration_ms: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    model: str = "whisper-1"
    prompt_tokens: int = 0


@dataclass
class TranscriptionMetrics:
    """Metrics for transcription operations."""
    total_requests: int = 0
    total_audio_seconds: float = 0.0
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    errors: int = 0
    
    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


# Domain vocabulary for reservoir engineering
DOMAIN_VOCABULARY = """
Reservoir simulation terms: permeability, porosity, water saturation, 
oil saturation, gas saturation, pressure, BHP, bottomhole pressure, 
OOIP, original oil in place, OGIP, original gas in place,
waterflood, waterflooding, gasflood, EOR, enhanced oil recovery,
injector, injection well, producer, production well, 
PROD1, PROD2, INJ1, INJ2, INJ3, INJ4,
millidarcy, mD, psi, bar, bbl/day, barrels per day, m3/day,
STB, stock tank barrels, MSTB, thousand stock tank barrels,
FOPT, field oil production total, FOPR, field oil production rate,
FWPT, field water production total, FWPR, field water production rate, 
FWCT, field water cut, FGOR, field gas oil ratio,
WOPT, well oil production total, WOPR, well oil production rate,
layer, grid, cell, block, timestep, schedule, deck, ECLIPSE, OPM Flow,
PORO, PERMX, PERMY, PERMZ, NTG, net to gross,
aquifer, fault, region, PVTNUM, SATNUM, EQLNUM,
SPE, comparative solution project, benchmark model,
history match, forecast, sensitivity, uncertainty quantification
"""

# Cost per minute for Whisper API (as of 2024)
WHISPER_COST_PER_MINUTE = 0.006


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except RateLimitError as e:
                    last_error = e
                    delay = max(e.retry_after, base_delay * (2 ** attempt))
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                except TranscriptionTimeout as e:
                    last_error = e
                    logger.warning(f"Timeout, retrying (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(base_delay)
                except Exception as e:
                    last_error = e
                    logger.error(f"Transcription error: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(base_delay * (2 ** attempt))
            raise last_error
        return wrapper
    return decorator


class WhisperTranscriber:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Features:
    - Domain-specific vocabulary prompting
    - Automatic retry with backoff
    - Latency and cost tracking
    - Async interface
    
    Usage:
        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(audio_bytes)
        print(f"Text: {result.text}")
        print(f"Latency: {result.latency_ms}ms")
        print(f"Cost: ${result.cost_usd:.4f}")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "en",
        timeout_s: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.language = language
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.metrics = TranscriptionMetrics()
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. "
                "Set it as environment variable or pass to constructor."
            )
    
    @retry_with_backoff(max_retries=3)
    async def transcribe(
        self,
        audio_data: Union[bytes, BinaryIO],
        prompt: Optional[str] = None,
        filename: str = "audio.wav",
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text using Whisper API.
        
        Args:
            audio_data: Audio bytes or file-like object (WAV format preferred)
            prompt: Optional prompt to guide transcription (domain vocab added)
            filename: Filename hint for the API
        
        Returns:
            TranscriptionResult with text, metrics, and cost
        """
        import httpx
        
        start_time = time.time()
        
        # Prepare prompt with domain vocabulary
        effective_prompt = DOMAIN_VOCABULARY
        if prompt:
            effective_prompt = f"{prompt}\n\n{DOMAIN_VOCABULARY}"
        
        # Prepare audio data
        if isinstance(audio_data, bytes):
            audio_file = io.BytesIO(audio_data)
        else:
            audio_file = audio_data
        
        # Estimate audio duration from file size (rough: 16kHz, 16bit, mono)
        audio_file.seek(0, 2)  # Seek to end
        file_size = audio_file.tell()
        audio_file.seek(0)  # Reset to start
        
        # Rough estimate: 32000 bytes per second for 16kHz 16bit mono
        audio_duration_s = file_size / 32000
        
        try:
            # Make API request
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    files={
                        "file": (filename, audio_file, "audio/wav"),
                    },
                    data={
                        "model": self.model,
                        "language": self.language,
                        "prompt": effective_prompt,
                        "response_format": "json",
                    },
                )
            
            # Handle response
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", 60))
                self.metrics.errors += 1
                raise RateLimitError(retry_after)
            
            if response.status_code != 200:
                self.metrics.errors += 1
                raise TranscriptionError(
                    f"API error {response.status_code}: {response.text}"
                )
            
            result_json = response.json()
            text = result_json.get("text", "").strip()
            
        except httpx.TimeoutException:
            self.metrics.errors += 1
            raise TranscriptionTimeout(f"Transcription timed out after {self.timeout_s}s")
        
        # Calculate metrics
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        cost_usd = (audio_duration_s / 60) * WHISPER_COST_PER_MINUTE
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.total_audio_seconds += audio_duration_s
        self.metrics.total_cost_usd += cost_usd
        self.metrics.total_latency_ms += latency_ms
        
        logger.info(
            f"Transcription complete: {len(text)} chars, "
            f"{latency_ms}ms latency, ${cost_usd:.4f}"
        )
        
        return TranscriptionResult(
            text=text,
            language=self.language,
            confidence=1.0,  # Whisper doesn't return confidence
            duration_ms=int(audio_duration_s * 1000),
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            model=self.model,
        )
    
    def transcribe_sync(
        self,
        audio_data: Union[bytes, BinaryIO],
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """Synchronous wrapper for transcribe()."""
        return asyncio.run(self.transcribe(audio_data, prompt))
    
    def get_metrics(self) -> TranscriptionMetrics:
        """Get current transcription metrics."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.metrics = TranscriptionMetrics()


class LocalWhisperTranscriber:
    """
    Transcribe using local Whisper model (for air-gapped deployments).
    
    Uses faster-whisper for optimized inference.
    
    Requirements:
        pip install faster-whisper
        # GPU: pip install torch (with CUDA)
    
    Model sizes and approximate VRAM:
        - tiny: 39 MB, ~1 GB VRAM
        - base: 74 MB, ~1 GB VRAM  
        - small: 244 MB, ~2 GB VRAM
        - medium: 769 MB, ~5 GB VRAM (recommended for offline)
        - large-v3: 1.5 GB, ~10 GB VRAM
    """
    
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "auto",
        compute_type: str = "auto",
        download_root: Optional[str] = None,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self._model = None
        self.metrics = TranscriptionMetrics()
    
    def _load_model(self):
        """Lazy-load Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise ImportError(
                    "faster-whisper not installed. "
                    "Install with: pip install faster-whisper"
                )
            
            logger.info(f"Loading Whisper {self.model_size} model...")
            start = time.time()
            
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=self.download_root,
            )
            
            logger.info(f"Model loaded in {time.time() - start:.1f}s")
        
        return self._model
    
    async def transcribe(
        self,
        audio_path: str,
        language: str = "en",
        initial_prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio file using local Whisper model.
        
        Args:
            audio_path: Path to audio file
            language: Language code
            initial_prompt: Optional prompt for context
        
        Returns:
            TranscriptionResult
        """
        start_time = time.time()
        model = self._load_model()
        
        # Use domain vocabulary as initial prompt
        effective_prompt = initial_prompt or DOMAIN_VOCABULARY
        
        # Run transcription (in thread pool to not block)
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: model.transcribe(
                audio_path,
                language=language,
                initial_prompt=effective_prompt,
            )
        )
        
        # Collect text from segments
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
        
        text = " ".join(text_parts).strip()
        
        # Calculate metrics
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.total_latency_ms += latency_ms
        
        logger.info(
            f"Local transcription complete: {len(text)} chars, "
            f"{latency_ms}ms latency"
        )
        
        return TranscriptionResult(
            text=text,
            language=info.language,
            confidence=info.language_probability,
            latency_ms=latency_ms,
            cost_usd=0.0,  # Local is free
            model=f"whisper-{self.model_size}",
        )
    
    def transcribe_sync(
        self,
        audio_path: str,
        language: str = "en",
    ) -> TranscriptionResult:
        """Synchronous wrapper for transcribe()."""
        return asyncio.run(self.transcribe(audio_path, language))


class TranscriberFactory:
    """
    Factory for creating appropriate transcriber based on environment.
    
    Usage:
        transcriber = TranscriberFactory.create()
        result = await transcriber.transcribe(audio_data)
    """
    
    @staticmethod
    def create(
        prefer_local: bool = False,
        api_key: Optional[str] = None,
        local_model_size: str = "medium",
    ) -> Union[WhisperTranscriber, LocalWhisperTranscriber]:
        """
        Create appropriate transcriber.
        
        Args:
            prefer_local: Prefer local model even if API key available
            api_key: OpenAI API key (or from env)
            local_model_size: Size for local model if used
        
        Returns:
            WhisperTranscriber or LocalWhisperTranscriber
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if prefer_local or not api_key:
            logger.info("Using local Whisper model")
            return LocalWhisperTranscriber(model_size=local_model_size)
        
        logger.info("Using OpenAI Whisper API")
        return WhisperTranscriber(api_key=api_key)
