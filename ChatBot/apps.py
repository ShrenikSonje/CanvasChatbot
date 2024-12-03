from django.apps import AppConfig
from .ChatBot import ChatbotManager

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ChatBot'

    def ready(self):
        # Initialize the chatbot instance as an attribute of ChatbotConfig
        self.chatbot_instance = ChatbotManager()
        
