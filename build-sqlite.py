import json
import pathlib
import sqlite3
import sys

from llm_functions import create_tables, embedding_for_text, fresh_db_connection


def _sliding_window(
    row_factory, window_size=4, overlap=1, min_length=80, max_length=160
):
    window = []
    for row in row_factory:
        if len(row) < min_length:
            continue
        elif len(row) > max_length:
            # Special case: just in case this combined with other entries goes over max length.
            if window:
                yield window
            yield [row]
            window = []
            continue
        elif len("".join(window)) > max_length:
            yield window
            window = []

        if len(window) >= window_size:
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
                item["text"]
                for item in json_object
                if item["type"] in ("Title", "NarrativeText")
            ):
                transaction.execute(
                    "insert into text_lines(filename, text_line) values(?, ?)",
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
            "select rowid, filename, text_line from text_lines where rowid not in "
            "(select rowid from vec_chat)"
        ):
            rowid, filename, text = row
            if current_filename != filename:
                if current_filename:
                    print()
                print(f"Doing embeddings for {filename}: ", end="")
                current_filename = filename
            embedding = embedding_for_text(text)
            if len(embedding) == 0:
                print("!", end="")
            else:
                print(".", end="")
                transaction.execute(
                    "update text_lines set embedding = ? where rowid = ?",
                    (json.dumps(embedding), rowid),
                )
                transaction.execute(
                    "insert into vec_chat(rowid, embedding) values (?, ?)",
                    (rowid, json.dumps(embedding)),
                )
            sys.stdout.flush()
    print()
    print("Done")


if __name__ == "__main__":
    connection = fresh_db_connection(overwrite=True)
    create_tables(connection)
    insert_text_items_for_folder(connection)
    insert_embeddings_for_database(connection)
