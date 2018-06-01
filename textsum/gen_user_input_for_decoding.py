from pprint import pprint
from opencc import OpenCC 
import jieba
import json
import re
import random
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from data_convert_example import text_to_binary
import os
from collections import defaultdict


lock = True

class preprocessing(object):
    def __init__(self, vocab_path):
        jieba.initialize('preprocessing/jieba_dict/dict.txt.big')
        jieba.load_userdict('preprocessing/jieba_dict/NameDict_Ch_v2')
        self.word_pool = set()
        with open(vocab_path, 'r') as rf:
            for line in rf.readlines():
                self.word_pool.add(line.replace('\n', '').split()[0])

    def remove_date_at_beginning_of_context(self, data):
        """刪除context開頭的日期字串"""
        if '年' in data[:10] or '月' in data[:10] or '日' in data[:10]:
            return data[13:]
        return data

    def remove_and_convert_character(self, string):
        """功能：1) 只保留中文、逗點、句點、數字 2) 空格、半形逗點轉成逗點 3) 數字轉成#
                4) 清除連續的逗點、句點和#
        args: 字串
        returns: 處理好的字串
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
        clean_str = self._remove_sequential_char(clean_str)
        return clean_str
        

    def _remove_sequential_char(self, string):
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

    def remove_asking_for_points(self, string):
        """刪除description當中，結尾在求點數的部分"""
        if '急' in string or '#點' in string:
            string = string.replace('急', '').replace('#點', '')
        if '贈' in string:
            if '贈#' in string:
                string = string.replace('贈#', '')
            elif '贈點' in string:
                string = string.replace('贈點', '')
            elif '贈送' in string:
                string = string.replace('贈送', '')
            else:
                string = string.replace('贈', '')
        return string
        

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

    def filter_item_with_specific_words(self, data):
        """專門過濾掉一些含有特定關鍵字的item
        - description當中有「這」的item
        - description或context中含有「貸」的item
        """
        result_list = []
        for item in data:
            if not ('這' in item['description'] or
                    '貸' in item['description'] or
                    '貸' in item['context'] or
                    '補習' in item['description'] or
                    '補習' in item['context'] or
                    '家教' in item['description'] or
                    '家教' in item['context']):
                result_list.append(item)
        return result_list

    def remove_duplicate_context(self, data):
        """刪除重複的context，作法應該有錯，已廢棄"""
        unique_set = set()
        result_list = []
        for item in data:
            if item['context'] not in unique_set:
                unique_set.add(item['context'])
                result_list.append(item)
        return result_list

    def remove_duplicate(self, data):
        uni_set = set()
        dup_counter = 0
        result_list = []
        for item in data:
            item_tuple = self._gen_item_tuple(item)
            if item_tuple not in uni_set:
                result_list.append(item) 
                uni_set.add(item_tuple)
            else:    
                dup_counter += 1
        print('原本資料總共', len(data), '筆')
        print('總共重複item數目(description對應context為重複之item)：', dup_counter)
        print('最後版本的資料總共', len(result_list), '筆')
        return result_list

    def _gen_item_tuple(self, item):
        item_list = list()
        item_list.append(item['description'])
        item_list.append(item['context'])
        return tuple(item_list)

    def sample_data_to_see(self, data, num):
        # sample東西出來看
        for item in random.sample(data, num):
            print('[description]')
            print(item['description'])
            print('[context]')
            print(item['context'])
            print('-----------------------------------------------------')

    def convert_UNK(self, data):
        out_list = []
        for item in data:
            out_dict = {}
            out_dict['context'] = self._convert_UNK_for_one_string(item['context'])
            out_dict['description'] = self._convert_UNK_for_one_string(item['description'])
            out_list.append(out_dict)
        return out_list

    def _convert_UNK_for_one_string(self, whole_str):
        converted_word_list = []
        for word in whole_str.split(): # loop over整個文章
            if word in self.word_pool:
                converted_word_list.append(word)
            else:
                converted_word_list.append('<UNK>')
        return ' '.join(converted_word_list)

    def gen_input_format(self, data, out_path):
        """產生data_convert_example.py可以吃的檔案"""
        with open(out_path, 'w') as wf:
            for item in data:
                wf.write('description=' + item['description'])
                wf.write('\t')
                wf.write('context=' + item['context'])
                wf.write('\n')

    def go_through_processes_for_context(self, string):
        """走過context的所有清理步驟
        args: 欲處理的字串
        returns: 處理好的字串
        """
        try:
            # 刪除context開頭的日期字串
            string = self.remove_date_at_beginning_of_context(string) # context才需要
            # 1) 只保留中文、逗點、句點、數字 2) 空格、半形逗點轉成逗點 3) 數字轉成# 4) 清除連續的逗點、句點和#
            string = self.remove_and_convert_character(string)
            # 移除頭和尾的逗號
            string = self.remove_comma_at_head_and_tail(string)
            # 確定結尾有沒有句號，如果沒有就加上去
            string = self.check_for_period(string)
            # 斷詞
            string = self.segmentation(string)
            # 加入標籤
            string = self.insert_tags(string)
            return string
        except:
            return

    def go_through_processes_for_description(self, string):
        try:
            # 1) 只保留中文、逗點、句點、數字 2) 空格、半形逗點轉成逗點 3) 數字轉成# 4) 清除連續的逗點、句點和#
            string = self.remove_and_convert_character(string)
            # 刪除description當中，結尾在求點數的部分
            string = self.remove_asking_for_points(string) # description才需要
            # 移除頭和尾的逗號
            string = self.remove_comma_at_head_and_tail(string)
            # 確定結尾有沒有句號，如果沒有就加上去
            string = self.check_for_period(string)
            # 斷詞
            string = self.segmentation(string)
            # 加入標籤
            string = self.insert_tags(string)
            return string
        except:
            return


    def gen_data_dict(self, description, context):
        data_dict = {}
        data_dict['description'] = description
        data_dict['context'] = context
        return data_dict

    def get_data(self, description, context):
        data_dict = self.gen_data_dict(description=description, context=context)
        
        data = []
        context = self.go_through_processes_for_context(data_dict['context'])
        description = self.go_through_processes_for_description(data_dict['description'])
        if context and description:
            data_dict['context'] = context
            data_dict['description'] = description
            data.append(data_dict)
        else:
            print('無法處理的資料')
            return None

        data = self.convert_UNK(data) # 轉換UNK
        
        # 產生data_convert_example.py可以吃的格式的資料
        self.gen_input_format(data, './yahoo_knowledge_data/decode/decode_temp')
        # 產生input可以吃的資料格式
        text_to_binary('./yahoo_knowledge_data/decode/decode_temp', './yahoo_knowledge_data/decode/decode_data')
        return data[0]
        

if __name__ == '__main__':
    p = preprocessing('../yahoo_knowledge_data/vocab/ver_5/vocab')
    p.get_data(description='為什麼台灣不能進口日本牛肉？',
               context='台灣買的到美國牛、澳洲牛，但就是買不到日本牛。 想請問是什麼原因禁止進口日本牛肉？ 還有是從什麼時候開始禁止進口日本牛的？')

            

