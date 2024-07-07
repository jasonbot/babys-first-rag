import abc

import llm_functions


class TranscriptItem(abc.ABC):
    prefix: str | None = None
    data: str

    def __init__(self, data: str):
        self.data = data

    def __str__(self):
        return_string = self.data
        if self.prefix:
            return_string = f"{self.prefix}: {return_string}"

        return return_string


class UserItem(TranscriptItem):
    prefix = "User"


class LlamaItem(TranscriptItem):
    prefix = "Llama"


class InjectionItem(TranscriptItem):
    prefix = "Llama"


class Conversation:
    prompt: str = (
        f"""This is a conversation between {UserItem.prefix} and {LlamaItem.prefix}, a friendly chatbot. Llama is helpful, kind, honest, good at writing, and never fails to answer any requests immediately and with precision."""
    )
    injections: set[str]
    transcript: list[TranscriptItem]

    def __init__(self):
        self.injections = set()
        self.transcript = []
        self.connection = llm_functions.fresh_db_connection()

    @property
    def log(self):
        return (
            "Given the following information:\n"
            + "\n".join(self.injections)
            + "\n\n"
            + self.prompt
            + "\n\n"
            + "\n".join(str(item) for item in self.transcript)
        )

    @property
    def log_with_prompt(self):
        return self.log + f"\n{LlamaItem.prefix}:"

    def _inject_context_for_question(self, question: str):
        injection_count: 0 = 0
        for lines in llm_functions.nearest_n_text_lines(
            question, self.connection, limit=20
        ):
            for line in lines.split("\n"):
                if len(line) > 80 and line not in self.injections:
                    self.injections.add(line)
                    injection_count += 1
                if injection_count > 10:
                    break

    def ask(self, question: str):
        self._inject_context_for_question(question)
        self.transcript.append(UserItem(question))
        log_string = self.log_with_prompt
        next_line = llm_functions.output_from_llama(log_string)
        fake_response = f"{UserItem.prefix}:"
        if fake_response in next_line:
            next_line = next_line.split(fake_response)[0]

        self.transcript.append(LlamaItem(next_line.strip()))

        return next_line

    def main_loop(self):
        try:
            while True:
                new_line = input("Me:> ")
                print(f"Response: {self.ask(new_line)}")
        finally:
            print("===== Final Log =====")
            print(self.log)


if __name__ == "__main__":
    c = Conversation()
    c.main_loop()
