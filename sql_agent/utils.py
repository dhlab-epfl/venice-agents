from langchain_community.utilities import SQLDatabase

from typing import List
from collections import Counter
import re

def get_majority_vote(answers: List[str], num_beams: int):
    answers = ["ERROR" if "error" in answer else answer for answer in answers]
    most_common_answer, most_common_count = Counter(answers).most_common(1)[0]
    if most_common_answer == "ERROR":
        if most_common_count == num_beams:
            return most_common_answer
        else:
            return Counter(answers).most_common(2)[1][0]
    else:
        return most_common_answer

def check_sql_executability(query: str, db: SQLDatabase):
    try:
        return db.run(query)
    except Exception as e:
        return str(e)

def post_process(sql_queries: List[str]):
    """clean the output"""
    # split on ;
    sql_queries = [query.split(';')[0].strip() + ';' for query in sql_queries]
    
    # replace ' with ''
    sql_queries = [re.sub(r"([a-z])'([a-z])",r"\1''\2", query) for query in sql_queries]

    return sql_queries

def get_prompt(
    table_metadata: str = "table catastici , columns = [ catastici.Property_ID ( integer ) , catastici.Owner_ID ( integer ) , catastici.Owner_First_Name ( text ) , catastici.Owner_Family_Name ( text ) , catastici.Property_Type ( text ) , catastici.Rent_Income ( integer ) , catastici.Property_Location ( text )]",
    columns_info: str  =  "Property_ID -- Primary key ; Owner_ID -- Unique ID of each owner of the property ; Owner_First_Name -- First name of the owner of the property ; Owner_Family_Name -- Family name of the owner of the property ; Property_Type -- Specific type of the property given in Italian ; Rent_Income -- Rent price of the property that the owner receives as income, given in Venice ancient gold coin ducats ; Property_Location -- Ancient approximate toponym of the property given in Italian"
):
    prompt = f"""database schema :
{table_metadata}
columns info :
{columns_info}
primary key :
catastici.Property_ID
matched contents : {{matched_contents}}
{{question}}
"""
    return prompt

def get_matched_contents(
    question: str,
    db: SQLDatabase,
    fields: List[str] = ["Property_ID","Owner_ID","Owner_First_Name","Owner_Family_Name","Property_Type","Rent_Income","Property_Location"]
):
    # find the keywords
    keywords = re.findall(r'"(.*?)"', question)
    if len(keywords) == 0:
        return "None"

    # get the matched keywords
    matched_contents = []
    for keyword in keywords:
        for field in fields:
            if len(db.run(f"""SELECT * FROM catastici WHERE "{field}" = "{keyword}" LIMIT 1;""")) > 0:
                matched_contents.append(f"catastici.{field} = '{keyword}'")
                break
    return "\n".join(matched_contents)