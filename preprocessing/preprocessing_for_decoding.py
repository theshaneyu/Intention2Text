from pprint import pprint
from opencc import OpenCC 
# import jieba
import json
import re
import random
from data_convert_example import text_to_binary
from tqdm import tqdm
from glob import glob


lock = True

class preprocessing(object):
    """docstring for preprocessing"""
    def __init__(self, vocab_path):
        # jieba custom setting.
        # jieba.initialize('jieba_dict/dict.txt.big')
        # jieba.load_userdict('jieba_dict/NameDict_Ch_v2')
        self.vocab_path = vocab_path

    def remove_date_at_beginning_of_context(self, data):
        """刪除context開頭的日期字串"""
        if '年' in data[:10] or '月' in data[:10] or '日' in data[:10]:
            return data[13:]
        return data

    def remove_and_convert_character(self, string):
        """功能：1) 只保留中文、逗點、句點、數字 2) 空格、半形逗點轉成逗點 3) 數字轉成#
                4) 清除連續的逗點、句點和#
        輸入：字串
        輸出：處理好的字串
        """
        clean_str = ''
        dirty_str = ''
        for ch in string:
            if u'\u4e00' <= ch <= u'\u9fff': # 如果是中文
                clean_str += ch
            else: # 不是中文
                if ch == '，' or ch == '。': # 如果是，或。就保留
                    clean_str += ch
                elif ch == ',': # 如果是半形的逗號，幫他轉成全型
                    clean_str += '，'
                elif ch == ' ':
                    clean_str += '，'
                elif ch.isdigit(): # 如果是數字，轉成#
                    clean_str += '#'
                else:
                    dirty_str += ch
        clean_str = self._remove_sequencial_char(clean_str)
        return clean_str
        

    def _remove_sequencial_char(self, string):
        """專門處理掉一連串的字元，例如逗號、句號、井字號"""
        previous_char = ''
        result_str = ''
        for c in string:
            if c == '，':
                if previous_char == '，' or previous_char == '。':
                    continue
                result_str += c
                previous_char = c
            elif c == '#':
                if previous_char == '#':
                    continue
                result_str += c
                previous_char = c
            elif c == '。':
                if previous_char == '。' or previous_char == '，':
                    continue
                result_str += c
                previous_char = c
            else:
                result_str += c
                previous_char = c
        return result_str

    def remove_comma_at_head_and_tail(self, string):
        """移除頭和尾的逗號"""
        if string[0] == '，':
            string = string[1:]
        if string[-1] == '，':
            string = string[:-1]
        return string

    def check_for_period(self, string):
        """確定結尾有沒有句號，如果沒有就加上去"""
        if string[-1] != '。':
            string += '。'
        return string

    def segmentation(self, string):
        return ' '.join(self._filter_blank(jieba.lcut(string, cut_all=False)))

    def _filter_blank(self, seg_list):
        """斷詞之後如果某個詞是空格，就丟掉"""
        clean_seg = []
        for word in seg_list:
            if word != ' ':
                clean_seg.append(word)
        return clean_seg

    def insert_tags(self, string):
        """把每個文章加上<s><p><d>標籤"""
        global lock
        sentence_list = string.split('。')
        final_output = ''
        for item in sentence_list: # 一個item是一個句子
            if item != '':
                final_output += self._sentence_tag(item)
        lock = True
        final_output = self._paragraph_tag(final_output)
        return final_output

    def _sentence_tag(self, sentence):
        """加上<s>標籤"""
        global lock
        if lock: # 第一行的<s>要加空白，其他不用
            lock = False
            return '<s> ' + sentence + '。 </s> '
        else:
            return '<s>' + sentence + '。 </s> '

    def _paragraph_tag(self, paragraph):
        """加上<p>標籤和<d>標籤"""
        return '<d> <p> ' + paragraph + '</p> </d>'

    def convert_UNK(self, data):
        word_pool = self._get_word_pool()
        out_list = []
        for item in data:
            out_dict = {}
            out_dict['context'] = self._convert_UNK_for_one_string(item['context'], word_pool)
            out_dict['discription'] = self._convert_UNK_for_one_string(item['discription'], word_pool)
            out_list.append(out_dict)
        return out_list

    def _get_word_pool(self):
        word_pool = set()
        with open(self.vocab_path, 'r') as rf:
            for line in rf.readlines():
                word_pool.add(line.replace('\n', '').split()[0])
        return word_pool

    def _convert_UNK_for_one_string(self, whole_str, word_pool):
        converted_word_list = []
        for word in whole_str.split(): # loop over整個文章
            if word in word_pool:
                converted_word_list.append(word)
            else:
                converted_word_list.append('<UNK>')
        return ' '.join(converted_word_list)

    def gen_input_format(self, data, out_path):
        """產生data_convert_example.py可以吃的檔案"""
        with open(out_path, 'w') as wf:
            for item in data:
                wf.write('discription=' + item['discription'])
                wf.write('\t')
                wf.write('context=' + item['context'])
                wf.write('\n')


    def go_through_processes_for_context(self, data):
        """走過context的所有清理步驟
        輸入：欲處理的字串
        輸出：處理好的字串
        """
        try:
            # 刪除context開頭的日期字串
            data = self.remove_date_at_beginning_of_context(data)
            # 1) 只保留中文、逗點、句點、數字 2) 空格、半形逗點轉成逗點 3) 數字轉成# 4) 清除連續的逗點、句點和#
            data = self.remove_and_convert_character(data)
            # 移除頭和尾的逗號
            data = self.remove_comma_at_head_and_tail(data)
            # 確定結尾有沒有句號，如果沒有就加上去
            data = self.check_for_period(data)
            # 斷詞
            data = self.segmentation(data)
            # 加入標籤
            data = self.insert_tags(data)
            return data
        except:
            return

    def go_through_processes_for_discription(self, data):
        try:
            data = self.remove_and_convert_character(data)
            data = self.remove_comma_at_head_and_tail(data)
            data = self.check_for_period(data)
            data = self.segmentation(data)
            data = self.insert_tags(data)
            return data
        except:
            return


    def gen_json(self, context, discription):
        output_list = []
        while True:
            content = dict()
            # context = input('[文章內容]\n')
            # discription = input('[文章標題]\n')
            # go_on = input('繼續輸入？(Y/N) ')
            content['context'] = context
            content['discription'] = discription
            output_list.append(content)
            # if go_on == 'N':
            #     break
            break
        return output_list

    def main(self):
        """
        這支程式用來產生decoding用的資料，可以在下方data更改輸入字串，會自動產生模型可以吃的input資料
        """
        data = self.gen_json(
            context='台灣買的到美國牛、澳洲牛，但就是買不到日本牛。 想請問是什麼原因禁止進口日本牛肉？ 還有是從什麼時候開始禁止進口日本牛的？',
            discription='為什麼台灣不能進口日本牛肉？')

        out_list = []
        for item in data:
            out_dict = {}
            context = self.go_through_processes_for_context(item['context'])
            discription = self.go_through_processes_for_discription(item['discription'])
            if context and discription:
                out_dict['context'] = context
                out_dict['discription'] = discription
                out_list.append(out_dict)
            else:
                print('無法處理的資料')

        data = self.convert_UNK(out_list) # 轉換UNK
        pprint(data)
        # 產生data_convert_example.py可以吃的格式的資料
        self.gen_input_format(data, '../yahoo_knowledge_data/decode/data_ready')
        # 產生input可以吃的資料格式
        text_to_binary('../yahoo_knowledge_data/decode/data_ready', '../yahoo_knowledge_data/decode/data')

def split_decode_data():
    file_num = 1
    with open('../yahoo_knowledge_data/decode/ver_2/readable_data_ready') as rf:
        for line in rf:
            with open('../yahoo_knowledge_data/decode/ver_2/dataset_ready/data_ready_' + str(file_num), 'w') as wf:
                wf.write(line.replace('\n', ''))
            file_num += 1
    file_num = 1
    for item in glob('../yahoo_knowledge_data/decode/ver_2/dataset_ready/*'):
        text_to_binary(item, '../yahoo_knowledge_data/decode/ver_2/dataset_input/data_' + str(file_num))
        file_num += 1


if __name__ == '__main__':
    # p = preprocessing('../yahoo_knowledge_data/vocab')
    # p.main()

    split_decode_data()

