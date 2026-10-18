# MAKI: a validation harness for local LLM coding agents

MAKI runs a small local coding pipeline (Ollama + LangGraph) on a laptop GPU (RTX 4050, 6 GB VRAM, WSL2): task text in, code and tests out, checked with ruff and pytest, committed on a throwaway git branch that you accept or reject.

The pipeline is the small part. The point of this repo is the **measurement around it**: hidden tests the agent never sees, validated against reference solutions, repeated runs, ablations and a failure taxonomy. Everything below is a small-sample result from one model on one machine. Read the limitations.

## What is in the repo

| Path | What it does |
|---|---|
| `crew.py` | Pipeline: optional planner, coder (qwen2.5-coder 7B), checks (ruff, pytest, AST stub detector), optional LLM reviewer |
| `analyzer.py` | Rule-based task complexity estimate (simple / medium / complex) and a capability table for routing. Implemented but not wired in: `crew.py` never writes the table and always skips planning, so the analyzer only logs its estimate |
| `rag.py` | Local RAG over project files (ChromaDB + nomic-embed-text). Implemented, **not measured** (disabled in all evals) |
| `verify.py` | Deterministic judge: ruff + pyright + pytest coverage. Not wired into `crew.py` |
| `eval/` | Evaluation harness: tasks with hidden tests, runner, comparison and failure analysis scripts |
| `bin/ai-env` | CLI: `agent`, `accept`, `reject`, `rag`, `doctor`, `clean`, `stop`, `vram`, `gui` |
| `openwebui_pipe.py` | Open WebUI function that exposes the pipeline as a model |
| `tests/` | Unit tests for the analyzer and pipeline helpers |

## Method

- Each task has a prompt and a hidden test file. Every run starts in a fresh git repo; the agent never sees the hidden tests.
- For the five medium tasks (`eval/tasks/m_*`) the hidden tests were checked against reference solutions (`ref/`): all 69 tests pass, so failures are model failures, not test errors. The five simple tasks were **not** checked this way.
- Every configuration is run repeatedly and logged to `eval/results.jsonl`. `eval/compare.py` compares labels, `eval/analyze_fail.py` classifies failures.
- The first medium-task batch (labels `m-skip`, `m-coder`, `m-qwen3`) was run twice, leaving duplicate rows (20 `m-skip`, 16 `m-coder`, 10 `m-qwen3`; 10 each were intended). It is excluded from every number below.

## Results

Simple tasks (5 tasks):

| Configuration | Runs | Passed | Mean time |
|---|---|---|---|
| qwen3:4b planner, then coder (`baseline`, `tokens`) | 10 | 10 | 107 s |
| no planner (`plan-skip`) | 15 | 15 | 21 s |
| coder model as planner (`plan-coder`) | 15 | 15 | about 38 s |

Medium tasks (5 tasks x 2 repeats per configuration):

| Configuration | Passed | Mean time | Hangs (900 s limit) |
|---|---|---|---|
| no planner (`m2-skip`) | 3/10 | 83 s | 0 |
| coder model as planner (`m2-coder`) | 3/10 | 264 s | 2 |
| no planner, full failure text (`m3-full`) | 1/10 | 548 s | 4 |
| no planner, generation cap + call timeout (`m4-cap`) | 1/10 | 83 s | 0 |
| full failure text, cap + timeout (`m5-fullcap`) | 1/10 | 81 s | 0 |

## Findings (with their weight)

1. On simple tasks the planner did not improve the pass rate and made runs about 5x slower. The simple tasks saturate (100%), so this says nothing about harder tasks.
2. One measured planner call (qwen3:4b with `think=False`) produced 4,561 tokens and a 411-line plan in 87 s: the model wrote its reasoning as ordinary text.
3. On medium tasks the pass rate was 10 to 30% depending on configuration. With 10 runs per configuration these differences are not statistically distinguishable.
4. Hangs appeared only in long-prompt configurations. A per-call timeout and a generation cap removed them (`m3-full` 548 s vs `m5-fullcap` 81 s on the same prompt style). The root cause was not isolated.
5. The agent's own "all tests pass" is not reliable: in 2 of 23 failed runs (`m2-*`, `m4-cap`) the agent reported success while a hidden test failed.
6. Recurring failures seen in the logs (not systematically counted): a class attribute shadowing a method of the same name (`self.stock` vs `stock()`, in all 3 inspected failing `m_inventory` directories) and indexing into empty inputs (`busy[0]`, `rows[0]`, `pop from empty list`) across three tasks.
7. Unexplained: `m_intervals` passed 3 of 4 times in the `m2-*` runs and 0 of 6 times in the later `m3-full`, `m4-cap` and `m5-fullcap` runs, which used a changed `crew.py`. With five tasks inspected, chance is a plausible explanation, but it was not tested.

## Limitations

- One coder model (Qwen2.5-Coder 7B), one planner (Qwen3 4B), one machine.
- Small samples: 10 to 25 runs per configuration. No formal significance testing beyond rough hand calculations.
- Tasks were written by me with AI assistance, and so is much of the code in this repo.
- Only five medium tasks. No real-world repositories.
- `ai-env agent` runs the RAG step by default and re-indexes the project on every call (`MAKI_RAG=0` disables it). The evaluation runs disable it, so RAG's effect is unmeasured.
- RAG is implemented but was never compared on vs off. The LLM reviewer (a 7B judge) produced generic output in the few runs I looked at; this was observed, not measured, and it is disabled by default.
- `install.sh` was not tested on a clean machine. It does not install Aider (`maki-aider`) or Open WebUI (`ai-env gui`).
- CLI messages in `bin/ai-env` are in Azerbaijani.
- `eval/results.jsonl` contains local working-directory paths.

## Run it

Requirements: Ollama, Python 3 with venv, an NVIDIA GPU for the Ollama models (the unit tests and the reference check need none).

    ./install.sh --models      # see the warning inside the script first
    export MAKI_HOME=$(pwd)
    ai-env agent "Create roman.py with to_roman(n: int) -> str for 1..3999. Include tests."
    ai-env accept              # or: ai-env reject

No GPU needed:

    python -m pytest -q
    eval/validate_tests.sh     # hidden tests vs reference solutions

Evaluation (GPU):

    python eval/run_eval.py --label demo --task roman --repeat 3
    python eval/compare.py demo

## Roadmap

- PII masker for anything that would leave the machine (phone, e-mail, IBAN, card numbers), measured on synthetic strings.
- Optional cloud fallback behind the masker, off by default.
- Experiment: stronger model writes the tests, local model implements.
- Measure judge reliability against hand-labelled samples.
- Calibrate the analyzer on 30 hand-labelled tasks.
