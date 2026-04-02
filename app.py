"""
UniUs — US University Chatbot
Flask application entry point.
"""

from flask import Flask, render_template, request, jsonify, session
import config
from core.topic_filter import is_university_question
from core.retriever import UniversityRetriever
from core.llm_client import LLMClient

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "unius-secret-key-change-in-production"

# Initialize components
print("[UniUs] Starting UniUs Chatbot...")
retriever = UniversityRetriever(config.CSV_PATH)
llm_client = LLMClient()
university_names = retriever.names_lower

print("[UniUs] All systems ready!")


@app.route("/")
def index():
    """Serve the chat interface."""
    session.clear()
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    data = request.get_json()
    
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400
    
    question = data["message"].strip()
    
    if not question:
        return jsonify({"error": "Empty message"}), 400
    
    # Initialize chat history in session
    if "history" not in session:
        session["history"] = []
    
    # Step 1: Topic filtering
    is_relevant, confidence, is_greeting_flag = is_university_question(
        question, university_names
    )
    
    # Step 2: Handle based on relevance
    if is_greeting_flag:
        response = llm_client.get_greeting()
    elif not is_relevant:
        response = (
            "I'm **UniUs** — I specialize exclusively in US universities "
            "and colleges! 🎓\n\n"
            "I can't help with that topic, but feel free to ask me about:\n"
            "- 🏛️ Any US university or college\n"
            "- 📍 Campus locations and details\n"
            "- 📊 Statistics and comparisons\n"
            "- 🎓 Institution types and programs\n\n"
            "What university would you like to know about?"
        )
    else:
        # Step 3: Retrieve relevant data
        context = retriever.search(question)
        
        # Step 4: Generate LLM response
        response = llm_client.generate(
            question=question,
            context=context,
            chat_history=session.get("history", [])
        )
    
    # Update chat history (keep last 8 messages)
    session["history"] = session.get("history", [])
    session["history"].append({"role": "user", "content": question})
    session["history"].append({"role": "assistant", "content": response})
    session["history"] = session["history"][-8:]
    session.modified = True
    
    return jsonify({
        "response": response,
        "confidence": confidence if not is_greeting_flag else 1.0,
        "is_relevant": is_relevant,
    })


@app.route("/api/stats", methods=["GET"])
def stats():
    """Return dataset statistics."""
    return jsonify(retriever.get_stats())


if __name__ == "__main__":
    print(f"\n[UniUs] Running at http://localhost:{config.PORT}\n")
    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG
    )
