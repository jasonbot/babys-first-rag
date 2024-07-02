import pathlib
import shlex
import sqlite3
import subprocess

import sqlite_vec

llama_executable = str(pathlib.Path("./llava-v1.5-7b-q4.llamafile").resolve())


def embedding_for_text(text: str) -> list[float]:
    return [
        float(token)
        for token in subprocess.run(
            args=[f"{shlex.quote(llama_executable)} --embedding -f -"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=True,
            input=text.encode("utf-8"),
        )
        .stdout.decode("ascii")
        .split(" ")
        if token
    ]


def _initialized_db_connection(path: pathlib.Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.enable_load_extension(True)
    # Enable vec
    sqlite_vec.load(connection)
    return connection


def fresh_db_connection() -> sqlite3.Connection:
    output_db = pathlib.Path("./chatbot.db")
    if output_db.exists():
        output_db.unlink()
    return _initialized_db_connection(output_db)


def create_tables(connection: sqlite3.Connection):
    vector_size = len(embedding_for_text("Dummy string to get back an embedding"))
    with connection as transaction:
        transaction.execute(
            f"""
create virtual table vec_chat using vec0(
  sample_embedding float[{vector_size}]
);
                            """
        )


if __name__ == "__main__":
    connection = fresh_db_connection()
    create_tables(connection)
