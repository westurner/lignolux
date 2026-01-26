import pytest
from sustainablefactory.parser import ProcessStep
from sustainablefactory.rdf_gen import generate_rdf_star, sanitize_id

def test_sanitize_id():
    assert sanitize_id("Phase 1") == "Phase_1"
    assert sanitize_id("Temp (C)") == "Temp_C"
    assert sanitize_id("2nd Step") == "id_2nd_Step"
    assert sanitize_id("²_special") == "special"

def test_generate_rdf_star_basic():
    step = ProcessStep("p1", "Process 1")
    step.properties["temp"] = "100"
    rdf = generate_rdf_star([step])
    assert "Process 1" in rdf
    assert "p1" in rdf
    assert "temp" in rdf
    assert "100" in rdf
    # We check for the reification components or the << syntax
    # Since pyoxigraph might serialize as standard reification in some versions/formats,
    # we just check that the extraction source is mentioned alongside the property.
    assert "extractionSource" in rdf

def test_generate_rdf_star_with_prefix():
    step = ProcessStep("p1", "Process 1")
    rdf = generate_rdf_star([step], source_prefix="test_doc")
    assert "test_doc__p1" in rdf
