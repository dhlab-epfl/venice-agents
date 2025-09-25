analysis_system_prompt = """You are an expert historian. You are working with 3 datasets, one detailing buildings in Venice from 1740, another one detailing buildings in Venice from 1808 and the last one listing landmarks such as churches and squares in Venice. In the Buildings datasets (1st and 2nd datasets), each row refers to a separate building, while in the Landmarks dataset (3rd dataset), each row referst to a separate landmark. The datasets are as follows:

1. 1740 Buildings Dataset (data/buildings_1740.csv) columns:
- owner_first_name -- first name of the building owner
- owner_family_name -- family name of the building owner
- owner_profession -- profession of the owner
- tenant_name -- name of the tenant in the building
- building_functions -- a comma separated list of the functions the building is used as.
- rent_price -- numerical value that refers to Italian ducats.
- parish -- parish that the building is located at
- building_functions_count -- numerical value that is the same as the length of building_functions
- longitude - float, longitude
- latitude - float, latitude

2. 1808 Buildings Dataset (data/buildings_1808.csv) columns:
- owner_first_name -- first name of the building owner
- owner_family_name -- family name of the building owner
- building_functions -- a list of the functions the building serves as
- building_functions_count -- numerical value that is the same as the length of building_functions
- building_area -- building area, in meters square.
- district -- district that the building is located at
- longitude - float, longitude
- latitude - float, latitude

3. Landmarks Dataset (data/landmarks.csv) columns:
- landmark_name -- the name of the church or the square
- landmark_type -- either "square" or "church"
- longitude - float, longitude
- latitude - float, latitude
"""

python_system_prompt = """You are a highly skilled Python developer with expertise in data analysis. You are working with 3 datasets, one detailing buildings in Venice from 1740, another one detailing buildings in Venice from 1808 and the last one listing landmarks such as churches and squares in Venice. In the Buildings datasets (1st and 2nd datasets), each row refers to a separate building, while in the Landmarks dataset (3rd dataset), each row referst to a separate landmark. The datasets are as follows:

1. 1740 Buildings Dataset (data/buildings_1740.csv) columns:
- owner_first_name -- first name of the building owner
- owner_family_name -- family name of the building owner
- owner_profession -- profession of the owner
- tenant_name -- name of the tenant in the building
- building_functions -- a comma separated list of the functions the building is used as.
- rent_price -- numerical value that refers to Italian ducats.
- parish -- parish that the building is located at
- building_functions_count -- numerical value that is the same as the length of building_functions
- longitude - float, longitude
- latitude - float, latitude

2. 1808 Buildings Dataset (data/buildings_1808.csv) columns:
- owner_first_name -- first name of the building owner
- owner_family_name -- family name of the building owner
- building_functions -- a list of the functions the building serves as
- building_functions_count -- numerical value that is the same as the length of building_functions
- building_area -- building area, in meters square.
- district -- district that the building is located at
- longitude - float, longitude
- latitude - float, latitude

3. Landmarks Dataset (data/landmarks.csv) columns:
- landmark_name -- the name of the church or the square
- landmark_type -- either "square" or "church"
- longitude - float, longitude
- latitude - float, latitude
"""

extract_direct_entity_prompt = """Given a question, your task is to hypothesise if the entities that appear in the question could correspond to a specific value in one of the columns in any of the datasets depending on the definition and data type of what should be given in the columns.
Only focus on the entities that refer to one or more columns in any of the above datasets. If none of the entities refer to a specific dataset column, respond with [].
If question only asks about 1740, entities should be matched to column(s) in dataset 1. If question only asks about 1808, entities should be matched to column(s) in dataset 2. If the question asks about both datasets, entities can be matched to column(s) in both datasets 1 and 2.
Your output should be in the format [(detected_entity_1, column_name_1, dataset_number_1), (detected_entity_2, column_name_2, dataset_number_2), ...]
Note that the same entity could correspond to a column that exist in more than 1 dataset.
Note that if an entity refers to more than one column in a single dataset, consider each column name separately.
Note that every row is about a separate building. When the questions is about a building / buildings, it is referring to the whole dataset, and not a specific column.

For example:
If the question is "Which squares are surrounded by the most diverse set of building functions from 1740?", respond with [("squares", "landmark_type", 3)], since "squares" corresponds to the "landmark_type" column in the landmarks dataset (2nd dataset).

Examples:

Question: "What is the average distance to the nearest square?"
Output: [("square", "landmark_type", 3)]

Question: "How many houses are located near Santa Maria della Salute in 1740?"
Output: [("houses", "building_functions", 1), ("Santa Maria della Salute", "landmark_name", 3)]

Question: "What is the average rent price of workshops in San Polo in 1808?"
Output: [("workshops", "building_functions", 2), ("San Polo", "district", 2)]

Question: "How many families are present in Venice in 1740 still exist in the 1808?"
Output: []

Question: "How many people live in Venice in 1808?"
Output: []

Please hypothesise, in a natural language, which entities may refer to a specific value in column(s) in the dataset(s) and respond, in the format [(detected_entity, column_name, dataset_number)].
Question: {question}

Let's think step by step:
"""

extract_reference_prompt = """Given a question, you need to match the phrases in the question with the columns in the dataset if applicable. Only focus on the phrases that refer to one or more columns in any of the above datasets. If none of the phrases refer to a specific dataset column, return an empty list.
If question only asks about 1740, phrases should be matched to column(s) in dataset 1. If question only asks about 1808, phrases should be matched to column(s) in dataset 2. If the question asks about both datasets, phrases can be matched to column(s) in both datasets 1 and 2.
Your output should be in the format [(detected_phrase_1, column_name_1, dataset_number_1), (detected_phrase_2, column_name_2, dataset_number_2), ...]
Note that the same phrase could correspond to a column that exist in more than 1 dataset.
Note that if a phrase refers to more than one column in a single dataset, consider each column name separately.
Note that every row is about a separate building. When the questions is about a building / buildings, it is referring to the whole dataset, and not a specific column.

For example:
If the question is "Which squares are surrounded by the most diverse set of building functions from 1740?", output [("squares", "landmark_type", 3), ("building functions", "building_functions", 1)], since "squares" corresponds to the "landmark_type" column in the landmarks dataset (2nd dataset), and the information about "building functions" can be found in the column "building_functions", and the question is asking about the time 1740, thus dataset 1.

Examples:

Question: "What is the average distance to the nearest square?"
Output: [("square", "landmark_type", 3)]

Question: "How many houses are located near Santa Maria della Salute in 1740?"
Output: [("houses", "building_functions", 1), ("Santa Maria della Salute", "landmark_name", 3)]

Question: "What is the average rent price of workshops in San Polo in 1808?"
Output: [("rent price", "rent_price", 2), ("workshops", "building_functions", 2), ("San Polo", "district", 2)]

Question: "How many families present in Venice in 1740 still exist in the 1808?"
Output: [("families", "owner_family_name", 1), ("families", "owner_family_name", 2)]

Question: "How many people live in Venice in 1808?"
Output: [("people", "owner_first_name", 2), ("people", "owner_family_name", 2)]

Please match the relevant phrases with their corresponding column names for the following question and respond, in a natural language, in the format [(detected_phrase, column_name, dataset_number)].
Question: {question}

Let's think step by step:
"""

extract_entity_prompt = """You are a given a mapping between a phrase and a column of a dataset. Your task is to hypothesise if the given phrase could correspond to a specific value in the matching column depending on the definition and data type of what should be given in the columns.
Respond [[True]] if you think the phrase may corresponds to one or more specific values in the corresponding column.
Respond [[False]] if you think the phrase is just referring to the corresponding column in general, not possibly not to any specific value.
Note that Dataset is referred to with its number.

For example:
If the matching is ("squares", "landmark_type", 3), respond [[True]] as "squares" is a specific value that should be found in the column "landmark_type". 
If the matching is ("building functions", "building_functions", 1), respond [[False]], as "building functions" just refers to "building_functions" column in general, and is not a spacific value we are looking for. 
Give your answer between [[]], for example [[True]] or [[False]]

Examples:

Mapping: [("square", "landmark_type", 3)]
Output: [[True]]

Mapping: [("Santa Maria della Salute", "landmark_name", 3)]
Output: [[True]]

Mapping: [("workshops", "building_functions", 2)]
Output: [[True]]

Mapping: [("families", "owner_family_name", 1)]
Output: [[False]]

Mapping: [("near houses", "building_functions", 2)]
Output: [[True]]

Mapping: [("people", "owner_family_name", 2)]
Output: [[False]]

Please hypothesise, in a natural language, if the given phrase in Mapping may refer to a specific value in the corresponding column. Resond with [[True]] or [[False]].
Mapping: {reference}
Output: """

plan_prompt = """Instruction:
First understand the problem, and provide a step-by-step data analysis plan only in natural language to answers the question using the provided datasets. Be as clear and explicit as possible in your instructions. 

You are given:
- Question
- Extracted Information of Entities: This contains the dataset and the column that the entity matches to, and the corresponding exact matches found in the dataset
- References to Corresponding Dataset and Column: This contains phrases found in the question linked to the specific dataset and column
- Expected Answer Format: yes/no or numerical or a single textual entity name

Requirements:
- The final answer should be in the format of {answer_format}.
- Use the provided entity information and datasets
- If any of the entity information or references is meaningless, ignore it.

Question:
{question}

Extracted Information of Entities:
{entities}

References to Corresponding Dataset and Column:
{references}

Step by Step Plan in Natural Language:
"""

code_prompt = """Instruction:
Your task is to generate Python code based on the provided detailed plan to answer the given question using the provided datasets.

Requirements:
- Use the necessary libraries for data analysis in Python (e.g., pandas, numpy). 
- The code should be well-structured, complete, and intended to be executed as a whole.
- Write your code in the most computationally efficient way
- Include all code in a single code block.
- Give your final answer in the format of {answer_format}.
- End your code by printing only the final answer strictly following this format: "[[final_answer]]", for example: print(f"The answer is: [[{{final_answer}}]]")
- Never use `exit()` function.

Question:
{question}

Step by Step Plan:
{plan}

Python Code:
"""

debug_prompt = """Instruction:
Debug and rewrite the provided Python code. The code follows the given plan to answer the given question using the given datasets, but it contains an error. Based on the error message, could you correct the code and provide a revised version?

You are given:
- Question
- Extracted Information of Entities: This contains the dataset and the column that the entity matches to, and the corresponding exact matches found in the dataset
- References to Corresponding Dataset and Column: This contains phrases found in the question linked to the specific dataset and column
- A detailed plan to write Python code that answers the question
- Incorrect python code that raises an error
- Corresponding error message

Requirements:
- If any of the entity information or references is meaningless, ignore it.
- Use the necessary libraries for data analysis in Python (e.g., pandas, numpy). 
- The code should be well-structured, complete and intended to be executed as a whole.
- Write your code in the most computationally efficient way
- All of your code should be included in a single code block.
- Give your final answer in the format of {answer_format}.
- End your code by printing only the final answer strictly following this format: "[[final_answer]]", for example: print(f"The answer is: [[{{final_answer}}]]")
- Never use `exit()` function.

Question:
{question}

Extracted Information of Entities:
{entities}

References to Corresponding Dataset and Column:
{references}

Step by Step Plan:
{plan}

Incorrect Python Code:
{code}

Error Message:
{error_message}

Corrected Python Code:
"""

num_row_prompt = """Instruction:
You will be given a question, the assistant's code to answer the question, and the final output. Please modify the last part of the code to print the number of rows of the final dataset used to get the final output.

Requirements:
- Copy the original code and modify only the last part.
- The modified code should be complete and executable as a whole.
- All of your code should be included in a single code block.
- End your code by printing only the number of rows of the final data frame strictly following this format: "[[num_rows]]", for example: print(f"The number of rows used is: [[{{num_rows}}]]")
- Never use `exit()` function.

Goal:
Execute the modified code to get the number of rows used to answer the question.

Question:
{question}

Python Code:
{code}

Output:
{code_output}

New Python Code:
"""