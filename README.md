# CV Pipeline

A stepped pipeline that uses the Claude API to improve your resume through 7 sequential steps, based on the [Riyaz Twitter thread](https://twitter.com/riyazz_ai).

## Features

- **7-step pipeline** – Brutal audit, positioning, achievements, ATS alignment, tone, scan optimization, final polish
- **CLI & GUI** – Run via `main.py` or web UI at http://127.0.0.1:5000
- **PDF extraction** – Extract text from PDFs (pypdf, no OCR)
- **Cost tracking** – Per-step and total token usage and USD cost
- **Prompt editor** – Edit prompts in a left sidebar (optional)
- **Payload inspector** – View request/response for each step after a run

## Quick Start

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Set API key:** `export ANTHROPIC_API_KEY=...` (or use `.env` with `python-dotenv`)
3. **Run the GUI:** `python gui/server.py`
4. Open http://127.0.0.1:5000
5. Paste your resume (or use "Upload PDF" to extract text), enter target role, optionally add job description
6. Click **Run Pipeline**

## GUI

- **Edit prompts** – Opens left panel to customize step prompts and guardrails
- **View payloads** – After a run, inspect request/response for each step
- **☰ button** – Toggle the left panel (Prompts / Payloads tabs)

## CLI

```bash
python main.py resume.txt --role "Senior Software Engineer"
python main.py resume.txt --role "Senior Software Engineer" --job-description jd.txt
```

| Option | Description |
|--------|-------------|
| `--role` / `-r` | Target role (required) |
| `--job-description` / `-j` | Path to job description file |
| `--output-dir` / `-o` | Output directory (default: `./output`) |
| `--log-dir` / `-l` | Log directory (default: `./log`) |
| `--verbose` / `-v` | Extra verbose logs |

## Pipeline Steps

1. Brutal Recruiter Audit  
2. Positioning and Personal Brand Reset  
3. Achievement Conversion  
4. ATS Keyword Alignment (skipped if no JD)  
5. Executive Tone Upgrade  
6. 10-Second Scan Optimization  
7. Final Executive Polish  

## Output

- `output/`: `resume_final.txt`
- `log/`: step-by-step logs

## Requirements

Python 3.11+. See `requirements.txt`.

## Credits

- Pipeline prompts inspired by [Riyaz's Twitter thread](https://twitter.com/riyazz_ai)
- Built with [Anthropic Claude](https://www.anthropic.com/), [Flask](https://flask.palletsprojects.com/), [pypdf](https://pypdf.readthedocs.io/)

## Dependencies & Licenses

| Package | License |
|---------|---------|
| anthropic | MIT |
| python-dotenv | BSD-3-Clause |
| flask | BSD-3-Clause |
| pypdf | BSD-3-Clause |

See each package for full license text.

## License

MIT – see [LICENSE](LICENSE).
