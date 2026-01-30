import yaml
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class ProcessStep:
    id: str
    label: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    cost_figures: List[str] = field(default_factory=list)
    latex_math: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)



def parse_markdown_tables(text):
    """
    Extracts markdown tables from the text.
    Returns a list of dictionaries where each dict is a row.
    """
    tables = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for a header line containing | and a separator line below it
        if (
            "|" in line
            and i + 1 < len(lines)
            and "---" in lines[i + 1]
            and "|" in lines[i + 1]
        ):
            # Found a table
            header_line = line
            sep_line = lines[i + 1]

            headers = [h.strip() for h in header_line.split("|")]
            if header_line.startswith("|"):
                headers = headers[1:]
            if header_line.endswith("|"):
                headers = headers[:-1]
            headers = [h for h in headers if h]  # Final clean

            if not headers:
                i += 1
                continue

            i += 2  # Skip header and separator
            rows = []
            while i < len(lines):
                row_line = lines[i].strip()
                if not row_line or "|" not in row_line:
                    break

                row_data = [d.strip() for d in row_line.split("|")]
                if row_line.startswith("|"):
                    row_data = row_data[1:]
                if row_line.endswith("|"):
                    row_data = row_data[:-1]

                # Allow some flexibility in column counts - sometimes Gemini misses cells
                if len(row_data) >= len(headers):
                    rows.append(dict(zip(headers, row_data[: len(headers)])))
                elif len(row_data) > 0:
                    # Pad with empty strings if too few cells (prevent crash)
                    padded = row_data + [""] * (len(headers) - len(row_data))
                    rows.append(dict(zip(headers, padded)))
                i += 1
            if rows:
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def parse_cost_figures(text):
    """
    Extracts potential cost figures ($./kg, $., etc.) from text.
    """
    figures = []
    # Patterns for $10, $10.50, $10/kg, 10 cents, etc.
    patterns = [
        r"\$\d+(?:\.\d+)?(?:/\w+)?",
        r"\d+(?:\.\d+)?\s?(?:USD|cents?|dollars?)",
        r"(?:-\s?)?\$\d+(?:\.\d+)?",  # credits/costs
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        figures.extend(matches)
    return sorted(list(set(figures)))


def parse_latex_math(text):
    """
    Extracts LaTeX math ($ inline $ and $$ block $$) from text.
    """
    math_found = []
    # Block math: $$ ... $$
    block_pattern = r"\$\$.*?\$\$"
    blocks = re.findall(block_pattern, text, re.DOTALL)
    math_found.extend(blocks)

    # Remove blocks to avoid inner $ being caught by inline pattern
    text_no_blocks = re.sub(block_pattern, "", text, flags=re.DOTALL)

    # Inline math: $ ... $
    # Negative lookbehind/lookahead to avoid matching single $ used for currency
    # if it is followed by a digit (most cases), though math can also have digits.
    # A common heuristic is that math has spaces or symbols inside.
    # For now, we take any $...$ pair that is not a cost figure.
    inline_pattern = r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)"
    inlines = re.findall(inline_pattern, text_no_blocks)
    for item in inlines:
        if item.strip() and not re.match(r"^\d", item.strip()):  # Simple skip for $10
            math_found.append(f"${item.strip()}$")

    return sorted(list(set(math_found)))


def parse_performance_metrics(text):
    """
    Extracts KPIs and metrics (e.g., 99.9%, 20 MGOe, 140 bar).
    """
    metrics = []
    # Patterns for numbers followed by common industrial/scientific units
    # Including common prefixes like k, M, G
    units = r"(?:MGOe|GPa|mW/cm2|bar|[kMG]?Hz|RPM|mbar|mN/m|[kmu]?V|[kmu]?A|[kmu]?W|[kM]Wth|[kM]We|COP|%|℃|°C|nm|µm|mm|cm|m|kg|ton|ms|ns|s|h|hours?|mins?)"
    # Match numbers, optionally with spaces before units, but also handle smashed ones
    pattern = rf"\b\d+(?:\.\d+)?(?:\s?{units})(?!\w)"
    # Also handle some specific ones like 1MA
    extra_pattern = r"\b\d+(?:\.\d+)?[kMG]?A\b"

    matches = re.findall(pattern, text)
    metrics.extend(matches)
    matches_extra = re.findall(extra_pattern, text)
    metrics.extend(matches_extra)

    return sorted(list(set(metrics)))


def parse_equipment_and_tools(text):
    """
    Extracts mentions of specific machines, tools, and hardware.
    """
    # TODO: update tools list from a better entities list
    tools = [
        "Centrifuge",
        "Induction Coil",
        "Laser",
        "LCS Laser",
        "Ultrasonic Transducer",
        "Plasma Reactor",
        "Sand Battery",
        "Heliostat",
        "Quartz Thermal Trap",
        "Heat Exchanger",
        "Spectrometer",
        "RFID",
        "VACNT",
        "Sieve",
        "Turbine",
        "Compressor",
        "Pump",
        "Airlock",
        "Vacuum",
        "Vortex Spinner",
        "Supercapacitor",
        "Cathode",
        "Anode",
        "CVD Reactor",
        "Sonic Razor",
        "Induction Furnace",
        "Wafer Stepper",
        "Inkjet Printer",
    ]
    found = []
    for tool in tools:
        if re.search(rf"\b{tool}\b", text, re.IGNORECASE):
            found.append(tool)
    return sorted(found)


def parse_materials_and_chemicals(text):
    """
    Extracts chemical formulas and key industrial materials.
    """
    # Simple regex for things like Fe16N2, CO2, R-744, LBGP, etc.
    # Also look for capitalized acronyms that are likely materials.
    patterns = [
        r"\b[A-Z][a-z]?\d*(?:-?[A-Z][a-z]?\d*)*\b",  # Chemicals like Fe16N2, CO2, MnBi, Fe-N
        r"\bR-\d{3}\b",  # Refrigerants like R-744
        r"\b(?:CNT|SWCNT|MWCNT|CNF|COF|LCF|PFO-BPy|Lignin|Vitrimer|Graphene|Phytic Acid|Ethyl Lactate)\b",
    ]
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        found.extend(matches)

    # Filter out common false positives
    exclude = {
        "The",
        "We",
        "If",
        "It",
        "To",
        "As",
        "In",
        "My",
        "Is",
        "At",
        "On",
        "By",
        "He",
        "She",
    }
    found = [f for f in found if f not in exclude and len(f) > 1 and not f.isdigit()]
    return sorted(list(set(found)))


def parse_citations_and_sources(text):
    """
    Extracts references to papers, researchers, or URLs.
    """
    citations = []
    # URLs
    urls = re.findall(r"https?://[^\s\)\>\]]+", text)
    citations.extend(urls)
    # DOI and arXiv
    doi_arxiv = re.findall(r"\b(?:doi:|arXiv:)\S+", text)
    citations.extend(doi_arxiv)
    # Citations like "Ryu et al." or "Moyer/Pint"
    ref_pattern = r"\b[A-Z][a-z]+ (?:et al\.|and [A-Z][a-z]+)\b"
    matches = re.findall(ref_pattern, text)
    citations.extend(matches)
    return sorted(list(set(citations)))


def parse_and_extract_from_markdown(file_path):
    """
    Naive parse of MyST/Markdown files for process information.
    """
    path = Path(file_path)
    content = ""
    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if path.name.lower().endswith(".copilot.json") or (
                isinstance(data, dict) and "requests" in data
            ):
                # Handle Copilot export JSON
                for i, req in enumerate(data.get("requests", [])):
                    prompt = req.get("message", {}).get("text", "")
                    content += f"## Prompt: {i + 1}\n\n{prompt}\n\n"

                    response_text = ""
                    for part in req.get("response", []):
                        if part.get("kind") == "markdown":
                            response_text += part.get("value", "") + "\n"
                        elif part.get("kind") == "textEditGroup" and "edits" in part:
                            for edit_group in part["edits"]:
                                for edit in edit_group:
                                    response_text += edit.get("text", "")
                            response_text += "\n"

                    if response_text:
                        content += f"## Response: {i + 1}\n\n{response_text}\n\n"
            elif isinstance(data, list):
                for item in data:
                    content += item.get("content", "") + "\n"
            elif isinstance(data, dict):
                if "content" in data:
                    content = data["content"]
                elif "messages" in data:
                    for i, msg in enumerate(data["messages"]):
                        # Map Gemini export structure (author: 'user'/'ai') to Prompt/Response headers
                        raw_author = msg.get("author", "unknown").lower()
                        if raw_author == "ai":
                            author = "Response"
                        elif raw_author == "user":
                            author = "Prompt"
                        else:
                            author = raw_author.capitalize()
                        content += f"## {author}: {i + 1}\n\n"
                        content += msg.get("content", "") + "\n\n"
            if not content:
                content = path.read_text(encoding="utf-8")
        except:
            content = path.read_text(encoding="utf-8")
    else:
        content = path.read_text(encoding="utf-8")

    # Simple extraction logic:
    # Look for Phase sections and High-level Process Flow items.

    steps = []

    # Split content by sections to parse properties/tables per section
    # Support up to level 5 headers
    sections = re.split(r"(^#{2,5} .*)", content, flags=re.MULTILINE)

    def populate_step(step, body):
        # Parse bullets in body
        for line in body.splitlines():
            if line.strip().startswith("*"):
                if "**" in line:
                    parts = line.split("**")
                    if len(parts) >= 3:
                        prop_name = (
                            parts[1]
                            .strip()
                            .strip(":")
                            .strip()
                            .lower()
                            .replace(" ", "_")
                        )
                        prop_name = "".join(
                            c for c in prop_name if c.isalnum() or c == "_"
                        )
                        prop_name = re.sub(r"^[^a-zA-Z_]+", "", prop_name)
                        prop_val = parts[2].strip().strip(":").strip()
                        if prop_name:
                            step.properties[prop_name] = prop_val
                else:
                    # Generic bullet item
                    item = line.strip("* ").strip()
                    if "input" in step.label.lower():
                        step.inputs.append(item)
                    elif "output" in step.label.lower():
                        step.outputs.append(item)

        # Parse tables in body
        step.tables = parse_markdown_tables(body)
        step.cost_figures = parse_cost_figures(body)
        step.latex_math = parse_latex_math(body)
        step.metrics = parse_performance_metrics(body)
        step.equipment = parse_equipment_and_tools(body)
        step.materials = parse_materials_and_chemicals(body)
        step.citations = parse_citations_and_sources(body)

    for j in range(0, len(sections)):
        section_text = sections[j]
        # Match headers like ## Phase 1: ... or ### Key Inputs ...
        header_match = re.match(
            r"#{2,5} (Phase \d+|Key Inputs|Key Outputs|Process Overview|Prompt|Response|.*): (.*)|#{2,5} (Phase \d+|Key Inputs|Key Outputs|Prompt|Response|.*)",
            section_text,
        )

        if header_match:
            groups = header_match.groups()
            label = groups[1] or groups[2] or groups[0]
            phase_id = (groups[0] or groups[2] or "Step").replace(" ", "_").strip()
            # Filter phase_id for IRI safety
            phase_id = "".join(c for c in phase_id if c.isalnum() or c == "_")
            phase_id = re.sub(r"^[^a-zA-Z_]+", "", phase_id)
            if not phase_id:
                phase_id = f"Step_{len(steps)}"

            # Use specific IDs for inputs/outputs if found
            if "Inputs" in label:
                phase_id = "Inputs_" + str(len(steps))
            if "Outputs" in label:
                phase_id = "Outputs_" + str(len(steps))

            current_step = ProcessStep(phase_id, label)
            steps.append(current_step)

            # The next element in sections will be the body of this header
            if j + 1 < len(sections):
                populate_step(current_step, sections[j + 1])

    # If no steps found or significant content before first header, add a summary step
    if not steps and content.strip():
        fallback = ProcessStep("File_Summary", "File Summary")
        populate_step(fallback, content)
        steps.append(fallback)
    elif sections and sections[0].strip() and len(sections[0].strip()) > 50:
        # Check if first section (pre-header) has content worth saving
        pre_step = ProcessStep("Introduction", "Introduction")
        populate_step(pre_step, sections[0])
        steps.insert(0, pre_step)

    # Mermaid extraction - support multiple blocks and different formats
    # 1. Standard ```mermaid blocks
    mermaid_blocks = []
    for m in re.finditer(r"```mermaid\s*\n(.*?)\n```", content, re.DOTALL):
        mermaid_blocks.append(m.group(1))

    # 2. Indented blocks starting with graph/flowchart (common in these chat logs)
    # Be more flexible with whitespace and "Code snippet" prefix
    indent_pattern = re.compile(
        r"(?:code snippet|source code|markdown).*?\s*\n+((?:    .*\n?)+)", re.IGNORECASE
    )
    for m in indent_pattern.finditer(content):
        block_text = m.group(1)
        if "graph" in block_text or "flowchart" in block_text:
            # Clean indentation
            block = "\n".join(
                line[4:] if line.startswith("    ") else line
                for line in block_text.splitlines()
            )
            mermaid_blocks.append(block)

    for block in mermaid_blocks:
        # nodes: ID["Label"] or ID(["Label"]) or ID(("Label")) etc.
        # IDs like L1, P1, A, B, etc.
        node_pattern = re.compile(
            r'(\w+)(?:\[|\(\[|\(\(|\(\[|\{)\s*["\']?(.*?)["\']?\s*(?:\]|\)\]|\)\)|\)\]|\})'
        )
        for m in node_pattern.finditer(block):
            node_id = m.group(1)
            node_label = m.group(2).replace("<br/>", " ").replace("\\n", " ").strip()
            # If we don't have this step yet, add it
            if not any(s.id == node_id for s in steps):
                steps.append(ProcessStep(node_id, node_label))
            else:
                # Update label if it was just a generic ID or shorter before
                for s in steps:
                    if s.id == node_id:
                        if (
                            not s.label
                            or s.label == s.id
                            or len(node_label) > len(s.label)
                        ):
                            s.label = node_label

        # edges: A --> B or A["Label"] --> B etc.
        # We simplify by just looking for IDs on either side of an arrow,
        # potentially followed by labels which we ignore for edge detection.
        edge_pattern = re.compile(
            r'(\w+)(?:\[.*?\]|\(.*?\))?\s*(?:---|-->|==>|-\.->|--\w+-->|--\s*".*?"\s*-->)\s*(\w+)'
        )
        for m in edge_pattern.finditer(block):
            source_id = m.group(1)
            target_id = m.group(2)
            # Find or create source/target
            source_step = next((s for s in steps if s.id == source_id), None)
            if not source_step:
                source_step = ProcessStep(source_id, source_id)
                steps.append(source_step)

            if target_id not in source_step.next_steps:
                source_step.next_steps.append(target_id)

            if not any(s.id == target_id for s in steps):
                steps.append(ProcessStep(target_id, target_id))

    # Add a summary step for the whole file to capture costs/tables not in sections
    summary_step = ProcessStep("File_Summary", "File Summary")
    summary_step.cost_figures = parse_cost_figures(content)
    summary_step.latex_math = parse_latex_math(content)
    summary_step.metrics = parse_performance_metrics(content)
    summary_step.equipment = parse_equipment_and_tools(content)
    summary_step.materials = parse_materials_and_chemicals(content)
    summary_step.citations = parse_citations_and_sources(content)
    # Filter for unique tables by header/row count to avoid duplication if already in steps
    all_tables = parse_markdown_tables(content)
    summary_step.tables = all_tables
    steps.append(summary_step)

    return steps
