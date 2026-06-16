import zipfile
import xml.etree.ElementTree as ET
import sys

def extract_docx_text(docx_path, txt_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            paragraphs = []
            # Find all text elements under paragraph tags
            # Docx uses namespaces, so we check both with and without namespace tags
            p_tag = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'
            t_tag = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
            
            for paragraph in root.iter(p_tag):
                texts = [node.text for node in paragraph.iter(t_tag) if node.text]
                if texts:
                    paragraphs.append("".join(texts))
                else:
                    paragraphs.append("")
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(paragraphs))
            print(f"Successfully extracted {len(paragraphs)} paragraphs to {txt_path}")
            
    except Exception as e:
        print(f"Error extracting docx: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    docx_file = "/home/opendude/VMShare/GP Template DSAI Major edited - Copy.docx"
    output_file = "/home/opendude/Documents/Aman Reformed/Tests/results/template_extracted.txt"
    extract_docx_text(docx_file, output_file)
