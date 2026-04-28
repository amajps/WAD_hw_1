try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    Llama = None
    LLAMA_AVAILABLE = False

from config import settings

_llm: object | None = None

# Mock responses for when LLM is not available
MOCK_RESPONSES = {
    "hello": "Hello! 👋 I'm an AI assistant. How can I help you today?",
    "how are you": "I'm doing well, thank you for asking! 😊 How can I assist you?",
    "what is": "That's a great question! ",
    "help": "I'm here to help! You can ask me anything and I'll do my best to assist you.",
    "thank": "You're welcome! Happy to help! 🙌",
}


def get_mock_response(prompt: str) -> str:
    """Return a mock response based on keywords in the prompt"""
    prompt_lower = prompt.lower()
    
    for keyword, response in MOCK_RESPONSES.items():
        if keyword in prompt_lower:
            return response
    
    # Default response
    return f"I understand you asked: '{prompt.strip()}'. I'm a mock AI assistant, but I'd love to help if you have a specific question! 💡"


def get_llm():
    global _llm
    if not LLAMA_AVAILABLE:
        return None
    if _llm is None:
        try:
            _llm = Llama(model_path=settings.LLAMA_MODEL_PATH, n_ctx=512, n_threads=4)
        except Exception as e:
            print(f"Warning: Could not load LLM model: {e}")
            return None
    return _llm


def generate_answer(prompt: str) -> str:
    model = get_llm()
    if model is None:
        # Use mock responses when model is not available
        return get_mock_response(prompt)
    try:
        result = model(prompt, max_tokens=200, stream=False)
        return result["choices"][0]["text"].strip()
    except Exception as e:
        return f"Error generating answer: {str(e)}"
