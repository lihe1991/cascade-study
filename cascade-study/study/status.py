import os
from math import log2


class Status(object):

    def __init__(self, filename, dataset_file, dataset_line, seed):

        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        if not os.path.isfile(filename):
            with open(filename, 'w') as f:
                f.write('dataset file,dataset line,channel error rate,real error rate,' +
                        'correct,ber,efficiency,channel uses,exchanged msg length,seed\n')
        self.filename = filename

        self.dataset_file = dataset_file
        self.dataset_line = dataset_line
        self.seed = seed

        self.correct_key = None
        self.channel_error_rate = 0.0
        self.real_error_rate = 0.0

        self.final_key = None
        self.channel_uses = []
        self.correct = True
        self.bit_error_ratio = 0
        self.efficiency = 1.0

    def initialize_run(self, c_key, channel_error, real_error):
        self.correct_key = c_key
        self.channel_error_rate = channel_error
        self.real_error_rate = real_error

    def start_iteration(self, channel_use):
        self.channel_uses.append([channel_use['len']])

    def start_block(self):
        self.channel_uses[-1].append([])

    def add_channel_use(self, channel_use):
        self.channel_uses[-1][-1].append(channel_use['len'])

    def _calculate_ber(self):
        num_errors = 0
        for i in range(0, len(self.final_key)):
            num_errors += int(self.final_key.bin[i]) ^ int(self.correct_key.bin[i])
        return num_errors / len(self.final_key)

    def _deep_sum(self, lst):
        return sum(self._deep_sum(el) if isinstance(el, list) else el for el in lst)

    def exchanged_msg_len(self):
        return self._deep_sum(self.channel_uses)

    def num_channel_uses(self):
        num = 0
        for iteration in self.channel_uses:
            num += 1
            max_len = 0
            for i in range(1, len(iteration)):  # for each iteration get the minimum needed number of uses
                max_len = max(max_len, len(iteration[i]))
            num += max_len
        return num

    def _calculate_efficiency(self):
        # return (1 - self.exchanged_msg_len() / len(self.correct_key)) / (
        #         -self.error_rate * log2(self.error_rate) - (1 - self.error_rate) * log2(1 - self.error_rate))
        return self.exchanged_msg_len() / (self.correct_key.length * (
              -self.channel_error_rate * log2(self.channel_error_rate) - (1 - self.channel_error_rate) * log2(
               1 - self.channel_error_rate)))

    def end_run(self, final_key):
        self.final_key = final_key
        self.calculate_parameters()
        self.flush_to_file()

    def calculate_parameters(self):
        if self.final_key != self.correct_key:
            self.correct = False
            self.bit_error_ratio = self._calculate_ber()

        self.efficiency = self._calculate_efficiency()

    def flush_to_file(self):
        with open(self.filename, 'a') as f:
            f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (self.dataset_file,
                                                         self.dataset_line,
                                                         self.channel_error_rate,
                                                         self.real_error_rate,
                                                         self.correct,
                                                         self.bit_error_ratio,
                                                         self.efficiency,
                                                         self.num_channel_uses(),
                                                         self.exchanged_msg_len(),
                                                         self.seed))

    @staticmethod
    def from_line(output_filename, input_filename, line_number):
        with open(input_filename, 'r') as f:
            for i, line in enumerate(f):
                if i == line_number:
                    split = line.split(',')
                    status = Status(output_filename, split[0], int(split[1]), split[-1].replace('\n', ''))
                    return status