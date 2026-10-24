# Sukhjeet — Day 2: admin package creation

## Prerequisite
The Day 1 database schema must be merged into `main`. This uses the existing `admin` blueprint and its `admin_required` check.

## Replace
- `app/admin/routes.py`
- `app/templates/admin/add_package.html`

Keep `app/admin/__init__.py`, `app/templates/admin/dashboard.html`, and `app/static/css/admin.css` from Day 1.

The form accepts multiple destinations, one per line, in this format:
`Place name | City | Short description | Image URL`
The image URL is optional for each location. The package itself has its own main image URL.

## Git commands
From the existing project folder, before copying the ZIP files:

```bash
git fetch origin
git switch main
git pull origin main
git switch -c feature/sukhjeet-day2-admin-package-create
```

Copy the files from this ZIP into the project root, preserving folders, then run:

```bash
git add app/admin/routes.py app/templates/admin/add_package.html README_SUKHJEET_DAY2.md
git commit -m "Day 2: support creating packages with multiple locations"
git push -u origin feature/sukhjeet-day2-admin-package-create
```

Open a Pull Request from `feature/sukhjeet-day2-admin-package-create` into `main`.
If the branch already exists, use `git switch feature/sukhjeet-day2-admin-package-create` instead of `git switch -c ...`.
