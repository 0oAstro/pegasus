from bs4 import BeautifulSoup

# Input HTML file and output text file
html_file = "bsw.html"  # Replace with your HTML file name
output_file = "hyperlinks.txt"

# Read the HTML file
with open(html_file, "r", encoding="utf-8") as file:
    content = file.read()

# Parse the HTML content
soup = BeautifulSoup(content, "html.parser")

# Open the output file for writing
with open(output_file, "w", encoding="utf-8") as file:
    # Find all <a> tags with href attribute
    for link in soup.find_all("a", href=True):
        name = link.get_text(strip=True)  # Get link text (name)
        href = link["href"]               # Get href (URL)
        file.write(f"Name: {name}\nLink: {href}\n\n")  # Write to file

print(f"Hyperlinks have been saved to {output_file}")