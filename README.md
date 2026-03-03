# CV Pipeline

A stepped pipeline that uses the Claude API to improve your resume through 7 sequential steps, based on the [Riyaz Twitter thread](https://twitter.com/riyazz_ai).

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key:

   ```bash
   export ANTHROPIC_API_KEY=your-api-key-here
   ```

   Or copy `.env.example` to `.env` and add your key (requires `python-dotenv`).

## Usage

```bash
python main.py resume.txt --role "Senior Software Engineer"
```

With job description (for ATS keyword alignment in step 4):

```bash
python main.py resume.txt --role "Senior Software Engineer" --job-description jd.txt
```

Resume input: use a plain text file. For PDFs, copy-paste the text to avoid token waste (no parsing).

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--role` | `-r` | Target role (required) |
| `--job-description` | `-j` | Path to job description file (optional) |
| `--output-dir` | `-o` | Directory for final resume only (default: `./output`) |
| `--log-dir` | `-l` | Directory for complete step logs (default: `./log`) |

## Pipeline Steps

1. **Brutal Recruiter Audit** – Identifies why your resume may be ignored within 10 seconds
2. **Positioning and Personal Brand Reset** – Rewrites professional summary for target role
3. **Achievement Conversion** – Converts responsibilities to measurable achievements
4. **ATS Keyword Alignment** – Aligns resume with job description (skipped if no JD provided)
5. **Executive Tone Upgrade** – Concise, confident language
6. **10-Second Scan Optimization** – Improves structure and visual hierarchy
7. **Final Executive Polish** – Interview-ready document

## Output

- **Output dir** (`-o`): `resume_final.txt` only
- **Log dir** (`-l`): `step_1_audit.txt`, `step_2_resume.txt`, … – complete logs of each step

## Web GUI

Minimal 00s-style web interface:

```bash
python gui/server.py
```

Open http://127.0.0.1:5000 in your browser. Paste resume text, enter target role, optionally add job description, and run.

## Model

The app queries the Anthropic API for available models and picks the best match. Default preference is Sonnet. Set `ANTHROPIC_MODEL` in `.env` to override (e.g. `claude-haiku-4-5`, `claude-opus-4-6`). The model list is cached for 1 hour.
