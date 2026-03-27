"""
マルチエージェント版のエントリーポイント。
親エージェントが自動車専門の子エージェントをToolとして持つ。
親エージェント自身も長期記憶（pgvector）を持ち、
セッションをまたいで会話の文脈を保持する。
"""

from core.tracing import setup_langfuse_tracing
from agents.parent_agent import build_parent_agent
from core.memory import LongTermMemory


def main():
    setup_langfuse_tracing()
    print("=== Multi-Agent (親 + 自動車専門エージェント) ===")
    print("自動車に関する質問は自動的に専門エージェントへ委譲されます。")
    print("終了するには 'exit' または 'quit' を入力してください。\n")

    agent = build_parent_agent()
    memory = LongTermMemory(agent_id="parent-agent")

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

        # 1. 長期記憶から関連する過去の情報を検索して質問に付加する
        memories = memory.search(user_input, top_k=3)
        if memories:
            context = "\n".join(f"- {m['content']}" for m in memories)
            augmented = f"[過去の記憶（参考情報）]\n{context}\n\n[ユーザーの入力]\n{user_input}"
        else:
            augmented = user_input

        # 2. 親エージェントに回答させる
        response = agent(augmented)
        answer = str(response)
        print(f"Agent: {answer}\n")

        # 3. 今回の Q&A を長期記憶に保存
        memory.add(
            content=f"Q: {user_input}\nA: {answer[:200]}",
            metadata={"type": "qa"},
        )

    memory.close()


if __name__ == "__main__":
    main()
