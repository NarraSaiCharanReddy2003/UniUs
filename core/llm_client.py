"""
LLM Client for UniUs Chatbot.
Handles communication with the Groq API for natural language responses.
"""

from groq import Groq
import config

SYSTEM_PROMPT = """You are UniUs 🎓, a friendly and knowledgeable AI assistant that ONLY answers questions about US universities, colleges, and higher education institutions.

## Your Personality
- Warm, encouraging, and professional
- Passionate about helping students find the right university
- You use occasional emojis to be friendly but not excessive

## Your Rules (STRICT)
1. ONLY answer questions related to US universities, colleges, and higher education
2. If someone asks about something NOT related to US universities, politely decline with: "I'm UniUs — I specialize exclusively in US universities and colleges! 🎓 Feel free to ask me about any institution, admissions, programs, or campus details."
3. Use the provided university data context to give accurate, factual answers
4. If the data doesn't contain info about a specific university, honestly say: "I don't have detailed data on that institution in my database, but here's what I can tell you..."
5. Never make up statistics, rankings, or data that isn't provided in the context
6. When showing university info, format it nicely with clear sections
7. For comparison questions, create a clear side-by-side comparison
8. Always include the university website when available

## Response Format
- Keep responses concise but informative (2-4 paragraphs max for simple questions)
- Use bullet points for listing multiple items
- Bold important details like university names, rankings
- Include website links when available

## University Data Context
{context}
"""

GREETING_RESPONSE = """Hey there! 👋 Welcome to **UniUs** 🎓

I'm your dedicated US university assistant! I can help you with:

🏛️ **University Information** — Details about any US college or university
📍 **Location & Campus** — Where institutions are located
🎓 **Institution Types** — Public, private, non-profit comparisons
👤 **Leadership** — Presidents and key administrators
🌐 **Websites** — Direct links to university pages
📊 **Statistics** — Counts and data across US higher education

Just ask me anything about US universities! For example:
- *"Tell me about MIT"*
- *"What universities are in California?"*
- *"Compare Harvard and Stanford"*
- *"How many public universities are there?"*

What would you like to know? 😊"""


class LLMClient:
    """Manages Groq API calls for generating responses."""
    
    def __init__(self):
        """Initialize the Groq client."""
        if not config.GROQ_API_KEY:
            print("[UniUs] WARNING: No GROQ_API_KEY found! Set it in .env file.")
            print("[UniUs] Get a free key at: https://console.groq.com")
            self.client = None
        else:
            self.client = Groq(api_key=config.GROQ_API_KEY)
            print(f"[UniUs] Groq API initialized with model: {config.GROQ_MODEL}")
    
    def generate(self, question: str, context: str, chat_history: list = None) -> str:
        """
        Generate a response using the Groq API.
        
        Args:
            question: The user's question
            context: Retrieved university data context
            chat_history: Optional list of previous messages for context
            
        Returns:
            str: The generated response
        """
        if not self.client:
            return (
                "⚠️ **API Key Not Configured**\n\n"
                "I need a Groq API key to generate responses. Please:\n"
                "1. Go to [console.groq.com](https://console.groq.com)\n"
                "2. Sign up for free and get an API key\n"
                "3. Create a `.env` file in the project root\n"
                "4. Add: `GROQ_API_KEY=your_key_here`\n"
                "5. Restart the server"
            )
        
        # Build the system prompt with context
        system_message = SYSTEM_PROMPT.format(context=context)
        
        # Build messages array
        messages = [{"role": "system", "content": system_message}]
        
        # Add chat history for conversational context (last 4 exchanges)
        if chat_history:
            for msg in chat_history[-8:]:  # Last 4 pairs (user+assistant)
                messages.append(msg)
        
        # Add current question
        messages.append({"role": "user", "content": question})
        
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                top_p=0.9,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                return (
                    "⏳ I'm getting too many requests right now. "
                    "Please wait a moment and try again!"
                )
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                return (
                    "🔑 **Invalid API Key**. Please check your Groq API key in the `.env` file."
                )
            else:
                print(f"[UniUs] LLM Error: {error_msg}")
                return (
                    "😓 Sorry, I encountered an error generating a response. "
                    "Please try again in a moment."
                )
    
    def get_greeting(self) -> str:
        """Return the greeting/welcome message."""
        return GREETING_RESPONSE
