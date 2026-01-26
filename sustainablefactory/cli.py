import click
from pathlib import Path
from .parser import parse_myst_paper
from .rdf_gen import generate_rdf_star

@click.group()
def main():
    """Sustainable Factory CLI tool."""
    pass

@main.command()
@click.argument('input_file', type=click.Path(exists=True))
def parse(input_file):
    """Parse MyST markdown for process steps."""
    steps = parse_myst_paper(input_file)
    for step in steps:
        click.echo(f"Found Process: {step.label} ({step.id})")

@main.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='process_data.ttl', help='Output Turtle-star file.')
def export_rdf(input_file, output):
    """Export process steps to RDF-star format."""
    steps = parse_myst_paper(input_file)
    rdf_data = generate_rdf_star(steps, source_prefix=Path(input_file).stem)
    Path(output).write_text(rdf_data)
    click.echo(f"Exported RDF-star to {output}")

@main.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('--output', '-o', default='all_processes.ttl', help='Output Turtle-star file.')
def batch_export(input_dir, output):
    """Batch export all MyST files in a directory to RDF-star."""
    all_steps = []
    p = Path(input_dir)
    files = list(p.glob("*.md"))
    if p.is_file():
        files = [p]
        
    for file_path in files:
        click.echo(f"Processing {file_path.name}...")
        steps = parse_myst_paper(file_path)
        # We pass source_prefix to generate_rdf_star inside the loop if we want separate files,
        # but here we collect all steps.
        # So we should probably give each step a unique source-based ID.
        file_prefix = file_path.stem
        for step in steps:
            # We add a source reference or prefix to the step itself
            step.id = f"{file_prefix}_{step.id}"
            all_steps.append(step)
    
    # We can pass a general prefix or none for the whole collection
    rdf_data = generate_rdf_star(all_steps, source_prefix="batch")
    Path(output).write_text(rdf_data)
    click.echo(f"Exported {len(all_steps)} steps from {input_dir} to {output}")

@main.command()
def info():
    """Display project info."""
    click.echo("Sustainable Factory Process Modeling Tool")
    click.echo("Version: 0.1.0")

if __name__ == "__main__":
    main()
