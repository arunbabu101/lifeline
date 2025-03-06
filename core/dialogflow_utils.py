import google.cloud.dialogflow_v2 as dialogflow
import os
from django.conf import settings

def detect_intent(text, session_id, project_id, language_code='en'):
    """
    Sends a user query to Dialogflow and returns the chatbot's response.
    """
    # Explicitly set credentials path before creating the client
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
    
    # Create the session client
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    
    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    
    return response.query_result.fulfillment_text