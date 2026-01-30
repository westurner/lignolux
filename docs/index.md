# Sustainable Factory Documentation

Welcome to the Sustainable Factory project documentation.


## Sustainable Factory Project
```{toctree}
:maxdepth: 3
:caption: Table of Contents:

readme
paper.myst
schema
visualization
cli_reference
```

## Appendices

```{toctree}
tables_and_figures.myst
chats/index
chats/*.myst
```

## `sustainablefactory` Software 
This project uses MyST Markdown and JSON to capture and model sustainable process and product information and generates RDF-star linked data.

This system parses industrial process descriptions (like [paper.myst.md](paper.myst.md)) and converts them into a structured graph linked data representation
using the **Industrial Ontologies Foundry (IOF)** and sustainablefactory process schema.
[ [schema](schema.md) ]

- **Parser**: Extracts steps, properties, and Mermaid diagrams.
- **RDF Generator**: Produces Turtle-star (`.ttl`) with reified confidence metrics.
- **Visualizer**: Integrated Mermaid diagrams for process flow overview.

- See {ref}`readme`
