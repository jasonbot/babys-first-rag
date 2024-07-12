import json
import pathlib

import unstructured_client
from unstructured_client.models import operations, shared


def unstructure_docs():
    in_path = pathlib.Path("./transcript_pages")
    out_path = pathlib.Path("./processed_pages")
    out_path.mkdir(exist_ok=True)

    s = unstructured_client.UnstructuredClient(
        api_key_auth=None, server_url="http://localhost:5435/general/v0/"
    )

    for file in in_path.glob("*.html"):
        print(f"Handling {file}...")
        with open(file, "rb") as in_handle:
            res = s.general.partition(
                request=operations.PartitionRequest(
                    partition_parameters=shared.PartitionParameters(
                        files=shared.Files(
                            content=in_handle.read(),
                            file_name=file.name,
                        ),
                        strategy=shared.Strategy.AUTO,
                    ),
                )
            )

            if res.elements is not None:
                # handle response
                pass

            with open(out_path / (file.name + ".json"), "w") as out_file:
                json.dump(res.elements, out_file, indent=4)


if __name__ == "__main__":
    unstructure_docs()
