import os
import glob
import json
import argparse
import logging
import sys
from sustainablefactory.parser import parse_and_extract_from_markdown

# Setup Logging
class ColorFormatter(logging.Formatter):
    RED = "\033[91m"
    RESET = "\033[0m"

    def format(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"{self.RED}{record.msg}{self.RESET}"
        return super().format(record)

logger = logging.getLogger("aggregate_technical_data")

def setup_logging(log_file=None, verbose=False, quiet=False):
    """Configure logging handlers."""
    logger.setLevel(logging.DEBUG)
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    if quiet:
        ch.setLevel(logging.ERROR)
    elif verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    
    ch.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)

    # File Handler
    if log_file:
        log_path = os.path.dirname(log_file)
        if log_path:
            os.makedirs(log_path, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

def main():
    parser = argparse.ArgumentParser(
        description="Aggregate technical and economic data from (MyST) Markdown files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--input-dir", default="data/chats", help="Directory containing input .md and .json files")
    parser.add_argument("--output", default="docs/tables_and_figures.myst.md", help="Output file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-q", "--quiet", action="store_true", help="Decrease output verbosity")
    parser.add_argument("--log-output", help="Path to log file")
    args = parser.parse_args()

    setup_logging(log_file=args.log_output, verbose=args.verbose, quiet=args.quiet)

    files = glob.glob(os.path.join(args.input_dir, "*.md")) + glob.glob(os.path.join(args.input_dir, "*.json"))
    files = sorted(files)
    
    logger.info(f"Found {len(files)} files in {args.input_dir}")
    for f_path in files:
        logger.debug(f"Found file: {f_path}")

    output_path = args.output
    
    with open(output_path, "w") as f:
        f.write("# All Technical and Economic Data\n\n")
        f.write("This document contains tables, cost figures, metrics, materials, equipment, and citations extracted from the workspace.\n\n")
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            logger.info(f"Processing {file_name}...")
            
            steps = parse_and_extract_from_markdown(file_path)
            if not steps:
                logger.warning(f"No steps found in {file_name}")
                continue
                
            f.write(f"## {file_name}\n\n")
            
            for step in steps:
                if step.label != "File Summary":
                    f.write(f"### {step.label}\n\n")
                
                if step.cost_figures:
                    f.write("#### Cost Figures\n\n")
                    f.write(", ".join([f"`{c}`" for c in step.cost_figures]) + "\n\n")
                
                if hasattr(step, 'metrics') and step.metrics:
                    f.write("#### Performance Metrics\n\n")
                    for m in step.metrics:
                        f.write(f"- {m}\n")
                    f.write("\n")

                if hasattr(step, 'materials') and step.materials:
                    f.write("#### Materials & Chemicals\n\n")
                    f.write(", ".join([f"`{m}`" for m in step.materials]) + "\n\n")

                if hasattr(step, 'equipment') and step.equipment:
                    f.write("#### Equipment & Tools\n\n")
                    f.write(", ".join([f"`{e}`" for e in step.equipment]) + "\n\n")

                if hasattr(step, 'latex_math') and step.latex_math:
                    f.write("#### Mathematical Formulas\n\n")
                    for m in step.latex_math:
                        f.write(f"- ${m}$\n")
                    f.write("\n")

                if hasattr(step, 'citations') and step.citations:
                    f.write("#### Citations & Sources\n\n")
                    for c in step.citations:
                        f.write(f"- {c}\n")
                    f.write("\n")

                if step.tables:
                    f.write("#### Tables\n\n")
                    for table in step.tables:
                        headers = table['headers']
                        f.write("| " + " | ".join(headers) + " |\n")
                        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                        for row in table['rows']:
                            f.write("| " + " | ".join([row.get(h, "") for h in headers]) + " |\n")
                        f.write("\n\n")
            
            f.write("---\n\n")

if __name__ == "__main__":
    main()
