"""
Appendix B Sample Dataset for FPT Software Europe Proposal Scorer.
Dynamically loads and manages official Markdown (.md) dataset files from sample_data/ directory:
- sample_data/rfp_nordframe.md
- sample_data/response_1_weak.md
- sample_data/response_2_medium.md
- sample_data/response_3_strong.md
- sample_data/response_4_overpromise.md
"""

import os
import re
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")


def load_markdown_file(filepath: str) -> str:
    """Reads a markdown file given an absolute or relative path."""
    if not os.path.isabs(filepath):
        filepath = os.path.join(SAMPLE_DATA_DIR, filepath)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def parse_markdown_metadata(content: str, default_title: str) -> Dict[str, str]:
    """Extracts title, company/submitter, and variant from markdown content."""
    title = default_title
    variant = "Standard"
    submitted_by = ""

    # Extract # Title
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()

    # Extract **Variant: ...**
    variant_match = re.search(r"\*\*Variant:\s*([^*]+)\*\*", content, re.IGNORECASE)
    if variant_match:
        variant = variant_match.group(1).strip()

    # Extract **Submitted by:** ...
    sub_match = re.search(r"\*\*Submitted by:\*\*\s*([^*]+)", content, re.IGNORECASE)
    if sub_match:
        submitted_by = sub_match.group(1).strip()

    return {
        "title": title,
        "variant": variant,
        "submitted_by": submitted_by,
    }


def build_sample_datasets() -> Dict[str, Any]:
    """
    Dynamically scans sample_data/ directory for .md files and constructs
    the structured SAMPLE_DATASETS dictionary.
    """
    datasets: Dict[str, Any] = {
        "rfp": {
            "title": "NordFrame Warehouse Inventory Dashboard RFP",
            "content": "",
            "file_path": "",
        },
        "proposals": {},
    }

    if not os.path.exists(SAMPLE_DATA_DIR):
        return datasets

    files = sorted(os.listdir(SAMPLE_DATA_DIR))

    # Priority order for standard benchmark variants
    known_order = [
        "response_3_strong",
        "response_2_medium",
        "response_4_overpromise",
        "response_1_weak",
    ]

    proposals_dict = {}

    for fname in files:
        if not fname.endswith(".md"):
            continue

        full_path = os.path.join(SAMPLE_DATA_DIR, fname)
        content = load_markdown_file(full_path)
        meta = parse_markdown_metadata(content, default_title=fname)

        if fname.startswith("rfp"):
            datasets["rfp"] = {
                "title": meta["title"],
                "content": content,
                "file_path": full_path,
            }
        else:
            key = os.path.splitext(fname)[0]
            display_title = meta["title"]
            if meta["submitted_by"]:
                display_title = f"{meta['title']} ({meta['submitted_by']})"

            proposals_dict[key] = {
                "title": f"{key.replace('_', ' ').title()} ({meta['submitted_by'] or meta['variant']})",
                "full_title": display_title,
                "variant": meta["variant"],
                "submitted_by": meta["submitted_by"],
                "content": content,
                "file_path": full_path,
            }

    sorted_proposals = {}
    for k in known_order:
        if k in proposals_dict:
            sorted_proposals[k] = proposals_dict.pop(k)

    for k, v in proposals_dict.items():
        sorted_proposals[k] = v

    datasets["proposals"] = sorted_proposals
    return datasets


SAMPLE_DATASETS = build_sample_datasets()

