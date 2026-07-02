"""signalcore Faz 0 demo: rejim-anahtarlamali sentetik OHLCV uret + dogrula.

Calistir:
    PYTHONPATH=. python3 scripts/run_signalcore_demo.py
"""
from __future__ import annotations

from datetime import timedelta

from signalcore.core.ohlcv import validate_series
from signalcore.feeds import synthetic_ohlcv


def main() -> None:
    bars = synthetic_ohlcv(500, symbol="SIM/USDT", seed=42, interval=timedelta(minutes=1))
    validate_series(bars, expected_interval=timedelta(minutes=1))

    closes = [b.close for b in bars]
    print(f"uretilen bar sayisi: {len(bars)}")
    print(f"ilk fiyat: {closes[0]:.2f}  son fiyat: {closes[-1]:.2f}")
    print(f"min: {min(closes):.2f}  max: {max(closes):.2f}")
    print("dogrulama: OK (validate_series hata firlatmadi)")


if __name__ == "__main__":
    main()
