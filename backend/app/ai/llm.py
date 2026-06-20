from groq import Groq

from app.core.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_answer(
    question: str,
    context: str,
    conversation_history: str = "",
) -> str:
    prompt = f"""
You are an AI customer support assistant.

Answer the user's question using:
1. The uploaded document context
2. The previous conversation history

If the answer is not present in either, say:
"I couldn't find that information in the uploaded documents."

Previous Conversation:
{conversation_history}

Document Context:
{context}

User Question:
{question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content



def stream_answer(
    question: str,
    context: str,
    conversation_history: str = "",
):
    prompt = f"""
You are an AI customer support assistant.

Answer the user's question using:
1. The uploaded document context
2. The previous conversation history

If the answer is not present in either, say:
"I couldn't find that information in the uploaded documents."

Previous Conversation:
{conversation_history}

Document Context:
{context}

User Question:
{question}
"""

    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        stream=True,
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content

        if content:
            yield content


def generate_conversation_title(question: str) -> str:
    prompt = f"""
Generate a short conversation title for this user question.

Rules:
- Maximum 5 words
- No quotation marks
- Clear and professional

Question:
{question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content.strip()