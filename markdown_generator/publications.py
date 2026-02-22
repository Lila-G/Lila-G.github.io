#!/usr/bin/env python3
"""Generate publication markdown files for academicpages from CSV/TSV data."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

EXIT_ERROR = 1
REQUIRED_FIELDS = [
    "pub_date",
    "title",
    "venue",
    "excerpt",
    "citation",
    "url_slug",
    "paper_url",
    "slides_url",
]

HTML_ESCAPE_TABLE = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
}


def html_escape(text: str) -> str:
    return "".join(HTML_ESCAPE_TABLE.get(ch, ch) for ch in text)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return cleaned.strip("-") or "publication"


def read_rows(data_path: Path) -> list[dict[str, str]]:
    delimiter = "," if data_path.suffix.lower() == ".csv" else "\t"

    with data_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            print("Input file is missing a header row", file=sys.stderr)
            sys.exit(EXIT_ERROR)

        missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
        if missing:
            print(f"Missing required fields: {', '.join(missing)}", file=sys.stderr)
            sys.exit(EXIT_ERROR)

        rows = []
        for raw in reader:
            row = {key: (value or "").strip() for key, value in raw.items()}
            if not row["pub_date"] or not row["title"] or not row["venue"]:
                print(
                    f"Skipping incomplete row with title '{row.get('title', '<missing>')}'",
                    file=sys.stderr,
                )
                continue
            rows.append(row)

    if not rows:
        print("No valid publication rows found", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    return rows


def build_markdown(row: dict[str, str]) -> tuple[str, str]:
    pub_date = row["pub_date"]
    slug = row["url_slug"] or slugify(row["title"])
    filename = f"{pub_date}-{slug}.md"
    permalink = f"/publication/{pub_date}-{slug}"
    category = row.get("category", "").strip() or "conferences"

    md_lines = [
        "---",
        f'title: "{row["title"]}"',
        "collection: publications",
        f"category: {category}",
        f"permalink: {permalink}",
        f"date: {pub_date}",
        f"venue: '{html_escape(row['venue'])}'",
    ]

    excerpt = row["excerpt"]
    if excerpt:
        md_lines.append(f"excerpt: '{html_escape(excerpt)}'")

    paper_url = row["paper_url"]
    if paper_url:
        md_lines.append(f"paperurl: '{paper_url}'")

    slides_url = row["slides_url"]
    if slides_url:
        md_lines.append(f"slidesurl: '{slides_url}'")

    citation = row["citation"]
    md_lines.append(f"citation: '{html_escape(citation)}'")
    md_lines.append("---")

    body = []
    if paper_url:
        body.append(f"<a href='{paper_url}'>Open publication record</a>")
    if excerpt:
        body.append(html_escape(excerpt))
    body.append(f"Recommended citation: {html_escape(citation)}")

    return filename, "\n".join(md_lines + [""] + body + [""])


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 markdown_generator/publications.py [filename.csv|filename.tsv]", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    data_path = Path(sys.argv[1]).resolve()
    if not data_path.exists():
        print(f"Input file not found: {data_path}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if data_path.suffix.lower() not in {".csv", ".tsv"}:
        print(f"Expected .csv or .tsv file, got: {data_path.name}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    rows = read_rows(data_path)

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / "_publications"
    output_dir.mkdir(parents=True, exist_ok=True)

    for existing in output_dir.glob("*.md"):
        existing.unlink()

    for row in rows:
        filename, content = build_markdown(row)
        (output_dir / filename).write_text(content, encoding="utf-8")

    print(f"Generated {len(rows)} publication files in {output_dir}")


if __name__ == "__main__":
    main()
