import abc


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
    prefix = "me"


class LlamaItem(TranscriptItem):
    prefix = "llama"


class InjectionItem(TranscriptItem): ...


class Conversation:
    prompt: str = "You are llama, a useful chatbot who is always helpful and polite."
    injections: list[InjectionItem]
    transcript: list[TranscriptItem]

    @property
    def log(self):
        return (
            self.prompt
            + "\n\n"
            + "\n".join(str(item) for item in self.injections)
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
