import xml.etree.ElementTree as ET
from pprint import pprint


def clean_junk_and_insert_root_tag():
    counter = 0
    with open('corpus.xml', 'w') as wf:
        wf.write('<root>\n')
        with open('./news_sohusite_xml_utf8.xml', 'r') as rf:
            for line in rf.readlines():
                wf.write(line.replace('', '').replace('&', '&amp;'))
                counter += 1
                if counter % 50000 == 0:
                    print(counter)
        wf.write('</root>')

def xml_to_json():
    tree = ET.parse('./corpus.xml')
    root = tree.getroot()

    output_list = []
    c = 0
    for doc in root.findall('doc'):
        output_dict = {}
        content = doc.find('content').text
        if content:
            output_dict['abstract'] = _strQ2B(doc.find('contenttitle').text.replace('　', ''))
            output_dict['article'] = _strQ2B(content.replace('　', '').replace('\n', ''))
            output_list.append(output_dict)
        else:
            print('沒東西')
        c += 1
        if c % 10 == 0:
            print(c)
        if c == 100:
            break
    pprint(output_list)

def _strQ2B(ustring):
    """把字符串全角转半角"""
    rstring = ''
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e: # 转完之后不是半角字符返回原来的字符
            rstring += uchar
        rstring += chr(inside_code)
    return rstring




if __name__ == '__main__':
    # clean_junk_and_insert_root_tag()
    xml_to_json()
