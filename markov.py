import random
from collections import defaultdict, Counter, deque
from itertools import tee
from sys import stderr
from typing import Iterator, List


def group_by_n(iterator: Iterator, n: int) -> Iterator:
    """ returns groups of n items from the iterator (ex [1, 2, 3], 2 returns (1, 2), (2, 3))

    :param iterator: The iterator to use
    :param n: the number of items to group together
    :return: a iterator of n-grouped items from the iterator
    """
    parallels = tee(iterator, n)
    for i, iterator in enumerate(parallels):
        if i == 0:
            continue
        for j, _ in enumerate(iterator):
            if i - 1 == j:
                break
    return zip(*parallels)


def calculate_frequencies(history, length_of_history=1):
    """ Calculates the frequencies of each item following a sequence of length length_of_history

    :param history: the history to build the list of frequencies off of
    :param length_of_history: the length of sequence to observe
    :return: a dictionary containing counters where frequency[tuple_of_sequence][future_element] is the number of times
    future_element followed the mentioned sequence.
    """
    # Could use fixed length queue instead of group_by_n for this
    frequencies = defaultdict(Counter)
    for (*pre, next_word) in group_by_n(history, length_of_history + 1):
        frequencies[tuple(pre)][next_word] += 1
    return frequencies


def generate_random_stream(source_stream, length_of_history=1, mixup_period=None):
    """ Generates an infinite stream based on the given source_stream

    :param source_stream: The inspiring material
    :param length_of_history: the length of sequences to base decisions off of
    :param mixup_period: the period after which a random transition should occur
    :return: a generator of random values based off of the source stream
    """
    frequencies = calculate_frequencies(source_stream, length_of_history)
    yield from generate_random_stream_from_frequencies(frequencies, length_of_history, mixup_period)


def generate_random_stream_from_frequencies(frequencies, length_of_history=1, mixup_period=None):
    """ Generates an infinite stream based on the given source_stream

    :param frequencies: The frequencies that dictate the frequencies of events occuring
    :param length_of_history: the length of sequences to base decisions off of
    :param mixup_period: the period after which a random transition should occur
    :return: a generator of random values based off of the provided frequencies
    """

    known_subsequences = list(frequencies.keys())
    recent = deque(maxlen=length_of_history)
    for item in random.choice(known_subsequences):
        yield item
        recent.append(item)

    i = 0
    while True:
        count = frequencies[tuple(recent)]

        options = list(count.keys())
        weights = [count[word] for word in options]

        if mixup_period and i % mixup_period == 0:
            for item in random.choice(known_subsequences):
                yield item
                recent.append(item)
        try:
            for item in random.choices(options, weights):
                yield item
                recent.append(item)
        except IndexError:
            print(f'IDK: {recent}', file=stderr)
            for item in random.choice(known_subsequences):
                yield item
                recent.append(item)


def predict_from_history(history: List, length_of_history: int):
    """ Returns the most likely next state based on the current state

    :param history: a list of events occuring in the past
    :param length_of_history: the length of sequence to base a decision off of
    :return: the most likely future event
    """
    frequencies = calculate_frequencies(history, length_of_history)

    return predict(frequencies, history[-length_of_history:])


def predict(frequencies, recently_seen):
    """ Returns the most likely move based on recently seen events and a table of frequencies

    :param frequencies: the frequencies at which events occur
    :param recently_seen: the most recently seen events
    :return: the most likely future event
    """
    count = frequencies[tuple(recently_seen)]
    try:
        return max(count, key=lambda x: count[x])
    except ValueError:
        print('Err', file=stderr)
        return random.choice(recently_seen)
