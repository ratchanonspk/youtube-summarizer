#!/usr/bin/env python3
import re
import sys
import subprocess
from datetime import date
from pathlib import Path

import requests
import anthropic
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

load_dotenv()

VAULT_DIR = Path("/Users/ratchanonspk/Library/CloudStorage/OneDrive-Personal/Obsidian/Rosetta")
TRANSCRIPT_DIR = VAULT_DIR / "Transcripts"
MAX_TRANSCRIPT_CHARS = 150_000


def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:embed/)([A-Za-z0-9_-]{11})",
        r"(?:shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_video_title(url: str) -> str:
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("title", "Untitled Video")
    except Exception:
        return "Untitled Video"


def get_transcript(video_id: str) -> str:
    api = YouTubeTranscriptApi()
    try:
        entries = api.fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        # Try any available language
        try:
            transcript_list = api.list(video_id)
            transcript = transcript_list.find_transcript(
                [t.language_code for t in transcript_list]
            )
            entries = transcript.fetch()
        except Exception as e:
            raise RuntimeError(f"No transcript available for this video: {e}")

    text = " ".join(entry.text for entry in entries)
    return text[:MAX_TRANSCRIPT_CHARS]


def _build_prompt(transcript: str, title: str, url: str) -> str:
    return f"""You are summarizing a YouTube video transcript. Be concise and extract only what is genuinely useful.

Video title: {title}
URL: {url}

Transcript:
{transcript}

As you write the summary, identify key proper nouns and concepts — people, organizations, technologies, tools, books, events, and domain-specific terms — and wrap them as Obsidian wiki-links using [[double brackets]].

Rules for linking:
- Only link a term the FIRST time it appears, not every occurrence
- Only link genuinely notable terms (not filler words like "video" or "content")
- Keep the link text natural, e.g. [[reinforcement learning]], [[Sam Altman]], [[GPT-4]]

Provide your response in this exact format:

## TL;DR
<3 sentences that capture the core message>

## Key Takeaways
- <takeaway>
- <takeaway>
- <takeaway>
(add more if genuinely important)

## Notable Quotes
> "<quote>"
(omit this section if there are no memorable quotes)
"""


def _claude_cli_available() -> bool:
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


def _summarize_via_cli(prompt: str) -> str | None:
    """Use the Claude CLI (subscription). Returns None if unavailable or fails."""
    try:
        proc = subprocess.Popen(
            [
                "claude", "-p",
                "--tools", "",
                "--system-prompt", "You are a concise text summarizer. Return only the formatted summary as plain text. No preamble, no tool use.",
                prompt,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        chunks = []
        for chunk in iter(lambda: proc.stdout.read(64), ""):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        proc.wait(timeout=180)
        if proc.returncode == 0 and chunks:
            return "".join(chunks).strip()
        return None
    except (FileNotFoundError, OSError):
        return None
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        return None


def _summarize_via_api(prompt: str) -> str:
    """Use the Anthropic API key (fallback)."""
    client = anthropic.Anthropic()
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        summary = ""
        for text in stream.text_stream:
            print(text, end="", flush=True)
            summary += text
    return summary


def summarize(transcript: str, title: str, url: str, use_cli: bool = True) -> str:
    prompt = _build_prompt(transcript, title, url)
    if use_cli:
        summary = _summarize_via_cli(prompt)
        if summary is not None:
            return summary
        print("\n[Claude subscription failed — falling back to API key]", flush=True)
    return _summarize_via_api(prompt)


def sanitize_filename(title: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "", title)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe[:80]


def save_note(title: str, url: str, summary: str) -> Path:
    today = date.today().isoformat()
    filename = f"{today} {sanitize_filename(title)}.md"
    note_path = VAULT_DIR / filename

    note = f"""---
url: {url}
date: {today}
---

# {title}

{summary}

[Watch on YouTube]({url})
"""

    note_path.write_text(note, encoding="utf-8")
    return note_path


def save_transcript(title: str, url: str, transcript: str) -> Path:
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filename = f"{today} {sanitize_filename(title)}.txt"
    transcript_path = TRANSCRIPT_DIR / filename
    transcript_path.write_text(f"{title}\n{url}\n\n{transcript}", encoding="utf-8")
    return transcript_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <youtube_url>")
        sys.exit(1)

    url = sys.argv[1]

    print(f"Fetching info for: {url}")
    video_id = extract_video_id(url)
    title = get_video_title(url)
    print(f"Title: {title}")

    print("Fetching transcript...")
    transcript = get_transcript(video_id)
    print(f"Transcript length: {len(transcript):,} chars")

    use_cli = _claude_cli_available()
    if use_cli:
        print("[Summarizer: Claude subscription]", flush=True)
    else:
        print("[Summarizer: Anthropic API key (fallback — Claude CLI not found)]", flush=True)

    print("\n" + "=" * 60)
    summary = summarize(transcript, title, url, use_cli=use_cli)
    print("\n" + "=" * 60)

    note_path = save_note(title, url, summary)
    transcript_path = save_transcript(title, url, transcript)
    print(f"\nNote saved to:       {note_path}")
    print(f"Transcript saved to: {transcript_path}")


if __name__ == "__main__":
    main()
