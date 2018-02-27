"""一些corpus前處理的工作"""
import xml.etree.ElementTree as ET
from pprint import pprint
from opencc import OpenCC 
import jieba
import json

lock = True

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
    """
    1. 簡轉繁
    2. xml轉json
    3. 全形符號轉半形
    """
    openCC = OpenCC('s2t')  # 簡轉繁

    tree = ET.parse('./corpus/corpus.xml')
    root = tree.getroot()

    output_list = []
    c = 0
    nothing = 0
    for doc in root.findall('doc'):
        c += 1
        if c % 10000 == 0:
            print('----處理進度 %d----' % c)
        
        output_dict = {}
        content = doc.find('content').text
        title = doc.find('contenttitle').text
        if content and title:
            output_dict['abstract'] = openCC.convert(_full_to_half(title))
            output_dict['article'] = openCC.convert(_full_to_half(content))
            output_list.append(output_dict)
        else:
            nothing += 1
            if nothing % 1000 == 0:
                print('沒東西筆數 %d' % nothing)
    with open('corpus/corpus.json', 'w') as wf:
        json.dump(output_list, wf)

def _full_to_half(s):
    """全形符號轉半行"""
    n = []
    s = s.replace('\n', '').replace('·', '') # 清理不要的字元
    for char in s:
        if char == '，': # 如果是全形逗點，就不轉半形
            n.append(char)
            continue
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:
            num -= 0xfee0
        num = chr(num)
        n.append(num)
    return ''.join(n)

def segmentation():
    """斷詞"""
    jieba.load_userdict('./jieba_dict/udic_jieba_dict.txt')
    output_list = []
    c = 0
    with open('./corpus/corpus_no_seg.json', 'r') as rf:
        for item in json.load(rf):
            output_dict = {}
            output_dict['abstract'] = ' '.join(_filter_junk_word(jieba.lcut(item['abstract'], cut_all=False)))
            output_dict['article'] = ' '.join(_filter_junk_word(jieba.lcut(item['article'], cut_all=False)))
            output_list.append(output_dict)
            c += 1
            if c % 1000 == 0:
                print('完成文章數: %d' % c)
    with open('./corpus/corpus.json', 'w') as wf:
        json.dump(output_list, wf)

def _filter_junk_word(seg_list):
    """過濾斷詞後不要的東西"""
    clean_seg = []
    for word in seg_list:
        if word != ' ':
            clean_seg.append(word)
    return clean_seg

def add_tags():
    c = 0
    out_list = []
    with open('./corpus/corpus.json', 'r') as rf:
        for item in json.load(rf):
            output_dict = {}
            output_dict['abstract'] = _insert_tags(item['abstract'])
            output_dict['article'] = _insert_tags(item['article'])
            out_list.append(output_dict)
            c += 1
            if c % 5000 == 0:
                print(c)
    with open('./corpus/corpus_with_tags.json', 'w') as wf:
        json.dump(out_list, wf)

def _insert_tags(string):
    """把每個文章加上<s><p><d>標籤"""
    global lock
    sentence_list = string.split('。')
    # print(len(sentence_list))
    final_output = ''
    for item in sentence_list: # 一個item是一個句子
        if item != '':
            final_output += _sentence_tag(item)
    lock = True
    final_output = _paragraph_tag(final_output)
    return final_output

def _sentence_tag(sentence):
    """加上<s>標籤"""
    global lock
    if lock: # 第一行的<s>要加空白，其他不用
        lock = False
        return '<s> ' + sentence + '。 </s> '
    else:
        return '<s>' + sentence + '。 </s> '

def _paragraph_tag(paragraph):
    """加上<p>標籤和<d>標籤"""
    return '<d> <p> ' + paragraph + '</p> </d>'

def check_result():
    c = 0
    with open('./corpus/corpus_with_tags.json', 'r') as rf:
        for item in json.load(rf):
            print(item)
            c += 1
            if c == 100:
                break


if __name__ == '__main__':
    # clean_junk_and_insert_root_tag()
    # xml_to_json()
    # segmentation()
    # add_tags()
    check_result()
    