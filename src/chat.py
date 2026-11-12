from search import search_prompt


def main() -> None:
    answer_question = search_prompt()
    print("Faça sua pergunta (digite 'sair' para encerrar).")

    while True:
        question = input("\nPERGUNTA: ").strip()
        if question.lower() in {"sair", "exit", "quit"}:
            break
        if not question:
            continue

        answer = answer_question(question)
        print(f"RESPOSTA: {answer}")


if __name__ == "__main__":
    main()
