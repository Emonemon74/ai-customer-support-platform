from groq import Groq

from app.core.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_answer(question: str, context: str) -> str:
    prompt = f"""
You are an AI customer support assistant.

Answer the user's question ONLY using the context below.

If the answer is not present in the context, say:
"I couldn't find that information in the uploaded documents."

Context:
{context}

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

    return response.choices[0].message.content