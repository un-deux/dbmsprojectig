import streamlit as st
import psycopg2
import os
import re
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")
API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)


st.title("Chat with your Database")
st.write("Enter a question about the Database!")


user_input = st.text_input("Enter your question:", "")


schema_details = """
CREATE TABLE employee (
    employeeid SERIAL PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    title TEXT,
    hiredate DATE,
    email TEXT NOT NULL,
    salary NUMERIC NOT NULL
);
"""

template = PromptTemplate(
    input_variables=["schema_details", "user_input"],
    template="""
    You are an expert PostgreSQL query generator. Convert the following natural language request into a fully functional PostgreSQL query.

    Schema details: {schema_details}

    ### User Request:
    "{user_input}"

    ### Output:
    Generate only the PostgreSQL query without any explanation or other text.
    """
)

def clean_query(response):
    """Sanitizes the SQL query to ensure it's a safe SELECT statement."""

    response = response.replace("```sql", "").replace("```", "").strip()

    if not re.match(r"^\s*SELECT\s", response, re.IGNORECASE):
        st.error("Only SELECT queries are allowed!")
        return None

    forbidden_patterns = [
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|CREATE|GRANT|REVOKE)\b",
        r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|CREATE|GRANT|REVOKE)"
    ]
    if any(re.search(pattern, response, re.IGNORECASE) for pattern in forbidden_patterns):
        st.error("Unsafe SQL query detected!")
        return None

    return response

if st.button("Retrieve from Database"):
    if user_input:
        formatted_prompt = template.format(schema_details=schema_details, user_input=user_input)
        response = llm.invoke(formatted_prompt)
        query = response.content if hasattr(response, "content") else str(response)
        cleaned_query = clean_query(query)

        if cleaned_query:


            try:
                conn = psycopg2.connect(
                    user=USER,
                    password=PASSWORD,
                    host=HOST,
                    port=PORT,
                    dbname=DBNAME
                )
                cursor = conn.cursor()
                cursor.execute(cleaned_query)
                result = cursor.fetchall()
                conn.close()

                st.write("Query Results:")
                st.dataframe(result)
                st.code(cleaned_query, language="sql")
            except Exception as e:
                st.error(f"Database error: {e}")