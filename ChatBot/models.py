from django.db import models
from django.contrib.auth.models import User

from django.utils.text import slugify

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True)  # Title can be auto-generated or renamed by user

    def generate_auto_title(self):
        """Generate a title based on session messages."""
        first_message = self.messages.first()  # Fetch the first message in the session
        if first_message and first_message.question:
            auto_title = ' '.join(first_message.question.split()[:5])  # First 5 words
            return auto_title.capitalize()
        return "New Chat Session"

    def update_title_if_empty(self):
        if not self.title or self.title.strip() == "New Session":
            self.title = self.generate_auto_title()
            self.save()

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    question = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.session.title} at {self.created_at}"
