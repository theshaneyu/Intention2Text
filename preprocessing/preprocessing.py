from pprint import pprint
from opencc import OpenCC 
import jieba
import json
import re
import random
from progress.bar import IncrementalBar # 顯示進度條
from gen_vocab import gen_vocab


lock = True

class preprocessing(object):
    """docstring for preprocessing"""
    def __init__(self):
        # jieba custom setting.
        jieba.initialize('jieba_dict/dict.txt.big')
        jieba.load_userdict('jieba_dict/NameDict_Ch_v2')

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
        # print(clean_str)
        # print('<>')
        # print('<>')
        # print('<>')
        # print(dirty_str)
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
            
            # print(data)
            # print('----------------------------------------------------------------------------')
            return data
        except:
            return


    def main(self):
        # with open('../yahoo_knowledge_data/crawler_result.json') as rf:
        #     data = json.load(rf) # 90148筆
        
        # # sample東西出來看
        # # data = random.sample(data, 50)

        # bar = IncrementalBar('Processing', max=90148)
        # out_list = []
        # for item in data:
        #     out_dict = {}
        #     context = self.go_through_processes_for_context(item['context'])
        #     discription = self.go_through_processes_for_discription(item['discription'])
        #     if context and discription: # 共有152個錯誤
        #         out_dict['context'] = context
        #         out_dict['discription'] = discription
        #         out_list.append(out_dict)
        #     bar.next()

        # with open('../yahoo_knowledge_data/preprocessed_result.json', 'w') as wf:
        #     json.dump(out_list, wf)

        
        """
        以上做完前處理，為了加速所以先存檔，接著下來用讀檔的比較快。之後也可以串起來一次做完。
        """

        with open('../yahoo_knowledge_data/preprocessed_result.json', 'r') as rf:
            data = json.load(rf) # 剩下89996筆

        # sample東西出來看
        # data = random.sample(data, 50)

        gen = gen_vocab()
        word_count = gen.get_word_count(data)
        print('字典共有', len(word_count), '個字')


        


                


if __name__ == '__main__':
    p = preprocessing()
    p.main()
