import json
import pathlib
import sqlite3
import sys

from llm_functions import embedding_for_text, fresh_db_connection


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
