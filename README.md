# CFG checker
This is a python implementation of Context Ffree Grammar that cross references a given CFG with a given language.
The program does not constitute a formal proof since there are infinite words in some CFGs, however it does give good
indication of whether the language fits the grammar.

## Usage instructions:
**There is a usage example in the code**

### Construct a CFG
Fill in the fields of your CFG in the main function:
- Variables (Single Characters)
- Alphabet a.k.a Terminals (Single Characters)
- The transition function (a dictionary with keys that are variables and values that are a combination of terminals and Variables
- A starting variable
Then construct your CFG.

### Create a function for the Language that you wish to check against your CFG
The function should receive a word and return true if the word is in the language, otherwise false

### Run the program
call the grammar_check function with the language and grammar that you created.

### notes

You can choose up to what length of word you want to check with the parameter SEARCH_DEPTH.
For instance if SEARCH_DEPTH is set to 12, the program will check all of the possible words of length of up to 12 that 
are in L (according to the function that describes the language, as described above).
