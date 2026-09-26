import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")


client = genai.Client(
    api_key=api_key
)


def analyze_message(message):

    prompt = f"""
You are an AI Meeting Assistant.

Analyze the following meeting message:

"{message}"

Your task:

1. Decide whether the message is a question.
2. Identify the main topic.
3. Give a short suggestion for how the speaker should respond.
4. Keep the suggestion practical and concise.

Return the response in this format:

Question: Yes/No
Topic: <topic>
Suggestion: <suggestion>
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    ai_text = response.text

    return {
        "is_question": "Question: Yes" in ai_text,
        "topic": extract_topic(ai_text),
        "suggestion": extract_suggestion(ai_text)
    }


def extract_topic(text):

    for line in text.splitlines():

        if line.startswith("Topic:"):

            return line.replace(
                "Topic:",
                ""
            ).strip()

    return "General Discussion"


def extract_suggestion(text):

    for line in text.splitlines():

        if line.startswith("Suggestion:"):

            return line.replace(
                "Suggestion:",
                ""
            ).strip()

    return "Continue the discussion."


def generate_meeting_summary(transcript):

    prompt = f"""
You are an AI Meeting Assistant.

Analyze this meeting transcript:

{transcript}

Generate the following:

1. Short Meeting Summary
2. Important Points
3. Action Items
4. Decisions

Keep the response clear and concise.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text