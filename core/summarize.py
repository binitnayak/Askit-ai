# from langchain_mistralai import ChatMistralAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# import os 

# def get_llm():
#     return ChatMistralAI(model = "mistral-small-latest", mistral_api_key = os.getenv("MISTRAL_API_KEY"),temperature=0.3)


# def split_transcript(transcript: str) -> list:
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size = 3000,
#         chunk_overlap = 200
#     )

#     return splitter.split_text(transcript)

# def summarize(transcript : str) -> str:
#     llm = get_llm()

#     map_prompt = ChatPromptTemplate.from_messages(
#         [
#         ("system", "Summarize this portion of a meeting transcript concisely."),
#         ("human", "{text}"),
#     ]
#     )

#     map_chain = map_prompt | llm | StrOutputParser()

#     chunks = split_transcript(transcript)

#     chunk_summaries = [map_chain.invoke({"text" : chunk}) for chunk in chunks]

#     combined = "\n\n".join(chunk_summaries)

#     combined_prompt = ChatPromptTemplate.from_messages(
#         [
#         (
#             "system",
#             "You are an expert meeting summarizer. Combine these partial summaries "
#             "into one final professional meeting summary in bullet points.",
#         ),
#         ("human", "{text}"),
#     ]
#     )

#     combined_chain = (
#         RunnablePassthrough() | RunnableLambda(lambda x:{"text":x}) | combined_prompt | llm | StrOutputParser()
#     )

#     return combined_chain.invoke(combined)

# def generate_title(transcipt : str) -> str:
#     llm = get_llm()

    

#     title_chain = (
#         RunnablePassthrough() | RunnableLambda(lambda x:{"text":x}) | 
#         ChatPromptTemplate.from_messages([
#              (
#                 "system",
#                 "Based on the meeting transcript, generate a short professional meeting title "
#                 "(max 8 words). Only return the title, nothing else.",
#             ),
#             ("human", "{text}"),
#         ])
#         | llm
#         |StrOutputParser()
#     )

#     return title_chain.invoke(transcipt[:2000])


import os
import time

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_llm():
    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY not found. Please check your .env file."
        )

    return ChatMistralAI(
        model="mistral-small-2603",
        mistral_api_key=api_key,
        temperature=0.3,
        max_retries=0
    )


def split_transcript(transcript: str) -> list:
    """
    Split long transcript into manageable pieces.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=6000,
        chunk_overlap=200
    )

    return splitter.split_text(transcript)


def call_mistral(chain, data, retries=2):
    """
    Safely call Mistral.

    If rate limit occurs, wait before retrying.
    """

    for attempt in range(retries):

        try:
            return chain.invoke(data)

        except Exception as e:

            error = str(e)

            if "429" not in error and "rate_limit" not in error.lower():
                raise

            if attempt == retries - 1:
                print("\n❌ Mistral API rate limit is still active.")
                print("Please wait a few minutes and try again.")
                raise RuntimeError(
                    "Mistral API rate limit is currently active."
                )

            wait_time = 20 * (attempt + 1)

            print(
                f"\n⚠️ Mistral rate limit reached."
                f"\n⏳ Waiting {wait_time} seconds before retry..."
            )

            time.sleep(wait_time)


def summarize(transcript: str) -> str:

    print("\n🧠 Starting transcript summarization...")

    llm = get_llm()

    chunks = split_transcript(transcript)

    print(f"📚 Transcript divided into {len(chunks)} chunks.")

    # If transcript is short, use ONE Mistral request.
    if len(chunks) == 1:

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert meeting summarizer. "
                    "Create a professional summary of the transcript. "
                    "Use clear bullet points. "
                    "Include important concepts, explanations, examples "
                    "and conclusions. "
                    "Do not invent information."
                ),
                (
                    "human",
                    "{text}"
                )
            ]
        )

        chain = prompt | llm | StrOutputParser()

        print("\n📝 Summarizing transcript...")

        result = call_mistral(
            chain,
            {"text": transcript}
        )

        print("\n✅ Summary generated successfully.")

        return result

    # For longer transcripts
    # summarize each chunk first.
    chunk_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Summarize this transcript section concisely. "
                "Keep important facts, concepts, examples and conclusions. "
                "Do not invent information."
            ),
            (
                "human",
                "{text}"
            )
        ]
    )

    chunk_chain = chunk_prompt | llm | StrOutputParser()

    summaries = []

    for i, chunk in enumerate(chunks, start=1):

        print(f"\n📝 Summarizing chunk {i}/{len(chunks)}...")

        result = call_mistral(
            chunk_chain,
            {"text": chunk}
        )

        summaries.append(result)

        # Stay below the request-per-second limit.
        if i < len(chunks):
            time.sleep(2)

    combined = "\n\n".join(summaries)

    print("\n🔗 Creating final summary...")

    final_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert summarizer. "
                "Combine the partial summaries into one "
                "professional and easy-to-read summary. "
                "Use bullet points. "
                "Remove repeated information. "
                "Keep the most important concepts and conclusions. "
                "Do not add information that is not present."
            ),
            (
                "human",
                "{text}"
            )
        ]
    )

    final_chain = final_prompt | llm | StrOutputParser()

    final_summary = call_mistral(
        final_chain,
        {"text": combined}
    )

    print("\n✅ Summary generated successfully.")

    return final_summary


def generate_title(transcript: str) -> str:
    """
    Generate title locally without calling Mistral.
    This saves one API request.
    """

    text = transcript.lower()

    if (
        "retrieval augmented generation" in text
        or "retrieval-augmented generation" in text
        or " rag " in f" {text} "
    ):
        return "RAG Explained - Retrieval Augmented Generation"

    if "machine learning" in text:
        return "Machine Learning Explained"

    if (
        "artificial intelligence" in text
        or "generative ai" in text
        or "gen ai" in text
    ):
        return "Generative AI Explained"

    return "AI Video Summary"