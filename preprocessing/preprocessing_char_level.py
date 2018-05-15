from preprocessing import preprocessing
from gen_vocab import gen_vocab
from data_convert_example import text_to_binary
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

def filter_specific_word(data):
    """專門過濾掉一些含有特定關鍵字的item
    - description當中有「這」的item
    - description或context中含有「貸」的item
    """
    result_list = []
    for item in data:
        if not ('這' in item['description'] or
                '貸' in item['description'] or
                '貸' in item['context'] or
                '補 習' in item['description'] or
                '補 習' in item['context'] or
                '家 教' in item['description'] or
                '家 教' in item['context']):
            result_list.append(item)
    return result_list





def main():
    # with open('../yahoo_knowledge_data/corpus/init_data.json') as rf:
    #     data = json.load(rf)

    # err = 0
    # out_list = []
    # for item in tqdm(data):
    #     out_dict = {}
    #     description = description_processes(item['description'])
    #     context = context_processes(item['context'])
    #     if context and description:
    #         out_dict['context'] = context
    #         out_dict['description'] = description
    #         out_list.append(out_dict)
    #     else:
    #         err += 1

    # with open('../yahoo_knowledge_data/corpus/ver_6/preprocessed_data.json', 'w') as wf:
    #     json.dump(out_list, wf)

    # print('全部資料總共', len(data), '筆')
    # print('前處理無法處理的數量共', err, '筆')
    # print('乾淨資料總計', (len(data) - err), '筆')

    """
    以上做完前處理，為了加速所以先存檔，接著下來用讀檔的比較快，之後也可以串起來一次做完。
    """

    with open('../yahoo_knowledge_data/corpus/ver_6/preprocessed_data.json', 'r') as rf:
        data = json.load(rf)
    
    
    # 過濾掉含有特定字串的item
    data = filter_specific_word(data)
    # 刪除重複context的item
    data = preprocessing.remove_duplicate(data)

    # # sample東西出來看
    # data = preprocessing._sample_data_to_see(data, 100)
    # pprint(data)

    gen = gen_vocab()
    word_count = gen.get_word_count_with_threshold(data, 100) # 用來轉換UNK的counter

    print('==== 開始轉換<UNK> ====')
    data = preprocessing.convert_UNK(word_count, data) # 轉換UNK

    word_count = gen.get_word_count_with_threshold(data, 0) # 這次的word_count有包含UNK
    print('最後版本的vocab是', len(word_count), '個字')

    # 產生vocab
    gen.gen_final_vocab_and_vocab_tsv(word_count, '../yahoo_knowledge_data/vocab/ver_6/vocab')
    
    print('==== 開始分train, valid ====')
    train, valid, test = preprocessing.split_train_valid(data, test_size=.0005, valid_size=.1) # 回傳(train, valid, test)
    print('train size', len(train))
    print('valid size', len(valid))
    print('test size', len(test))

    # 產生data_convert_example.py可以吃的格式的資料
    print('==== 開始產生input data ====')
    preprocessing.gen_input_format(train, '../yahoo_knowledge_data/train/ver_6/readable_data_ready')
    preprocessing.gen_input_format(valid, '../yahoo_knowledge_data/valid/ver_6/readable_data_ready')
    preprocessing.gen_input_format(test, '../yahoo_knowledge_data/decode/ver_6/readable_data_ready')
    text_to_binary('../yahoo_knowledge_data/train/ver_6/readable_data_ready', '../yahoo_knowledge_data/train/ver_6/data')
    text_to_binary('../yahoo_knowledge_data/valid/ver_6/readable_data_ready', '../yahoo_knowledge_data/valid/ver_6/data')
    text_to_binary('../yahoo_knowledge_data/decode/ver_6/readable_data_ready', '../yahoo_knowledge_data/decode/ver_6/data')




if __name__ == '__main__':
    main() 
