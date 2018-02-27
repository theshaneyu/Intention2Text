import json
from collections import Counter
from operator import itemgetter


with open('./corpus/corpus.json', 'r') as rf:
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
    if count % 5000 == 0:
        print('已完成 %d 筆' % count)

print('全部的詞數量', len(cnt))

with open('./vocab', 'w') as wf:
    for pair in sorted(cnt.items(), key=itemgetter(1), reverse=True):
        wf.write(pair[0] + ' ' + str(pair[1]) + '\n')
