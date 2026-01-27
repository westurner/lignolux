"""
Docstring for sustainablefactory.rdf_gen
"""
import re
import pyoxigraph as ox


def sanitize_id(text):
    if not text:
        return "unknown"
    # Keep only a-z, A-Z, 0-9, and _ for absolute safety in Turtle local names
    s = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    # Ensure it starts with a letter or underscore
    if not re.match(r"^[a-zA-Z_]", s):
        s = "id_" + s
    # Clean up double underscores
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "id"


def generate_rdf_star(steps, source_prefix="", verbose: bool = False):
    store = ox.Store()

    # Prefix for this specific export to avoid ID collisions
    pfx = sanitize_id(source_prefix) + "__" if source_prefix else ""

    # Helper to create named nodes
    def n(uri):
        return ox.NamedNode(uri)

    # We'll build a Turtle-star string and parse it into the store to ensure RDF-star support
    ttl_star = """
@prefix sfpro: <http://westurner.github.io/sustainablefactory/process/#> .
@prefix iof: <https://spec.industrialontologies.org/ontology/core/Core/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""
    for step in steps:
        step_id = pfx + sanitize_id(step.id)
        step_uri = f"sfpro:{step_id}"
        ttl_star += f"{step_uri} a iof:PlannedProcess ;\n"
        ttl_star += f"    rdfs:label {ox.Literal(step.label)} .\n"

        if step.properties:
            for prop, val in step.properties.items():
                prop_id = sanitize_id(prop)
                lit_val = ox.Literal(str(val))
                ttl_star += f"{step_uri} sfpro:{prop_id} {lit_val} .\n"
                # RDF-star part
                ttl_star += (
                    f"<< {step_uri} sfpro:{prop_id} {lit_val} >> sfpro:confidence 0.8 ;\n"
                )
                ttl_star += '    sfpro:extractionSource "MyST-Parser-Regex" .\n'

        if step.inputs:
            for i, input_item in enumerate(step.inputs):
                input_id = f"Input_{step_id}_{i}"
                input_uri = f"sfpro:{input_id}"
                ttl_star += f"{input_uri} a iof:MaterialResource ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(input_item)} .\n"
                ttl_star += (
                    f"{step_uri} iof:participates_in_at_some_time {input_uri} .\n"
                )

        if step.outputs:
            for i, output_item in enumerate(step.outputs):
                output_id = f"Output_{step_id}_{i}"
                output_uri = f"sfpro:{output_id}"
                ttl_star += f"{output_uri} a iof:Product ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(output_item)} .\n"
                ttl_star += f"{output_uri} iof:is_output_of {step_uri} .\n"

        if step.next_steps:
            for next_id in step.next_steps:
                sanitized_next_id = pfx + sanitize_id(next_id)
                ttl_star += f"{step_uri} iof:precedes sfpro:{sanitized_next_id} .\n"

        if hasattr(step, "cost_figures") and step.cost_figures:
            for i, figure in enumerate(step.cost_figures):
                figure_id = f"Cost_{step_id}_{i}"
                figure_uri = f"sfpro:{figure_id}"
                ttl_star += f"{figure_uri} a sfpro:CostFigure ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(figure)} .\n"
                ttl_star += f"{step_uri} sfpro:hasCost {figure_uri} .\n"

        if hasattr(step, "latex_math") and step.latex_math:
            for i, math_item in enumerate(step.latex_math):
                math_id = f"Math_{step_id}_{i}"
                math_uri = f"sfpro:{math_id}"
                ttl_star += f"{math_uri} a sfpro:LatexMath ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(math_item)} .\n"
                ttl_star += f"{step_uri} sfpro:hasMath {math_uri} .\n"

        if hasattr(step, "metrics") and step.metrics:
            for i, metric in enumerate(step.metrics):
                metric_uri = f"sfpro:Metric_{step_id}_{i}"
                ttl_star += f"{metric_uri} a sfpro:PerformanceMetric ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(metric)} .\n"
                ttl_star += f"{step_uri} sfpro:hasMetric {metric_uri} .\n"

        if hasattr(step, "equipment") and step.equipment:
            for i, tool in enumerate(step.equipment):
                tool_uri = f"sfpro:Tool_{step_id}_{i}"
                ttl_star += f"{tool_uri} a sfpro:Equipment ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(tool)} .\n"
                ttl_star += f"{step_uri} sfpro:usesEquipment {tool_uri} .\n"

        if hasattr(step, "materials") and step.materials:
            for i, mat in enumerate(step.materials):
                mat_uri = f"sfpro:Material_{step_id}_{i}"
                ttl_star += f"{mat_uri} a sfpro:ChemicalMaterial ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(mat)} .\n"
                ttl_star += f"{step_uri} sfpro:consumesMaterial {mat_uri} .\n"

        if hasattr(step, "citations") and step.citations:
            for i, cit in enumerate(step.citations):
                cit_uri = f"sfpro:Source_{step_id}_{i}"
                ttl_star += f"{cit_uri} a sfpro:InformationSource ;\n"
                ttl_star += f"    rdfs:label {ox.Literal(cit)} .\n"
                ttl_star += f"{step_uri} sfpro:hasSource {cit_uri} .\n"

        if step.tables:
            for tidx, table in enumerate(step.tables):
                table_id = f"Table_{step_id}_{tidx}"
                table_uri = f"sfpro:{table_id}"
                ttl_star += f"{table_uri} a sfpro:DataTable ;\n"
                ttl_star += (
                    f"    rdfs:label {ox.Literal(f'Data Table in {step.label}')} .\n"
                )
                ttl_star += f"{step_uri} sfpro:hasDataTable {table_uri} .\n"

                for ridx, row in enumerate(table["rows"]):
                    row_uri = f"sfpro:{table_id}_Row_{ridx}"
                    ttl_star += f"{row_uri} a sfpro:TableRow .\n"
                    ttl_star += f"{table_uri} sfpro:hasRow {row_uri} .\n"
                    for col, val in row.items():
                        col_id = sanitize_id(col)
                        ttl_star += f"{row_uri} sfpro:{col_id} {ox.Literal(str(val))} .\n"

    try:
        store.load(ttl_star.encode("utf-8"), ox.RdfFormat.TURTLE)

        if verbose:
            print(ttl_star)
    except Exception as e:
        # Write to a temp file for debugging
        with open("error_debug.ttl", "w") as f:
            f.write(ttl_star)
        print(f"Error loading Turtle-star: {e}. See error_debug.ttl")
        raise

    # Return the constructed string instead of store.dump() to preserve namespaces/prefixes
    return ttl_star


def _TODO():
    import io

    output = io.BytesIO()
    store = ox.Store()
    store.dump(output, ox.RdfFormat.TURTLE, from_graph=ox.DefaultGraph())
    return output.getvalue().decode("utf-8")
