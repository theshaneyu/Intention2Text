import json
from collections import Counter
from operator import itemgetter

class gen_vocab(object):
    """用於產生vocab"""
    def __init__(self):
        pass

    def gen_all_words_vocab(self, cnt):
        """產生所有詞的詞頻"""
        with open('./all_vocab', 'w') as wf:
            for pair in sorted(cnt.items(), key=itemgetter(1), reverse=True):
                wf.write(pair[0] + ' ' + str(pair[1]) + '\n')

    def gen_vocab_before_UNK(self, cnt):
        """由全部的文本產生前400000的vocab，可以用此vocab來標記<UNK>標籤"""
        with open('./vocab_before_UNK', 'w') as wf:
            for pair in cnt.most_common(400000):
                wf.write(pair[0] + ' ' + str(pair[1]) + '\n')

    def gen_final_vocab(self, cnt):
        """產生正式的vocab（有門檻限制）"""
        with open('./vocab', 'w') as wf:
            for pair in cnt.most_common(400000):
                wf.write(pair[0] + ' ' + str(pair[1]) + '\n')
            wf.write('<PAD> 0')
        
    def get_word_count(self, input_file_name):
        """回傳word count的Counter"""
        with open('./corpus/' + input_file_name, 'r') as rf:
            corpus = json.load(rf)

        cnt = Counter()

        count = 0
        for item in corpus:
            for key in item.keys(): # abstrct and article
                for word in item[key].split():
                    if word == ' ':
                        continue
                    cnt[word] += 1
            count += 1
            if count % 10000 == 0:
                print('word count已算完 %d 筆' % count)
        # print('全部的詞數量', len(cnt)) # 數字轉sharp前1373057，數字轉sharp後1197601
        return cnt

    def main(self):
        cnt = self.get_word_count('corpus_converted_num_and_UNK_4.json')
        self.gen_final_vocab(cnt)


def checking(self, threshold):
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
