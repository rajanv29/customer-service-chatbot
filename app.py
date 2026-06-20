import streamlit as st
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Main page configuration
st.set_page_config(
    page_title="Smart E-Commerce Customer Support Chatbot",
    page_icon="🛍️",
    layout="wide"
)

# Reading data
@st.cache_data
def load_data():
    return pd.read_csv("faq_data.csv")
faq_df=load_data()

# Data preprocessing
def preprocess_text(text):
    text=str(text).lower()
    text=re.sub(r"[^\w\s]", "", text)
    text=re.sub(r"\s+", " ", text).strip()
    return text
faq_df["processed_question"]=faq_df["Question"].apply(preprocess_text)

# Vectorization
vectorizer=TfidfVectorizer()
faq_vectors=vectorizer.fit_transform(
    faq_df["processed_question"]
)

# Understanding texts
CONFIDENCE_THRESHOLD=0.50
GREETINGS={
    "hi",
    "hello",
    "hey",
    "good morning",
    "good evening",
    "good afternoon"
}
EXIT_WORDS={
    "bye",
    "exit",
    "quit",
    "thank you",
    "thanks"
}
POPULAR_QUESTIONS=[
    "Where is my package?",
    "What is your refund policy?",
    "How long does delivery take?",
    "Can I cancel my order after placing it?",
    "My payment failed. What should I do?",
    "How do I reset my password?",
    "How can I contact customer support?"
]
RELATED_QUESTIONS={
    "Orders": [
        "How long does delivery take?",
        "Can I cancel my order after placing it?",
        "How can I contact customer support?"
    ],
    "Shipping": [
        "Where is my package?",
        "What are the shipping charges?",
        "How can I contact customer support?"
    ],
    "Refunds & Returns": [
        "How can I check my refund status?",
        "How can I return a product?",
        "How can I contact customer support?"
    ],
    "Payments": [
        "My payment failed. What should I do?",
        "How can I get an invoice for my purchase?",
        "How can I contact customer support?"
    ],
    "Account & Support": [
        "How do I reset my password?",
        "How can I change my email address?",
        "How can I contact customer support?"
    ]
}

# State of the session
if "messages" not in st.session_state:
    st.session_state.messages=[
        {
            "role": "assistant",
            "content": "👋 Hello! Welcome to our customer support chatbot. How can I assist you today?"
        }
    ]
if "recent_queries" not in st.session_state:
    st.session_state.recent_queries=[]
if "questions_asked" not in st.session_state:
    st.session_state.questions_asked=0
if "pending_question" not in st.session_state:
    st.session_state.pending_question=None

# Response generation using NLP
def get_response(user_query):
    query = preprocess_text(user_query)
    if query in GREETINGS:
        return (
            "Hello! 👋 How can I help you today?",
            None
        )
    if query in EXIT_WORDS:
        return (
            "Thank you for contacting us. Have a great day! 😊",
            None
        )
    query_vector=vectorizer.transform([query])
    similarity_scores=cosine_similarity(
        query_vector,
        faq_vectors
    )
    best_match_index=similarity_scores.argmax()
    best_score=similarity_scores[0][best_match_index]
    if best_score < CONFIDENCE_THRESHOLD:
        return (
            "Sorry, I couldn't understand your query. Please contact customer support for further assistance.",
            None
        )
    answer=faq_df.iloc[best_match_index]["Answer"]
    category=faq_df.iloc[best_match_index]["Category"]
    return answer,category

# Question handling
def process_question(question):
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )
    answer,category=get_response(question)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "category": category
        }
    )
    st.session_state.questions_asked+=1
    if question in st.session_state.recent_queries:
        st.session_state.recent_queries.remove(question)
    st.session_state.recent_queries.insert(0, question)
    st.session_state.recent_queries=(
        st.session_state.recent_queries[:10]
    )

# Streamlit UI Sidebar
with st.sidebar:
    st.title("🛍️ Support Bot")
    st.subheader("🕒 Recent Queries")
    if len(st.session_state.recent_queries)==0:
        st.caption("No queries yet.")
    else:
        for idx, query in enumerate(
            st.session_state.recent_queries
        ):
            col1,col2=st.columns([4, 1])
            with col1:
                st.caption(query)
            with col2:
                if st.button(
                    "↻",
                    key=f"history_{idx}"
                ):
                    st.session_state.pending_question = query
    st.divider()
    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):
        st.session_state.messages=[
            {
            "role": "assistant",
            "content": "👋 Hello! Welcome to our customer support chatbot. How can I assist you today?"
            }
        ]
        st.rerun()

# Streamlit UI Main Area
st.title(
    "🛍️ Customer Support Chatbot for E-Commerce"
)
st.markdown(
    "Ask your questions or use the quick actions below."
)

st.subheader("🔥 Frequently asked Questions")
cols=st.columns(4)
for i,question in enumerate(POPULAR_QUESTIONS):
    with cols[i % 4]:
        if st.button(
            question,
            key=f"popular_{i}",
            use_container_width=True
        ):
            st.session_state.pending_question = question

# Process button questions
if st.session_state.pending_question:
    process_question(
        st.session_state.pending_question
    )
    st.session_state.pending_question = None
    st.rerun()

# Showing Chat History
for msg_index, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if (
            msg["role"]=="assistant"
            and "category" in msg
            and msg["category"] in RELATED_QUESTIONS
        ):
            st.markdown("**You might also ask:**")
            related_cols=st.columns(
                len(
                    RELATED_QUESTIONS[
                        msg["category"]
                    ]
                )
            )
            for idx,related_q in enumerate(
                RELATED_QUESTIONS[
                    msg["category"]
                ]
            ):
                with related_cols[idx]:
                    if st.button(
                        related_q,
                        key=f"{msg_index}_{msg['category']}_{idx}"
                    ):
                        st.session_state.pending_question=related_q
                        st.rerun()

# Getting input
user_input=st.chat_input(
    "Type your question here..."
)
if user_input:
    process_question(user_input)
    st.rerun()
