# Claude Code rules for Volume-Delta

## Tools
- NEVER use the Read tool on binary files: *.pkl, *.parquet, *.png, *.zip,
  model weights, pickled caches. Read is text-only.
- To inspect a binary cache, WRITE AND RUN a small Python script
  (pandas.read_pickle / pyarrow.parquet) and print only the summary
  (shape, columns, date range, dtypes). Do not dump raw bytes.

## Loop prevention
- If a tool returns an error or an unexpected result, DO NOT repeat the
  same tool call. In one sentence either propose an alternative approach
  or stop and ask the user. Repeating an identical action twice is forbidden.
- If you catch yourself writing "let me check again" or "hasn't changed
  since last read", STOP and switch strategy or ask.

## Task decomposition
- One session = one phase. Analysis and execution are separate sessions.
- Prefer writing a script under scripts/ and running it, over interactive
  multi-step file reading.

## Parameters
- The run period must be overridable without editing config.py.
  If asked for a date range different from config, pass it via CLI args
  or a temp config, and say so in the plan.

## How to run Volume-Delta

- NEVER edit config.py directly. All parameters are overridable via CLI.
- Always use `python run.py --days-back N` for rolling windows
  or `python run.py --since YYYY-MM-DD --until YYYY-MM-DD` for fixed ranges.
- Use `python run.py --info` to inspect resolved config without running.
- The pickle cache (cache/*.pkl) is binary — NEVER use Read on it.