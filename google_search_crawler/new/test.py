from MagicGoogle import MagicGoogle
from pprint import pprint
import random
import time
import json
import sys
import logging


PROXIES = None

mg = MagicGoogle()


def query_func(term):
    # Get {'title','url','text'}
    return_list = []
    for item in mg.search(query=term, num=10):
        result_dict = {}
        result_dict['description'] = term
        if item['text'] == '':
            result_dict['context'] = '@'
        else:
            result_dict['context'] = item['text']
        return_list.append(result_dict)

    return return_list


def sleep_time(num):
    # 回傳整數
    return random.sample(set(range(1, num+1)), 1)[0]


c = 0
err = 0
with open('../questions_40532.txt', 'r') as rf:
    with open('./result_40532.txt', 'w') as wf:
        for line in rf:
            try:
                return_list = query_func(line)
                for item_dict in return_list:
                    wf.write(item_dict['description'])
                    wf.write(item_dict['context'].replace('\n', '') + '\n')
                    wf.write('---' + '\n')

                c += 1
                logging.info('===> 已完成Question筆數: ' + str(c) + '/40532\n')
                
            except:
                err += 1
                continue
            # 睡隨機長度的時間，參數5的意思是1-5秒隨機睡
            time.sleep(sleep_time(5))

logging.info('最後爬蟲出錯的數量：' + str(err))

