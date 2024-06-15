import os, xml.etree.ElementTree as ET

root = ET.Element("library")

books = [
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "edition": "First", "publication_year": "1951"},
    {"title": "1984", "author": "George Orwell", "edition": "Second", "publication_year": "1949"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "edition": "Third", "publication_year": "1960"}
]

for book in books:
    book_element = ET.SubElement(root, "book", {
        "edition": book["edition"],
        "publication_year": book["publication_year"]
    })
    title_element = ET.SubElement(book_element, "title")
    title_element.text = book['title']
    author_element = ET.SubElement(book_element, "author")
    author_element.text = book['author']

# Convert the tree to a string
tree = ET.ElementTree(root)
tree.write("library.xml")

# Pretty print XML for viewing
from xml.dom.minidom import parseString
xmlstr = parseString(ET.tostring(root)).toprettyxml(indent="   ")
print(xmlstr)

##### 

xml_data = """
<library>
    <book title="The Catcher in the Rye" author="J.D. Salinger" edition="First" publication_year="1951"/>
    <book title="1984" author="George Orwell" edition="First" publication_year="1949"/>
    <book title="To Kill a Mockingbird" author="Harper Lee" edition="Third" publication_year="1960"/>
</library>
"""

# Parse the XML data
root = ET.fromstring(xml_data)

# Find the book with the title "1984"
book = root.find(".//book[@title='1984']")

if book is not None:
    # Change the edition attribute
    book.set("edition", "Revised Edition")

    # If you want to add new attributes or modify child elements, do so here
    # For example, changing the author:
    # book.set("author", "New Author Name")

    # Print out the modified XML
    xmlstr = ET.tostring(root, encoding='unicode')
    print(xmlstr)
else:
    print("Book not found")


import xml.etree.ElementTree as ET

# Create the root element
root = ET.Element("library")

# Add multiple books using SubElement
ET.SubElement(root, "book", {"title": "Book One", "author": "Author A"})
ET.SubElement(root, "book", {"title": "Book Two", "author": "Author B"})

# Print the resulting XML
tree = ET.ElementTree(root)
xmlstr = ET.tostring(root, encoding='unicode')
print(xmlstr)