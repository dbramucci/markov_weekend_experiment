import random
import argparse

from markov import predict_from_history


def bot() -> str:
    """ bot makes a decision"""
    ans, = random.choices(['r', 'p', 's'], [0.5, 0.25, 0.25])
    print(f'I, bad bot, choose {ans}')
    return ans


def ask() -> str:
    """ ask human for a move"""
    while True:
        ans = input('Please type in "r", "p" or "s": ').strip().casefold()[0]
        if ans in {'r', 'p', 's'}:
            return ans


beats = {
    'r': 's',
    's': 'p',
    'p': 'r'
}

loses_to = {v: k for (k, v) in beats.items()}


def play_game(player_play, turns, pause):
    """ Starts an infinite loop of rock paper scissors """
    turn = 0
    wins = 0
    losses = 0
    history = []
    while True:
        if pause and turn % turns == 0:
            input()
        turn += 1
        if len(history) > 0:  # random.choices(['r', 'p', 's'], [0.5, 0.25, 0.25])#random.choice(list(beats.keys()))
            user_prediction, = predict_from_history(history, min(len(history) - 1, 3))
        else:
            user_prediction = random.choice(list(beats.keys()))
        computer_choice = loses_to[user_prediction]
        user_choice = player_play()
        history.append(user_choice)
        if beats[computer_choice] == user_choice:
            print(f'I win, I choose {computer_choice}, you choose, {user_choice}')
            wins += 1
        elif loses_to[computer_choice] == user_choice:
            print(f'I lose, I choose {computer_choice}, you choose, {user_choice}')
            losses += 1
        else:
            print(f'tie, I choose {computer_choice}, you choose, {user_choice}')
        print(f'I predicted you would choose {user_prediction}')
        if max(wins, losses) != 0:
            print(f'my winrate is {wins / (wins + losses):.2%}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates music using Markov Chain inspired techniques")
    parser.add_argument('history_length', help='The length of history to base decisions on', type=int, default=2)
    parser.add_argument('-turns_to_jump', type=int, default=100)
    parser.add_argument('-c', '--computer', action='store_true')
    args = parser.parse_args()

    history_length = args.history_length
    computer_play = args.computer

    play_game(bot if computer_play else ask, 100, computer_play)
