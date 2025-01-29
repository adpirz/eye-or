import os

import openai
from dotenv import load_dotenv


def main():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the OpenAI client
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Create chat completion request
    completion = openai.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "user", "content": "Tell me a funny joke"}]
    )

    # Print the response
    print("Here's a joke from GPT-4:")
    print(completion.choices[0].message["content"])


if __name__ == "__main__":
    main()
