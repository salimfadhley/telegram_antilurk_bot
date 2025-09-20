"""Default puzzles for the bot."""

from typing import List
from .schemas import Puzzle, PuzzleChoice


def get_default_puzzles() -> List[Puzzle]:
    """Generate default puzzles for first-time setup."""
    puzzles = []

    # Arithmetic puzzles
    arithmetic_data = [
        ("What is 2 + 2?", ["3", "4", "5", "6"], 1),
        ("What is 10 - 3?", ["5", "6", "7", "8"], 2),
        ("What is 3 × 4?", ["10", "11", "12", "13"], 2),
        ("What is 15 ÷ 3?", ["3", "4", "5", "6"], 2),
        ("What is 7 + 8?", ["13", "14", "15", "16"], 2),
        ("What is 20 - 12?", ["6", "7", "8", "9"], 2),
        ("What is 6 × 7?", ["40", "41", "42", "43"], 2),
        ("What is 24 ÷ 6?", ["3", "4", "5", "6"], 1),
        ("What is 9 + 6?", ["13", "14", "15", "16"], 2),
        ("What is 18 - 9?", ["7", "8", "9", "10"], 2),
        ("What is 5 × 5?", ["20", "25", "30", "35"], 1),
        ("What is 30 ÷ 5?", ["4", "5", "6", "7"], 2),
        ("What is 11 + 11?", ["20", "21", "22", "23"], 2),
        ("What is 25 - 15?", ["8", "9", "10", "11"], 2),
        ("What is 8 × 3?", ["22", "23", "24", "25"], 2),
        ("What is 36 ÷ 9?", ["3", "4", "5", "6"], 1),
        ("What is 13 + 7?", ["18", "19", "20", "21"], 2),
        ("What is 50 - 25?", ["23", "24", "25", "26"], 2),
        ("What is 4 × 9?", ["34", "35", "36", "37"], 2),
        ("What is 48 ÷ 8?", ["4", "5", "6", "7"], 2),
        ("What is 17 + 13?", ["28", "29", "30", "31"], 2),
        ("What is 100 - 45?", ["53", "54", "55", "56"], 2),
        ("What is 7 × 6?", ["40", "41", "42", "43"], 2),
        ("What is 63 ÷ 7?", ["7", "8", "9", "10"], 2),
        ("What is 19 + 21?", ["38", "39", "40", "41"], 2),
    ]

    for i, (question, choices_text, correct_idx) in enumerate(arithmetic_data):
        choices = [
            PuzzleChoice(text=text, is_correct=(j == correct_idx))
            for j, text in enumerate(choices_text)
        ]
        puzzles.append(Puzzle(
            id=f"arithmetic_{i+1:03d}",
            type="arithmetic",
            question=question,
            choices=choices
        ))

    # Common sense puzzles
    common_sense_data = [
        ("Where does a snail live?", ["In his shell", "In outer space", "In our thoughts and prayers", "In our collective imagination"], 0),
        ("What color is a ripe banana?", ["Red", "Blue", "Yellow", "Purple"], 2),
        ("What do fish live in?", ["Trees", "Water", "Sand", "Air"], 1),
        ("How many legs does a dog have?", ["Two", "Three", "Four", "Six"], 2),
        ("What is frozen water called?", ["Steam", "Ice", "Sand", "Oil"], 1),
        ("Which is bigger?", ["Mouse", "Elephant", "Ant", "Fly"], 1),
        ("What do we use to see?", ["Ears", "Nose", "Eyes", "Mouth"], 2),
        ("What season comes after summer?", ["Winter", "Spring", "Fall", "Summer"], 2),
        ("How many days are in a week?", ["Five", "Six", "Seven", "Eight"], 2),
        ("What do birds use to fly?", ["Fins", "Wings", "Legs", "Tail"], 1),
        ("What is the opposite of hot?", ["Warm", "Cold", "Wet", "Dry"], 1),
        ("Which animal says 'meow'?", ["Dog", "Cat", "Cow", "Bird"], 1),
        ("What do we wear on our feet?", ["Hat", "Gloves", "Shoes", "Scarf"], 2),
        ("What shape is a ball?", ["Square", "Triangle", "Round", "Rectangle"], 2),
        ("What do plants need to grow?", ["Darkness", "Sunlight", "Cold", "Rocks"], 1),
        ("Which is a fruit?", ["Carrot", "Potato", "Apple", "Onion"], 2),
        ("What do we use to write?", ["Spoon", "Pen", "Fork", "Plate"], 1),
        ("How many months in a year?", ["Ten", "Eleven", "Twelve", "Thirteen"], 2),
        ("What comes from chickens?", ["Milk", "Eggs", "Wool", "Honey"], 1),
        ("Which can fly?", ["Penguin", "Ostrich", "Eagle", "Chicken"], 2),
        ("What is rain made of?", ["Sand", "Water", "Sugar", "Salt"], 1),
        ("What do we breathe?", ["Water", "Food", "Air", "Light"], 2),
        ("Which is tallest?", ["Mountain", "Hill", "Valley", "Hole"], 0),
        ("What makes honey?", ["Ants", "Bees", "Flies", "Spiders"], 1),
        ("Which is a vegetable?", ["Orange", "Banana", "Carrot", "Grape"], 2),
        ("What do we use to hear?", ["Eyes", "Ears", "Entrenching Tool", "Bethoven's 5th Symphony"], 1),
    ]

    for i, (question, choices_text, correct_idx) in enumerate(common_sense_data):
        choices = [
            PuzzleChoice(text=text, is_correct=(j == correct_idx))
            for j, text in enumerate(choices_text)
        ]
        puzzles.append(Puzzle(
            id=f"common_{i+1:03d}",
            type="common_sense",
            question=question,
            choices=choices
        ))

    return puzzles