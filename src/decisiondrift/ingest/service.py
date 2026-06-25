from __future__ import annotations

from pathlib import Path

import click

from decisiondrift.adr.dedup import is_duplicate
from decisiondrift.adr.id_allocator import allocate_id
from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.writer import write_adr
from decisiondrift.ingest.extractor import extract_candidates
from decisiondrift.ingest.segmenter import segment_notes
from decisiondrift.llm.client import LLMClient, LLMResponseError
from decisiondrift.models.schema import DecisionRecord


def run_ingest(file_path: str, adr_dir: str) -> None:
    path = Path(file_path)
    if not path.exists():
        click.echo(f"Error: file not found: {file_path}", err=True)
        return

    content = path.read_text(encoding="utf-8", errors="replace")
    segments = segment_notes(content)

    if not segments:
        click.echo("No content found to ingest.")
        return

    client = LLMClient()
    if not client.available():
        click.echo("Error: LLM API key not configured. Set DECISIONDRIFT_LLM_API_KEY.", err=True)
        return

    adr_path = Path(adr_dir)
    existing_adrs = load_adrs(str(adr_path)) if adr_path.exists() else []

    click.echo(f"Analyzing {len(segments)} segment(s) from {path.name}...")

    candidates = []

    for i, segment in enumerate(segments):
        try:
            extracted = extract_candidates(segment, client)
            for e in extracted:
                title = e.get("title")
                if not title:
                    continue

                cand_adr = DecisionRecord(
                    id="TEMP",
                    title=title,
                    status="proposed",
                    severity="medium",
                    source="ingest",
                    rationale=f"## Context\nCaptured from {path.name}.\n\n{e.get('rationale', '')}\n\n## Decision (candidate)\n{e.get('decision', '')}\n",
                )

                is_dup, dup_id = is_duplicate(cand_adr, existing_adrs)
                if is_dup:
                    click.echo(f"  Skipping '{title}': already documented as {dup_id}")
                    continue

                cand_adr.id = allocate_id(adr_dir)

                candidates.append(cand_adr)
                existing_adrs.append(cand_adr)

                # Write immediately to disk so `allocate_id` works for the next candidate
                adr_path.mkdir(parents=True, exist_ok=True)
                file_dest = adr_path / f"{cand_adr.id}.md"
                metadata = cand_adr.model_dump(exclude={"embedding", "rationale"}, exclude_none=True)
                write_adr(file_dest, metadata, cand_adr.rationale)
                click.echo(f"✓ Proposed {cand_adr.id}: {cand_adr.title}")

        except LLMResponseError as err:
            click.echo(f"Warning: LLM extraction failed for segment {i}: {err}")

    if not candidates:
        click.echo("No new decisions extracted.")
        return

    click.echo(f"\nGenerated {len(candidates)} candidate ADR(s) in {adr_dir}.")
    click.echo("Run `decisiondrift adr list --status proposed` to review.")
