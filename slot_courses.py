import json
import re
from PyPDF2 import PdfReader

def extract_course_data_from_pdf(pdf_path):
    course_data = {}

    # Load the PDF
    reader = PdfReader(pdf_path)
    text = "".join(page.extract_text() for page in reader.pages)

    # Split the text by lines
    lines = text.splitlines()

    # Buffer to collect multi-line entries
    buffer = []

    for line in lines:
        # Check for lines that continue the previous entry
        if re.match(r"\s*[A-Za-z0-9._%+-]+@[a-zA-Z.-]+", line):
            if buffer:
                buffer[-1] += " " + line.strip()
        elif re.match(r".*-\s*[A-Z]{3}\d{3}\s+[A-Z]+\s+\d\.\d-\d\.\d-\d\.\d.*", line):
            buffer.append(line.strip())

    # Process buffered lines
    for entry in buffer:
        match = re.match(
            r"(?P<course_name>.+?)-(?P<course_code>[A-Z]{3}\d{3})\s+(?P<slot>[A-Z]+)\s+(?P<units>\d\.\d-\d\.\d-\d\.\d)\s+(?P<instructor>[A-Za-z .'-]+)\s+(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z.-]+)\s+(?P<vacancy>\d+)\s+(?P<current_strength>\d+)",
            entry
        )
        if match:
            course_code = match.group("course_code")
            course_data[course_code] = {
                "name": match.group("course_name").strip(),
                "slot": match.group("slot"),
                "units": match.group("units"),
                "instructor": match.group("instructor").strip(),
                "email": match.group("email"),
                "vacancy": int(match.group("vacancy")),
                "current_strength": int(match.group("current_strength"))
            }

    return course_data

def update_json_with_course_data(json_path, course_data):
    with open(json_path, 'r') as f:
        catalog = json.load(f)

    for course in catalog.get("courses", []):
        course_code = course.get("code")
        if course_code in course_data:
            course.update(course_data[course_code])

    with open(json_path, 'w') as f:
        json.dump(catalog, f, indent=4)

pdf_path = "Courses_Offered.pdf"  # Replace with your PDF file path
json_path = "course_catalog.json"  # Replace with your JSON file path

course_data = extract_course_data_from_pdf(pdf_path)
update_json_with_course_data(json_path, course_data)

print(f"Successfully updated {json_path} with data from {pdf_path}.")
