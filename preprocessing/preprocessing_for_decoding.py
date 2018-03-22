import json
import jieba
from pprint import pprint
import re


lock = True

class preprocessing(object):
    def __init__(self):
        jieba.load_userdict('./jieba_dict/udic_jieba_dict.txt')
        self.vocab_set = set()
        with open('../data/vocab', 'r') as rf:
            for line in rf.readlines():
                self.vocab_set.add(line.replace('\n', '').split()[0])

    def main(self, in_file_path, out_json_name, out_file_name):
        corpus_json = self.get_json(in_file_path)
        with open(out_json_name, 'w') as wf: # 保留一份json檔
            json.dump(corpus_json, wf)
        self.gen_input_data(corpus_json, out_file_name)

    def gen_input_data(self, content, out_file_name):
        with open(out_file_name, 'w') as wf:
            for item in content:
                wf.write('abstract=' + item['abstract'])
                wf.write('\t')
                wf.write('article=' + item['article'])
                wf.write('\n')

    def get_json(self, in_file_path):
        output_list = []
        c = 0
        with open(in_file_path, 'r') as rf:
            for item in json.load(rf):
                output_dict = {}
                for a in item: # abstract和article
                    after_seg = self.segmentation(item[a])
                    after_insert_tags = self.insert_tags(after_seg)
                    after_convert_num = self._convert_num(after_insert_tags)
                    after_convert_UNK = self._convert_UNK(after_convert_num)
                    output_dict[a] = after_convert_UNK
                output_list.append(output_dict)
        return output_list

    def segmentation(self, string):
        return ' '.join(self._filter_junk_word(jieba.lcut(string, cut_all=False)))

    def _filter_junk_word(self, seg_list):
        """過濾斷詞後不要的東西"""
        clean_seg = []
        for word in seg_list:
            if word != ' ':
                clean_seg.append(word)
        return clean_seg

    def insert_tags(self, string):
        """把每個文章加上<s><p><d>標籤"""
        global lock
        sentence_list = string.split('。')
        # print(len(sentence_list))
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

    def _convert_num(self, whole_str):
        return re.sub('\d', '#', whole_str)

    def _convert_UNK(self, whole_str):
        converted_word_list = []
        for word in whole_str.split(): # loop over整個文章
            if word in self.vocab_set:
                converted_word_list.append(word)
            else:
                converted_word_list.append('<UNK>')
        return ' '.join(converted_word_list)


if __name__ == '__main__':
    obj = preprocessing()
    obj.main('decoding_corpus/decoding_corpus.json', 'decoding_corpus/test.json', 'decoding_corpus/test')

    # with open('./test_decoding.json', 'r') as rf:
    # for news in json.load(rf):
    #     for item in news: # abstract和article
