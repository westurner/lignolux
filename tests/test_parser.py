import pytest
from sustainablefactory.parser import parse_markdown_tables, ProcessStep, parse_myst_paper
from pathlib import Path
from textwrap import dedent

def test_parse_markdown_tables():
    text = """
| Header 1 | Header 2 |
| --- | --- |
| Val 1 | Val 2 |
| Val 3 | Val 4 |
"""
    tables = parse_markdown_tables(text)
    assert len(tables) == 1
    assert tables[0]['headers'] == ['Header 1', 'Header 2']
    assert len(tables[0]['rows']) == 2
    assert tables[0]['rows'][0]['Header 1'] == 'Val 1'

def test_process_step_init():
    step = ProcessStep("id1", "Label 1")
    assert step.id == "id1"
    assert step.label == "Label 1"
    assert step.inputs == []
    assert step.next_steps == []

def test_parse_myst_paper_comprehensive(tmp_path):
    p = tmp_path / "comprehensive.md"
    p.write_text(dedent("""
        ## Phase 1: Heat Treatment
        * **Temperature**: 500C
        * **Duration**: 2h
        * Precursor A
        
        ### Key Outputs: Refined Material
        * Material B
        
        Code snippet:
            graph TD
            P1["Phase 1: Heat Treatment"] --> P2["Phase 2: Stretching"]
        
        ```mermaid
        graph LR
            P2 --> P3["Phase 3: Final"]
        ```
    """).strip())
    steps = parse_myst_paper(str(p))
    
    # Check Phase 1
    p1 = next((s for s in steps if s.id == "Phase_1"), None)
    assert p1 is not None
    assert p1.properties["temperature"] == "500C"
    
    # Mermaid nodes
    assert any(s.id == "P1" for s in steps)
    assert any(s.id == "P2" for s in steps)
    assert any(s.id == "P3" for s in steps)

    # Check Mermaid edges (P1 -> P2, P2 -> P3)
    p1_nodes = [s for s in steps if s.id == "P1"]
    assert "P2" in p1_nodes[0].next_steps
    
    p2_nodes = [s for s in steps if s.id == "P2"]
    assert "P3" in p2_nodes[0].next_steps
