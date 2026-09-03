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

Confirm `private` or `public` visibility and select an appropriate license before a public release. The package does not overwrite an existing repository and does not select a license on the author's behalf.

## 3. Create or connect the repository

From this package directory, a new private repository can be created with:

```text
gh repo create Tzzzzzzzz/scan-book-to-native-pdf --private --source . --remote origin --push
```

Replace `--private` with `--public` only after the visibility and redistribution rights are confirmed. For an already-created empty repository:

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
```

The repository should contain the skill package, WikiSkill evidence, scripts, references, and the two Markdown guides. It should not contain source books, reconstructed book PDFs, rendered page images, OCR caches, or credentials. `RELEASE-MANIFEST.json` records hashes for every packaged file except the manifest itself.

## 5. Optional GitHub release

After the repository is visible at the intended URL, create a tag only from the verified commit and attach no source-book PDFs unless redistribution rights are established:

```text
git tag -a v0.2.0 -m "WikiSkill release 2"
git push origin v0.2.0
```
