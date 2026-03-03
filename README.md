# CV Pipeline

A stepped pipeline that uses the Claude API to improve your resume through 7 sequential steps, based on the [Riyaz Twitter thread](https://twitter.com/riyazz_ai).

## Quick Start

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Run the GUI:** `python gui/server.py`
3. Open http://127.0.0.1:5000 for GUI 
4. Click "Upload PDF (extract text)", choose a PDF, and the text will be extracted and pasted into the resume field
5. Run the pipeline as usual

**PDF extraction:** Uses pypdf's `extract_text()` in reading order, similar to selecting all and copying in a PDF viewer. Scanned/image-only PDFs will not yield useful text; OCR would be needed for those.

## Setup

Set `ANTHROPIC_API_KEY` (e.g. `export ANTHROPIC_API_KEY=...` or via `.env` with `python-dotenv`).

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

## License

MIT
