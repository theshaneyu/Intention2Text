from pprint import pprint
from opencc import OpenCC 
import jieba
import json
import re
import random
from tqdm import tqdm
from gen_vocab import gen_vocab
from sklearn.model_selection import train_test_split
from data_convert_example import text_to_binary
import os
from collections import defaultdict
from plots import contexts_number_histogram


lock = True

class preprocessing(object):
    def __init__(self):
        jieba.initialize('jieba_dict/dict.txt.big')
        jieba.load_userdict('jieba_dict/NameDict_Ch_v2')
        self.global_counter = 0

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

    def convert_UNK(self, word_count, data):
        word_pool = self._gen_word_pool(word_count)
        out_list = []
        for item in data:
            out_dict = {}
            out_dict['context'] = self._convert_UNK_for_one_string(item['context'], word_pool)
            out_dict['description'] = self._convert_UNK_for_one_string(item['description'], word_pool)
            out_list.append(out_dict)
        return out_list

    def _gen_word_pool(self, word_count):
        word_pool = set()
        for item in word_count: # 一個item像('日本', 8264)
            word_pool.add(item[0])
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

    def split_train_valid_test(self, data, test_size, valid_size):
        """
        切割train, valid, test資料
        train先切給test
        剩下的train再切給valid
        """
        train, test = train_test_split(data, test_size=test_size, random_state=34) # 抽test_size筆出來當testing data
        train, valid = train_test_split(train, test_size=valid_size, random_state=34) # 剩下的再來分train, valid
        return (train, valid, test)

    def split_decode_data(self, decode_data_path):
        file_num = 1
        with open(decode_data_path + 'readable_data_ready', 'r') as rf:
            for line in rf:
                with open(decode_data_path + 'dataset_ready/data_ready_' + str(file_num), 'w') as wf:
                    wf.write(line.replace('\n', ''))
                file_num += 1

    def make_sure_path_exists(self, ver_num):
        if not os.path.exists('../yahoo_knowledge_data/train/ver_' + ver_num + '/'):
            os.makedirs('../yahoo_knowledge_data/vocab/ver_' + ver_num + '/')
            os.makedirs('../yahoo_knowledge_data/train/ver_' + ver_num + '/')
            os.makedirs('../yahoo_knowledge_data/valid/ver_' + ver_num + '/')
            os.makedirs('../yahoo_knowledge_data/decode/ver_' + ver_num + '/')
            os.makedirs('../yahoo_knowledge_data/decode/ver_' + ver_num + '/dataset_ready/')

    def gen_dict_with_descriptions_as_key(self, data):
        description_dict = defaultdict(list)
        for item in data:
            description_dict[item['description']].append(item['context'])
        return description_dict

    def allocate_data_by_description(self, data_keys, description_dict): # data_tuple是(train, valid, test)
        data = []
        for key in data_keys:
            for context in description_dict[key]: # description_dict是查表用
                item_dict = {}
                item_dict['description'] = key
                item_dict['context'] = context
                data.append(item_dict)
        random.shuffle(data)
        return data


    def main(self):
        # with open('../yahoo_knowledge_data/corpus/init_data.json') as rf:
        #     data = json.load(rf)
        
        # # sample東西出來看
        # data = random.sample(data, 100)

        # err = 0
        # out_list = []
        # for item in tqdm(data):
        #     out_dict = {}
        #     context = self.go_through_processes_for_context(item['context'])
        #     description = self.go_through_processes_for_description(item['description'])
        #     if context and description:
        #         out_dict['context'] = context
        #         out_dict['description'] = description
        #         out_list.append(out_dict)
        #     else:
        #         err += 1

        # with open('../yahoo_knowledge_data/corpus/ver_4/preprocessed_data.json', 'w') as wf:
        #     json.dump(out_list, wf)

        # print('全部資料總共', len(data), '筆')
        # print('前處理清資料總共清掉', err, '筆')    
        # print('乾淨資料總計', (len(data) - err), '筆')
        
        """
        以上做完前處理，為了加速所以先存檔，接著下來用讀檔的比較快，之後也可以串起來一次做完。
        """

        with open('../yahoo_knowledge_data/corpus/ver_4/preprocessed_data.json', 'r') as rf:
            data = json.load(rf)
        
        # 過濾掉含有特定字串的item
        data = self.filter_item_with_specific_words(data)
        # 過濾掉description和context皆為相同的item
        data = self.remove_duplicate(data)

        gen = gen_vocab()
        word_count = gen.get_word_count_with_threshold(data, 10) # 用來轉換UNK的counter

        print('==== 開始轉換<UNK> ====')
        data = self.convert_UNK(word_count, data) # 轉換UNK

        word_count = gen.get_word_count_with_threshold(data, 0) # 這次的word_count有包含UNK
        print('最後版本的vocab是', len(word_count), '個字')

        # 新版保證description在train, valid, test中不重複的切法（依據keys(descriptions去切)）#########################
        description_dict = self.gen_dict_with_descriptions_as_key(data)        
        # # 畫出Context數量分布histogram
        # contexts_number_histogram(description_dict)
        print('==== 開始分train, valid ====')
        train_keys, valid_keys, test_keys = self.split_train_valid_test(list(description_dict.keys()), test_size=.0004, valid_size=.1)
        train = self.allocate_data_by_description(train_keys, description_dict)
        valid = self.allocate_data_by_description(valid_keys, description_dict)
        test = self.allocate_data_by_description(test_keys, description_dict)
        print('train size', len(train))
        print('valid size', len(valid))
        print('test size', len(test))
        ##########################################################################################################

        print('==== 開始產生vocab和input data ====')
        ver_num = '8'
        # 檢查路徑是否存在
        self.make_sure_path_exists(ver_num)
        # 產生vocab，順便產生vocab.tsv
        gen.gen_final_vocab_and_vocab_tsv(word_count, '../yahoo_knowledge_data/vocab/ver_' + ver_num + '/vocab')
        # 產生可以模型吃的資料
        self.gen_input_format(train, '../yahoo_knowledge_data/train/ver_' + ver_num + '/readable_data_ready')
        self.gen_input_format(valid, '../yahoo_knowledge_data/valid/ver_' + ver_num + '/readable_data_ready')
        self.gen_input_format(test, '../yahoo_knowledge_data/decode/ver_' + ver_num + '/readable_data_ready')
        text_to_binary('../yahoo_knowledge_data/train/ver_' + ver_num + '/readable_data_ready', '../yahoo_knowledge_data/train/ver_' + ver_num + '/data')
        text_to_binary('../yahoo_knowledge_data/valid/ver_' + ver_num + '/readable_data_ready', '../yahoo_knowledge_data/valid/ver_' + ver_num + '/data')
        self.split_decode_data('../yahoo_knowledge_data/decode/ver_' + ver_num + '/')


if __name__ == '__main__':
    p = preprocessing()
    p.main()
