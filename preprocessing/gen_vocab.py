import json
from collections import Counter
from operator import itemgetter
from tqdm import tqdm


class gen_vocab(object):
    """用於產生vocab"""
    def __init__(self):
        pass

    def gen_final_vocab_and_vocab_tsv(self, cnt, out_path):
        """產生正式的vocab，順便產生vocab.tsv"""
        with open(out_path, 'w') as wf:
            for pair in cnt:
                wf.write(pair[0] + ' ' + str(pair[1]) + '\n')
            wf.write('<PAD> 0')
        
        with open(out_path + '.tsv', 'w') as wf:
            wf.write('word' + '\t' + 'id' + '\n')
            for pair in cnt:
                wf.write(pair[0] + '\t' + str(pair[1]) + '\n')
            wf.write('<PAD>' + '\t' + '0')

    def _filter_words_with_threshold(self, ordered_itemized_cnt, threshold):
        """
        returns:
            1. 根據門檻值過濾完的itemized_cnt
            2. 順便回傳「UNK總共會出現多少次」
        """
        return_list = []
        UNK_appear_time = 0
        for item in ordered_itemized_cnt:
            if item[1] > threshold:
                return_list.append(item)
            else:
                UNK_appear_time += item[1]
        return return_list, UNK_appear_time
        
    def get_word_count_with_threshold(self, data, threshold, top_k=0):
        """
        args:
            data: 輸入json格式data
            top_k: 如果要取「word_count排名前幾的詞」，則輸入數值，預設不取排名，數值為0
            threshold: 只取word_count數值為多少以上的詞，如果為0，則回傳完整word_count
        return:
            cnt的items格式

        """
        cnt = Counter()

        word_count = 0
        for item in tqdm(data):
            for key in item.keys(): # abstrct and article
                for word in item[key].split():
                    if word == ' ':
                        continue
                    cnt[word] += 1
                    word_count += 1
        print('===== 全部文章總詞數', '{:,}'.format(word_count), '=====')
        print('===== 全部文章詞種類數（字典大小）', '{:,}'.format(len(cnt)), '=====')
        if top_k == 0:
            if threshold == 0:
                return sorted(cnt.items(), key=itemgetter(1), reverse=True)
            else:
                sorted_cnt = sorted(cnt.items(), key=itemgetter(1), reverse=True)
                filtered_list, UNK_appear_time = self._filter_words_with_threshold(sorted_cnt, threshold)
                print('如果門檻設', threshold, '則有', '{:,}'.format(UNK_appear_time), '個字會變 <UNK>')
                print('且詞種類數（字典大小）會變', '{:,}'.format(len(filtered_list)))
                return filtered_list
        else:
            return cnt.most_common(top_k)

    def main(self):
        cnt = self.get_word_count_with_threshold('corpus_converted_num_and_UNK_4.json')
        self.gen_final_vocab(cnt)


def checking(self, threshold):
    """測試用function"""
    greater = 0
    smaller = 0
    with open('./vocab', 'r') as rf:
        for line in rf.readlines():
            if int(line.replace('\n', '').split()[1]) > threshold:
                greater += 1
            else:
                smaller += 1
    print('greater than', threshold, greater)
    print('smaller than', threshold, smaller)



if __name__ == '__main__':
    obj = gen_vocab()
    obj.main()
    # checking()
