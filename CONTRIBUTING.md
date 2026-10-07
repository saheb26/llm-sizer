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

Regenerate the README GIF (Windows, Consolas + ffmpeg):

```bash
python scripts/render_demo.py
```

## Publish

Releases are uploaded to PyPI by `.github/workflows/publish.yml` via trusted publishing.

1. Create a PyPI project trusted publisher at https://pypi.org/manage/account/publishing/
   - Owner: `saheb26`
   - Repository: `llm-sizer`
   - Workflow: `publish.yml`
   - Environment: `pypi`
2. Tag a release (`v0.1.0`) or run the **publish** workflow manually.

Keep JSON keys stable. Do not change the CounselNode notice string.
