"""
Spectral Analysis — FFT-based spectral analysis, PSD, periodogram, Welch method.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging, math, uuid
logger = logging.getLogger(__name__)


@dataclass
class SpectralAnalysisResult:
    result_id: str
    frequencies: List[float]
    power_spectrum: List[float]
    dominant_frequencies: List[float]
    metrics: Dict[str, float]


class SpectralAnalysisSystem:
    """FFT-based spectral analysis system."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[SpectralAnalysisResult] = []
        logger.info("SpectralAnalysis initialized")

    def _dft(self, data: List[float]) -> List[complex]:
        """Discrete Fourier Transform (direct computation)."""
        n = len(data)
        result = []
        for k in range(n):
            s = 0j
            for t in range(n):
                angle = -2 * math.pi * k * t / n
                s += data[t] * complex(math.cos(angle), math.sin(angle))
            result.append(s)
        return result

    def _fft_recursive(self, data: List[complex]) -> List[complex]:
        """Cooley-Tukey FFT (recursive, radix-2)."""
        n = len(data)
        if n <= 1:
            return data
        if n % 2 != 0:
            return self._dft([x.real for x in data])
        even = self._fft_recursive(data[0::2])
        odd = self._fft_recursive(data[1::2])
        result = [0j] * n
        for k in range(n // 2):
            w = complex(math.cos(-2 * math.pi * k / n), math.sin(-2 * math.pi * k / n))
            result[k] = even[k] + w * odd[k]
            result[k + n // 2] = even[k] - w * odd[k]
        return result

    def _fft(self, data: List[float]) -> List[complex]:
        n = len(data)
        # Pad to power of 2
        m = 1
        while m < n:
            m *= 2
        padded = [complex(x) for x in data] + [0j] * (m - n)
        return self._fft_recursive(padded)[:n]

    def _periodogram(self, data: List[float], fs: float = 1.0) -> Tuple[List[float], List[float]]:
        n = len(data)
        fft_result = self._fft(data)
        freqs = [k * fs / n for k in range(n // 2)]
        psd = [(abs(fft_result[k]) ** 2) / n for k in range(n // 2)]
        return freqs, psd

    def _welch(self, data: List[float], segment_len: int = None, overlap: float = 0.5, fs: float = 1.0) -> Tuple[List[float], List[float]]:
        n = len(data)
        if segment_len is None:
            segment_len = min(256, n)
        step = max(1, int(segment_len * (1 - overlap)))
        segments = []
        for start in range(0, n - segment_len + 1, step):
            segments.append(data[start:start + segment_len])
        if not segments:
            return self._periodogram(data, fs)
        avg_psd = [0.0] * (segment_len // 2)
        for seg in segments:
            # Apply Hanning window
            windowed = [seg[i] * (0.5 - 0.5 * math.cos(2 * math.pi * i / (len(seg) - 1))) for i in range(len(seg))]
            _, psd = self._periodogram(windowed, fs)
            for k in range(min(len(psd), len(avg_psd))):
                avg_psd[k] += psd[k]
        avg_psd = [p / len(segments) for p in avg_psd]
        freqs = [k * fs / segment_len for k in range(segment_len // 2)]
        return freqs, avg_psd

    def _find_dominant(self, freqs: List[float], psd: List[float], n_peaks: int = 5) -> List[float]:
        if len(psd) < 3:
            return []
        peaks = []
        for i in range(1, len(psd) - 1):
            if psd[i] > psd[i - 1] and psd[i] > psd[i + 1]:
                peaks.append((psd[i], freqs[i]))
        peaks.sort(reverse=True)
        return [f for _, f in peaks[:n_peaks] if f > 0]

    def analyze(self, data: List[float], method: str = "welch", fs: float = 1.0) -> SpectralAnalysisResult:
        n = len(data)
        mean = sum(data) / n
        centered = [x - mean for x in data]
        if method == "welch":
            freqs, psd = self._welch(centered, fs=fs)
        else:
            freqs, psd = self._periodogram(centered, fs=fs)
        dominant = self._find_dominant(freqs, psd)
        total_power = sum(psd)
        peak_power = max(psd) if psd else 0
        result = SpectralAnalysisResult(
            result_id=str(uuid.uuid4()),
            frequencies=freqs[:50],
            power_spectrum=psd[:50],
            dominant_frequencies=dominant,
            metrics={"total_power": total_power, "peak_power": peak_power, "spectral_entropy": -sum(p / total_power * math.log(p / total_power + 1e-10) for p in psd if p > 0) if total_power > 0 else 0},
        )
        self.results.append(result)
        return result

    def process(self, text: str) -> SpectralAnalysisResult:
        data = [float(x) for x in text.split(",") if x.strip()]
        if not data:
            data = [math.sin(2 * math.pi * i / 10) + 0.5 * math.sin(2 * math.pi * i / 3) for i in range(100)]
        return self.analyze(data)


_spectral_analysis: Optional[SpectralAnalysisSystem] = None
def get_spectral_analysis() -> Optional[SpectralAnalysisSystem]: return _spectral_analysis
def initialize_spectral_analysis(data_dir) -> SpectralAnalysisSystem:
    global _spectral_analysis
    _spectral_analysis = SpectralAnalysisSystem(data_dir)
    return _spectral_analysis
