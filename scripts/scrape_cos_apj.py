import json
f=open("CoursesofStudy.txt","r")
d=f.readlines()
dic={}
prev="start"
dic[prev]=""
credit={}
prereq={}
overlaps={}
bswlink={}
coursewebpage={}
for i in range(0,len(d)):
    line=d[i]
    flag=0
    dat=line.split()
    if(len(dat[0])==6):
       if(dat[0][0]>='A' and dat[0][0]<='Z' and dat[0][1]>='A' and dat[0][1]<='Z' and dat[0][2]>='A' and dat[0][2]<='Z' and dat[0][3]>='0' and dat[0][3]<='9' and dat[0][4]>='0' and dat[0][4]<='9' and dat[0][5]>='0' and dat[0][5]<='9'):
          prev=dat[0]
          dic[prev]=""
          prereq[prev]=[]
          overlaps[prev]=[]
    for j in range(0,len(dat)):
              if(dat[j]=='Credits' or dat[j]=='Credit'):
                  x=""
                  for k in range(0,len(dat[j-1])):
                      if((dat[j-1][k]>='0' and dat[j-1][k]<='9') or dat[j-1][k]=='.'):
                          x+=dat[j-1][k]
                  flag=1
                  credit[prev]=x
                  continue
    y=line.split()
    u=""
    if(flag==1):
       continue
    if(y[0]=='Pre-requisite(s):'):
       for e in range(1,len(y)):
           if(len(y[e])==6):
              prereq[prev].append(y[e])
       continue
    if(y[0]=='overlaps'):
        for e in range(2,len(y)):
            overlaps[prev].append(y[e])
        continue
    dic[prev]+=line
all_courses = {}
for course_code in dic.keys():
    if(len(course_code)!=6):
        continue
    all_courses[course_code] = {
        "credits": credit.get(course_code, ""),
        "prerequisites": prereq.get(course_code, []),
        "overlaps": overlaps.get(course_code, []),
        "data": dic.get(course_code, "").strip()
    }

# Convert the entire dictionary to JSON
all_courses_json = json.dumps(all_courses, indent=4)

# Save JSON to a file (optional)
with open("all_courses.json", "w") as file:
    file.write(all_courses_json)