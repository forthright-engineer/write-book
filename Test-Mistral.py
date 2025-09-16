from mistralai import Mistral, UserMessage

client = Mistral(api_key="00NyigJah3RWjccJZ1J3fJah1jfkKEZv")

chat_response = client.chat.complete(
    model="mistral-tiny",  # or "mistral-small", "mistral-medium", etc.
    messages=[UserMessage(content="Hello!")]
)

print(chat_response.choices[0].message.content)