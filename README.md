# container

Container images that milabench needs and that upstream does not publish for every architecture.

## terminal-bench/

Terminal-Bench 2.0 task images for arm64 (DGX Spark / GB10). Upstream (`docker.io/alexgshaw/<task>:<tag>`) is
amd64 only. `.github/workflows/terminal-bench.yml` builds each task's own `environment/Dockerfile` (from
`harbor download terminal-bench@2.0`) natively on an arm64 runner and publishes:

| image | content |
|---|---|
| `ghcr.io/milabench/terminal-bench/<task>:<tag>-arm64` | our arm64 build |
| `ghcr.io/milabench/terminal-bench/<task>:<tag>` | multi-arch: upstream amd64 + our arm64 |

milabench's `terminalbench` pass rewrites each task's `docker_image` to the multi-arch name, so the same task
files work on x86_64 and aarch64. A task whose build fails has no multi-arch tag and is skipped (and reported).

- Pinned inputs: `terminal-bench/images.json` (dataset version, harbor version, task -> upstream image).
  Refresh: `harbor download terminal-bench@2.0 -o src && python scripts/tb2_images.py sync src/terminal-bench`.
- Run: Actions -> "terminal-bench images" -> Run workflow (optionally a space-separated task list, or `rebuild`).
  It also runs when `images.json` changes on `main`. Existing images are skipped.
- After the first run, make the `terminal-bench/*` packages public (GitHub -> milabench -> Packages -> settings)
  so the nodes pull without logging in.

Known arm64 risks: caffe-cifar-10, install-windows-3.11, qemu-startup, qemu-alpine-ssh (x86 guests under TCG),
custom-memory-heap-crash (builds GCC twice: slow), mteb-leaderboard / mteb-retrieve (~20 GB images).
