import streamlit as st
import psycopg2
import os
import re
import pandas as pd
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

st.title("Chat with Your Database 🤖")
st.write("📊 Enter a question about the Database!")
user_input = st.text_area(" Enter your question:",
                          placeholder="Enter your query here")

schema_details = """
CREATE TABLE dept (
    dept_id INT PRIMARY KEY,           -- Department ID (Primary Key)
    dept_name VARCHAR(100) NOT NULL    -- Department Name
);

CREATE TABLE job_title (
    job_id INT PRIMARY KEY,            -- Job ID (Primary Key)
    job_title_name VARCHAR(100) NOT NULL  -- Job Title (e.g., Software Engineer)
);

CREATE TABLE employee (
    emp_id INT PRIMARY KEY,               -- Employee ID (Primary Key)
    emp_name VARCHAR(100) NOT NULL,       -- Employee Name
    hire_date DATE,                       -- Date the employee was hired
    salary DECIMAL(10, 2),                -- Employee's salary
    dept_id INT,                          -- Department ID (Foreign Key)
    job_id INT,                           -- Job Title ID (Foreign Key)
    FOREIGN KEY (dept_id) REFERENCES dept(dept_id),  -- Link to dept table
    FOREIGN KEY (job_id) REFERENCES job_title(job_id) -- Link to job_title table
);

CREATE TABLE employee_address (
    address_id INT PRIMARY KEY,         -- Address record ID (Primary Key)
    emp_id INT,                         -- Employee ID (Foreign Key)
    street_address VARCHAR(255),        -- Street address
    city VARCHAR(100),                  -- City
    state VARCHAR(100),                 -- State
    zip_code VARCHAR(20),               -- Zip code
    FOREIGN KEY (emp_id) REFERENCES employee(emp_id) -- Link to the employee
);

CREATE TABLE employee_contact (
    contact_id INT PRIMARY KEY,         -- Contact record ID (Primary Key)
    emp_id INT,                         -- Employee ID (Foreign Key)
    phone_number VARCHAR(20),           -- Employee's phone number
    email VARCHAR(100),                 -- Employee's email address
    FOREIGN KEY (emp_id) REFERENCES employee(emp_id) -- Link to the employee
);
"""

template = PromptTemplate(input_variables=["schema_details", "user_input"],
                          template="""
    You are an expert SQL query generator. Convert the following natural language request into a fully functional PostgreSQL query.

    Schema details: {schema_details}

    ### User Request:
    "{user_input}"

    ### Output:
    Generate only the SQL query without any explanation or other text.
    """)


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
    if any(
            re.search(pattern, response, re.IGNORECASE)
            for pattern in forbidden_patterns):
        st.error("Unsafe SQL query detected!")
        return None

    return response


if st.button("Retrieve from Database 🔍"):
    if user_input:
        formatted_prompt = template.format(schema_details=schema_details,
                                           user_input=user_input)
        response = llm.invoke(formatted_prompt)
        query = response.content if hasattr(response,
                                            "content") else str(response)

        cleaned_query = clean_query(query)

        if cleaned_query:
            try:
                conn = psycopg2.connect(user=USER,
                                        password=PASSWORD,
                                        host=HOST,
                                        port=PORT,
                                        dbname=DBNAME)
                cursor = conn.cursor()
                cursor.execute(cleaned_query)
                columns = [desc[0] for desc in cursor.description]
                result = cursor.fetchall()
                conn.close()

                df = pd.DataFrame(result, columns=columns)
                st.write("Query Results:")
                st.dataframe(df)
                st.code(cleaned_query, language="sql")
            except Exception as e:
                st.error(f"Database error: {e}")
