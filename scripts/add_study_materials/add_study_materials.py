import json

# Load JSON data from a file
with open('all_courses.json', 'r') as file:
    data = json.load(file)

# Print the loaded data
for i in data:
    data[i]["study_material"] = []
    try:
        f =open("{}.txt".format(i),"r")
        lines =f.readlines()
        
        for j in range(2,len(lines)-1):
            data[i]["study_material"].append(lines[j].rstrip('\n'))
    except:
        pass
with open("all_courses_with_study_material.json","w") as file:
    json.dump(data,file)