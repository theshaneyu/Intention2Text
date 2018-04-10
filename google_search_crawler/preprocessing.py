import json
from pprint import pprint


class process_crawler_result(object):
    """這個類別專門拿來把爬蟲的結果處理成"""
    def __init__(self):
        pass

    def checking(self):
        """(一次性)產生json檔"""
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

    def gen_final_json(self):
        with open('./result.json', 'r') as rf:
            content = json.load(rf)

        c = 0
        previous_label = ''
        output = []
        for item in content:
            if item['label'] == previous_label:
                continue
            output.append(item)
            previous_label = item['label']
            c += 1
            if c % 1000 == 0:
                print(c)
        print('共有', len(output), '筆資料')
        with open('../yahoo_knowledge_data/crawler_result.json', 'w') as wf:
            json.dump(output, wf)


if __name__ == '__main__':
    p_obj = process_crawler_result()
    p_obj.gen_final_json()
