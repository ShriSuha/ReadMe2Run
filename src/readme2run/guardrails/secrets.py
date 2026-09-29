import re

# A token prefix, then the rest of the token. The value is replaced.
_TOKEN_PREFIXES = re.compile(
    r"\b(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|sk-)[A-Za-z0-9_\-]+"
    r"|\bAKIA[A-Z0-9]{16}\b"
)
# NAME=value for names that usually hold a secret. The name stays visible.
_SECRET_ASSIGNMENT = re.compile(
    r"\b(?P<name>GITHUB_TOKEN|GH_TOKEN|OPENAI_API_KEY|API_KEY|SECRET|PASSWORD|TOKEN)"
    r"\s*=\s*\S+",
    re.IGNORECASE,
)


def redact_secrets(text: str) -> str:
    """Hide token values in text before it is printed or saved.

    The name of a variable can stay, so a log still shows that a token was
    present. The value is replaced with ***. Host files are not read.
    """
    hidden = _TOKEN_PREFIXES.sub("***", text)
    return _SECRET_ASSIGNMENT.sub(r"\g<name>=***", hidden)


def host_env_for_container() -> dict[str, str]:
    """Return host environment variables to copy into the container.

    Always empty. Tokens and other variables on this machine stay here
    and are not given to the repo's commands.
    """
    return {}
