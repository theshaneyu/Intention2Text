from pprint import pprint
from opencc import OpenCC 
import jieba
import json
import re
import random


"""
代辦事項：
- 移除注音符號
- 
"""
class preprocessing(object):
    """docstring for preprocessing"""
    def __init__(self):
        pass

    def function(self):
        pass

    def remove_date_at_beginning_of_context(self, data):
        """刪除context開頭的日期字串"""
        if '年' in data[:10] or '月' in data[:10] or '日' in data[:10]:
            return data[13:]
        return data

    def main(self):
        with open('../yahoo_knowledge_data/crawler_result.json') as rf:
            data = json.load(rf) # 90148筆
        c = 0
        for item in data:
            context = self.go_through_all_process(item['context'])
            # discription = self.go_through_all_process(item['discription'])
            c += 1
            if c == 200:
                break

    def go_through_all_process(self, data):
        """走過所有清理步驟
        輸入：字串
        輸出：處理好的字串
        """
        data = self.remove_date_at_beginning_of_context(data)
        data = self.simplified_to_tradition()

        print(data)
        print('-----------------------------------')


if __name__ == '__main__':
    p = preprocessing()
    p.main()