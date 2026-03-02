#!/usr/bin/env python3
"""
Medical Form PDF Generator

This script fills out the medical form HTML template with provided data
and converts it to a PDF file.

Requirements:
    pip install weasyprint

Usage:
    from fill_medical_form import MedicalFormGenerator

    generator = MedicalFormGenerator()
    generator.fill_form(
        date="03/01/2026",
        patient_name="John Doe",
        injury_date="02/15/2026",
        review_time_minutes="50",
        validated_tests="MRI scan results..."
    )
    generator.save_pdf("output.pdf")
"""

from pathlib import Path
from datetime import datetime
from weasyprint import HTML, CSS
from typing import Optional, Dict, Any
import random


class MedicalFormGenerator:

    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the form generator.

        Args:
            template_path: Path to HTML template file. If None, uses default.
        """
        if template_path is None:
            template_path = Path(__file__).parent / "medical_form_template.html"
        else:
            template_path = Path(template_path)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()

        self.filled_html = None

    def fill_form(
        self,
        date: str = "",
        patient_name: str = "",
        injury_date: str = "",
        review_time_minutes: str = str(random.randrange(30, 50, 3)),
        validated_tests: str = ""
    ) -> str:
        """
        Fill the form with provided data.

        Args:
            date: Date of the form (e.g., "03/01/2026")
            patient_name: Full name of the patient
            injury_date: Date when injury occurred
            review_time_minutes: Time spent reviewing (default "50")
            validated_tests: Content for validated tests section

        Returns:
            Filled HTML string
        """
        # Replace placeholders with actual values
        html = self.template
        html = html.replace("{{date}}", date)
        html = html.replace("{{patient_name}}", patient_name)
        html = html.replace("{{injury_date}}", injury_date)
        html = html.replace("{{review_time_minutes}}", review_time_minutes)
        html = html.replace("{{validated_tests}}", validated_tests)

        self.filled_html = html
        return html

    def fill_form_from_extract(
        self,
        extract_data: Dict[str, Any],
        review_time_minutes: str = str(random.randrange(30, 50, 3)),
        validated_tests: str = ""
    ) -> str:
        """
        Fill the form using output from extract_pdf_info function.

        Args:
            extract_data: Dictionary from extract_pdf_info containing:
                - patient_name: Name of the patient
                - doi_date: Date of injury
                - current_date: Current date on the page
                - table_of_contents: List of test names
                - text: Full text extracted
            review_time_minutes: Time spent reviewing (default "50")
            validated_tests: Content for validated tests section. If empty,
                           will be automatically generated from table_of_contents

        Returns:
            Filled HTML string
        """
        # If validated_tests is empty, generate from table_of_contents
        if not validated_tests and extract_data.get('table_of_contents'):
            test_names = [item['title'] for item in extract_data['table_of_contents']]
            validated_tests = '<br>\n'.join(test_names)

        return self.fill_form(
            date=extract_data.get('current_date', ''),
            patient_name=extract_data.get('patient_name', ''),
            injury_date=extract_data.get('doi_date', ''),
            review_time_minutes=review_time_minutes,
            validated_tests=validated_tests
        )

    def save_html(self, output_path: str) -> None:
        """
        Save the filled HTML to a file.

        Args:
            output_path: Path where HTML file should be saved
        """
        if self.filled_html is None:
            raise ValueError("Form must be filled before saving. Call fill_form() first.")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.filled_html)

        print(f"HTML saved to: {output_path}")

    def save_pdf(self, output_path: str) -> None:
        """
        Save the filled form as a PDF file.

        Args:
            output_path: Path where PDF file should be saved
        """
        if self.filled_html is None:
            raise ValueError("Form must be filled before saving. Call fill_form() first.")

        # Convert HTML to PDF
        HTML(string=self.filled_html).write_pdf(output_path)
        print(f"PDF saved to: {output_path}")

    def preview_html(self) -> str:
        """
        Get the filled HTML for preview.

        Returns:
            Filled HTML string
        """
        if self.filled_html is None:
            raise ValueError("Form must be filled before preview. Call fill_form() first.")

        return self.filled_html


def main():
    """Example usage of the MedicalFormGenerator."""
    import sys

    # Check if using extract_pdf_info integration
    if len(sys.argv) > 1 and sys.argv[1] == "--from-extract":
        # Example showing integration with extract_pdf_info
        from uniter import extract_pdf_info

        if len(sys.argv) < 3:
            print("Usage: python fill_medical_form.py --from-extract <pdf_file>")
            print("\nThis will automatically extract:")
            print("  - Patient name")
            print("  - Date of injury")
            print("  - Current date")
            print("  - Validated test names from table of contents")
            sys.exit(1)

        pdf_file = sys.argv[2]

        # Extract info from PDF
        print(f"Extracting info from: {pdf_file}")
        extract_data = extract_pdf_info(pdf_file)

        # Display extracted information
        print(f"\nExtracted Information:")
        print(f"  Patient Name: {extract_data.get('patient_name', 'N/A')}")
        print(f"  Date of Injury: {extract_data.get('doi_date', 'N/A')}")
        print(f"  Current Date: {extract_data.get('current_date', 'N/A')}")
        print(f"  Validated Tests: {len(extract_data.get('table_of_contents', []))} tests found")

        # Create generator and fill form (automatically uses table_of_contents for validated_tests)
        generator = MedicalFormGenerator()
        generator.fill_form_from_extract(
            extract_data=extract_data,
            review_time_minutes= str(random.randrange(30, 50, 3))
        )

        # Generate output filename
        patient_name = extract_data.get('patient_name', 'output')
        output_name = f"medical_form_{patient_name.replace(' ', '_')}.pdf"
        generator.save_pdf(output_name)
        generator.save_html(output_name.replace('.pdf', '.html'))
        print(f"\nGenerated: {output_name}")

    else:
        # Original example with manual data
        generator = MedicalFormGenerator()

        # Fill the form with sample data
        generator.fill_form(
            date="03/01/2026",
            patient_name="John Doe",
            injury_date="02/15/2026",
            review_time_minutes="50",
            validated_tests="MRI Cervical Spine, X-Ray Lumbar Spine, EMG/NCV Study"
        )

        # Save as PDF
        generator.save_pdf("medical_form_output.pdf")

        # Optionally save HTML for debugging
        generator.save_html("medical_form_output.html")


if __name__ == "__main__":
    main()
