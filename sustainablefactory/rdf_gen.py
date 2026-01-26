import pyoxigraph as ox
import re

def sanitize_id(text):
    if not text:
        return "unknown"
    # Keep only a-z, A-Z, 0-9, and _ for absolute safety in Turtle local names
    s = re.sub(r'[^a-zA-Z0-9_]', '_', text)
    # Ensure it starts with a letter or underscore
    if not re.match(r'^[a-zA-Z_]', s):
        s = 'id_' + s
    # Clean up double underscores
    s = re.sub(r'_+', '_', s).strip('_')
    return s or "id"

def generate_rdf_star(steps, source_prefix=""):
    store = ox.Store()
    
    # Prefix for this specific export to avoid ID collisions
    pfx = sanitize_id(source_prefix) + "__" if source_prefix else ""

    # Helper to create named nodes
    def n(uri): return ox.NamedNode(uri)

    # We'll build a Turtle-star string and parse it into the store to ensure RDF-star support
    ttl_star = """
@prefix ex: <http://westurner.github.io/sustainablefactory/process/#> .
@prefix iof: <https://spec.industrialontologies.org/ontology/core/Core/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""
    for step in steps:
        step_id = pfx + sanitize_id(step.id)
        step_uri = f"ex:{step_id}"
        ttl_star += f"{step_uri} a iof:PlannedProcess ;\n"
        ttl_star += f"    rdfs:label {ox.Literal(step.label)} .\n"
        
        if step.properties:
            for prop, val in step.properties.items():
                prop_id = sanitize_id(prop)
                lit_val = ox.Literal(str(val))
                ttl_star += f"{step_uri} ex:{prop_id} {lit_val} .\n"
                # RDF-star part
                ttl_star += f"<< {step_uri} ex:{prop_id} {lit_val} >> ex:confidence 0.8 ;\n"
                ttl_star += "    ex:extractionSource \"MyST-Parser-Regex\" .\n"
        
        if step.inputs:
            for i, input_item in enumerate(step.inputs):
                input_id = f"Input_{step_id}_{i}"
                input_uri = f"ex:{input_id}"
                ttl_star += f"{input_uri} a iof:MaterialResource ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(input_item)} .\n"
                ttl_star += f"{step_uri} iof:participates_in_at_some_time {input_uri} .\n"

        if step.outputs:
            for i, output_item in enumerate(step.outputs):
                output_id = f"Output_{step_id}_{i}"
                output_uri = f"ex:{output_id}"
                ttl_star += f"{output_uri} a iof:Product ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(output_item)} .\n"
                ttl_star += f"{output_uri} iof:is_output_of {step_uri} .\n"

        if step.next_steps:
            for next_id in step.next_steps:
                sanitized_next_id = pfx + sanitize_id(next_id)
                ttl_star += f"{step_uri} iof:precedes ex:{sanitized_next_id} .\n"

        if step.tables:
            for tidx, table in enumerate(step.tables):
                table_id = f"Table_{step_id}_{tidx}"
                table_uri = f"ex:{table_id}"
                ttl_star += f"{table_uri} a ex:DataTable ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(f'Data Table in {step.label}')} .\n"
                ttl_star += f"{step_uri} ex:hasDataTable {table_uri} .\n"
                
                for ridx, row in enumerate(table['rows']):
                    row_uri = f"ex:{table_id}_Row_{ridx}"
                    ttl_star += f"{row_uri} a ex:TableRow .\n"
                    ttl_star += f"{table_uri} ex:hasRow {row_uri} .\n"
                    for col, val in row.items():
                        col_id = sanitize_id(col)
                        ttl_star += f"{row_uri} ex:{col_id} {ox.Literal(str(val))} .\n"
                
    try:
        store.load(ttl_star.encode("utf-8"), ox.RdfFormat.TURTLE)
    except Exception as e:
        # Write to a temp file for debugging
        with open("error_debug.ttl", "w") as f:
            f.write(ttl_star)
        print(f"Error loading Turtle-star: {e}. See error_debug.ttl")
        raise
    
    import io
    output = io.BytesIO()
    store.dump(output, ox.RdfFormat.TURTLE, from_graph=ox.DefaultGraph())
    return output.getvalue().decode("utf-8")
