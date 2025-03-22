from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Set up Gemini model
import os
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ["GEMINI_API_KEY"])

# Define a prompt template
template = PromptTemplate(
    input_variables=["topic"],
    template="Explain {topic} in simple terms with examples."
)

# Format the prompt
formatted_prompt = template.format(topic="Quantum Computing")

# Run it through Gemini
response = llm.predict(formatted_prompt)
print(response)
