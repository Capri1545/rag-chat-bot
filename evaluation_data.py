import os

# Define the content for evaluation_data.csv
evaluation_data_content = """question,expected_answer_snippet,is_in_kb
What is the Sun?,The Sun is the star at the center of the Solar System.,TRUE
How massive is Earth compared to the Sun?,Its mass is about 330,000 times that of Earth, accounting for about 99.86% of the total mass of the Solar System.,TRUE
What are the two moons of Mars?,Mars has two small moons, Phobos and Deimos.,TRUE
What is the Great Red Spot?,Its most famous feature is the Great Red Spot, a persistent anticyclonic storm larger than Earth.,TRUE
How many planets are in the Solar System?,These objects include eight planets, five dwarf planets, numerous moons, and billions of small Solar System bodies.,TRUE
What are the four inner planets?,Mercury, Venus, Earth, and Mars,TRUE
What is the largest planet in the Solar System?,Jupiter is the fifth planet from the Sun and the largest in the Solar System.,TRUE
When did Earth form?,Earth formed over 4.5 billion years ago.,TRUE
What is the name of Earth's only natural satellite?,the Moon,TRUE
What is Mars often referred to as?,the "Red Planet",TRUE
What is the capital of France?,N/A,FALSE
Tell me a joke.,N/A,FALSE
What is the color of the sky?,N/A,FALSE
What is the population of Earth?,N/A,FALSE
Who was the first person on the Moon?,N/A,FALSE
What is the best programming language?,N/A,FALSE
How many days in a week?,N/A,FALSE
Who invented the internet?,N/A,FALSE
"""

# Define the path for the evaluation data file
evaluation_data_file_path = "data/evaluation_data.csv"

# Ensure the 'data' directory exists
os.makedirs("data", exist_ok=True)

# Write the content to the CSV file
with open(evaluation_data_file_path, "w") as f:
    f.write(evaluation_data_content)

print(f"'{evaluation_data_file_path}' has been created/updated with the provided content.")
print("You can now proceed to create the `evaluate.py` script and run the evaluation.")