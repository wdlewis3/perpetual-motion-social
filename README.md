# perpetual-motion-social

Image host and working files for Perpetual Motion's weekly Instagram routine.

- `generate.py` — renders the post graphics (see its docstring for the spec format). Needs Pillow; `pyoxipng` optional.
- `posts/log.md` — one line per run; drives the topic/format rotation.
- `posts/YYYY-MM-DD-slug.md` — the full copy for each post (caption, slides, or Reel script).
- `images/YYYY/` — the rendered graphics. Public raw URLs from here are what Metricool/Instagram fetch.

Everything in this repo is public. Only post graphics and post copy belong here; never credentials.
