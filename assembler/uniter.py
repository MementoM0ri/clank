import os
import subprocess
import re
from PyPDF2 import PdfReader
from datetime import datetime


def extract_pdf_info(pdf_file):
    """
    Extract patient name, DOI date, current date, and table of contents from a PDF file.

    Args:
        pdf_file: Path to the PDF file

    Returns:
        Dictionary containing:
        - patient_name: Name of the patient (if found)
        - doi_date: Date of injury (if found)
        - current_date: Current date on the page (if found)
        - table_of_contents: List of TOC entries (if found)
        - text: Full text extracted from the PDF
    """
    result = {
        'patient_name': None,
        'doi_date': None,
        'current_date': None,
        'table_of_contents': [],
        'text': ''
    }

    try:
        reader = PdfReader(pdf_file)
        text = ''

        # Extract text from all pages
        for page in reader.pages:
            text += page.extract_text() + '\n'

        result['text'] = text

        # Pattern for patient name (adjust based on your PDF format)
        # Common patterns: "Patient Name:", "Name:", "Patient:"
        # Updated to handle names with 2+ words, hyphens, apostrophes, internal capitals (McDonald, O'Brien, etc.)
        # Stops at newlines or other delimiters to avoid over-capturing
        name_patterns = [
            r"Patient Name[:\s]+([A-Z][a-zA-Z]+(?:[-' ][A-Z][a-zA-Z]+)+)(?=\s*[\n,;]|$)",
            r"Name[:\s]+([A-Z][a-zA-Z]+(?:[-' ][A-Z][a-zA-Z]+)+)(?=\s*[\n,;]|$)",
            r"Patient[:\s]+([A-Z][a-zA-Z]+(?:[-' ][A-Z][a-zA-Z]+)+)(?=\s*[\n,;]|$)"
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                result['patient_name'] = match.group(1).strip()
                break

        # Pattern for DOI (Date of Injury)
        # Common patterns: "DOI:", "Date of Injury:", various date formats
        doi_patterns = [
            r"DOI[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Date of Injury[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Injury Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"DOI[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})"
        ]

        for pattern in doi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['doi_date'] = match.group(1).strip()
                break

        # Pattern for current date
        # Common patterns: "Date:", current date at top of page
        date_patterns = [
            r"Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Current[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})"
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                result['current_date'] = match.group(1).strip()
                break

        # Extract table of contents from PDF metadata/bookmarks
        toc_entries = []
        if hasattr(reader, 'outline') and reader.outline:
            def extract_outline(outline, level=0):
                entries = []
                for item in outline:
                    if isinstance(item, list):
                        entries.extend(extract_outline(item, level + 1))
                    else:
                        if hasattr(item, 'title'):
                            entry = {'title': item.title, 'level': level}
                            if hasattr(item, 'page'):
                                try:
                                    page_num = reader.pages.index(item.page) + 1
                                    entry['page'] = page_num
                                except:
                                    pass
                            entries.append(entry)
                return entries

            toc_entries = extract_outline(reader.outline)

        result['table_of_contents'] = toc_entries

    except Exception as e:
        print(f"Error reading PDF {pdf_file}: {e}")

    return result


def get_all_pdfs(folder="."):
    """
    Locate all PDF files in the specified folder and return them as an array.

    Args:
        folder: Folder to scan for PDF files (default: ".")

    Returns:
        List of PDF filenames found in the folder
    """
    pdf_files = []

    for filename in os.listdir(folder):
        if filename.lower().endswith('.pdf'):
            pdf_files.append(filename)

    return pdf_files


def unite_pdfs(year, month, folder="."):
    """
    Process all PDFs in folder: extract info, generate medical forms, and combine with headless.pdf.

    Args:
        year: Year as string or int (e.g., "2026" or 2026)
        month: Month as string or int (e.g., "02" or 2)
        folder: Folder to scan for PDF files (default: ".")
    """
    from fill_medical_form import MedicalFormGenerator

    # Ensure month is zero-padded
    month_str = str(month).zfill(2)
    year_str = str(year)

    # Get all PDF files in folder
    pdf_files = []
    for filename in os.listdir(folder):
        if filename.lower().endswith('.pdf') and filename not in ['headless.pdf', 'Correct.pdf']:
            pdf_files.append(filename)

    if not pdf_files:
        print(f"No PDF files found in folder: {folder}")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process\n")

    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder, pdf_file)
        print(f"Processing: {pdf_file}")

        # Extract info from PDF
        extract_data = extract_pdf_info(pdf_path)

        patient_name = extract_data.get('patient_name')
        if not patient_name:
            print(f"  ⚠ Warning: Could not extract patient name from {pdf_file}, skipping...")
            continue

        # Generate medical form frontpage
        print(f"  → Generating medical form for {patient_name}...")
        generator = MedicalFormGenerator()
        generator.fill_form_from_extract(extract_data=extract_data)

        # Save frontpage as temporary PDF
        frontpage_pdf = f"frontpage_{patient_name.replace(' ', '_')}.pdf"
        frontpage_path = os.path.join(folder, frontpage_pdf)
        generator.save_pdf(frontpage_path)

        # Combine: frontpage.pdf + headless.pdf + original.pdf
        current_date = extract_data.get('current_date')
        if not current_date:
            print(f"  ⚠ Warning: Could not extract current_date from {pdf_file}, skipping...")
            continue

        # Parse date from MM/DD/YYYY to YYYY-MM-DD format
        try:
            parts = current_date.replace('/', '-').split('-')
            if len(parts) == 3:
                month, day, year = parts
                if len(year) == 2:
                    year = '20' + year
                current_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            # If parsing fails, use as-is but replace slashes
            current_date = current_date.replace('/', '-')

        final_name = f"{current_date}-{patient_name.replace(' ', '_')}-ProlongedEval.pdf"
        final_path = os.path.join(folder, final_name)

        # headless.pdf is located in the same directory as uniter.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        headless_path = os.path.join(script_dir, 'headless.pdf')

        # Check if headless.pdf exists
        if not os.path.exists(headless_path):
            print(f"  ⚠ Warning: headless.pdf not found, combining frontpage + original only")
            input_files = [frontpage_path, pdf_path]
        else:
            input_files = [frontpage_path, headless_path, pdf_path]

        print(f"  → Combining PDFs into: {final_name}")
        cmd = ["pdfunite"] + input_files + [final_path]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ Successfully created: {final_name}\n")

            # Clean up temporary frontpage
            if os.path.exists(frontpage_path):
                os.remove(frontpage_path)
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error combining PDFs: {e}")
            print(f"    {e.stderr.decode() if e.stderr else ''}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--extract":
            # Extract info from a single PDF
            if len(sys.argv) < 3:
                print("Usage: python uniter.py --extract <pdf_file>")
                sys.exit(1)
            pdf_file = sys.argv[2]
            info = extract_pdf_info(pdf_file)
        elif sys.argv[1] == "--process":
            # Process PDFs in a folder
            folder = sys.argv[2] if len(sys.argv) > 2 else "."
            year = int(sys.argv[3]) if len(sys.argv) > 3 else 2026
            month = int(sys.argv[4]) if len(sys.argv) > 4 else 2

            print(f"Processing PDFs in folder: {folder}")
            print(f"Year: {year}, Month: {month}\n")
            unite_pdfs(year=year, month=month, folder=folder)
        else:
            # Assume it's a folder path
            folder = sys.argv[1]
            year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
            month = int(sys.argv[3]) if len(sys.argv) > 3 else 2

            print(f"Processing PDFs in folder: {folder}")
            print(f"Year: {year}, Month: {month}\n")
            unite_pdfs(year=year, month=month, folder=folder)
    else:
        # Default behavior - process current directory
        print("Usage:")
        print("  python uniter.py <folder> [year] [month]")
        print("  python uniter.py --process <folder> [year] [month]")
        print("  python uniter.py --extract <pdf_file>")
        print("\nExample:")
        print("  python uniter.py . 2026 3")
        print("\nProcessing current directory with defaults (year=2026, month=2)...\n")
        unite_pdfs(year=2026, month=2)

