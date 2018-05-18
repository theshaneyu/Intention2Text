def gen_tsv(in_path, out_path):
    id_counter = 0
    with open(in_path, 'r') as rf:
        with open(out_path, 'w') as wf:
            wf.write('word' + '\t' + 'id' + '\n')
            for line in rf:
                wf.write(line.split()[0] + '\t' + str(id_counter) + '\n')
                id_counter += 1


if __name__ == '__main__':
    in_path = '../yahoo_knowledge_data/vocab/ver_2/vocab'
    out_path = in_path + '.tsv'

    gen_tsv(in_path, out_path)
