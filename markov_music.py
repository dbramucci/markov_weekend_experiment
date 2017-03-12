import argparse
import random
from collections import Counter
from itertools import islice
from textwrap import wrap
from typing import List, Generator, Callable

import music21
from music21.duration import Duration
from music21.note import Note
from music21.pitch import Pitch

from markov import generate_random_stream


NoteGen = Generator[Note, None, None]

# the classes in music21 haven't implemented a hash function but
# generate_random_stream relies on one so I have added one to the classes that need it
Pitch.__hash__ = Note.__hash__ = Duration.__hash__ = lambda self: hash(
    self.fullName)


def read_note_sequence(filename: str) -> List[Note]:
    """ Reads the note sequence from a single line music xml file.

    :param filename: the file to open
    :return: the list of notes in the piece
    """
    with open(filename) as f:
        music_raw = f.read()
    score = music21.converter.parseData(music_raw)
    notes = []
    for p in score.parts[0]:
        try:
            for i in p:
                if isinstance(i, Note):
                    notes.append(i)
        except TypeError:  # ignore non-iterable items
            pass
    return notes


def convert_note_to_lilypond(note: Note) -> str:
    """ Converts a note into a lilypond representation of said note

    :param note: the note to convert
    :return: the lilypond version of the note
    """
    length_convert = {
        'whole': 1,
        'half': 2,
        'quarter': 4,
        'eighth': 8,
        '16th': 16,
        '32nd': 32,
    }
    pitch = note.pitch
    duration = note.duration
    octave = int(pitch.nameWithOctave[-1])
    name = pitch.name.replace('-', 'es').replace('#', 'is').lower()
    lily_octave = ''
    if octave > 3:
        lily_octave = (octave - 3) * "'"
    elif octave < 3:
        lily_octave = -1 * (octave - 3) * ','
    try:
        return name + lily_octave + str(length_convert[duration.type]) + '.' * duration.dots
    except (ZeroDivisionError, KeyError):
        return ''


def create_lilypond_file(notes: str) -> str:
    """ Surround the provided text with a lilypond template

    :param notes: the music to place in the template
    :return: the full ready to compile piece of music
    """
    return (fr"" "\n"
            fr'\version "2.18.2"' "\n"
            fr"" "\n"
            fr"\paper {{" "\n"
            fr'  #(set-paper-size "letter")' "\n"
            fr"}}" "\n"
            fr"" "\n"
            fr"\header {{" "\n"
            fr'  title = "Markov Music"' "\n"
            fr'  composer = "Danny Bramucci"' "\n"
            fr"  tagline = \markup {{" "\n"
            fr"    Engraved at" "\n"
            fr'    \simple #(strftime "%Y-%m-%d" (localtime (current-time)))' "\n"
            fr"  }}" "\n"
            fr"}}" "\n"
            fr"" "\n"
            fr"\score{{" "\n"
            fr"" "\n"
            fr"  \new Staff {{" "\n"
            fr"    \set Score.barNumberVisibility = #all-bar-numbers-visible" "\n"
            fr'    \new Voice = "rhythm"{{' "\n"
            fr'      \set midiInstrument = #"cello"' "\n"
            fr"      \tempo 4 = 120" "\n"
            fr"      \absolute{{" "\n"
            fr"      \time 4/4" "\n"
            fr"\clef treble" "\n"
            fr"{notes}" "\n"
            fr"    }}" "\n"
            fr"  }}" "\n"
            fr"  }}" "\n"
            fr"  \midi {{" "\n"
            fr"    \context {{" "\n"
            fr"      \Voice" "\n"
            fr'      \consists "Staff_performer"' "\n"
            fr"    }}" "\n"
            fr"  }}" "\n"
            fr"  \layout {{" "\n"
            fr"    #(layout-set-staff-size 25)" "\n"
            fr"  }}" "\n"
            fr"}}" "\n"
            fr"    ")


def generate_rhythms(notes: List[Note], performed_pitches: List[Pitch]) -> NoteGen:
    """ Generate notes based on a list of notes and the pitches that are to be used for these notes

    :param notes: the notes to generate the relationships from
    :param performed_pitches: the pitches to be used in the sequence of notes returned
    :return: a generator of notes
    """
    frequencies = {}
    for pitch in {i.pitch for i in notes}:
        frequencies[pitch] = Counter(i.duration for i in notes if i.pitch == pitch)

    for pitch in performed_pitches:
        count = frequencies[pitch]
        possible_rhythms = list(count.keys())
        weights = [count[beat] for beat in possible_rhythms]
        yield Note(pitch, duration=random.choices(possible_rhythms, weights)[0])


def generate_random_music_by_notes(starting_notes: List[Note], length_of_history: int = 1,
                                   mixup_period: int = None) -> NoteGen:
    """ Generates notes based on the provided notes

    :param starting_notes: the notes to inspire to new song
    :param length_of_history: the length of history to base the decisions on
    :param mixup_period: after this many notes, the generator will yield a completely random note
    :return: a generator of notes
    """
    yield from generate_random_stream(starting_notes, length_of_history, mixup_period)


def generate_random_music_independent_duration(starting_notes: List[Note], length_of_history: int = 1,
                                               mixup_period: int = None) -> NoteGen:
    """ Generates pitches and durations independently and then combines them into a series of notes

    :param starting_notes: the notes to base the generator off of
    :param length_of_history: the length of history to base decisions on
    :param mixup_period: after this many notes, the generator will yield a completely random note
    :return: a generator of notes
    """
    pitches = generate_random_stream((n.pitch for n in starting_notes), length_of_history, mixup_period)
    durations = generate_random_stream((n.duration for n in starting_notes), length_of_history, mixup_period)
    yield from (Note(p, duration=d) for (p, d) in zip(pitches, durations))


def generate_random_music_dependent_duration(starting_notes: List[Note], length_of_history: int = 1,
                                             mixup_period: int = None) -> NoteGen:
    """ Generates pitches and then bases durations off of those notes

    :param starting_notes: the notes to base the generator off of
    :param length_of_history: the length of history to base decisions on
    :param mixup_period: after this many notes, the generator will yield a completely random note
    :return: a generator of notes
    """
    pitches = generate_random_stream((n.pitch for n in starting_notes),
                                     length_of_history, mixup_period)
    yield from generate_rhythms(starting_notes, pitches)


def make_text(starting_notes: List[Note], strategy: Callable[[List[int], int, int], NoteGen],
              length: int, length_of_history: int = 1, mixup_period: int = None) -> str:
    """ Generates the lilypond file

    :param starting_notes: The notes to base the new piece off of
    :param strategy: a generator of notes that takes starting_notes, length_of_history, mixup_period as arguments
    :param length: the length of the piece to create
    :param length_of_history: the length of history to base decisions on
    :param mixup_period: after this many notes, the music will randomly change
    :return: the lilypond source for the new song
    """
    lily_pond_notes = '\n'.join(
        wrap(' '.join(convert_note_to_lilypond(n)
                      for n in islice(strategy(starting_notes, length_of_history, mixup_period), length)), width=80))
    return create_lilypond_file(lily_pond_notes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates music using Markov Chain inspired techniques")
    parser.add_argument('file_in', help='This is the file you would like to use to learn from')
    parser.add_argument('file_out', help='The name of the file to save to')
    parser.add_argument('strategy', help='The strategy to generate the music')
    parser.add_argument('length', help='The length of the piece to generate', type=int, default=250)
    parser.add_argument('history_length', help='The length of history to base decisions on', type=int, default=2)
    parser.add_argument('mixup_period',
                        help='The period that should pass before switching melodies randomly to prevent stallness',
                        type=int, default=None)
    args = parser.parse_args()

    file_in = args.file_in
    file_out = args.file_out
    strategy = args.strategy
    length = args.length
    history_length = args.history_length
    mixup_period = args.mixup_period

    if strategy == 'a' or strategy == 'note':
        strategy = generate_random_music_by_notes
    elif strategy == 'b' or strategy == 'dependent':
        strategy = generate_random_music_dependent_duration
    elif strategy == 'c' or strategy == 'independent':
        strategy = generate_random_music_independent_duration

    result = make_text(read_note_sequence(file_in), strategy, length, history_length, mixup_period)
    with open(file_out, mode='w') as f:
        f.write(result)
