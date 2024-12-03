from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.apps import apps
from .models import ChatSession, ChatMessage
import json
from .responses import PREDEFINED_RESPONSES  # Import predefined responses


# Access the chatbot_instance initialized in apps.py
chatbot_instance = apps.get_app_config('ChatBot').chatbot_instance

def index(request):
    """Landing page for the chatbot application."""
    return render(request, 'chatbot/index.html')

def login_view(request):
    """User login view with authentication handling."""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat')  # Redirect to chat after successful login
        else:
            return render(request, 'chatbot/login.html', {'error': 'Invalid username or password'})
    return render(request, 'chatbot/login.html')

@login_required
def logout_view(request):
    """Logs out the user and redirects to the index page."""
    logout(request)
    return redirect('index')

@login_required
def chat(request, session_id=None):
    """
    Handles chat interactions within a session.
    """
    if session_id:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        # Find the latest session or create a new one
        session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
        if not session:
            session = ChatSession.objects.create(user=request.user, title="New Session")
            return redirect('chat', session_id=session.id)

    messages = session.messages.all()

    if request.method == 'POST':
        user_message = request.POST.get('user_input')
        if user_message:
            # Save the user's message
            user_message_obj = ChatMessage(session=session, question=user_message, response="")

            # Save bot's response in the database
            user_message_obj.response = bot_response
            user_message_obj.save()

            # Update session title if needed
            session.update_title_if_empty()

            # Refresh messages to include the latest interaction
            messages = session.messages.all()

    return render(request, 'chatbot/canvas.html', {
        'messages': messages,
        'sessions': ChatSession.objects.filter(user=request.user),
        'current_session': session
    })


@login_required
def create_session(request):
    """Creates a new chat session and redirects to it."""
    session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
    if session and session.messages.exists():
        session = ChatSession.objects.create(user=request.user, title="New Session")
    elif not session:
        session = ChatSession.objects.create(user=request.user, title="New Session")
    return redirect('chat', session_id=session.id)

@login_required
def edit_session_title(request, session_id):
    """Edits the title of a specific chat session."""
    if request.method == 'POST':
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        data = json.loads(request.body)
        new_title = data.get('title', 'Untitled Session')
        session.title = new_title
        session.save()
        return JsonResponse({'success': True, 'title': session.title})
    return JsonResponse({'success': False})

@login_required
def delete_session(request, session_id):
    """Deletes a specific chat session."""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()

    remaining_sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    if remaining_sessions.exists():
        return JsonResponse({'success': True, 'redirect_url': f"/canvas/{remaining_sessions.first().id}/"})
    else:
        new_session = ChatSession.objects.create(user=request.user, title="New Session")
        return JsonResponse({'success': True, 'redirect_url': f"/canvas/{new_session.id}/"})


def build_context(messages, user_input):
    """
    Builds the context for the chatbot using previous messages and the user's input.
    Args:
        messages (QuerySet): A queryset of ChatMessage objects.
        user_input (str): The user's current input.
    Returns:
        str: Formatted context string.
    """
    context = ""
    for message in reversed(messages):  # Maintain chronological order
        context += f"User: {message.question}\nBot: {message.response}\n"
    context += f"User: {user_input}\nBot:"
    return context


def get_predefined_response(query: str):
    """
    Check if the query matches a predefined response.
    """
    query = query.strip().lower()  # Normalize the query to lowercase
    return PREDEFINED_RESPONSES.get(query, None)


@csrf_exempt
def stream_response(request):
    """
    Streams chatbot responses in real-time and saves them in the database.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")
        session_id = data.get("session_id")

        if user_message and session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)

            # Save the user's message
            user_message_obj = ChatMessage(session=session, question=user_message, response="")
            user_message_obj.save()

            session.update_title_if_empty()

            previous_messages = session.messages.order_by('-created_at')[:5]
            context = build_context(previous_messages, user_message)

            # Check for predefined responses
            predefined_response = get_predefined_response(user_message)
            if predefined_response:
                # Save predefined response in the database
                user_message_obj.response = predefined_response
                user_message_obj.save()

                # Stream predefined response
                def generate_streamed_response():
                    for token in predefined_response.split():
                        yield token + ' '  # Streaming the predefined response word by word

                return StreamingHttpResponse(generate_streamed_response(), content_type="text/plain")

            # If no predefined response, stream LLM response
            def generate_streamed_response(query):
                response_text = ""
                try:
                    for token in chatbot_instance.get_response_stream(query):
                        response_text += token
                        yield token  # Stream token to client

                    # Save LLM response in the database
                    user_message_obj.response = response_text
                    user_message_obj.save()
                except Exception as e:
                    yield f"Error: {str(e)}"

            return StreamingHttpResponse(generate_streamed_response(context), content_type="text/plain")

    return JsonResponse({'error': 'Invalid request'}, status=400)



@login_required
def chat_history_view(request):
    """Displays the chat history with messages for each session."""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'chatbot/chat_history.html', {'sessions': sessions})
