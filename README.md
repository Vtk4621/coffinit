# coffinit

> Things OSS projects do before they die.

## Demo output

```
🪣 coffinit — numpy/numpy

    _________          _________
   /_________\\       /   ___   \\
  //          \\     /    | |    \\
 //  [ALIVE]   \\   / ____| |____ \\
//      C       \\ / |____   ____| \\
\\      O       // \\     | |      //
 \\     F      //   \\    | |     //
  \\    F     //     \\   | |    //
   \\   I    //       \\  | |   //
    \\  N   //         \\ |_|  //
     \\____//           \\    //
      \\__//             \\__//
Score: 91 / 100  ✅ Alive

📋 Detail Score
┌──────────────────────────────┬────────┐
│ Maintenance                  │ 25/25  │
│ PR response                  │ 18/25  │
│ Bug backlog                  │ 23/25  │
│ Author activity              │ 25/25  │
└──────────────────────────────┴────────┘

🕐 Last commit: 3 days ago
🔀 Latest PR: 21 days ago
🐛 bug-labelled issues: 8%
👤 Recent contributor: 2 days ago
```

## 1. Concept / Why

`coffinit` is a CLI tool that diagnoses whether a GitHub OSS project is alive or dead. It scores the repository from four angles and shows the result with coffin ASCII art.

## 2. Installation

```bash
# clone the repo
git clone https://github.com/<owner>/<repo>.git
cd coffinit

# install in editable mode
pip install -e .
```

## 3. Setup (GitHub token)

Create a GitHub personal access token and store it in `.env`:

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Token steps (classic PAT):

1. GitHub → Settings
2. Developer settings
3. Personal access tokens → Generate new token
4. Enable `public_repo` scope
5. Copy the token into `.env`

## 4. Usage

### 起動の仕方

```bash
coffinit
```

### コマンド一覧

```bash
coffinit --help
coffinit --version
coffinit check <owner>/<repo>
coffinit set-lang
```

### 言語切り替え

- Default language is `ja`.
- `coffinit set-lang` is interactive (arrow keys + Enter) and saves your selection to a user config file.
- Per-run overrides:
	- `--lang ja|en`
	- `COFFINIT_LANG=ja|en`

Examples:

```bash
# Persist selection (ja/en)
coffinit set-lang

# One-off override (CLI option)
coffinit --lang en check numpy/numpy

# One-off override (env var)
COFFINIT_LANG=en coffinit check numpy/numpy
```

## 5. Scoring

Total: 100 points (4 axes × 25 points).

### 1) Maintenance (last commit)

| Days since last commit | Score |
|---|---|
| 0-30 | 25 |
| 31-90 | 18 |
| 91-180 | 10 |
| 181-365 | 5 |
| 365+ | 0 |

### 2) PR response (latest open PR)

| Days since latest open PR | Score |
|---|---|
| No open PR | 25 |
| 0-14 | 25 |
| 15-30 | 18 |
| 31-90 | 10 |
| 91-180 | 5 |
| 180+ | 0 |

### 3) Bug backlog (open rate)

Open rate = `open / (open + closed)` for issues with `bug` label.

| Open rate | Score |
|---|---|
| No bug-labelled issues | 25 |
| 0-10% | 25 |
| 11-30% | 18 |
| 31-50% | 10 |
| 51-70% | 5 |
| 71%+ | 0 |

### 4) Author activity (contributors)

Based on the most recent activity among top 3 contributors.

| Last activity | Score |
|---|---|
| <= 30 days | 25 |
| 31-90 days | 18 |
| 91-180 days | 10 |
| 181-365 days | 5 |
| 365+ days | 0 |

### Final judgement

| Total score | Label | Lid |
|---|---|---|
| 80-100 | ✅ Alive | Fully open |
| 50-79 | ⚠️ Struggling | Half open |
| 20-49 | 🪦 On The Bucket List | Slightly open |
| 0-19 | ⚰️ Dead | Closed |

## 6. Error Messages

Error messages are kept in Japanese, and in `en` mode the English text is appended in parentheses.

| Case | Message (JA) |
|---|---|
| Token missing | 神父の名前も知らねぇのか？（GITHUB_TOKENを.envに設定しろ） |
| Repository not found | この棺桶は空だ。死に損ないのジジババが終活のために買ったものなようだ。 |
| Private repo | おいおい、家族以外葬儀の立ち合いはできねぇぜ？ |
| Rate limit | 神父は今日はお休みだってよ。 |
| Network error | 霊柩車がパンクしちまった。 |
| Unknown error | なんか葬儀場で事故が起きたみたいだ。 |

## 7. Project Structure

```
coffinit/
	coffinit/
		__init__.py
		cli.py
		config.py
		display.py
		github.py
		i18n.py
		scorer.py
	LICENSE
	pyproject.toml
	README.md
```

## 8. Requirements

- Python >= 3.11
- Dependencies:
	- typer
	- rich
	- python-dotenv
	- requests

## 9. License

MIT License. See LICENSE.
