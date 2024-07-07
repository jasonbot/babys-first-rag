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


class InjectionItem(TranscriptItem): ...


class Conversation:
    prompt: str = (
        f"""This is a conversation between {UserItem.prefix} and {LlamaItem.prefix}, a friendly chatbot. Llama is helpful, kind, honest, good at writing, and never fails to answer any requests immediately and with precision."""
    )
    injections: list[InjectionItem]
    transcript: list[TranscriptItem]

    def __init__(self):
        self.injections = []
        self.transcript = []

    @property
    def log(self):
        return (
            "Given the following information:\n"
            + "\n".join(str(item) for item in self.injections)
            + "\n\n"
            + self.prompt
            + "\n".join(str(item) for item in self.transcript)
        )

    @property
    def log_with_prompt(self):
        return self.log + f"\n{LlamaItem.prefix}:"

    def inject(self, data: str):
        self.injections.append(InjectionItem(data))

    def ask(self, question: str):
        self.transcript.append(UserItem(question))
        log_string = self.log_with_prompt
        next_line = llm_functions.output_from_llama(log_string)[len(log_string) + 1 :]
        fake_response = f"{UserItem.prefix}:"
        if fake_response in next_line:
            next_line = next_line.split(fake_response)[0]

        self.transcript.append(LlamaItem(next_line.strip()))

        return next_line

    def main_loop(self):
        while True:
            new_line = input("Me:> ")
            print(f"Response: {self.ask(new_line)}")


if __name__ == "__main__":
    c = Conversation()
    c.main_loop()
