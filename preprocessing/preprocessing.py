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


lock = True

class preprocessing(object):
    def __init__(self):
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

    def filter_specific_word(self, data):
        """專門過濾掉一些含有特定關鍵字的item
        - descripttion當中有「這」
        """
        result_list = []
        for item in data:
            found = False
            for ch in item['description']:
                if ch == '這':
                    found = True
                    break
            if not found:
                result_list.append(item)
        return result_list

    def _sample_data_to_see(self, data, num):
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

    def go_through_processes_for_context(self, data):
        """走過context的所有清理步驟
        args: 欲處理的字串
        returns: 處理好的字串
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

    def go_through_processes_for_description(self, data):
        try:
            data = self.remove_and_convert_character(data)
            data = self.remove_comma_at_head_and_tail(data)
            data = self.check_for_period(data)
            data = self.segmentation(data)
            data = self.insert_tags(data)
            return data
        except:
            return

    def split_train_valid(self, data, test_size, valid_size):
        """
        切割train, valid, test資料
        train先切給test
        剩下的train再切給valid
        """
        train, test = train_test_split(data, test_size=test_size, random_state=34) # 抽99筆出來當testing data
        train, valid = train_test_split(train, test_size=valid_size, random_state=34) # train有80907筆，valid有8990筆
        return (train, valid, test)


    def main(self):
        # with open('../yahoo_knowledge_data/corpus/ver_2/init_data.json') as rf:
        #     data = json.load(rf)
        
        # # # sample東西出來看
        # # data = random.sample(data, 50)

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

        # # 全部資料總共 894065 筆
        # # 無法處理的資料共 1180 筆
        # with open('../yahoo_knowledge_data/corpus/ver_2/preprocessed_data.json', 'w') as wf:
        #     json.dump(out_list, wf)

        
        """
        以上做完前處理，為了加速所以先存檔，接著下來用讀檔的比較快。之後也可以串起來一次做完。
        """

        with open('../yahoo_knowledge_data/corpus/ver_2/preprocessed_data.json', 'r') as rf:
            data = json.load(rf)

        data = self.filter_specific_word(data)
        
        # # sample東西出來看
        # self._sample_data_to_see(data, 100)

        # gen = gen_vocab()
        # word_count = gen.get_word_count_with_threshold(data, 10) # 用來轉換UNK的counter

        # print('==== 開始轉換<UNK> ====')
        # data = self.convert_UNK(word_count, data) # 轉換UNK


        # word_count = gen.get_word_count_with_threshold(data, 0) # 這次的word_count有包含UNK
        # print('最後版本的vocab是', len(word_count), '個字')

        # # 產生vocab
        # gen.gen_final_vocab(word_count, '../yahoo_knowledge_data/vocab/ver_3/vocab')
        
        # train, valid, test = self.split_train_valid(data, test_size=.0001, valid_size=.2) # 回傳(train, valid, test)
        # print('train size', len(train))
        # print('valid size', len(valid))
        # print('test size', len(test))

        # # 產生data_convert_example.py可以吃的格式的資料
        # self.gen_input_format(train, '../yahoo_knowledge_data/train/ver_3/readable_data_ready')
        # self.gen_input_format(valid, '../yahoo_knowledge_data/valid/ver_3/readable_data_ready')
        # self.gen_input_format(test, '../yahoo_knowledge_data/decode/ver_3/readable_data_ready')
        # text_to_binary('../yahoo_knowledge_data/train/ver_3/readable_data_ready', '../yahoo_knowledge_data/train/ver_3/data')
        # text_to_binary('../yahoo_knowledge_data/valid/ver_3/readable_data_ready', '../yahoo_knowledge_data/valid/ver_3/data')
        # text_to_binary('../yahoo_knowledge_data/decode/ver_3/readable_data_ready', '../yahoo_knowledge_data/decode/ver_3/data')


if __name__ == '__main__':
    p = preprocessing()
    p.main()
