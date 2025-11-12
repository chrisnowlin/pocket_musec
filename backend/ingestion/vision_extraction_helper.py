"""
Helper functions for vision-based PDF extraction with improved completeness
"""

import base64
import io
import json
import re
from typing import List, Dict, Any, Tuple
from pdf2image import convert_from_path
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def extract_standards_from_image(
    image: Image.Image, llm_client, page_num: int, grade_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Extract standards from a single page image using vision model

    Args:
        image: PIL Image object
        llm_client: ChutesClient instance
        page_num: Page number for logging
        grade_filter: Optional grade filter (e.g., "K", "1", "2")

    Returns:
        List of standard dictionaries with id, text, and objectives
    """
    from backend.llm.chutes_client import Message

    # Encode image
    buffered = io.BytesIO()
    image.save(buffered, format="PNG", optimize=True, quality=85)
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Build extraction prompt
    grade_hint = f" Focus on grade {grade_filter}." if grade_filter else ""

    prompt = f"""Extract ALL music education standards and objectives from this page.{grade_hint}

Look for standard IDs in formats like:
- Kindergarten: K.CN.1, K.CR.2, K.PR.1, K.RE.2
- Elementary: 1.CN.1, 2.PR.2, 3.RE.1, 4.CR.2, 5.CN.1, etc.
- Secondary: 6.CN.1, 7.PR.2, 8.RE.1
- Level-based: BE.CN.1, IN.PR.1, AD.RE.2, AC.CR.1

IMPORTANT: Extract EVERYTHING visible, even if text is partially cut off at page boundaries.

For EACH standard found, provide:
1. Standard ID (e.g., K.PR.2)
2. Complete standard text
3. ALL objectives with their IDs and full text

Return valid JSON only:
{{
  "page": {page_num},
  "standards": [
    {{
      "id": "K.PR.2",
      "text": "Develop musical presentations.",
      "objectives": [
        {{"id": "K.PR.2.1", "text": "Name the production elements needed..."}},
        {{"id": "K.PR.2.2", "text": "Identify appropriate audience and performer etiquette."}}
      ]
    }}
  ]
}}

If content is cut off at bottom, still include the standard ID and note "PARTIAL" in text."""

    # Create multimodal message
    message = Message(
        role="user",
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"},
            },
        ],
    )

    # Call vision model
    try:
        response = llm_client.chat_completion(
            messages=[message],
            model="Qwen/Qwen3-VL-235B-A22B-Instruct",
            temperature=0.0,  # Zero temp for accuracy
            max_tokens=4000,
        )

        # Parse JSON response
        content = response.content.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # Try to find JSON object
        if not content.startswith("{"):
            # Find first { and last }
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start : end + 1]

        data = json.loads(content)
        standards = data.get("standards", [])

        logger.info(f"Page {page_num}: Extracted {len(standards)} standards")
        return standards

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from vision response: {e}")
        logger.debug(f"Response content: {response.content[:500]}")

        # Fallback: extract using regex
        return extract_standards_from_text(response.content, page_num)

    except Exception as e:
        logger.error(f"Vision extraction failed for page {page_num}: {e}")
        return []


def extract_standards_from_text(text: str, page_num: int) -> List[Dict[str, Any]]:
    """
    Fallback extraction using regex when JSON parsing fails

    Args:
        text: Raw text response from vision model
        page_num: Page number

    Returns:
        List of standard dictionaries
    """
    standards = []

    # Pattern for standard IDs: K.CN.1, 1.PR.2, BE.RE.1, etc.
    std_pattern = r"([K123456789]|BE|IN|AD|AC)\.(?:CN|CR|PR|RE)\.\d+"

    # Find all standard IDs
    std_ids = re.findall(std_pattern, text)
    std_ids_unique = list(dict.fromkeys(std_ids))  # Remove duplicates

    logger.info(f"Fallback extraction found {len(std_ids_unique)} standards")

    for std_id in std_ids_unique:
        # Try to extract text for this standard
        # This is a simple implementation - could be enhanced
        standards.append(
            {
                "id": std_id,
                "text": f"[Extracted from page {page_num}]",
                "objectives": [],
                "page": page_num,
            }
        )

    return standards


def recover_missing_grade_prefixes(
    standards: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Intelligently recover missing grade prefixes from standards.

    Sometimes the vision model extracts standards like "RE.1" without the grade prefix.
    This function infers the grade from surrounding standards on the same page.

    Args:
        standards: List of standard dictionaries

    Returns:
        List with recovered grade prefixes
    """
    recovered_count = 0

    for std in standards:
        std_id = std.get("id", "")
        dot_count = std_id.count(".")

        # Check if missing grade prefix (only 1 dot: e.g., "RE.1")
        if dot_count == 1 and re.match(r"^(CN|CR|PR|RE)\.\d+$", std_id):
            # This is a standard missing its grade prefix
            # Try to infer grade from page context or other standards
            page_num = std.get("page", None)

            # Look for other standards from the same page with valid IDs
            if page_num:
                same_page_stds = [
                    s
                    for s in standards
                    if s.get("page") == page_num and s.get("id", "").count(".") == 2
                ]

                if same_page_stds:
                    # Extract grade from first valid standard on same page
                    sample_id = same_page_stds[0].get("id", "")
                    grade_prefix = sample_id.split(".")[0]

                    # Reconstruct the standard ID
                    new_id = f"{grade_prefix}.{std_id}"
                    logger.info(
                        f"Recovered grade prefix: '{std_id}' → '{new_id}' "
                        f"(inferred from page {page_num} context)"
                    )
                    std["id"] = new_id
                    recovered_count += 1

    if recovered_count > 0:
        logger.info(
            f"Recovered {recovered_count} standards with missing grade prefixes"
        )

    return standards


def clean_malformed_standards(standards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove malformed standard IDs that are actually objectives.

    Standards have format: GRADE.STRAND.NUMBER (e.g., K.PR.2, 8.RE.1)
    Objectives have format: GRADE.STRAND.NUMBER.NUMBER (e.g., K.PR.2.1, 8.RE.1.3)

    This filter removes entries where the ID has 3 dots instead of 2,
    indicating an objective was mistakenly extracted as a top-level standard.

    Args:
        standards: List of standard dictionaries

    Returns:
        Filtered list with malformed entries removed
    """
    filtered = []
    removed_count = 0

    for std in standards:
        std_id = std.get("id", "")

        # Count dots - standards should have exactly 2 dots
        dot_count = std_id.count(".")

        if dot_count == 2:
            # Valid standard ID format
            filtered.append(std)
        else:
            # Malformed entry (likely an objective extracted as a standard)
            removed_count += 1
            logger.warning(
                f"Filtering out malformed standard ID '{std_id}' "
                f"(has {dot_count} dots, expected 2)"
            )

    if removed_count > 0:
        logger.info(f"Removed {removed_count} malformed standard entries")

    return filtered


def extract_standards_from_pdf_multipage(
    pdf_path: str,
    llm_client,
    page_range: Tuple[int, int] = None,
    grade_filter: str = None,
    dpi: int = 300,
) -> List[Dict[str, Any]]:
    """
    Extract standards from multiple PDF pages, merging overlapping content

    Args:
        pdf_path: Path to PDF file
        llm_client: ChutesClient instance
        page_range: Optional (start, end) page numbers (1-indexed)
        grade_filter: Optional grade filter
        dpi: DPI for PDF conversion (default 300 for high quality)

    Returns:
        List of unique standards merged from all pages
    """
    # Convert PDF to images
    if page_range:
        images = convert_from_path(
            pdf_path, dpi=dpi, first_page=page_range[0], last_page=page_range[1]
        )
        start_page = page_range[0]
    else:
        images = convert_from_path(pdf_path, dpi=dpi)
        start_page = 1

    logger.info(f"Processing {len(images)} pages from {pdf_path}")

    # Extract from each page
    all_standards = {}

    for idx, image in enumerate(images):
        page_num = start_page + idx
        logger.info(f"Extracting from page {page_num}...")

        standards = extract_standards_from_image(
            image, llm_client, page_num, grade_filter
        )

        # Merge standards (later pages override earlier if more complete)
        for std in standards:
            std_id = std["id"]

            # If new or has more objectives, update
            if std_id not in all_standards:
                all_standards[std_id] = std
            else:
                existing = all_standards[std_id]
                new_obj_count = len(std.get("objectives", []))
                old_obj_count = len(existing.get("objectives", []))

                # Keep version with more objectives (more complete)
                if new_obj_count > old_obj_count:
                    all_standards[std_id] = std
                    logger.info(
                        f"Updated {std_id} with more complete version from page {page_num}"
                    )

                # Or if text is longer (less likely to be cut off)
                elif len(std.get("text", "")) > len(existing.get("text", "")):
                    if "PARTIAL" not in std.get("text", "") or "CUT OFF" not in std.get(
                        "text", ""
                    ):
                        all_standards[std_id] = std
                        logger.info(
                            f"Updated {std_id} with more complete text from page {page_num}"
                        )

    result = list(all_standards.values())
    logger.info(f"Total unique standards extracted: {len(result)}")

    # Apply intelligent grade prefix recovery
    result = recover_missing_grade_prefixes(result)

    # Apply post-processing filter to remove malformed entries
    result = clean_malformed_standards(result)
    logger.info(f"After filtering malformed entries: {len(result)} standards")

    return result


def get_extraction_statistics(standards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about extracted standards"""
    total = len(standards)
    by_grade = {}
    by_strand = {}
    total_objectives = 0

    for std in standards:
        std_id = std["id"]
        parts = std_id.split(".")

        if len(parts) >= 3:
            grade = parts[0]
            strand = parts[1]

            by_grade[grade] = by_grade.get(grade, 0) + 1
            by_strand[strand] = by_strand.get(strand, 0) + 1

        total_objectives += len(std.get("objectives", []))

    return {
        "total_standards": total,
        "total_objectives": total_objectives,
        "by_grade": by_grade,
        "by_strand": by_strand,
        "avg_objectives_per_standard": total_objectives / total if total > 0 else 0,
    }
