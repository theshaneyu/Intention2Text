import json
from pprint import pprint
from opencc import OpenCC
import random


class process_crawler_result(object):
    """專門拿來把爬蟲的結果處理成preprocessing.py可以吃的格式"""
    def __init__(self):
        pass

    def checking(self):
        """輸入學姊的文檔，生成json檔"""
        output = []
        count = 0
        with open('./googleresult.json', 'r') as rf:
            for line in rf:
                one_line = ast.literal_eval(line)
                output.append(one_line)
                count += 1
                if count % 5000 == 0:
                    print(count)

        print(len(output))
        with open('result.json', 'w') as wf:
            json.dump(output, wf)

    def gen_final_json(self, content):
        """功能：1) 去掉重複label的項目 2) 簡轉繁 3) 處理成preprocessing可以吃的格式
        輸入：爬蟲結果的json檔
        回傳：preprocessing可以吃的格式的dict
        """
        openCC = OpenCC('s2twp')  # 簡轉繁

        c = 0
        previous_label = ''
        output_list = []
        for item in content:
            if item['label'] == previous_label:
                continue
            item_dict = {}
            item_dict['discription'] = openCC.convert(item['label'])
            item_dict['context'] = openCC.convert(item['search_result'])
            output_list.append(item_dict)
            previous_label = item['label'] # 為了只取第一個，其他一樣的都不要
            c += 1
            if c % 1000 == 0:
                print(c)

        print('共有', len(output_list), '筆資料')
        return output_list
    
    def main(self):
        with open('./result.json', 'r') as rf: # result.json是學姊給的文檔整理成的json檔
            content = json.load(rf)
        
        data = self.gen_final_json(content)
        
        with open('../yahoo_knowledge_data/crawler_result.json', 'w') as wf:
            json.dump(data, wf)

        pprint(random.sample(data, 100))

        




if __name__ == '__main__':
    p_obj = process_crawler_result()
    p_obj.main()
