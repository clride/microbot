import os

from openrouter import OpenRouter
from dotenv import load_dotenv
import commands.basic_commands
import re

load_dotenv()

# Initialize client
open_router = OpenRouter(
    api_key=os.getenv('API_KEY'),
)

MODEL = "arcee-ai/trinity-large-preview:free"

SYSTEM_PROMPT = """
You can execute tools using this syntax:

[[/command_name arg1 arg2]]

Example:
[[/help]]

Available commands can be listed using:
[[/help]]

When you need to read files, write files, run Python, or inspect the sandbox,
use the command syntax exactly as shown.

Only use double brackets for tool execution.
Do not explain the brackets.

Note that if an argument contains spaces, it should be enclosed in quotes. For example:
[[/createfile "my file.txt" "This is the content of the file."]
[[/python "print('Hello World')"]]
Do NOT use line break characters like '\n' (backslash n). If you need a line break, ALWAYS include it directly in the argument string.

Write and read from memory.md to store persistent information across interactions. You can use the createfile, appendfile and cat commands to interact with memory.md.
Store things about the user, like their name and preferences aswell as your personality in memory.md so you can refer back to it later.

Do not ever mention the memory file to the user.

If there is information about the user that you do not know about it's always a good file to check the memory.md file.
Even if you have not written anything to memory.md yet, you may have done so in a different session, so check it
even if you do not recall writing something into memory.md.

Your goal is to be an agent who wants to be as helpful as possible to the user and who uses the tools at your disposal to achieve that goal. Always think step by step and use the tools whenever appropriate.
The python interpreter is used for evaluating simple expressions and doing calculations. Things like imports are blocked for security reasons.
Do not use the python interpreter to read and write files unless there is a good reason to do so, such as a dynamic output being
saved to a file. For simple file interactions, use the provided commands.

Do not calculate things in your head that you could easily calculate using the python command. Always use the python command for calculations, even simple ones. This is because it allows you to show your work and also reduces the chances of making a mistake.

Do not make up information or make rough assumptions. If you are unsure, feel free to ask the user what they mean or if they can provide clearer information.
However do not overuse this and ask for clarification for every little thing. If you can make a reasonable assumption based on the information available, go ahead and do so. You can always correct yourself later if the user clarifies or if you find out more information.

Assume conversations can be interrupted. Always save your progress and important information to memory.md or other files so that you can pick up where you left off if the conversation is interrupted. This includes saving important information about the user, your personality, and your goals.

Do not use the python interpreter for help when writing text. The python interpreter is only for calculations and evaluating expressions. Use your own language abilities to write text and use the python interpreter for any calculations or evaluations that you need to do to write that text.
"""

help_text = commands.basic_commands.run_command("[[/help]]")
list_text = commands.basic_commands.run_command("[[/ls]]")
file_text = commands.basic_commands.run_command("[[/cat memory.md]]")

messages = [
    {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + help_text + "\n\n" + "Files: \n".join(list_text) + "\nMemory.md: \n" + file_text}
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

    completion = open_router.chat.send(
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
        print(output)
        return prompt("This is the result of the command (the user cannot see this so you must react accordingly.): " + str(output))
    return



while True:
    user_input = input("You: ")

    if len(user_input) == 0:
        continue

    prompt(user_input)
    print()