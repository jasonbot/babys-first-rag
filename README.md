# Baby's First RAG

This is the companion repo [to my blog post about creating a RAG](https://www.jasonscheirer.com/weblog/babys-first-rag/).

Please keep in mind this repo may be used for inspiration, but the code _may not be used for commercial purposes_.

# Contents:

- `spider.py`: Script to find and fetch all the Joe Rogan transcripts
- `cleanup.py`: Script to clean up all the transcripts into RAG-importable JSON files
- `run-unstructured.py`: Script to process transcript HTML through the Unstructured API
- `build-sqlite.py`: Script to build the SQLite database
- `llm_functions.py`: Some shared routines I use between multiople scripts
