"""
Docstring for tests.test_aggregate_technical_data
"""

import argparse
import json
import logging
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock, mock_open

# Add project root to sys.path ensuring we can import from tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.aggregate_technical_data import (
    get_files,
    generate_report_content,
    generate_jsonld_content,
    main,
    setup_logging,
    ColorFormatter,
)


class TestAggregateTechnicalData(unittest.TestCase):
    @patch("tools.aggregate_technical_data.glob.glob")
    def test_get_files(self, mock_glob):
        # Setup mock to return different lists for .md and .json calls
        def side_effect(pattern):
            if pattern.endswith("*.md"):
                return ["data/file2.md", "data/file1.md"]
            elif pattern.endswith("*.json"):
                return ["data/file3.json"]
            return []

        mock_glob.side_effect = side_effect

        files = get_files("data")

        # Check that it returns sorted list of all files
        self.assertEqual(files, ["data/file1.md", "data/file2.md", "data/file3.json"])
        self.assertEqual(mock_glob.call_count, 2)

    @patch("tools.aggregate_technical_data.parse_and_extract_from_markdown")
    def test_generate_report_content(self, mock_parse):
        # Create mock steps
        step1 = MagicMock()
        step1.label = "Step 1"
        step1.cost_figures = ["$100"]
        step1.metrics = ["Efficiency: 90%"]
        step1.materials = ["Steel"]
        step1.equipment = ["Hammer"]
        step1.latex_math = ["E=mc^2"]
        step1.citations = ["Ref 1"]
        step1.tables = [{"headers": ["Col1"], "rows": [{"Col1": "Val1"}]}]

        step2 = MagicMock()
        step2.label = "File Summary"  # This should be skipped title printing
        # But we still process its attributes if any?
        # Code: "if step.label != "File Summary": output_handle.write(f"### {step.label}\n\n")"
        step2.cost_figures = []
        step2.metrics = []
        step2.materials = []
        step2.equipment = []
        step2.latex_math = []
        step2.citations = []
        step2.tables = []

        mock_parse.return_value = [step2, step1]

        output = StringIO()
        files = ["dummy/path/test_file.md"]

        generate_report_content(files, output)

        content = output.getvalue()

        # Verify Headers
        self.assertIn("# All Technical and Economic Data", content)
        self.assertIn("## test_file.md", content)

        # Verify Step 1 content
        self.assertIn("### Step 1", content)
        self.assertIn("#### Cost Figures", content)
        self.assertIn("`$100`", content)
        self.assertIn("#### Performance Metrics", content)
        self.assertIn("- Efficiency: 90%", content)
        self.assertIn("#### Materials & Chemicals", content)
        self.assertIn("`Steel`", content)
        self.assertIn("#### Equipment & Tools", content)
        self.assertIn("`Hammer`", content)
        self.assertIn("#### Mathematical Formulas", content)
        self.assertIn("- $E=mc^2$", content)
        self.assertIn("#### Citations & Sources", content)
        self.assertIn("- Ref 1", content)
        self.assertIn("#### Tables", content)
        self.assertIn("| Col1 |", content)
        self.assertIn("| Val1 |", content)

        # Verify File Summary label skipped
        self.assertNotIn("### File Summary", content)

    @patch("tools.aggregate_technical_data.parse_and_extract_from_markdown")
    def test_generate_report_content_no_steps(self, mock_parse):
        mock_parse.return_value = []
        output = StringIO()
        files = ["test.md"]

        generate_report_content(files, output)

        content = output.getvalue()
        self.assertNotIn("## test.md", content)

    @patch("tools.aggregate_technical_data.parse_and_extract_from_markdown")
    def test_generate_jsonld_content(self, mock_parse):
        step1 = MagicMock()
        step1.id = "http://example.org/step1"
        step1.label = "Step 1"
        step1.metrics = ["Efficiency: 90%"]
        step1.cost_figures = ["$100"]
        step1.materials = ["Steel"]
        step1.equipment = ["Hammer"]
        step1.latex_math = ["E=mc^2"]
        step1.citations = ["Ref 1"]

        mock_parse.return_value = [step1]

        output = StringIO()
        files = ["test.md"]

        generate_jsonld_content(files, output)

        content = output.getvalue()
        data = json.loads(content)

        self.assertIn("@context", data)
        self.assertIn("@graph", data)
        self.assertEqual(len(data["@graph"]), 1)
        node = data["@graph"][0]
        self.assertEqual(node["@id"], "http://example.org/step1")
        self.assertEqual(node["rdfs:label"], "Step 1")
        self.assertEqual(node["sf:metric"], ["Efficiency: 90%"])
        self.assertEqual(node["sf:costEstimate"], ["$100"])
        self.assertEqual(node["sf:usesMaterial"], ["Steel"])
        self.assertEqual(node["sf:usesEquipment"], ["Hammer"])
        self.assertEqual(node["sf:formula"], ["E=mc^2"])
        self.assertEqual(node["sf:citation"], ["Ref 1"])

    @patch("tools.aggregate_technical_data.get_files")
    @patch("tools.aggregate_technical_data.generate_report_content")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main(self, mock_args, mock_gen, mock_get_files):
        mock_args.return_value = argparse.Namespace(
            input_dir="data/chats",
            output="out.md",
            verbose=False,
            quiet=False,
            log_output=None,
        )
        mock_get_files.return_value = ["file1.md"]

        with patch("builtins.open", mock_open()) as m:
            main()

        mock_get_files.assert_called_once()
        mock_gen.assert_called_once()

    @patch("tools.aggregate_technical_data.logging.FileHandler")
    @patch("tools.aggregate_technical_data.logger.addHandler")
    def test_setup_logging(self, mock_add, mock_file):
        # 1. Default
        setup_logging(verbose=False, quiet=False)

        # 2. Quiet
        setup_logging(quiet=True)

        # 3. Verbose
        setup_logging(verbose=True)

        # 4. File
        mock_file_instance = MagicMock()
        mock_file.return_value = mock_file_instance
        setup_logging(log_file="/tmp/test.log")
        mock_file.assert_called_with("/tmp/test.log")

        # Test ColorFormatter
        formatter = ColorFormatter()
        rec = logging.LogRecord("n", logging.ERROR, "p", 1, "Error", (), None)
        res = formatter.format(rec)
        self.assertIn("\033[91m", res)


if __name__ == "__main__":
    unittest.main()
