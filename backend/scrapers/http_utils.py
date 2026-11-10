"""
Shared HTTP settings for the no-browser scrapers (City Winery feeds, MetroTix HTML).
"""
import ssl

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Some sites (e.g. citywinery.com behind Cloudflare) return 403 without normal
# browser Accept headers.
BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/calendar,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def ssl_context() -> ssl.SSLContext:
    """Verified TLS (certificate chain + hostname), without Python 3.13's extra
    VERIFY_X509_STRICT check. Some company proxies re-sign HTTPS with
    certificates missing the optional Authority Key Identifier, which strict
    mode rejects. Matches Python 3.12 behavior."""
    context = ssl.create_default_context()
    strict = getattr(ssl, "VERIFY_X509_STRICT", 0)
    if strict:
        context.verify_flags &= ~strict
    return context
