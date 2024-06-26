# Findings

## Taboo

### Folder Structure:

```plaintext
Root
├── Benchmark Version (e.g. V0.9)
│   ├── Model Name (vicuna-13b-t0.0--vicuna-13b-t0.0)
│       ├── Game (e.g. Taboo)
│           ├── Game Variants (e.g. 0_high_en)
│               └── episeodes (e.g episode_0)
│                   ├──  instances.json     // contains the info about the word to be guessed
│                   ├──  interactions.json  // contains information about the turns and outcomes
│                   ├──  requests.json      // contains the propmnts and answers

```

### General Info about the available Data:

A game is stored as JSON object with the following structure:

```JSON
{
  "players": {
    "GM": "Game master for taboo",
    "Player 1": "WordDescriber, text-davinci-003",
    "Player 2": "WordGuesser, text-davinci-003"}, 
  "turns": [[{
    "from": "GM",
    "to": "Player 2",
    "timestamp": "2023-06-16T10:47:47.818600",
    "action": {
      "type": "get message", 
      "content": "CLUE: Measurement of something.",
    }}
  ]]
}
```


**turn** contains an array of all turns.
The last turn indicates whether a game ended successful or not.
The turn object contains an action object with the key type. This action type can have the following values:
- "correct guess" -> indicates that a game ended with a correct guess of the player
- "invalid format" -> indicates that a game ended because the answer format was incorrect. This can happen when a related word was used or the output is not in the CLUE: \< ... \> Format
- "max turns reached" -> indicates that a game ended because the maximum amount of turns is reached
- invalid clue -> indicates that a model used a word that it is now allowed too by the game.


### Info clustered by Benchmark Version
### Taboo
| Benchmark Version | Number of Episodes | Number of Successfully Played Episodes | Number of turns | Number of target words |
|-------------------|--------------------|----------------------------------------|-----------------|------------------------|
| v0.9              | 644                | 193                                    | 226             | 52                     |
| v1.0              | 2419               | 641                                    | 739             | 57                     |
| v1.5              | 2400               | 909                                    | 1068            | 60                     |
| v1.5_quantized    | 480                | 131                                    | 163             | 51                     |
| v1.6              | 3180               | 1221                                   | 1488            | 60                     |
| v1.6_backends     | 360                | 224                                    | 326             | 53                     |
| v1.6_quantized    | 360                | 162                                    | 193             | 49                     |

### Wordle No Clue No Critic
| Benchmark Version | Number of Episodes | Number of Successfully Played Episodes | Number of turns | Number of target words |
|-------------------|--------------------|----------------------------------------|-----------------|------------------------|
| v0.9              | 269                | 6                                      | 32              | 5                      |
| v1.0              | 1211               | 20                                     | 98              | 13                     |
| v1.5              | 1200               | 65                                     | 320             | 26                     |
| v1.5_quantized    | 240                | 0                                      | 0               | 0                      |
| v1.6              | 1590               | 95                                     | 467             | 27                     |
| v1.6_backends     | 180                | 10                                     | 62              | 5                      |
| v1.6_quantized    | 180                | 3                                      | 21              | 2                      |

### Wordle With Clue No Critic
| Benchmark Version | Number of Episodes | Number of Successfully Played Episodes | Number of turns | Number of target words |
|-------------------|--------------------|----------------------------------------|-----------------|------------------------|
| v0.9              | 270                | 52                                     | 138             | 22                     |
| v1.0              | 1227               | 216                                    | 525             | 26                     |
| v1.5              | 1200               | 221                                    | 621             | 24                     |
| v1.5_quantized    | 240                | 13                                     | 22              | 6                      |
| v1.6              | 1590               | 312                                    | 865             | 27                     |
| v1.6_backends     | 180                | 36                                     | 111             | 14                     |
| v1.6_quantized    | 180                | 42                                     | 117             | 15                     |

### Wordle With Clue and Critic
| Benchmark Version | Number of Episodes | Number of Successfully Played Episodes | Number of turns | Number of target words |
|-------------------|--------------------|----------------------------------------|-----------------|------------------------|
| v0.9              | 319                | 63                                     | 330             | 24                     |
| v1.0              | 1156               | 175                                    | 860             | 26                     |
| v1.5              | 1200               | 178                                    | 1108            | 25                     |
| v1.5_quantized    | 222                | 12                                     | 54              | 8                      |
| v1.6              | 1590               | 260                                    | 1610            | 29                     |
| v1.6_backends     | 179                | 45                                     | 346             | 20                     |
| v1.6_quantized    | 180                | 31                                     | 182             | 17                     |
