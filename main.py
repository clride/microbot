from openai import OpenAI
from openrouter import OpenRouter
from dotenv import load_dotenv
from agent_config import MODEL, SYSTEM_PROMPT, PROVIDER
import commands.basic_commands
import re
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")

match PROVIDER:
    case "openai":
        client = OpenAI(api_key=API_KEY)
    case "openrouter":
        client = OpenRouter(api_key=API_KEY)
    case _:
        raise ValueError("PROVIDER must be 'openai' or 'openrouter'")

if API_KEY == "<insert your API Key here>":
    raise ValueError("You haven't inserted an API Key yet.")

help_text = commands.basic_commands.run_command("[[/help]]")
list_text = commands.basic_commands.run_command("[[/ls]]")
file_text = commands.basic_commands.run_command("[[/cat memory.md]]")

messages = [
    {
    "role": "system", "content": 
        SYSTEM_PROMPT + "\n\n" + help_text + "\n\n" + 
        "Files: \n".join(list_text) + "\n" +
        "Memory.md: \n" + file_text
     }
]

COMMAND_PATTERN = r"\[\[(.*?)\]\]"


def execute_and_embed_commands(text: str):
    matches = re.findall(COMMAND_PATTERN, text)
    updated_text = text

    output = ""

    for match in matches:
        original_block = f"[[{match}]]"
        output = commands.basic_commands.run_command(original_block)
        print("Running command:", original_block)
        print("Output:", output)

        embedded_block = f"[[{match}\n\n{output}]]"
        updated_text = updated_text.replace(original_block, embedded_block)

    return (output, updated_text, len(matches))


def prompt(message: str):
    messages.append({
        "role": "user",
        "content": message,
    })

    match PROVIDER:
        case "openai":
            completion = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True,
            )
        case "openrouter":
            completion = client.chat.send(
                model=MODEL,
                messages=messages,
                stream=True,
            )
    result: str = ""

    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            piece = chunk.choices[0].delta.content
            result += piece
            print(piece, end="", flush=True)

    print()

    output, result, count = execute_and_embed_commands(result)

    messages.append({
        "role": "assistant",
        "content": result,
    })

    if count > 0:
        print("\n--- Updated With Command Results Embedded ---\n")
        print("[[" + output + "]]")
        return prompt("This is the result of the command (the user cannot see this so you must react accordingly.): " + str(output))
    return



while True:
    user_input = input("You: ")

    if len(user_input) == 0:
        continue

    prompt(user_input)
    print()