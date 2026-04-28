# YouTube Summarizer

Fetches a YouTube video transcript and produces a Markdown summary with TL;DR, key takeaways, and notable quotes — saved as a `.md` file. Optionally integrates with Obsidian for a linked note-taking experience.

## Two ways to run

### Option A — Claude Code (uses your Claude.ai subscription, no API charge)

With the MCP server registered, tell Claude Code in natural language:

> Summarize this YouTube video: https://youtu.be/...

Claude Code calls the transcript and saving tools automatically — no API key needed.

### Option B — Terminal (`yt` alias, uses Anthropic API key)

```zsh
yt https://youtu.be/...
```

Requires `ANTHROPIC_API_KEY` in `.env`.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ratchanonspk/youtube-summarizer.git
cd youtube-summarizer
```

### 2. Set your output folder

> **Important:** Both scripts have a hardcoded output path you must change before running.

Open **`summarize.py`** and **`mcp/server.py`** and update line 15 / line 10 respectively:

```python
# Change this to wherever you want your notes saved
VAULT_DIR = Path("/your/output/folder")
```

**Examples:**
| Setup | Path |
|---|---|
| No Obsidian (just save files anywhere) | `Path.home() / "Documents" / "summaries"` |
| Obsidian on Mac | `Path.home() / "Documents" / "Obsidian" / "YourVault"` |
| Obsidian with iCloud | `Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/YourVault"` |
| Obsidian with OneDrive | `Path("/Users/yourname/Library/CloudStorage/OneDrive-Personal/Obsidian/YourVault")` |

### 3. Install Python dependencies

For the terminal fallback (`yt` alias):
```bash
pip3 install -r requirements.txt
```

For the MCP server (requires Python 3.10+):
```bash
/opt/homebrew/bin/python3 -m venv mcp/.venv
mcp/.venv/bin/pip install -r mcp/requirements.txt
```

### 4. Add your API key (Option B only)

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

Then edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Get your key at [console.anthropic.com](https://console.anthropic.com).

### 5. Register the MCP server with Claude Code (Option A only)

Add to `~/.claude/settings.json` — replace the paths with your actual clone location:

```json
{
  "mcpServers": {
    "youtube-summarizer": {
      "command": "/your/clone/path/mcp/.venv/bin/python3",
      "args": [
        "/your/clone/path/mcp/server.py"
      ]
    }
  }
}
```

Then restart Claude Code.

### 6. Add the `yt` alias (Option B only)

Add to `~/.zshrc` — replace the path with your actual clone location:

```zsh
yt() {
  python3 "/your/clone/path/summarize.py" "$1"
}
```

Then reload your shell:
```bash
source ~/.zshrc
```

---

## Want the Obsidian experience?

Obsidian is a free note-taking app that renders Markdown files and supports `[[wiki-links]]` — the summarizer wraps key terms in these automatically so they become clickable connections between your notes.

1. Download Obsidian at [obsidian.md](https://obsidian.md) (free)
2. Open Obsidian → **Open folder as vault** → select your output folder
3. Your summaries will appear as linked notes automatically

---

## Output

| File | Location |
|---|---|
| Summary note | `<VAULT_DIR>/<date> <title>.md` |
| Raw transcript | `<VAULT_DIR>/Transcripts/<date> <title>.txt` |

Each summary includes:
- YAML frontmatter (url, date)
- **TL;DR** — 3-sentence overview
- **Key Takeaways** — bullet points with `[[wiki-links]]` on key terms
- **Notable Quotes** — memorable lines from the video

---

## Project structure

```
youtube-summarizer/
├── summarize.py       # standalone script (Option B / yt alias)
├── requirements.txt   # Python deps for Option B
├── .env.example       # copy to .env and add your API key
└── mcp/
    ├── server.py      # MCP server for Option A (Claude Code)
    ├── requirements.txt
    └── .venv/         # virtualenv (not committed)
```
