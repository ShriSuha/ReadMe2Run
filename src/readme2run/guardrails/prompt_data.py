# Markers that tell the model the block between them is repo data, not instructions.
UNTRUSTED_START = "----- BEGIN UNTRUSTED DATA -----"
UNTRUSTED_END = "----- END UNTRUSTED DATA -----"


def wrap_untrusted(text: str) -> str:
    """Put repo text between data markers.

    Prompts can say that anything between the markers is data from the
    repository, not an instruction the model should obey.
    """
    return f"{UNTRUSTED_START}\n{text}\n{UNTRUSTED_END}\n"
