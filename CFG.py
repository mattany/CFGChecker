import copy
import itertools
from queue import PriorityQueue
import sys

from typing import Set, Dict, List, Callable, Iterable


# Change this to a higher number if you want to be more sure. Time will rise exponentialy. This is in practice
# The Max word length plus one
SEARCH_DEPTH = 7


LINE_FEED_BUFFER_SIZE = 25
SIGMA_STAR_WORD_AMOUNT = 2 ** SEARCH_DEPTH - 1
CFG_WORD_AMOUNT = 2 * SIGMA_STAR_WORD_AMOUNT

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
        self.free_search()

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

    def free_search(self):
        # maintain priority queue for BFS-like traversal
        # element[0] = priority, element[1][0] = word, element[1][1] = path to word
        to_traverse = PriorityQueue()
        # maintain set for fast access
        to_traverse_set = {self._start}

        to_traverse.put((0, (self._start, list())))
        while to_traverse.qsize() > 0 and len(self.language) < CFG_WORD_AMOUNT:
            word, path = to_traverse.get()[1]
            if self.is_terminal(word) and word not in self.language:
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
    cfg_language = list(sorted((grammar.language.keys()), key=lambda i: len(i)))
    bad_words = [i for i in cfg_language if not is_in_language(i)]
    if len(bad_words) > 0:
        success = False
        prompt = f"{len(bad_words)} words were in the cfg even though they aren't in the language.\n" \
                 f"Would you like to see the paths to them? y/n?"
        show_to_user(prompt, bad_words, grammar)
    else:
        prompt = f"all {len(cfg_language)} words in your cfg's language are legal. Would you like to see the paths to them? y/n?"
        show_to_user(prompt, cfg_language, grammar)
    sigma_star = [''.join(i) for j in range(SEARCH_DEPTH) for i in itertools.product("10", repeat=j)]
    actual_language = [i for i in sigma_star if is_in_language(i)]

    difference = set(actual_language) - set(cfg_language)
    if len(difference):
        success = False
        print(
            f"Out of a total of {len(actual_language)} words your language missed the following {len(difference)} words:\n")
        print(list(sorted(difference, key=lambda i: len(i))))
    else:
        print(f"Your language didn't miss any of the first {SIGMA_STAR_WORD_AMOUNT} words")
    print("Well Done, you succeeded!") if success else print("Try again.")


def show_to_user(prompt, word_list: List[str], grammar: CFG):
    answer = input(prompt)
    if answer in ["Y", 'y']:
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
        return all(word[:i].count('0') >= word[:i].count('1') for i in range(len(word)))


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
