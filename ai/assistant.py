"""AI analysis with safe fallbacks for the meeting assistant."""
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as error:
        print(f"Gemini client unavailable: {error}")
        return None

def detect_question_locally(message):
    words = message.lower().strip().split()
    return bool("?" in message or (words and words[0] in {"what", "why", "how", "when", "where", "who", "which", "can", "could", "would", "should", "is", "are", "do", "does", "will"}))

def detect_topic_locally(message):
    topics = {"Project": ("project", "development", "feature", "module"), "Programming": ("python", "java", "code", "programming", "api", "database"), "Meeting": ("meeting", "discussion", "agenda"), "Schedule": ("schedule", "time", "deadline", "tomorrow", "today"), "Task": ("task", "work", "assignment", "responsibility"), "Problem": ("problem", "issue", "error", "bug")}
    text = message.lower()
    return next((topic for topic, words in topics.items() if any(word in text for word in words)), "General Discussion")

def _field(text, label, default):
    for line in text.splitlines():
        if line.strip().lower().startswith(f"{label.lower()}:"):
            return line.split(":", 1)[1].strip() or default
    return default

def _unavailable_analysis(is_question, topic):
    return {"is_question": is_question, "topic": topic, "answer": "AI answer temporarily unavailable. Please try again." if is_question else "Not a question.", "suggestion": "AI analysis is temporarily unavailable. The meeting transcript is still being saved."}

def analyze_message(message):

    message = message.strip()

    if not message:
        return {
            "is_question": False,
            "topic": "General Discussion",
            "answer": "",
            "suggestion": "Please enter a meeting message."
        }

    # Local detection is always available
    local_question = detect_question_locally(message)
    local_topic = detect_topic_locally(message)

    client = _get_client()

    if client is None:
        return _unavailable_analysis(
            local_question,
            local_topic
        )

    prompt = f"""
You are an AI Meeting Assistant analyzing an authorized live meeting.

Analyze this meeting message:

"{message}"

Return exactly four lines:

Question: Yes or No
Topic: short specific topic in 2 to 5 words
Answer: direct useful answer, or Not a question.
Suggestion: one concise practical suggestion

Rules:
- Detect the topic from the actual meaning.
- Do not use a fixed topic list.
- Keep the topic specific and short.
- Answer the actual question.
- Do not invent information.
- If it is not a question, write "Not a question."
"""

    # Try Gemini up to 3 times
    for attempt in range(3):

        try:

            print(
                f"Gemini analysis attempt "
                f"{attempt + 1}/3: {message}"
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            text = (response.text or "").strip()

            if not text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            result = {
                "is_question": _field(
                    text,
                    "Question",
                    "No"
                ).lower().startswith("yes"),

                "topic": _field(
                    text,
                    "Topic",
                    local_topic
                ),

                "answer": _field(
                    text,
                    "Answer",
                    "No answer generated."
                ),

                "suggestion": _field(
                    text,
                    "Suggestion",
                    "Continue the discussion."
                )
            }

            print("Gemini result:", result)

            return result

        except Exception as error:

            print(
                f"Gemini AI Error "
                f"(attempt {attempt + 1}/3): {error}"
            )

            # Wait before retrying
            import time
            time.sleep(1.5)

    # All attempts failed
    print("Gemini failed after 3 attempts.")

    return _unavailable_analysis(
        local_question,
        local_topic
    )

    prompt = f'''You are an AI Meeting Assistant analyzing an authorized live meeting.

Analyze the following meeting message.

Return exactly these four lines:

Question: Yes or No
Topic: a short specific topic in 2 to 5 words
Answer: if it is a question, give a direct and useful answer; otherwise write Not a question.
Suggestion: one concise practical suggestion related to the discussion.

Rules:
- Detect the topic from the actual meaning of the message.
- Do not use a fixed topic list.
- Do not always return "General Discussion".
- Make the topic specific when possible.
- If the message is about multiple things, choose the main topic.
- Keep the topic short.
- Answer the actual question when there is one.
- Do not invent information.

Message:
{message}
'''
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = (response.text or "").strip()
        return {"is_question": _field(text, "Question", "No").lower().startswith("yes"), "topic": _field(text, "Topic", topic), "answer": _field(text, "Answer", "No answer generated."), "suggestion": _field(text, "Suggestion", "Continue the discussion.")}
    except Exception as error:
        print(f"Gemini AI Error: {error}")
        return _unavailable_analysis(is_question, topic)

def generate_meeting_summary(transcript, title="AI Meeting Assistant", participants=None):
    participants = participants or []
    client = _get_client()
    if transcript.strip() and client is not None:
        prompt = f'''Summarize this authorized meeting transcript. Return sections exactly named: Meeting Title, Date/Time, Participants, Short Summary, Key Points, Decisions, Action Items, Important Questions Discussed. Be concise.\n\nTranscript:\n{transcript}'''
        try:
            return (client.models.generate_content(model=MODEL_NAME, contents=prompt).text or "").strip()
        except Exception as error:
            print(f"Gemini Summary Error: {error}")
    return "[Basic transcript-based summary; AI generation was unavailable.]\n\n" + _local_summary(transcript, title, participants)

def _local_summary(transcript, title, participants):
    lines = [line.strip() for line in transcript.splitlines() if line.strip()]
    messages = [line.split(":", 1)[-1].strip() for line in lines]
    questions = [item for item in messages if detect_question_locally(item)][:5]
    actions = [item for item in messages if any(term in item.lower() for term in ("will ", "need to", "assigned", "action item", "task"))][:5]
    decisions = [item for item in messages if any(term in item.lower() for term in ("decided", "agreed", "final decision", "will use"))][:5]
    def bullets(items, empty): return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"
    return f'''Meeting Title\n{title}\n\nDate/Time\nGenerated from the stored transcript\n\nParticipants\n{", ".join(participants) or "No participants recorded"}\n\nShort Summary\n{len(messages)} transcript message(s) were recorded.\n\nKey Points\n{bullets(messages[:5], "No key points detected.")}\n\nDecisions\n{bullets(decisions, "No decisions detected.")}\n\nAction Items\n{bullets(actions, "No action items detected.")}\n\nImportant Questions Discussed\n{bullets(questions, "No questions detected.")}'''
