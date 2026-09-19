import io
import wave

from app.ai.worker.client import WorkerClient, WorkerClientProtocol, get_worker_client
from app.ai.worker.mock import MockWorkerClient, silence_wav
from app.core.config import Settings


def test_mock_conforms_to_protocol() -> None:
    assert isinstance(MockWorkerClient(), WorkerClientProtocol)
    assert MockWorkerClient.mode == "mock"


async def test_mock_stt() -> None:
    result = await MockWorkerClient().stt(b"RIFF", lang="uz", initial_prompt="salom")
    assert result.text == "salom"
    assert result.confidence == 0.9
    assert len(result.segments) == 1 and result.segments[0].text == "salom"
    assert result.latency_ms >= 0
    assert result.provider == "worker_mock"


async def test_mock_tts_is_one_second_silence() -> None:
    result = await MockWorkerClient().tts("Salom, Bobur aka!")
    audio = result.audio_wav
    assert audio.startswith(b"RIFF") and audio[8:12] == b"WAVE"
    assert len(audio) == 44 + 16_000 * 2  # header + 1 s of 16 kHz mono 16-bit
    with wave.open(io.BytesIO(audio)) as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 16_000)
        assert wav.getnframes() == 16_000
        assert wav.readframes(16_000) == b"\x00" * 32_000


def test_silence_wav_length_scales() -> None:
    assert len(silence_wav(seconds=0.5)) == 44 + 8_000 * 2


async def test_mock_voice_emotion_neutral() -> None:
    result = await MockWorkerClient().voice_emotion(b"RIFF")
    assert result.label == "neutral"
    assert (result.valence, result.arousal, result.dominance) == (0.0, 0.0, 0.0)
    assert result.scores["neutral"] == 1.0


async def test_mock_health_models() -> None:
    health = await MockWorkerClient().health()
    assert set(health.models) >= {"stt", "tts", "voice_emotion"}
    assert set(health.models.values()) == {"mock"}
    assert health.gpu is None


async def test_worker_client_sets_required_headers() -> None:
    client = WorkerClient(base_url="https://x.ngrok-free.app/", key="secret-key", timeout_s=4)
    try:
        assert client.headers["X-Worker-Key"] == "secret-key"
        assert client.headers["ngrok-skip-browser-warning"] == "1"
        assert client.base_url == "https://x.ngrok-free.app"
        assert isinstance(client, WorkerClientProtocol)
    finally:
        await client.aclose()


async def test_factory_picks_mock_or_http() -> None:
    assert isinstance(get_worker_client(Settings(_env_file=None)), MockWorkerClient)
    upper = Settings(_env_file=None, ai_worker_url="MOCK")
    assert isinstance(get_worker_client(upper), MockWorkerClient)
    http_client = get_worker_client(
        Settings(_env_file=None, ai_worker_url="https://w.example", ai_worker_key="k")
    )
    assert isinstance(http_client, WorkerClient)
    await http_client.aclose()
