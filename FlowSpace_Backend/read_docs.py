import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.XML(xml_content)
            
            # The namespace for Word XML
            namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Find all text nodes
            paragraphs = []
            for paragraph in tree.findall('.//w:p', namespace):
                texts = [node.text for node in paragraph.findall('.//w:t', namespace) if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
            
            return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error extracting from {docx_path}: {e}"

docs_dir = 'FlowSpace-documentation'
for file in os.listdir(docs_dir):
    if file.endswith('.docx'):
        path = os.path.join(docs_dir, file)
        text = extract_text_from_docx(path)
        out_path = path + '.txt'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Extracted {file} to {out_path}")
