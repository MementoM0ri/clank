#!/usr/bin/env python3
"""
Integration script to select a PDF file and process it.
"""

from file_path_selector import main as select_file
from outcome import process_pdf


def main():
    """Main function to integrate file selection and PDF processing."""
    # Get PDF file path from user
    print("Please select a PDF file to process...")
    pdf_path = select_file()

    # Check if a file was selected
    if pdf_path:
        print(f"\nProcessing PDF: {pdf_path}")
        # Process the selected PDF
        process_pdf(pdf_path)
        print("\nPDF processing complete!")
    else:
        print("\nNo file was selected. Exiting.")


if __name__ == "__main__":
    main()
