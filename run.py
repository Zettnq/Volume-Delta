"""
Volume Delta — CLI entry point.

Run without arguments to use defaults from config.CVDConfig.
Use CLI flags to override any field (agent-friendly, no file edits needed).

Date semantics:
    --since YYYY-MM-DD   inclusive, midnight UTC if date-only
    --until YYYY-MM-DD   inclusive, end-of-day UTC if date-only
    --days-back N        rolling window [now - N days, now]

Examples:
    python run.py
    python run.py --symbol BTC/USDT --days-back 30
    python run.py --symbol ETH/USDT --since 2026-01-01 --until 2026-10-22 --target-tf 1h
    python run.py --symbol BTC/USDT --method candle --no-plot
    python run.py --info --days-back 30
"""

import argparse
import dataclasses
import inspect
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from config import CVDConfig
from engine import VolumeDeltaEngine
from plotter import plot_volume_delta


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Calculate and plot Volume Delta from exchange OHLCV data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ─── Identity ────────────────────────────────────────────────────────
    p.add_argument("--symbol", type=str,
                   help="Trading symbol, e.g. BTC/USDT (default from CVDConfig)")
    p.add_argument("--exchange", type=str,
                   help="Exchange name recognized by ccxt (default: bybit)")

    # ─── Timeframe ───────────────────────────────────────────────────────
    p.add_argument("--target-tf", "--tf", dest="target_tf", type=str,
                   help="Aggregation timeframe: 1m, 5m, 15m, 1h, 4h, 1d, ... "
                        "(default from CVDConfig)")

    # ─── Date range ──────────────────────────────────────────────────────
    time_group = p.add_mutually_exclusive_group()
    time_group.add_argument("--since", type=str,
                            help="Start date, YYYY-MM-DD or full ISO. "
                                 "Inclusive; midnight UTC if date-only.")
    time_group.add_argument("--days-back", "--days", dest="days_back", type=int,
                            help="Rolling window: [now - N days, now]. "
                                 "Overrides --since; explicit --until still wins.")
    p.add_argument("--until", type=str,
                   help="End date, YYYY-MM-DD or full ISO. "
                        "Inclusive; END-OF-DAY UTC if date-only.")

    # ─── Method & parameters ─────────────────────────────────────────────
    p.add_argument("--method", type=str, choices=["bvc", "candle"],
                   help="Volume classification method (default: bvc)")
    p.add_argument("--bvc-ewma-span", dest="bvc_ewma_span", type=int,
                   help="EWMA span for BVC volatility estimate (default: 50)")

    # ─── Paths & behavior ────────────────────────────────────────────────
    p.add_argument("--cache-dir", dest="cache_dir", type=str,
                   help="Directory for cached minute candles (default: cache)")
    p.add_argument("--output-dir", dest="output_dir", type=str,
                   help="Directory for CSV + PNG output (default: output)")
    p.add_argument("--force-reload", dest="force_reload", action="store_true",
                   help="Ignore cache and refetch minute data from exchange")

    # ─── Output toggles ──────────────────────────────────────────────────
    p.add_argument("--no-plot", dest="plot", action="store_false",
                   help="Skip rendering the PNG chart")
    p.add_argument("--no-csv", dest="save_csv", action="store_false",
                   help="Skip saving CSV export")
    p.set_defaults(plot=True, save_csv=True)

    # ─── Utility ─────────────────────────────────────────────────────────
    p.add_argument("--info", action="store_true",
                   help="Print the resolved config and exit without running")

    return p.parse_args()


# ─── Date helpers ──────────────────────────────────────────────────────────

def _parse_cli_date(text: str, end_of_day: bool = False) -> datetime:
    """Parse 'YYYY-MM-DD' or full ISO into tz-aware UTC datetime."""
    dt = datetime.fromisoformat(text.strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    is_date_only = ("T" not in text.upper()) and (":" not in text)
    if end_of_day and is_date_only:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def _coerce_to_field_type(new_dt: datetime, existing):
    """Return the date in the same representation the config field already uses
    (datetime stays datetime, str stays str) so engine comparisons never break."""
    if isinstance(existing, str):
        return new_dt.strftime("%Y-%m-%d")
    return new_dt


def apply_overrides(cfg: CVDConfig, a: argparse.Namespace) -> CVDConfig:
    """Build a NEW CVDConfig with CLI overrides (works for frozen dataclasses)."""

    overrides: dict = {}

    # Rolling window first; explicit --since/--until below can still win
    if a.days_back is not None:
        now = datetime.now(timezone.utc)
        overrides["since"] = _coerce_to_field_type(
            now - timedelta(days=a.days_back), cfg.since)
        overrides["until"] = _coerce_to_field_type(now, cfg.until)

    # Simple per-field overrides — only flags the user actually passed
    simple = {
        "symbol":        a.symbol,
        "exchange":      a.exchange,
        "target_tf":     a.target_tf,
        "method":        a.method,
        "bvc_ewma_span": a.bvc_ewma_span,
        "cache_dir":     a.cache_dir,
        "output_dir":    a.output_dir,
    }
    for field, value in simple.items():
        if value is not None:
            overrides[field] = value

    # Explicit dates (typed to match config field representation)
    if a.since is not None:
        overrides["since"] = _coerce_to_field_type(
            _parse_cli_date(a.since), cfg.since)
    if a.until is not None:
        overrides["until"] = _coerce_to_field_type(
            _parse_cli_date(a.until, end_of_day=True), cfg.until)

    if a.force_reload:
        overrides["force_reload"] = True

    # Keep only fields that actually exist in this CVDConfig version
    valid = {f.name for f in dataclasses.fields(cfg)}
    overrides = {k: v for k, v in overrides.items() if k in valid}

    return replace(cfg, **overrides) if overrides else cfg


def print_config(cfg: CVDConfig) -> None:
    print("Resolved CVDConfig:")
    print("-" * 44)
    for f in dataclasses.fields(cfg):
        print(f"  {f.name:<16} = {getattr(cfg, f.name)!r}")
    print("-" * 44)


def _accepts_df(fn) -> bool:
    """True if callable takes at least one positional arg (e.g. df)."""
    return any(
        p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        for p in inspect.signature(fn).parameters.values()
    )

def _call_plotter(fn, df, cfg, title: str):
    """Call plot_volume_delta filling parameters by name from cfg.

    Tolerates signature differences across repo versions:
    passes only parameters the function actually declares,
    and fails loudly if a required parameter cannot be inferred.
    """
    sig = inspect.signature(fn)
    candidates = {
        # dataframe
        "df": df, "data": df, "frame": df, "ohlcv": df,
        # identity / timeframe
        "symbol": cfg.symbol,
        "target_tf": cfg.target_tf, "tf": cfg.target_tf,
        "timeframe": cfg.target_tf,
        # method / paths / cosmetics
        "method": cfg.method,
        "output_dir": cfg.output_dir, "outdir": cfg.output_dir,
        "save_dir": cfg.output_dir, "save_path": cfg.output_dir,
        "title": title,
    }
    kwargs = {}
    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name in candidates:
            kwargs[name] = candidates[name]
        elif param.default is param.empty:
            raise TypeError(
                f"plotter requires argument '{name}' which run.py cannot infer")
    return fn(**kwargs)


def main() -> int:
    args = parse_args()
    cfg = apply_overrides(CVDConfig(), args)

    if args.info:
        print_config(cfg)
        return 0

    engine = VolumeDeltaEngine(cfg)
    df = engine.run()

    if df is None or len(df) == 0:
        print("ERROR: engine returned empty DataFrame", file=sys.stderr)
        return 1

    print(f"Produced {len(df)} rows for {cfg.symbol} "
          f"[{cfg.since} -> {cfg.until}] @ {cfg.target_tf} "
          f"(method={cfg.method})")

    if args.save_csv:
        try:
            if _accepts_df(engine.export_csv):
                engine.export_csv(df)
            else:
                engine.export_csv()
            print(f"CSV exported to {cfg.output_dir}/")
        except Exception as e:
            print(f"WARNING: CSV export failed: {e}", file=sys.stderr)

    if args.plot:
        try:
            title = (f"{cfg.symbol} {cfg.target_tf} "
                     f"Volume Delta ({cfg.method})")
            _call_plotter(plot_volume_delta, df, cfg, title)
            print("Chart rendered.")
        except Exception as e:
            print(f"WARNING: plotting failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())