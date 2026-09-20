import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# ==================================================
# GROQ MODELS
# ==================================================

GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "allam-2-7b",
]


# ==================================================
# BUILD RAG CHAIN
# ==================================================

def build_rag_chain(vector_store):
    """Returns retriever package."""

    return {
        "retriever": vector_store.as_retriever(
            search_kwargs={"k": 6}
        )
    }


# ==================================================
# GET RELEVANT DOCUMENTS
# ==================================================

def get_relevant_docs(rag_package, query: str):
    """Fetch relevant chunks for a query."""

    retriever = rag_package["retriever"]

    return retriever.invoke(query)


# ==================================================
# FORMAT CHAT HISTORY
# ==================================================

def format_history(
    chat_history: list,
    max_turns: int = 3
) -> str:

    if not chat_history:
        return "No previous conversation."

    recent = chat_history[-(max_turns * 2):]

    lines = []

    for msg in recent:

        # ------------------------------------------
        # Dictionary format
        # ------------------------------------------

        if isinstance(msg, dict):

            if msg.get("role") == "user":
                speaker = "User"
            else:
                speaker = "AskIt"

            content = msg.get(
                "content",
                ""
            )

            lines.append(
                f"{speaker}: {content}"
            )

        # ------------------------------------------
        # Tuple format
        # ------------------------------------------

        elif isinstance(msg, tuple):

            if len(msg) >= 2:

                lines.append(
                    f"User: {msg[0]}"
                )

                lines.append(
                    f"AskIt: {msg[1]}"
                )

    return "\n".join(lines)


# ==================================================
# ASK QUESTION
# ==================================================

def ask_question_stream(
    rag_package,
    query: str,
    chat_history: list = None
):

    try:

        # ------------------------------------------
        # Get relevant documents
        # ------------------------------------------

        docs = get_relevant_docs(
            rag_package,
            query
        )

        # ------------------------------------------
        # Create context
        # ------------------------------------------

        if docs:

            context = "\n\n".join(
                [
                    doc.page_content
                    for doc in docs
                ]
            )

        else:

            context = "No context found."


        # ------------------------------------------
        # Format previous conversation
        # ------------------------------------------

        history_text = format_history(
            chat_history or []
        )


        # ==================================================
        # PROMPT
        # ==================================================

        prompt = f"""
You are AskIt, a helpful AI assistant.

Your job is to answer the user's question using
the document/video context provided below.

==================================================
CONVERSATION HISTORY
==================================================

{history_text}


==================================================
LANGUAGE RULE
==================================================

IMPORTANT:

Always answer in the same language style as the
CURRENT USER QUESTION.

Examples:

User:
"ye video kis bare mein hai?"

Answer:
Natural Hinglish.

User:
"accha ji, isko thoda aur explain karo"

Answer:
Natural Hinglish.

User:
"What is this video about?"

Answer:
English.

User:
"इस वीडियो के बारे में बताओ"

Answer:
Hindi in Devanagari.

Do NOT automatically switch to English.

Do NOT use overly formal Hindi.

For Hinglish, use natural everyday Roman Hindi
mixed with English.

==================================================
CONVERSATION RULE
==================================================

Use previous conversation history when the user asks
follow-up questions.

For example:

User:
"video kis bare mein hai?"

AskIt:
"Ye video water ke baare mein hai."

User:
"accha ji"

Respond naturally.

User:
"iske baare mein aur batao"

Understand that "iske" refers to the previous topic.

==================================================
ANSWER RULES
==================================================

1. Use the document context as the main source.

2. Do not invent facts that are not supported by
the document.

3. If the answer is not available in the document,
clearly say that the information is not available.

4. Give a useful explanation instead of only one
short sentence when more explanation is possible.

5. For multiple points, use bullets or numbered lists.

6. Keep the answer natural and easy to understand.

7. Match the CURRENT question's language style.

==================================================
DOCUMENT / VIDEO CONTEXT
==================================================

{context}


==================================================
CURRENT QUESTION
==================================================

{query}


==================================================
ANSWER
==================================================
"""


        # ==================================================
        # GROQ API KEY
        # ==================================================

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            print(
                "❌ GROQ_API_KEY is missing!",
                flush=True
            )

            yield (
                "⚠️ GROQ_API_KEY missing "
                "in Railway environment variables."
            )

            return


        # ==================================================
        # GROQ CLIENT
        # ==================================================

        client = Groq(
            api_key=api_key
        )


        # ==================================================
        # TRY MODELS
        # ==================================================

        for model in GROQ_MODELS:

            try:

                print(
                    f"🔄 Trying: {model}",
                    flush=True
                )


                # ==================================================
                # NON-STREAMING GROQ REQUEST
                # ==================================================

                response = client.chat.completions.create(

                    model=model,

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0.4,

                    max_tokens=2048,

                    stream=False,
                )


                # ==================================================
                # GET ANSWER
                # ==================================================

                if not response.choices:

                    print(
                        f"❌ {model} returned no choices",
                        flush=True
                    )

                    continue


                answer = response.choices[0].message.content


                # ==================================================
                # SUCCESS
                # ==================================================

                print(
                    f"✅ {model} worked!",
                    flush=True
                )


                yield answer

                return


            except Exception as e:

                err = str(e)

                # ------------------------------------------
                # MODEL UNAVAILABLE
                # ------------------------------------------

                if (
                    "404" in err
                    or "model_not_found" in err
                ):

                    print(
                        f"⏭️ {model} not available, "
                        "trying next...",
                        flush=True
                    )

                    continue


                # ------------------------------------------
                # RATE LIMIT
                # ------------------------------------------

                elif (
                    "429" in err
                    or "rate_limit" in err
                ):

                    print(
                        f"⏭️ {model} rate limited, "
                        "trying next...",
                        flush=True
                    )

                    continue


                # ------------------------------------------
                # OTHER ERROR
                # ------------------------------------------

                else:

                    print(
                        f"❌ {model} ERROR: "
                        f"{type(e).__name__}: {e}",
                        flush=True
                    )

                    yield (
                        "⚠️ Groq connection error. "
                        "Check Railway logs for the exact error."
                    )

                    return


        # ==================================================
        # NO MODEL AVAILABLE
        # ==================================================

        print(
            "❌ No Groq model was available.",
            flush=True
        )

        yield (
            "⚠️ No models available. "
            "Check the Groq model configuration."
        )


    except Exception as e:

        print(
            f"❌ RAG ERROR: {type(e).__name__}: {e}",
            flush=True
        )

        yield (
            f"⚠️ Error: {str(e)}"
        )