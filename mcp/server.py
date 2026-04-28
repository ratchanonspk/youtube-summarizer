#!/usr/bin/env python3
import re
from datetime import date
from pathlib import Path

import requests
from mcp.server.fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

VAULT_DIR = Path("/Users/ratchanonspk/Library/CloudStorage/OneDrive-Personal/Obsidian/Rosetta")
TRANSCRIPT_DIR = VAULT_DIR / "Transcripts"
MAX_TRANSCRIPT_CHARS = 150_000

mcp = FastMCP("youtube-summarizer")


def _extract_video_id(url: str) -> str:
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


def _get_video_title(url: str) -> str:
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


def _sanitize_filename(title: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "", title)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe[:80]


@mcp.tool()
def get_video_info(url: str) -> dict:
    """Return the video title and ID for a YouTube URL."""
    video_id = _extract_video_id(url)
    title = _get_video_title(url)
    return {"title": title, "video_id": video_id}


@mcp.tool()
def get_transcript(url: str) -> str:
    """Fetch the full transcript text for a YouTube video.

    After receiving the transcript, summarize it with this exact format:

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

    As you write the summary, identify key proper nouns and concepts — people,
    organizations, technologies, tools, books, events, and domain-specific terms —
    and wrap them as Obsidian wiki-links using [[double brackets]].

    Rules for linking:
    - Only link a term the FIRST time it appears, not every occurrence
    - Only link genuinely notable terms (not filler words like "video" or "content")
    - Keep the link text natural, e.g. [[reinforcement learning]], [[Sam Altman]], [[GPT-4]]
    """
    video_id = _extract_video_id(url)
    api = YouTubeTranscriptApi()
    try:
        entries = api.fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
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


@mcp.tool()
def save_note(title: str, url: str, summary: str) -> str:
    """Save the summary as an Obsidian markdown note. Returns the saved file path."""
    today = date.today().isoformat()
    filename = f"{today} {_sanitize_filename(title)}.md"
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
    return str(note_path)


@mcp.tool()
def save_transcript(title: str, url: str, transcript: str) -> str:
    """Save the raw transcript to the Transcripts subfolder. Returns the saved file path."""
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filename = f"{today} {_sanitize_filename(title)}.txt"
    transcript_path = TRANSCRIPT_DIR / filename
    transcript_path.write_text(f"{title}\n{url}\n\n{transcript}", encoding="utf-8")
    return str(transcript_path)


if __name__ == "__main__":
    mcp.run()
