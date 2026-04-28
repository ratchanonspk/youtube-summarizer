# YouTube Summarizer

Fetches a YouTube video transcript and produces an Obsidian-formatted summary with TL;DR, key takeaways, and notable quotes. Saves the note and raw transcript to your Obsidian vault.

## Two ways to run

### Option A — Claude Code (uses your Claude.ai subscription, no API charge)

With the MCP server registered, tell Claude Code in natural language:

> Summarize this YouTube video: https://youtu.be/...

Claude Code calls the transcript and saving tools automatically — no API key needed.

### Option B — Terminal fallback (`yt` alias, uses Anthropic API key)

Use this when your Claude.ai subscription usage runs out:

```zsh
yt https://youtu.be/...
```

Requires `ANTHROPIC_API_KEY` in `.env`.

---

## Setup

### 1. Install Python dependencies

For the terminal fallback (`yt` alias):
```bash
pip3 install -r requirements.txt
```

For the MCP server (requires Python 3.10+, uses a venv):
```bash
# Install Homebrew Python if needed: brew install python3
/opt/homebrew/bin/python3 -m venv mcp/.venv
mcp/.venv/bin/pip install -r mcp/requirements.txt
```

### 2. Add your API key (for terminal fallback only)

Create `.env` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Register the MCP server with Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "youtube-summarizer": {
      "command": "/Users/ratchanonspk/Library/CloudStorage/OneDrive-Personal/Obsidian/youtube-summarizer/mcp/.venv/bin/python3",
      "args": [
        "/Users/ratchanonspk/Library/CloudStorage/OneDrive-Personal/Obsidian/youtube-summarizer/mcp/server.py"
      ]
    }
  }
}
```

Then restart Claude Code.

### 4. Add the `yt` alias (for terminal fallback)

Add to `~/.zshrc`:

```zsh
yt() {
  python3 "/Users/ratchanonspk/Library/CloudStorage/OneDrive-Personal/Obsidian/youtube-summarizer/summarize.py" "$1"
}
```

---

## Output

| File | Location |
|---|---|
| Summary note | `Obsidian/Rosetta/<date> <title>.md` |
| Raw transcript | `Obsidian/Rosetta/Transcripts/<date> <title>.txt` |

---

## Project structure

```
youtube-summarizer/
├── summarize.py       # standalone script (Option B / yt alias)
├── requirements.txt   # main Python deps
├── .env               # ANTHROPIC_API_KEY for terminal fallback
└── mcp/
    ├── server.py      # MCP server exposing transcript + saving tools
    ├── requirements.txt
    └── .venv/         # Python 3.14 virtualenv (not committed)
```
