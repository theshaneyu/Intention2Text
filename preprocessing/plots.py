import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def contexts_number_histogram(description_dict):
    num_list = []
    for k, v in description_dict.items():
        num_list.append(len(v))

    plt.hist(num_list, histtype='bar', rwidth=0.8)
    plt.title('Context Number Histogram')
    plt.xlabel('Value')
    plt.ylabel('Number')
    plt.savefig('Histogram.png', dpi=150, format='png')