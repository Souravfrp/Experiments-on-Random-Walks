# Preparing the first public GitHub repository

I want the public repository title to read **Experiments on Random Walks**. The repository URL should use the GitHub-compatible name `Experiments-on-Random-Walks` under `Souravfrp`.

Before publishing, I will review the mathematics and first-person research notes, run the tests, and check the collected data policy. The public archive includes the explicit and optimized Python/C++ code, numerical summaries, a notebook, figure examples and the optimization appendix. Local full experiments under `runs/` and `runs_baseline/` are excluded from Git to avoid storing every sampled coordinate in repository history.

## Create the empty repository on GitHub

1. Sign in to GitHub and visit https://github.com/new.
2. Select account `Souravfrp` and repository name `Experiments-on-Random-Walks`.
3. Choose **Public** if the intention is an openly accessible research project.
4. **Do not pre-add a README, `.gitignore` or license** on the GitHub creation screen, because the downloaded folder already contains the first two and a license has not yet been chosen.
5. Click **Create repository**.

## Publish the reviewed contents from my Mac

Extract the ZIP into `~/Downloads/Experiments-on-Random-Walks` first. In Terminal:

```bash
cd ~/Downloads/Experiments-on-Random-Walks
conda activate random-walks-viz
python -m unittest discover -s tests -v
git init -b main
git add .
git status --short
git commit -m "Added explicit and optimized random-walk research framework"
git remote add origin https://github.com/Souravfrp/Experiments-on-Random-Walks.git
git push -u origin main
```

Before committing, I should inspect `git status --short` and verify that it contains no large raw trajectory files, account credentials or executables. If GitHub requires authentication for `git push`, I should sign in using Git Credential Manager, GitHub CLI or an appropriate personal access token; never put a token in source code or chat.

When the push finishes, the project should appear at:

https://github.com/Souravfrp/Experiments-on-Random-Walks

## After initial publication

The repository's notebook runs the same published algorithms but only **local** experiments are automatically recorded. Later, selected runs may be contributed as small reviewed CSV entries. I will not promise that every visitor's results automatically upload to GitHub.

There is no license in the review copy. I should choose a license intentionally before inviting broad reuse and contributions.
