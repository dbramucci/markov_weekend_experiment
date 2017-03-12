import argparse
from itertools import islice
from textwrap import wrap
from typing import List

from markov import generate_random_stream


def read_words(filename: str) -> List[str]:
    with open(filename, encoding='utf-8') as f:
        return [''.join(let.lower() for let in word) for word in f.read().split()]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates music using Markov Chain inspired techniques")
    parser.add_argument('file_in', help='This is the file you would like to use to learn from')
    parser.add_argument('file_out', help='The name of the file to save to')
    parser.add_argument('-length', help='The length of the piece to generate', type=int, default=250)
    parser.add_argument('-history_length', help='The length of history to base decisions on', type=int, default=2)
    parser.add_argument('-mixup_period', help='The period that should pass before switching melodies randomly to prevent stallness', type=int, default=None)
    args = parser.parse_args()

    file_in = args.file_in
    file_out = args.file_out
    length = args.length
    history_length = args.history_length
    mixup_period = args.mixup_period

    in_text = read_words(file_in)
    print(in_text)
    result = '\n'.join(
        wrap(' '.join(islice(generate_random_stream(in_text, history_length, mixup_period), length)), width=80))
    with open(file_out, mode='w', encoding='utf-8') as f:
        f.write(result)
