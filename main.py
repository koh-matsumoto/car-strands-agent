"""
エントリーポイント。
対話型ループでエージェントと会話できる。
"""

from core.tracing import setup_langfuse_tracing
from agents.agent import build_agent


def main():
    setup_langfuse_tracing()
    print("=== Strands Agent ===")
    print("終了するには 'exit' または 'quit' を入力してください。\n")

    agent = build_agent()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("終了します。")
            break

        response = agent(user_input)
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    main()
