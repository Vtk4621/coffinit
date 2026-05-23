# coffinit
A CLI tool that diagnoses whether an OSS project is dead or alive.

## Language

- Default language is `ja`.
- You can persist a default language for your user by running `coffinit set-lang` (interactive). This writes a config file under your user config directory.
- You can override per-run with `--lang` or `COFFINIT_LANG`.

Examples:

```bash
# Persist selection (ja/en)
coffinit set-lang

# One-off override
coffinit --lang en check numpy/numpy

# One-off override via env var
COFFINIT_LANG=en coffinit check numpy/numpy
```
