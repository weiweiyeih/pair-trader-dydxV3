To remove the current Git repository and initialize a new one, you can use the following commands in your terminal:

```
# Navigate to your project directory
cd /path/to/your/project

# Remove the existing Git repository
rm -rf .git
```

Create a new repo on GitHub and touch `.gitignore` (`.env`, `venv`...)

```
# Initialize a new Git repository
git init

git add .

# review the added files before commit
git status

git commit -m "first commit"

git branch -M main

git remote add origin https://github.com/...git

git push -u origin main
```

Make an update to GitHub

```
git add .

git commit -m "2nd commit"

git push -u origin main
```

List conda-installed packages for pip install

```
pip list --format=freeze > requirements.txt
```
