# Sustainable Factory Documentation

Welcome to the Sustainable Factory project documentation. This project uses MyST Markdown to capture process information and exports it to RDF-star for advanced manufacturing ontologies.

```{toctree}
:maxdepth: 2
:caption: Contents:

readme
paper.myst
schema
visualization
cli_reference
```

## Overview
This system parses industrial process descriptions (like [paper.myst.md](paper.myst.md)) and converts them into a structured graph linked data represention
using the **Industrial Ontologies Foundry (IOF)** and sustainablefactory process schema.
[ [schema](schema.md) ]

- **Parser**: Extracts steps, properties, and Mermaid diagrams.
- **RDF Generator**: Produces Turtle-star (`.ttl`) with reified confidence metrics.
- **Visualizer**: Integrated Mermaid diagrams for process flow overview.
