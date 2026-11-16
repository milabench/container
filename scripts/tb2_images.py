"""Terminal-Bench task images: list them, and print the build plan for one task.

    python scripts/tb2_images.py list                 # JSON list of task names (the CI matrix)
    python scripts/tb2_images.py sync <tasks-dir>     # rewrite terminal-bench/images.json from a `harbor download`
    python scripts/tb2_images.py target <task>        # the image names milabench uses for <task>

Image names (REGISTRY defaults to ghcr.io/milabench):
    <REGISTRY>/terminal-bench/<task>:<upstream tag>-arm64   built here, natively on an arm64 runner
    <REGISTRY>/terminal-bench/<task>:<upstream tag>         multi-arch: upstream amd64 + our arm64

With the multi-arch name, the task.toml milabench rewrites has the same docker_image on every machine.
"""

import json
import os
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(HERE, "..", "terminal-bench", "images.json")
REGISTRY = os.environ.get("REGISTRY", "ghcr.io/milabench")


def load() -> dict:
    return json.load(open(IMAGES))


def target(task: str) -> dict:
    upstream = load()["tasks"][task]
    tag = upstream.rsplit(":", 1)[1]
    base = f"{REGISTRY}/terminal-bench/{task}"
    return {"upstream": f"docker.io/{upstream}", "arm64": f"{base}:{tag}-arm64", "multiarch": f"{base}:{tag}"}


def sync(tasks_dir: str):
    data = load()
    tasks = {}
    for name in sorted(os.listdir(tasks_dir)):
        toml = os.path.join(tasks_dir, name, "task.toml")
        if os.path.exists(toml):
            tasks[name] = tomllib.load(open(toml, "rb"))["environment"]["docker_image"]
    data["tasks"] = tasks
    with open(IMAGES, "w") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    print(f"{len(tasks)} tasks -> {IMAGES}")


def main(argv):
    cmd = argv[0] if argv else "list"
    if cmd == "list":
        print(json.dumps(sorted(load()["tasks"])))
    elif cmd == "sync":
        sync(argv[1])
    elif cmd == "target":
        print(json.dumps(target(argv[1])))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
