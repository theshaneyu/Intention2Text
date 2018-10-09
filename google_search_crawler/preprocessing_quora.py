from pprint import pprint
from random import shuffle


class preprocessing_quora(object):
    def __init__(self, data_path):
        self.rf = open(data_path, 'r')

    def split_train_valid(self):
        pass

    def clean_and_format(self):
        result_set = set()
        c = 0
        dup = 0
        for line in self.rf:
            c += 1
            if line[0] == ' ':
                if line[1:] not in result_set:
                    result_set.add(line[1:])
                else:
                    dup += 1
            else:
                result_set.add(line)

        print(dup)
        # print(len(result_set))


    def main(self):
        self.clean_and_format()
        # self.split_train_valid()
        self.rf.close()


if __name__ == '__main__':
    pre_obj = preprocessing_quora('./corpus/final_result.txt')
    pre_obj.main()
        

# 有1143筆重複