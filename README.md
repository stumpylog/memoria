# README

## Snippets

Fix DTL url to Jinja2:

- `\{%\s*url\s+'([^']+)'\s*%\}` -> `{{ url('$1') }}`
