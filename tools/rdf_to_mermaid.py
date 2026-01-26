import pyoxigraph as ox
import sys
from pathlib import Path

def ttl_to_mermaid(ttl_path):
    store = ox.Store()
    with open(ttl_path, "rb") as f:
        store.load(f, ox.RdfFormat.TURTLE)
    
    # Query for precede relations
    query = """
    PREFIX iof: <https://spec.industrialontologies.org/ontology/core/Core/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?s ?s_label ?o ?o_label WHERE {
        ?s iof:precedes ?o .
        ?s rdfs:label ?s_label .
        ?o rdfs:label ?o_label .
    }
    """
    
    results = store.query(query)
    
    mermaid = "graph TD\n"
    for row in results:
        # Simple ID generation from URI
        s_id = row["s"].value.split("#")[-1].split("/")[-1]
        o_id = row["o"].value.split("#")[-1].split("/")[-1]
        s_label = row["s_label"].value
        o_label = row["o_label"].value
        
        mermaid += f'    {s_id}["{s_label}"] --> {o_id}["{o_label}"]\n'
    
    return mermaid

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rdf_to_mermaid.py <input.ttl>")
        sys.exit(1)
    
    print(ttl_to_mermaid(sys.argv[1]))
