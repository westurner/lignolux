import yaml
import re
from pathlib import Path

class ProcessStep:
    def __init__(self, id, label, inputs=None, outputs=None, properties=None, tables=None):
        self.id = id
        self.label = label
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.properties = properties or {}
        self.tables = tables or []
        self.next_steps = []

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
        if '|' in line and i + 1 < len(lines) and '---' in lines[i+1] and '|' in lines[i+1]:
            # Found a table
            headers = [h.strip() for h in line.split('|') if h.strip()]
            if not headers:
                i += 1
                continue
            i += 2 # Skip header and separator
            rows = []
            while i < len(lines) and ('|' in lines[i]):
                row_data = [d.strip() for d in lines[i].split('|') if d.strip()]
                # Allow some flexibility in column counts
                if len(row_data) >= len(headers):
                    rows.append(dict(zip(headers, row_data[:len(headers)])))
                i += 1
            if rows:
                tables.append({'headers': headers, 'rows': rows})
        else:
            i += 1
    return tables

def parse_myst_paper(file_path):
    """
    Naive parse of MyST/Markdown files for process information.
    """
    content = Path(file_path).read_text()
    steps = []
    
    # Split content by sections to parse properties/tables per section
    sections = re.split(r'(^#{2,4} .*)', content, flags=re.MULTILINE)
    
    for j in range(len(sections)):
        section_text = sections[j]
        # Match headers like ## Phase 1: ... or ### Key Inputs ...
        header_match = re.match(r'#{2,4} (Phase \d+|Key Inputs|Key Outputs|Process Overview|.*): (.*)|#{2,4} (Phase \d+|Key Inputs|Key Outputs|.*)', section_text)
        
        if header_match:
            groups = header_match.groups()
            label = groups[1] or groups[2] or groups[0]
            phase_id = (groups[0] or groups[2]).replace(" ", "_").strip()
            # Filter phase_id for IRI safety (simple for now, rdf_gen will clean more)
            phase_id = "".join(c for c in phase_id if c.isalnum() or c == '_')
            phase_id = re.sub(r'^[^a-zA-Z_]+', '', phase_id)
            if not phase_id:
                phase_id = f"Step_{len(steps)}"
            
            if "Inputs" in phase_id:
                phase_id = "Inputs_" + str(len(steps))
            if "Outputs" in phase_id:
                phase_id = "Outputs_" + str(len(steps))

            current_step = ProcessStep(phase_id, label)
            steps.append(current_step)
            
            if j + 1 < len(sections):
                body = sections[j+1]
                # Parse bullets in body
                for line in body.splitlines():
                    if line.strip().startswith('*'):
                        if '**' in line:
                            parts = line.split('**')
                            if len(parts) >= 3:
                                prop_name = parts[1].strip().strip(':').strip().lower().replace(" ", "_")
                                prop_name = "".join(c for c in prop_name if c.isalnum() or c == '_')
                                prop_name = re.sub(r'^[^a-zA-Z_]+', '', prop_name)
                                prop_val = parts[2].strip().strip(':').strip()
                                if prop_name:
                                    current_step.properties[prop_name] = prop_val
                        else:
                            item = line.strip('* ').strip()
                            if "input" in label.lower():
                                current_step.inputs.append(item)
                            elif "output" in label.lower():
                                current_step.outputs.append(item)
                
                # Parse tables in body
                current_step.tables = parse_markdown_tables(body)
                
    # Mermaid extraction - support multiple blocks and different formats
    # 1. Standard ```mermaid blocks
    mermaid_blocks = []
    for m in re.finditer(r'```mermaid\s*\n(.*?)\n```', content, re.DOTALL):
        mermaid_blocks.append(m.group(1))
    
    # 2. Indented blocks starting with graph/flowchart (common in these chat logs)
    # Be more flexible with whitespace and "Code snippet" prefix
    indent_pattern = re.compile(r'(?:code snippet|source code|markdown).*?\s*\n+((?:    .*\n?)+)', re.IGNORECASE)
    for m in indent_pattern.finditer(content):
        block_text = m.group(1)
        if "graph" in block_text or "flowchart" in block_text:
            # Clean indentation
            block = "\n".join(line[4:] if line.startswith("    ") else line for line in block_text.splitlines())
            mermaid_blocks.append(block)

    for block in mermaid_blocks:
        # nodes: ID["Label"] or ID(["Label"]) or ID(("Label")) etc.
        # IDs like L1, P1, A, B, etc.
        node_pattern = re.compile(r'(\w+)(?:\[|\(\[|\(\(|\(\[|\{)\s*"(.*?)"\s*(?:\]|\)\]|\)\)|\)\]|\})')
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
                        if not s.label or s.label == s.id or len(node_label) > len(s.label):
                             s.label = node_label
        
        # edges: A --> B or A["Label"] --> B(["Label"]) etc.
        # Handle nodes with shapes/labels in edge definitions
        edge_pattern = re.compile(
            r'(\w+)(?:\[|(?:\(\[)|\(\(|\(\[|\{)?(?:".*?")?(?:\]|(?:\)\])|\)\)|\)\]|\})?\s*'
            r'(?:---|-->|==>|-\.->|--\w+-->|--\s*".*?"\s*-->)\s*'
            r'(\w+)(?:\[|(?:\(\[)|\(\(|\(\[|\{)?(?:".*?")?(?:\]|(?:\)\])|\)\)|\)\]|\})?'
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
    
    return steps
