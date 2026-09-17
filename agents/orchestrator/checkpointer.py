import os

checkpointer = None

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    DB_URI = os.getenv("DATABASE_URL")
    if DB_URI:
        _checkpointer_context = PostgresSaver.from_conn_string(DB_URI)
        checkpointer = _checkpointer_context.__enter__()
    else:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
except Exception:
    checkpointer = None


def setup_checkpointer():
    if checkpointer and hasattr(checkpointer, "setup"):
        try:
            checkpointer.setup()
            print("POSTGRES CHECKPOINTER SETUP OK")
        except Exception as e:
            print(f"Checkpointer setup notice: {e}")