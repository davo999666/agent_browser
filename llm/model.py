from langchain_openai import ChatOpenAI

# LM Studio OpenAI-compatible endpoint
model = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",  # dummy key required
    model="unsloth/qwen3.5-9b"
)