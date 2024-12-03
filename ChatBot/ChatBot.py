import os
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from .responses import PREDEFINED_RESPONSES  


class ChatbotManager:
    def __init__(self, device="cpu", llm_model="finetunepodcast_V01:latest"):
        self.device = device
        self.llm_model = llm_model
    

        # Initialize the Fine-Tuned LLM
        self.llm = OllamaLLM(model=self.llm_model)

        # Define a system prompt for context-aware behavior
        self.prompt_template = """
"Your name is Canvas. You are an expert in the printing industry and you generally keep your answers brief unless asked for detail."

Question: {question}
Answer:
"""
        # Initialize the prompt
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=['question']
        )

    def get_predefined_response(self, query: str):
        """
        Check if the query matches a predefined response.
        """
        query = query.strip().lower()  # Normalize the query to lowercase
        return PREDEFINED_RESPONSES.get(query, None)

    def get_response_stream(self, query: str):
        """
        Use the fine-tuned LLM directly to generate answers.
        """
        # First, check for predefined responses
        predefined_response = self.get_predefined_response(query)
        if predefined_response:
            yield predefined_response  # Immediately return the predefined response
            return  # Exit to avoid LLM processing

        # If no predefined response, fall back to LLM
        prompt = self.prompt.template.format(question=query)
        response_stream = self.llm._stream(prompt)
        for token in response_stream:
            yield token.text
