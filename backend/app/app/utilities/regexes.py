from dataclasses import dataclass
import re
from urllib.parse import urlparse

# from app.core.config import settings


@dataclass
class Regexes:
    """
    Inspired by https://github.com/superseriousbusiness/gotosocial/blob/main/internal/regexes/regexes.go
    and https://stackoverflow.com/a/55827638/295606
    Check https://regex101.com/r/A326u1/5 for reference
    """

    # STANDARDS
    users: str = r"users"
    actors: str = r"actors"
    statuses: str = r"statuses"
    inbox: str = r"inbox"
    outbox: str = r"outbox"
    followers: str = r"followers"
    following: str = r"following"
    liked: str = r"liked"
    featured: str = r"featured"
    publicKey: str = r"main-key"
    follow: str = r"follow"
    blocks: str = r"blocks"
    reports: str = r"reports"

    # DEFINITIONS
    # Allowed URI protocols for parsing links in text.
    schemes: str = r"(http|https)://"
    # A single number or script character in any language, including chars with accents.
    alphaNumeric: str = r"\p{L}\p{M}*|\p{N}"
    # Non-capturing group that matches against a single valid actorname character.
    actornameGrp: str = r"(?:" + alphaNumeric + r"|\.|\-|\_)"
    # Non-capturing group that matches against a single valid domain character.
    domainGrp: str = r"(?:" + alphaNumeric + r"|\.|\-|\:)"
    # Extract parts of one mention, maybe including domain.
    mentionName: str = r"^@(" + actornameGrp + r"+)(?:@(" + domainGrp + r"+))?$"
    # Extract all mentions from a text, each mention may include domain.
    mentionFinder: str = r"(?:^|\s)(@" + actornameGrp + r"+(?:@" + domainGrp + r"+)?)"
    # Pattern for emoji shortcodes. maximumEmojiShortcodeLength = 30
    emojiShortcode: str = r"\w{2,30}"
    # Extract all emoji shortcodes from a text.
    emojiFinder: str = r"(?:\b)?:(" + emojiShortcode + r"):(?:\b)?"
    # Validate a single emoji shortcode.
    emojiValidator: str = r"^" + emojiShortcode + r"$"
    # Pattern for actornames on THIS instance. maximumactornameLength = 64
    actornameStrict: str = r"^[a-z0-9_]{1,64}$"
    # Relaxed version of actorname that can match instance accounts too.
    actornameRelaxed: str = r"[a-z0-9_\.]{1,}"
    # Extract reported Note URIs from the text of a Misskey report/flag.
    misskeyReportNotesFinder: str = r"(?m)(?:^Note: ((?:http|https):\/\/.*)$)"
    # Pattern for ULID.
    ulid: str = r"[0123456789ABCDEFGHJKMNPQRSTVWXYZ]{26}"
    # Validate one ULID.
    ulidValidate: str = r"^" + ulid + r"$"

    # PATH PARTS
    actorPathPrefix: str = r"^/?" + actors + r"/(" + actornameRelaxed + r")"
    actorPath: str = actorPathPrefix + r"$"
    actorWebPathPrefix: str = r"^/?" + r"@(" + actornameRelaxed + r")"
    actorWebPath: str = actorWebPathPrefix + r"$"
    publicKeyPath: str = actorPathPrefix + r"/" + publicKey + r"$"
    inboxPath: str = actorPathPrefix + r"/" + inbox + r"$"
    outboxPath: str = actorPathPrefix + r"/" + outbox + r"$"
    followersPath: str = actorPathPrefix + r"/" + followers + r"$"
    followingPath: str = actorPathPrefix + r"/" + following + r"$"
    likedPath: str = actorPathPrefix + r"/" + liked + r"$"
    followPath: str = actorPathPrefix + r"/" + follow + r"/(" + ulid + r")$"
    likePath: str = actorPathPrefix + r"/" + liked + r"/(" + ulid + r")$"
    statusesPath: str = actorPathPrefix + r"/" + statuses + r"/(" + ulid + r")$"
    blockPath: str = actorPathPrefix + r"/" + blocks + r"/(" + ulid + r")$"
    reportPath: str = r"^/?" + reports + r"/(" + ulid + r")$"
    filePath: str = r"^/?(" + ulid + r")/([a-z]+)/([a-z]+)/(" + ulid + r")\.([a-z0-9]+)$"

    # COMPILED
    DOMAIN_FORMAT: re.Pattern = re.compile(
        r"(?:^(\w{1,255}):(.{1,255})@|^)"  # http basic authentication [optional]
        r"(?:(?:(?=\S{0,253}(?:$|:))"  # check full domain length to be less than or equal to 253 (starting after http basic auth, stopping before port)
        r"((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"  # check for at least one subdomain (maximum length per subdomain: 63 characters), dashes in between allowed
        r"(?:[a-z0-9]{1,63})))"  # check for top level domain, no dashes allowed
        r"|localhost)"  # accept also "localhost" only
        r"(:\d{1,5})?",  # port [optional]
        re.IGNORECASE,
    )
    SCHEME_FORMAT: re.Pattern = re.compile(r"^(http|hxxp|ftp|fxp)s?$", re.IGNORECASE)  # scheme: http(s) or ftp(s)

    def matches(self, exp: str, term: str) -> bool:
        if re.fullmatch(exp, term):
            return True
        return False

    def url_validates(self, url: str) -> bool:
        try:
            url = str(url).strip()
            if not url or len(url) > 2048:
                return False
            result = urlparse(url)
            scheme = result.scheme
            domain = result.netloc
            return all(
                [
                    scheme in ["file", "http", "https"],
                    self.matches(self.SCHEME_FORMAT, scheme),
                    domain,
                    self.matches(self.DOMAIN_FORMAT, domain),
                ]
            )
        except (AttributeError, ValueError, TypeError):
            pass
        return False

    def url_root(self, url: str) -> str:
        if self.url_validates(url):
            return urlparse(str(url)).netloc
        return url


regex = Regexes()
