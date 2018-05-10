from preprocessing import preprocessing
from pprint import pprint
import json
from tqdm import tqdm
import random


preprocessing = preprocessing()

def context_processes(string):
    try:
        
        string = preprocessing.remove_date_at_beginning_of_context(string)
        string = preprocessing.remove_and_convert_character(string)
        string = preprocessing.remove_comma_at_head_and_tail(string)
        string = preprocessing.check_for_period(string)
        string = split_characters(string)
        string = preprocessing.insert_tags(string)
        return string
    except:
        return

def description_processes(string):
    try:
        
        string = preprocessing.remove_and_convert_character(string)
        string = preprocessing.remove_asking_for_points(string)
        string = preprocessing.remove_comma_at_head_and_tail(string)
        string = preprocessing.check_for_period(string)
        string = split_characters(string)
        string = preprocessing.insert_tags(string)
        return string
    except:
        return

def split_characters(string):
    return ' '.join(list(string))



def main():
    with open('../yahoo_knowledge_data/corpus/init_data.json') as rf:
        data = json.load(rf)

    # # sample東西出來看
    # data = random.sample(data, 100)
    # pprint(data)

    err = 0
    out_list = []
    for item in tqdm(data):
        out_dict = {}
        description = description_processes(item['description'])
        context = context_processes(item['context'])
        if context and description:
            out_dict['context'] = context
            out_dict['description'] = description
            out_list.append(out_dict)
        else:
            err += 1

    with open('../yahoo_knowledge_data/corpus/ver_6/preprocessed_data.json', 'w') as wf:
        json.dump(out_list, wf)

    print('全部資料總共', len(data), '筆')
    print('前處理無法處理的數量共', err, '筆')
    print('乾淨資料總計', (len(data) - err), '筆')

    """
    以上做完前處理，為了加速所以先存檔，接著下來用讀檔的比較快，之後也可以串起來一次做完。
    """

    




if __name__ == '__main__':
    main() 
