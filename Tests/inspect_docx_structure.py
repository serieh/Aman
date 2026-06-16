import zipfile
import xml.etree.ElementTree as ET
import sys

def inspect_docx(docx_path):
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            p_tag = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'
            t_tag = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
            pPr_tag = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr'
            pStyle_tag = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle'
            val_attr = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'
            
            headings = []
            paragraphs_count = 0
            
            for p_idx, paragraph in enumerate(root.iter(p_tag)):
                paragraphs_count += 1
                style = None
                pPr = paragraph.find(pPr_tag)
                if pPr is not None:
                    pStyle = pPr.find(pStyle_tag)
                    if pStyle is not None:
                        style = pStyle.get(val_attr)
                
                texts = [node.text for node in paragraph.iter(t_tag) if node.text]
                p_text = "".join(texts).strip()
                
                if p_text and (style or p_text.startswith("Chapter") or p_text.startswith("5.") or p_text.startswith("6.") or p_text.startswith("7.")):
                    headings.append((p_idx, style, p_text[:100]))
            
            print(f"Total paragraphs parsed: {paragraphs_count}")
            print(f"Total headings/milestones identified: {len(headings)}")
            for idx, style, text in headings[:50]:
                print(f"  Line {idx} | Style: {style} | Text: {text}")
                
            if len(headings) > 50:
                print(f"  ... and {len(headings) - 50} more headings.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    inspect_docx("/home/opendude/VMShare/GP Template DSAI Major edited - Copy.docx")
