from pprint import pprint
from opencc import OpenCC 
import jieba
import json
import re
import random


"""
筆記：
只保留中文字，除了中文字之外，保留逗號，句號。
空格、半形逗號換成逗號
接著處理連續問號的問題

"""
class preprocessing(object):
    """docstring for preprocessing"""
    def __init__(self):
        pass

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
        print(clean_str)
        print('<>')
        print('<>')
        print('<>')
        print(dirty_str)
        

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







    def go_through_all_process(self, data):
        """走過所有清理步驟
        輸入：字串
        輸出：處理好的字串
        """
        # 砍掉context開頭的日期部分
        data = self.remove_date_at_beginning_of_context(data)
        # 砍掉一些不要的字元
        data = self.remove_and_convert_character(data)

        print()
        print('---------------------------------------------------------------------------')
        print()


    def main(self):
        with open('../yahoo_knowledge_data/crawler_result.json') as rf:
            data = json.load(rf) # 90148筆

        # sample東西出來看
        data = random.sample(data, 100)
        
        for item in data:
            context = self.go_through_all_process(item['context'])
            # discription = self.go_through_all_process(item['discription'])


if __name__ == '__main__':
    p = preprocessing()
    p.main()
