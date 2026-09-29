from urllib.parse import urlparse

from pydantic import BaseModel

from readme2run.configurations.loader import Settings


class UrlDecision(BaseModel):
    """The result of checking one URL.

    allowed is true when the URL may be cloned. reason explains a rejection
    and is empty when the URL is allowed. This object does not clone anything.
    """

    allowed: bool
    reason: str = ""


def url_policy(url: str, settings: Settings) -> UrlDecision:
    """Allow or reject a repository URL.

    https is allowed for real runs. file is allowed only when
    settings.allow_file_urls is on, so tests can point at a local fixture.
    Every other scheme, including ssh and http, is rejected.
    This function does not clone the URL, run a command, or call a model.
    """
    scheme = urlparse(url).scheme.lower()
    if scheme == "https":
        return UrlDecision(allowed=True)
    if scheme == "file":
        if settings.allow_file_urls:
            return UrlDecision(allowed=True)
        return UrlDecision(
            allowed=False,
            reason="file URLs are allowed only when the test flag is on",
        )
    shown = scheme or "(none)"
    return UrlDecision(
        allowed=False,
        reason=f"scheme {shown} is not allowed; use https",
    )
