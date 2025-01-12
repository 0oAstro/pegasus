import json
import csv

# Function to read a JSON file
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to read a CSV file
def read_csv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        data = [row for row in reader]
    return data

# Example usage
json_file_path = '/path/to/your/file.json'
csv_file_path = '/path/to/your/file.csv'

courses = read_json_file("all_courses_with_study_material.json")
courses_slots = read_csv_file("Courses_offered.csv")

for row in courses_slots:
    course_code = row[1][-6:]
    if course_code in courses:
        courses[course_code]['course_name'] = row[1][:-7].strip()
        courses[course_code]['slot'] = row[3]
        courses[course_code]['credit_structure'] = row[5]
        courses[course_code]['instructor'] = row[8].strip()
        courses[course_code]['instructor_mail'] = row[10]
        courses[course_code]['lec_time'] = row[13]
        courses[course_code]['tut_time'] = row[14]
        courses[course_code]['practical_time'] = row[16]
        courses[course_code]['vacancy'] = row[18]
        courses[course_code]['current_strength'] = row[19]


# Write the updated courses data to a new JSON file
with open('final_courses.json', 'w') as file:
    json.dump(courses, file, indent=2)