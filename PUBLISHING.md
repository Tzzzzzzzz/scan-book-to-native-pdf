# Publishing checklist

本文件用于把已准备好的技能包发布到 GitHub。它不要求、也不记录密码、个人访问令牌或 SSH 私钥。

## 1. Authenticate locally

Install GitHub CLI (`gh`) or configure a Git Credential Manager/SSH key on the publishing machine. For the CLI flow:

```text
gh auth login
gh auth status
```

Choose the `Tzzzzzzzz` account in the interactive prompt. Never paste a token into a commit, issue, chat message, or README.

## 2. Choose the destination

Use a new repository unless the owner explicitly selected an existing one. The recommended name is:

```text
Tzzzzzzzz/scan-book-to-native-pdf
```

The repository is intended to be public and now carries the MIT License in `LICENSE`. The license covers this skill package and its documentation only; it does not cover source books, reconstructed books, or third-party fonts.

## 3. Create or connect the repository

From this package directory, a new repository can be created with:

```text
gh repo create Tzzzzzzzz/scan-book-to-native-pdf --public --source . --remote origin --push
```

For an already-created empty repository:

```text
git remote add origin https://github.com/Tzzzzzzzz/scan-book-to-native-pdf.git
git push -u origin main
```

If `origin` already exists, inspect it with `git remote -v` before changing it. Do not force-push over unrelated history.

## 4. Verify the release

```text
git status --short
git log -1 --oneline
git ls-tree -r --name-only HEAD
python scripts/validate_wikiskill.py .
Get-Content LICENSE -TotalCount 3
```

The repository should contain the skill package, WikiSkill evidence, scripts, references, and the two Markdown guides. It should not contain source books, reconstructed book PDFs, rendered page images, OCR caches, or credentials. `RELEASE-MANIFEST.json` records hashes for every packaged file except the manifest itself.

## 5. Optional GitHub release

After the repository is visible at the intended URL, create a tag only from the verified commit and attach no source-book PDFs unless redistribution rights are established:

```text
git tag -a v0.2.0 -m "WikiSkill release 2"
git push origin v0.2.0
```
