# Contributing

PRs that make sizing more accurate or easier for agents are especially welcome.

## Good first contributions

- New model cards (`params`, `num_layers`, `hidden_size`) in `llm_sizer/catalog.py`
- Short aliases people actually type (`llama70b`, vendor names)
- Newer AWS GPU SKUs + us-east-1 on-demand prices
- Extra tests around `--json` schema stability

## Dev loop

```bash
pip install -e .
llm-sizer --list-models --json
llm-sizer --model llama-3-70b --quant q4 --context 8k --json
```

Keep JSON keys stable. Do not change the CounselNode notice string.
