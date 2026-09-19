# AskIt — AI-Powered Video & Document Q&A 🚀

AskIt is an AI-powered question-answering application that allows users to interact with **YouTube videos and documents using natural language**.

Instead of manually going through a long video or document to find specific information, users can simply ask a question and get a context-aware answer.

## 💡 Why I Built AskIt

While learning about **LLMs, embeddings, and Retrieval-Augmented Generation (RAG)**, I wanted to move beyond tutorials and build something practical.

I wanted to understand how these concepts work together in a real application:

**Content → Text Processing → Chunking → Embeddings → Vector Search → Relevant Context → LLM → Answer**

That led me to build AskIt.

## ✨ Features

* 🎥 Ask questions about YouTube videos
* 📄 Ask questions about documents
* 🔍 Semantic search using vector embeddings
* 🤖 AI-generated answers using an LLM
* 💬 Follow-up questions and conversational interaction
* ⚡ FastAPI backend
* 🖥️ React frontend
* 🚀 Deployed application

## 🧠 How It Works

AskIt follows a Retrieval-Augmented Generation (RAG) approach.

```text
YouTube Video / Document
          ↓
     Text Extraction
          ↓
       Chunking
          ↓
      Embeddings
          ↓
    FAISS Vector Store
          ↓
   Similarity Retrieval
          ↓
   Relevant Context
          ↓
       Groq LLM
          ↓
     Final Answer
```

When a user asks a question, AskIt retrieves the most relevant pieces of information from the processed content and provides them to the LLM to generate a contextual response.

## 🛠️ Tech Stack

### Frontend

* React
* JavaScript
* Vercel

### Backend

* Python
* FastAPI
* Uvicorn

### AI / RAG

* LangChain
* Hugging Face Embeddings
* FAISS
* Groq

### Data Processing

* YouTube Transcript API
* PyPDF

## 📂 Project Structure

```text
Askit-ai/
│
├── backend/
│   └── main.py
│
├── core/
│   └── rag_engine.py
│
├── utils/
│
├── vector_db/
│
├── frontend/
│
├── requirements.txt
└── README.md
```

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/binitnayak/Askit-ai.git
cd Askit-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and add your required API key:

```env
GROQ_API_KEY=your_groq_api_key
```

**Never commit your `.env` file or API keys to GitHub.**

### 5. Start the backend

```bash
uvicorn backend.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

## 🔑 API Documentation

Once the FastAPI backend is running, you can access the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## 🎯 Example Questions

After adding a YouTube video or document, users can ask:

```text
What is this video mainly about?

What are the key points discussed?

Can you explain the second point in simple words?

What examples were mentioned?
```

## 🚀 What I Learned

Building AskIt gave me practical experience with:

* Understanding RAG architecture
* Working with text extraction and chunking
* Creating and using embeddings
* Vector similarity search with FAISS
* Integrating LLMs into an application
* Building APIs with FastAPI
* Connecting an AI backend with a React frontend
* Deploying an AI application

## 🔮 Future Improvements

* User authentication
* Support for more document formats
* Better conversation memory
* Streaming responses
* Improved retrieval and ranking
* More LLM provider options
* Better error handling and monitoring

## 👨‍💻 Author

**Binit Nayak**

GitHub:
https://github.com/binitnayak

Project Repository:
https://github.com/binitnayak/Askit-ai
