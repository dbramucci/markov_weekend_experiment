from sys import argv

from markov import calculate_frequencies, predict

history_length = int(argv[1])
test_number = int(argv[2])


for i in range(test_number):
    ans1 = []
    with open('test1.txt') as f:
        for line in f.readlines():
            ans1.append(line.strip())

    # my_ans = islice(generate_random_stream_from_frequencies(frequencies, history_length), 50)

    my_ans = []
    for i in range(history_length + 1):
        frequencies = calculate_frequencies(ans1, i)
        my_ans.append(predict(frequencies, my_ans[-history_length:]))
    while len(my_ans) < 50:
        my_ans.append(predict(frequencies, my_ans[-history_length:]))
    # Check accuracy of guess

    ans2 = []
    with open('test2.txt') as f:
        for line in f.readlines():
            ans2.append(line.strip())

    print(sum(i == j for (i, j) in zip(my_ans, ans2)))
