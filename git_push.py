#!/bin/python3

import sys
import subprocess
from pathlib import Path
from datetime import datetime

help = ("""
Usage:
    python3 script.py <path_to_directory> [--dry-run | -d]

Arguments:
    <path_to_directory>   Path where the program will search for git repositories.
    --dry-run, -d         Show which commits would be made, but do not push changes.
    -h, --help            Show this help message.

Example:
    python3 script.py /home/user/projects --dry-run
""")

class Git_command():
    def has_changes(self, repo_path):
        result = subprocess.run(['git', '-C', repo_path, 'status', '--porcelain'], stdout=subprocess.PIPE, text=True)
        return bool(result.stdout.strip())
    
    def auto_commit(self, repo_path, flag_dry):
        if flag_dry:
                print("dry-mode")
        print(f"repo_path: {repo_path}")
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        lines = [f"Auto-commit: {timestamp}"]

        try:
            ignored_files = subprocess.run(['git', '-C', repo_path, 'ls-files', '-i', '--exclude-standard', '-c'], stdout=subprocess.PIPE, text=True).stdout.strip().split("\n")
            print(ignored_files)
            if ignored_files and ignored_files != ['']:
                subprocess.run(['git', '-C', repo_path, 'rm', '--cached', '--ignore-unmatch'] + ignored_files, check=True)


            subprocess.run(['git', '-C', repo_path, 'reset'], check=True, stdout=subprocess.PIPE)               # Удалить все файлы из staged
            subprocess.run(['git', '-C', repo_path, 'add', '--all'], check=True, stdout=subprocess.PIPE)        # Добавляем все изменения
            result = subprocess.run(['git', '-C', repo_path, 'diff', '--cached', '--name-status'], stdout=subprocess.PIPE, text=True)   # Добываем изменения
            added, modified, deleted = [], [], []
    
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                status = parts[0]
                
                if status == "A":
                    added.append(parts[1])
                elif status == "M":
                    modified.append(parts[1])
                elif status == "D":
                    deleted.append(parts[1])
                elif status.startswith("R"):
                    deleted.append(parts[1])
                    added.append(parts[2])          # новая версия имени файла

            if added:
                lines.append(f"Added:    {', '.join(added)}")
            if modified:
                lines.append(f"Modified: {', '.join(modified)}")
            if deleted:
                lines.append(f"Deleted:  {', '.join(deleted)}")

            commit_message = "\n".join(lines)
            print(commit_message)

            if flag_dry:
                subprocess.run(['git', '-C', repo_path, 'reset'], check=True, stdout=subprocess.PIPE)               # Удалить все файлы из staged
                return True

            subprocess.run(['git', '-C', repo_path, 'commit', '-m', commit_message], check=True, stdout=subprocess.PIPE, text=True) # Делаем коммит
            subprocess.run(['git', '-C', repo_path, 'push'], check=True, stdout=subprocess.PIPE, text=True) # Пушим в текущую ветку
            return True
        except subprocess.CalledProcessError:
            return False

def list_dirs(full_path, git):
    list_dirs = []
    for git_dir in full_path.rglob(".git"):
        if git_dir.is_dir():
            repo_root = git_dir.parent
            if git.has_changes(repo_root):
                list_dirs.append(repo_root)
                print(f"repo {repo_root} added.                      <-----")
                print("==============================================")
            else:
                print(f"repo {repo_root} no changes. Skipping.")
                print("==============================================")
    return list_dirs


def main():
    git = Git_command()
    flag_dry = 0
    repos = []

    args = sys.argv[1:]
    if len(args) == 0 or "-h" in args or "--help" in args:
        print(help)
        exit(0)

    if "--dry-run" in args or "-d" in args:
        flag_dry = 1

    full_paths = [Path(arg).resolve() for arg in args if not arg.startswith('-')]

    for full_path in full_paths:
        if full_path.exists() and full_path.is_dir():
            repos.extend(list_dirs(full_path, git))
        else:
            print(f"{full_path} isn't dir or  not exists")

    if repos:
        for repo in repos:
            if git.auto_commit(repo, flag_dry):
                if not flag_dry:
                    print(f"repo {repo} commited")
                print("==============================================")
            else:
                print(f"repo {repo} commited error")
                print("==============================================")
    else:
        print("NO changes!!!")
        exit(0)


if __name__ == "__main__":
    main()
