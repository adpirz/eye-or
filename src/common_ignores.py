COMMON_IGNORE_PATTERNS = {
    # Version Control
    ".git/",
    ".svn/",
    ".hg/",
    ".bzr/",
    # GitHub and CI/CD
    ".github/",
    ".gitlab/",
    ".circleci/",
    ".travis.yml",
    # Python
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "*.so",
    "*.egg",
    "*.egg-info/",
    "dist/",
    "build/",
    "eggs/",
    "parts/",
    "bin/",
    "var/",
    "sdist/",
    "develop-eggs/",
    "*.egg-info/",
    ".installed.cfg",
    "lib/",
    "lib64/",
    # Virtual Environments
    "venv/",
    ".venv/",
    "env/",
    ".env",
    ".env.*",
    "ENV/",
    # IDE and Editor Files
    ".idea/",
    ".vscode/",
    "*.swp",
    "*.swo",
    "*~",
    ".vs/",
    "*.sublime-workspace",
    "*.sublime-project",
    # Node/JavaScript
    "node_modules/",
    "npm-debug.log*",
    "yarn-debug.log*",
    "yarn-error.log*",
    ".npm/",
    ".yarn/",
    # Logs and Databases
    "*.log",
    "*.sqlite",
    "*.db",
    # OS Generated Files
    ".DS_Store",
    ".DS_Store?",
    "._*",
    ".Spotlight-V100",
    ".Trashes",
    "ehthumbs.db",
    "Thumbs.db",
    # Coverage and Test Reports
    "htmlcov/",
    ".tox/",
    ".coverage",
    ".coverage.*",
    ".cache",
    "nosetests.xml",
    "coverage.xml",
    "*.cover",
    ".hypothesis/",
    ".pytest_cache/",
    # Documentation
    "docs/_build/",
    "site/",
    # Misc
    "*.bak",
    "*.tmp",
    "*.temp",
    "*.orig",
    "*.rej",
}
