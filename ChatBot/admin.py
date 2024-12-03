from django.contrib import admin

# Register your models here.
# Register your models here.
from .models import ChatSession, ChatMessage

admin.site.register(ChatSession)
admin.site.register(ChatMessage)