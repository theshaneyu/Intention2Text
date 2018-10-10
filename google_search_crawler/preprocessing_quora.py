from pprint import pprint
from random import shuffle
from sklearn.model_selection import train_test_split
from data_convert_example import text_to_binary


class preprocessing_quora(object):
    def __init__(self, data_path, train_path, valid_path):
        self.data_path = data_path
        self.train_path = train_path
        self.valid_path = valid_path

    def get_data_list(self):
        data_list = []
        with open(self.data_path, 'r') as rf:
            for line in rf:
                data_list.append(line.replace('\n', ''))
        return data_list

    def split_train_valid(self, data_list):
        train, valid = train_test_split(data_list, test_size=0.3, random_state=34)
        return train, valid

    def write_file(self, train, valid):
        with open(self.train_path, 'w') as wf:
            for item in train:
                wf.write(item + '\n')
        with open(self.valid_path, 'w') as wf:
            for item in valid:
                wf.write(item + '\n')

    def convert_to_bin(self):
        text_to_binary(self.train_path, './train/data')
        text_to_binary(self.valid_path, './valid/data')

    def main(self):
        data_list = self.get_data_list()
        train, valid = self.split_train_valid(data_list)
        self.write_file(train, valid)
        self.convert_to_bin()

# def temp():
#         with open('./corpus/final_result_clean.txt', 'w') as wf:
#             with open('./corpus/final_result.txt', 'r') as rf:
#                 for line in rf:
#                     if line[0] == ' ':
#                         wf.write(line[1:])
#                     else:
#                         wf.write(line)



if __name__ == '__main__':
    pre_obj = preprocessing_quora('./corpus/final_result_clean.txt',
                                  './corpus/train.txt',
                                  './corpus/valid.txt')
    pre_obj.main()
    
