"""Which terminal-bench packages on ghcr.io can be pulled anonymously, and links to make the rest public.

GitHub has no API to change a package's visibility (UI only: Package settings -> Danger Zone -> Change
visibility -> Public). What worked here: with the repo public, delete the private packages
(`gh api -X DELETE /orgs/milabench/packages/container/<url-encoded name>`, needs the delete:packages scope)
and re-run the terminal-bench workflow; packages it recreates are public. `links` / `open` are the manual
fallback (one click per package).

    python scripts/ghcr_visibility.py check          # public / private per package (anonymous pull test)
    python scripts/ghcr_visibility.py links          # settings URLs of the packages still private
    python scripts/ghcr_visibility.py open [N]       # open the next N (default 10) private ones in the browser

Needs no token: the check asks ghcr.io for an anonymous pull token, as `podman pull` without login would.
"""

import concurrent.futures as cf
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(HERE, "..", "terminal-bench", "images.json")
ORG = os.environ.get("GHCR_ORG", "milabench")
ACCEPT = "application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json"


def packages() -> dict[str, str]:
    """package name -> tag, from images.json."""
    tasks = json.load(open(IMAGES))["tasks"]
    return {f"terminal-bench/{t}": image.rsplit(":", 1)[1] for t, image in tasks.items()}


def public(package: str, tag: str) -> bool | None:
    """True: anonymous pull works; False: denied (private); None: not found or other error."""
    try:
        url = f"https://ghcr.io/token?scope=repository:{ORG}/{package}:pull"
        token = json.load(urllib.request.urlopen(url, timeout=30)).get("token", "")
        req = urllib.request.Request(f"https://ghcr.io/v2/{ORG}/{package}/manifests/{tag}",
                                     headers={"Authorization": f"Bearer {token}", "Accept": ACCEPT}, method="HEAD")
        urllib.request.urlopen(req, timeout=30)
        return True
    except urllib.error.HTTPError as e:
        return False if e.code in (401, 403) else None
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def status() -> dict[str, bool | None]:
    pkgs = packages()
    with cf.ThreadPoolExecutor(16) as ex:
        return dict(zip(pkgs, ex.map(lambda p: public(p, pkgs[p]), pkgs)))


def settings_url(package: str) -> str:
    return f"https://github.com/orgs/{ORG}/packages/container/{urllib.parse.quote(package, safe='')}/settings"


def main(argv):
    cmd = argv[0] if argv else "check"
    st = status()
    private = [p for p, s in sorted(st.items()) if s is False]
    if cmd == "check":
        unknown = [p for p, s in sorted(st.items()) if s is None]
        print(f"public {sum(s is True for s in st.values())} / private {len(private)} / unknown {len(unknown)}"
              f" (of {len(st)})")
        for p in unknown:
            print("  unknown (missing image or network error):", p)
    elif cmd == "links":
        for p in private:
            print(settings_url(p))
    elif cmd == "open":
        n = int(argv[1]) if len(argv) > 1 else 10
        for p in private[:n]:
            webbrowser.open_new_tab(settings_url(p))
        print(f"opened {min(n, len(private))} of {len(private)} private packages; run again for the next batch")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
