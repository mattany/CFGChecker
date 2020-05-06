# CFG checker (buggy right now, don't use yet)
This is a python implementation of Context Ffree Grammar that cross references a given CFG with a given language.

## Usage instructions:
**There is a usage example in the code**

### Construct a CFG
Fill in the fields of your CFG in the main function:
-Variables (Single Characters)
-Alphabet a.k.a Terminals (Single Characters)
-The transition function (a dictionary with keys that are variables and values that are a combination of terminals and Variables
-A starting variable
Then construct your CFG.

### Create a function for the Language that you wish to check against your CFG
The function should receive a word and return true if the word is in the language, otherwise false

### Run the program
call the grammar_check function with the language and grammar that you created.
