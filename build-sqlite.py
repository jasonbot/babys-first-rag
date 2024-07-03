import json
import pathlib
import shlex
import sqlite3
import subprocess
import sys

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
                    embedding float[{vector_size}]
                );
            """
        )

        transaction.execute(
            """
                create table utterances(
                    filename text,
                    utterance text
                );
            """
        )


def _sliding_window(row_factory, window_size=9, overlap=3):
    window = []
    for row in row_factory:
        if len(window) == window_size:
            yield window
            window = window[-overlap:]
        window.append(row)
    if window:
        yield window


def insert_text_items_for_folder(
    connection: sqlite3.Connection,
    folder: pathlib.Path = pathlib.Path("./processed_pages"),
):
    for file in folder.glob("*.json"):
        print(f"Loading transcript from {file}: ", end="")
        with connection as transaction, open(file, "r") as in_json:
            json_object = json.load(in_json)
            for text in _sliding_window(
                item["text"] for item in json_object if item["type"] == "NarrativeText"
            ):
                transaction.execute(
                    "insert into utterances(filename, utterance) values(?, ?)",
                    (str(file), "\n".join(text)),
                )
                print(".", end="")
        print()


def insert_embeddings_for_database(
    connection: sqlite3.Connection,
):
    current_filename = None
    with connection as transaction:
        for row in transaction.execute(
            "select rowid, filename, utterance from utterances"
        ):
            rowid, filename, text = row
            if current_filename != filename:
                if current_filename:
                    print()
                print(f"Doing embeddings for {filename}: ", end="")
                current_filename = filename
            print(".", end="")
            sys.stdout.flush()
            embedding = embedding_for_text(text)
            transaction.execute(
                "insert into vec_chat(rowid, embedding) values (?, ?)",
                (rowid, json.dumps(embedding)),
            )
    print()
    print("Done")


if __name__ == "__main__":
    connection = fresh_db_connection()
    create_tables(connection)
    insert_text_items_for_folder(connection)
    insert_embeddings_for_database(connection)
