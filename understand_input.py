with open('./data/data', 'rb') as rf:
    for line in rf.read():
        print(type(line))
        break