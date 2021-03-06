import copy
import itertools
from queue import PriorityQueue
from threading import Thread
import functools
from typing import Set, Dict, List, Callable, Iterable

# Change this to a higher number if you want to be more sure. Time will rise exponentially in relation to this variable. This is in practice
# The Max word length plus one
SEARCH_DEPTH = 10

# Change this to higher if you think you have false negatives or if you greatly increase the search depth.
# It will check more words just in case.
# Timeout value in seconds
TIMEOUT = 3


LINE_FEED_BUFFER_SIZE = 25


def timeout(seconds_before_timeout):
    """
    Timeout wrapper function from stackoverflow by acushner
    https://stackoverflow.com/questions/21827874/timeout-a-function-windows
    :param seconds_before_timeout:
    :return:
    """

    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, seconds_before_timeout))]

            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(seconds_before_timeout)
            except Exception as e:
                print('error starting thread')
                raise e
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret

        return wrapper

    return deco


class CFG(object):
    def __init__(self, variables: Set[str], alphabet: Set[str], transitions: Dict[str, List[str]], start: str):

        self._variables = variables
        self._alphabet = alphabet
        diff = variables - set(transitions.keys())
        try:
            assert len(diff) == 0
        except AssertionError:
            print(f"No transition functions defined for {diff}")
            exit(1)
        for variable, substitution in transitions.items():
            try:
                assert (self.is_variable(variable))
            except AssertionError:
                print(f"Unrecognized variable '{variable}' in Transition function")
                exit(1)
            try:
                assert (all(self.is_valid_substitution(s) for s in substitution))
            except AssertionError:
                print(f"Invalid substitution: '{variable}: {substitution}'")
                exit(1)
        noterm = self.will_not_terminate(transitions)
        try:
            assert noterm == False
        except AssertionError:
            print(f"Your Transition function for {noterm} will never terminate. (No base case)")
            exit(1)
        self._transitions = transitions
        try:
            assert self.is_variable(start)
        except AssertionError:
            print("Unrecognized starting variable")
            exit(1)
        self._start = start
        self.language = dict()

    def will_not_terminate(self, transitions: Dict[str, List[str]]):
        terminable_variables = set()
        done = False
        while not done:
            done = True
            temp = copy.deepcopy(terminable_variables)
            for var in set(transitions.keys()) - terminable_variables:
                # Check that one of the substitutions is a terminal, or that all of its variables are terminable
                if any(self.is_terminal(sub) for sub in transitions[var]) or \
                        any(all(v in terminable_variables for v in self.variables_of(w)) for w in transitions[var]):
                    done = False
                    temp.add(var)
            terminable_variables = temp
        if len(terminable_variables) != len(transitions):
            return set(transitions.keys()) - terminable_variables
        return False

    def variables_of(self, word: str) -> Set[str]:
        return {v for v in word if self.is_variable(v)}

    @timeout(TIMEOUT)
    def generate_n_words(self, n: int):
        # maintain priority queue for BFS-like traversal
        # element[0] = priority, element[1][0] = word, element[1][1] = path to word
        to_traverse = PriorityQueue()
        # maintain set for fast access
        to_traverse_set = {self._start}

        to_traverse.put((0, (self._start, list())))
        while to_traverse.qsize() > 0 and len(self.language) < n:
            word, path = to_traverse.get()[1]
            if self.is_terminal(word) and word not in self.language and len(word) < SEARCH_DEPTH:
                self.language[word] = tuple(path)
            else:
                # There are variables in the word
                for letter in word:
                    if self.is_variable(letter):
                        variable = letter
                        new_path = copy.deepcopy(path)
                        new_path.append(word)
                        for substitution in self._transitions[variable]:
                            substituted = word.replace(variable, substitution, 1)
                            # Add to traversal list
                            if substituted not in to_traverse_set:
                                to_traverse_set.add(substituted)
                                to_traverse.put((len(substituted), (substituted, new_path)))

    def is_valid_substitution(self, transition: str):
        return all(self.is_terminal(l) or self.is_variable(l) for l in transition)

    def is_terminal(self, word: str):
        return all(letter in self._alphabet for letter in word)

    def is_variable(self, letter: str):
        return letter in self._variables


def grammar_check(is_in_language: Callable[[str], bool], grammar: CFG):
    success = True
    sigma_star = [''.join(i) for j in range(SEARCH_DEPTH) for i in itertools.product(grammar._alphabet, repeat=j)]
    actual_language = [i for i in sigma_star if is_in_language(i)]
    try:
        grammar.generate_n_words(len(actual_language))
    except Exception:
        print(
            f"Timed out!\nIncrease TIMEOUT if the following amount of found words is not identical between runs:\n {len(grammar.language)}")
    cfg_language = list(sorted((grammar.language.keys()), key=lambda i: len(i)))
    bad_words = [i for i in cfg_language if not is_in_language(i)]
    if len(bad_words) > 0:
        success = False
        prompt = f"{len(bad_words)} words were in the cfg even though they aren't in the language.\n"
        show_to_user(prompt, bad_words, grammar)
    else:
        prompt = f"all {len(cfg_language)} words in your cfg's language are legal."
        show_to_user(prompt, cfg_language, grammar)

    difference = set(actual_language) - set(cfg_language)
    if len(difference):
        success = False
        diff = list(sorted(difference, key=lambda i: len(i)))
        print(f"Out of a total of {len(actual_language)} words your language missed {len(difference)} words:\n")
        for i, word in enumerate(diff):
            print(f"{word}  ", end="")
            if i % LINE_FEED_BUFFER_SIZE == 0 and i >= LINE_FEED_BUFFER_SIZE:
                answer_2 = input("print more? y/n")
                if answer_2 not in ["Y", "y"]:
                    break

    else:
        print(f"Your language didn't miss any of the first {len(actual_language)} words in L")
    print("Well Done, you succeeded!") if success else print("Try again.")


def show_to_user(prompt, word_list: List[str], grammar: CFG):
    print(prompt)
    for i, word in enumerate(word_list):
        print(f"{word}, path to word: {'->'.join(grammar.language[word])}->{word}")
        if i % LINE_FEED_BUFFER_SIZE == 0 and i >= LINE_FEED_BUFFER_SIZE:
            answer_2 = input("print more? y/n")
            if answer_2 not in ["Y", "y"]:
                return


if __name__ == "__main__":
    # Usage Example

    # The following functions determine whether a word is in a given language.
    def is_in_lang_a(word: str):
        """
        :param word:
        :return: true if the word isn't equal to itself reversed
        """
        return word != word[::-1]


    def is_in_lang_b(word: str):
        """
        :param word:
        :return: true if the number of zeros is equal to the number of ones
        """
        return word.count('0') == word.count('1')


    def is_in_lang_c(word):
        return all(word[:i].count('0') >= word[:i].count('1') for i in range(len(word) + 1))


    # this is V (the variables)
    a_variables = {'S', 'R'}
    b_variables = {'S'}

    # this is Sigma (the terminals)
    one_and_zero = {'0', '1'}

    # this is the transition function R
    a_transitions = {
        'S': ['R', '1'],
        'R': ['RRR1', 'R0S0', 'R1', 'R0S'],
    }
    b_transitions = {
        # empty string is the empty word epsilon
        'S': ['SS', 'SSS', '', ]
    }

    # this is the constructor for the CFG
    a_cfg = CFG(a_variables, one_and_zero, a_transitions, 'S')
    b_cfg = CFG(b_variables, one_and_zero, b_transitions, 'S')

    # this is the program
    grammar_check(is_in_language=is_in_lang_a, grammar=a_cfg)
    grammar_check(is_in_language=is_in_lang_b, grammar=b_cfg)
