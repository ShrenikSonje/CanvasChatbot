from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('canvas/', views.chat, name='chat'),  # Redirect to the latest session or create new
    path('canvas/<int:session_id>/', views.chat, name='chat'),  # Access a specific chat session
    path('stream_response/', views.stream_response, name='stream_response'),  # Chatbot response streaming
    path('login/', views.login_view, name='login'),  # Login page
    path('logout/', views.logout_view, name='logout'),  # Logout function
    path('create_session/', views.create_session, name='create_session'),  # Create new session
    path('edit_session_title/<int:session_id>/', views.edit_session_title, name='edit_session_title'),  # Edit session
    path('delete_session/<int:session_id>/', views.delete_session, name='delete_session'),  # Delete session
    path('chat_history/', views.chat_history_view, name='chat_history'),
]
