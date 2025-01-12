import PyPDF2
import re
import json

def read_pdf(pdf_path, debug=False):
    """Extract text from PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        if debug == True:
            with open('raw_pdf_text_cos.txt', 'w', encoding='utf-8') as f:
                f.write(text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        raise
    return text

def remove_page_numbers(text):
    """Remove page numbers from the raw PDF text."""
    return re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

def normalize_overlaps(text):
    """Normalize 'overlaps with:' to 'Overlaps with:' in the text."""
    text = re.sub(r'ov\nerlaps with[ ]:', 'Overlaps with:', text, flags=re.IGNORECASE)
    text = re.sub(r'C\nol', 'COL', text, flags=re.IGNORECASE)
    text = re.sub(r'EC 50', ',EC50', text, flags=re.IGNORECASE)
    text = re.sub(r' EC50', ',EC50', text, flags=re.IGNORECASE)
    return text

def extract_prerequisites(text):
    """Extract prerequisites from text."""
    text = text.replace('/', ',')
    text = text.replace('or', ',')
    text = text.replace('and', ',')
    prereq_match = re.search(r'Pre-requisite\(s\):\s*([^\n]+)', text)
    if prereq_match:
        prereqs = [p.strip() for p in prereq_match.group(1).split(',')]

        return prereqs
    return []
def extract_overlaps(text):
    """Extract overlapping courses."""
    text = text.replace('/', ',')
    overlap_match = re.search(r'Overlaps with:\s*([^\n]+)', text)
    if overlap_match:
        overlaps = []
        for overlap in overlap_match.group(1).replace('\n', '').split(','):
            overlap = overlap.strip()
            # Handle cases like XYZ123/ABC123
            if '/' in overlap:
                overlaps.extend([o.strip() for o in overlap.split('/')])
            # Handle cases like COL100 approx 80%
            elif 'approx' in overlap:
                overlaps.append(overlap.split('approx')[0].strip())
            else:
                overlaps.append(overlap)
        return overlaps
    return []

def parse_course_catalog(text):
    """Parse course catalog text and structure data."""
    catalog = {}
    current_course = None
    buffer = ""

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue


        # Detect course headers with codes, names, credits, and structure
        course_match = re.match(r'\b[A-Z]{3}\d{3}\b(?!.*Pre-requisite\(s\):)', line)
        if course_match:
            # Finalize the previous course
            if current_course:
                buffer = normalize_overlaps(buffer)
                prereqs = extract_prerequisites(buffer)
                overlaps = extract_overlaps(buffer)
                catalog[current_course]["prereqs"] = prereqs
                catalog[current_course]["overlaps"] = overlaps


                # description = re.sub(r'Pre-requisite\(s\):.*?\n', '', buffer)
                # description = re.sub(r'Overlaps with:.*?\n', '', description, flags=re.IGNORECASE | re.DOTALL)
                # Extract credits and credit structure
                credit_match = re.search(r'(\d+)\s*Credit[s]?\s*\((\d+-\d+-\d+)\)', buffer)
                if credit_match:
                    credits = int(credit_match.group(1))
                    credit_structure = credit_match.group(2)
                # Remove credits and credit structure from description
                # description = re.sub(r'\d+\s*Credits\s*\(\d+-\d+-\d+\)\n', '', description)
                catalog[current_course]["credits"] = credits
                catalog[current_course]["credit_structure"] = credit_structure
                catalog[current_course]["description"] = buffer.strip()

            # Start a new course
            current_course = course_match.group(0)
            if len(catalog.get(current_course, [])) == 0:
                # Initialize credits and credit structure as None
                credits = None
                credit_structure = None
                catalog[current_course] = {
                    "credits": credits,
                    "credit_structure": credit_structure,
                    "description": "",
                    "overlaps": [],
                    "prereqs": []
                }
                print(f"Current Course: {current_course}")
                buffer = ""
                continue

        # Add line to buffer for current course
        if current_course:
            buffer += line + "\n"

    # Finalize the last course
    if current_course:
        prereqs = extract_prerequisites(buffer)
        overlaps = extract_overlaps(buffer)
        catalog[current_course]["prerequisites"] = prereqs
        catalog[current_course]["overlaps"] = overlaps

        description = re.sub(r'Pre-requisite\(s\):.*?\n', '', buffer)
        description = re.sub(r'Overlaps with:.*?\n', '', description)
        catalog[current_course]["description"] = description.strip()

    return catalog

def main():
    pdf_path = 'Courses of Study 2023-24.pdf'
    try:
        print("Reading PDF file...")
        pdf_text = read_pdf(pdf_path, debug=True)

        print("Removing page numbers...")
        pdf_text = remove_page_numbers(pdf_text)

        print("Normalizing overlaps...")
        pdf_text = normalize_overlaps(pdf_text)

        print("Parsing course information...")
        parsed_catalog = parse_course_catalog(pdf_text)

        output_file = 'course_catalog.json'
        print(f"Writing output to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_catalog, f, indent=2, ensure_ascii=False)

        print("Processing completed successfully!")

    except FileNotFoundError:
        print(f"Error: Could not find the file {pdf_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
