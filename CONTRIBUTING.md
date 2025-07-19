# 🤝 Contributing to This Project

Thanks for considering a contribution to **DuoSubs**.

Whether you're fixing bugs, improving the CLI, refining alignment logic, or just cleaning up docs — contributions are always welcome.

---

## 🚀 Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/REPO/REPO.git
   cd your-repo
   ```
3. Create a **virtual environment** and install dev dependencies:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    pip install -e .[dev]
    ```

---

## 🛠️ Making a Change

1. Create a new branch:

    ```bash
    git checkout -b fix/your-branch-name
    ```

2. Make your changes and commit them based on the [commit message format](#-commit-message-format):

    ```bash
    git add .
    git commit -m "fix: clear description of your fix"
    ```

3. Push to your fork:

    ```bash
    git push origin fix/your-branch-name
    ```

4. Open a **pull request** against the `master` branch.

---

## 🧹 Code Quality

Run this before submitting a pull request:

    ```bash
    ruff check . --fix     # Lint + format (like black)
    mypy .                 # Type checks
    pytest                 # Run tests
    ```

---

## ✅ Commit Message Format

This project follows the **Conventional Commits** format to keep things consistent and automatable:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

*Examples*:
```text
feat: add support for .sbv subtitle format
fix(cli): handle missing secondary file error
docs: update CLI usage in README
```

### 🔑 Common Types

| Type        | Use for...                         |
|-------------|-------------------------------------|
| **feat**    | A new feature                       |
| **fix**     | A bug fix                           |
| **docs**    | Documentation-only changes          |
| **style**   | Code style (formatting, no logic)   |
| **refactor**| Refactoring code (no new feature)   |
| **perf**    | Performance improvements            |
| **test**    | Adding or improving tests           |
| **chore**   | Maintenance (deps, tooling, etc.)   |
| **ci**      | CI/CD pipeline changes              |

### 🚨 Breaking Changes

Use `!` to indicate breaking changes:
```bash
feat!: change output structure of merged files
```

---

## ✅ Final Notes

- Be respectful and clear in PR discussions
- Try to include tests when fixing bugs or adding features
- If you're not sure — just ask in an issue!

Thanks again for helping improve DuoSubs! 🙌
