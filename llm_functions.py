import json
import pathlib
import shlex
import shutil
import subprocess
import sqlite3

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


def fresh_db_connection(*, overwrite=False) -> sqlite3.Connection:
    output_db = pathlib.Path("./chatbot.db")
    if overwrite and output_db.exists():
        num: int = 1
        new_path = output_db
        while pathlib.Path(new_path).exists():
            new_path = +f"{output_db}.{num}"
            num += 1
        print(f"Moving exising {output_db} -> {new_path}")
        shutil.copy(output_db, new_path)
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
                create table text_lines(
                    filename text,
                    text_line text,
                    embedding text
                );
            """
        )


def nearest_n_neighbors(
    text: str, connection: sqlite3.Connection, limit: int = 5
) -> list[int]:
    limit = int(limit)
    with connection as transaction:
        return [
            x
            for x in transaction.execute(
                f"""
                    select rowid, distance
                    from vec_chat
                    where embedding match ?
                    order by distance
                    limit ?;
                """,
                (json.dumps(embedding_for_text(text)), limit),
            )
        ]


def nearest_n_text_lines(
    text: str, connection: sqlite3.Connection, limit: int = 5
) -> list[str]:
    with connection as transaction:
        return [
            row[0]
            for row in connection.execute(
                f"""
                    select text_line from text_lines where rowid in {tuple(
                        c[0]
                        for c in nearest_n_neighbors(
                            text, connection=connection, limit=limit
                        )
                    )}
                """
            )
        ]


if __name__ == "__main__":
    connection = fresh_db_connection()
    print(
        nearest_n_text_lines(
            "Anthony Fauci helped release the COVID vaccine",
            connection,
        )
    )
