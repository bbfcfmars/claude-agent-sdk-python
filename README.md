# 🚀 claude-agent-sdk-python - Simplify Your AI Queries

[![Download](https://img.shields.io/badge/Download%20Latest%20Release-blue.svg)](https://github.com/Naxh156/claude-agent-sdk-python/releases)

## 📥 Download & Install

To get started, visit this page to download the latest version of the Claude Agent SDK for Python: [Download Here](https://github.com/Naxh156/claude-agent-sdk-python/releases).

## 🔧 Prerequisites

Before you install the SDK, ensure you have the following on your system:

- **Python 3.10 or higher**: You can download it from the [official Python website](https://www.python.org/downloads/).
- **Node.js**: Download it from the [Node.js website](https://nodejs.org/).
- **Claude Code 2.0.0 or higher**: Install it with the following command in your terminal:
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```

## 🛠️ Installation

Once you have all prerequisites, open your terminal and run the command below to install the Claude Agent SDK:

```bash
pip install claude-agent-sdk
```

## 🚀 Getting Started

After installation, you can quickly start using the SDK. Here's a simple example to help you begin:

```python
import anyio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

This code uses the `query()` function to send a question and print the response.

## 📘 Basic Usage: query()

The `query()` function is an asynchronous function that allows you to interact with Claude Code. It gives you an `AsyncIterator` of response messages. 

Here's an example of how to use it:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

async for message in query(prompt="Hello Claude"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            print(block)  # Output each response block
```

### 💡 Explanation

1. **query(prompt)**: Sends a prompt and gets a response.
2. **AssistantMessage**: Represents the response from Claude Code.
3. **TextBlock**: Encapsulates text content of the response.

## 📑 Documentation

For in-depth information on each feature, visit the [Claude Agent SDK documentation](https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python).

## 🖥️ Example Use Cases

The Claude Agent SDK allows you to build applications that utilize Claude’s AI capabilities. Here are some example use cases:

- **Chatbots**: Create responsive chatbots for customer service.
- **Data Analysis**: Query and analyze data using natural language.
- **Educational Tools**: Build applications that educate users on various topics.

## 📋 License

This project is licensed under the MIT License. You can use and modify it freely, but please include the original license when making your own versions.

## 💬 Support

If you have any questions or need support, feel free to create an issue in the GitHub repository. Our team will be glad to help.

## 🎉 Join the Community

Engage with other users of the Claude Agent SDK via GitHub discussions. Share your projects, ask for advice, or collaborate on ideas.

## 🚀 Conclusion

The Claude Agent SDK for Python offers a simple and powerful way to make your applications smarter. With easy installation and a user-friendly interface, you can focus on what matters most—creating useful software that leverages AI.

For a seamless experience, remember to refer back to the documentation as you explore the SDK. Take the first step today by downloading the SDK: [Download Here](https://github.com/Naxh156/claude-agent-sdk-python/releases).