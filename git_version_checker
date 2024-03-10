import subprocess
import sys

def get_local_latest_commit(repo_path, branch='main'):
    """Gets the latest commit hash of the local repository."""
    try:
        completed_process = subprocess.run(['git', '-C', repo_path, 'rev-parse', branch], 
                                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return completed_process.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error obtaining local latest commit: {e.stderr.decode()}")
        sys.exit(1)

def get_remote_latest_commit(repo_url, branch='main'):
    """Gets the latest commit hash from the remote repository."""
    try:
        completed_process = subprocess.run(['git', 'ls-remote', repo_url, branch], 
                                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        commit_hash = completed_process.stdout.decode().split()[0]
        return commit_hash
    except subprocess.CalledProcessError as e:
        print(f"Error obtaining remote latest commit: {e.stderr.decode()}")
        sys.exit(1)

def compare_versions(local_commit, remote_commit):
    """Compares the local and remote commit hashes."""
    if local_commit == remote_commit:
        print("Local repository is up-to-date with the remote repository.")
    else:
        print("Local repository is not up-to-date. Please pull the latest changes.")

if __name__ == "__main__":
    REPO_PATH = '/path/to/your/local/repo'  # Local Git repository path
    REPO_URL = 'https://github.com/yourusername/yourrepo.git'  # Remote repository URL
    BRANCH = 'main'  # Branch to check

    local_commit = get_local_latest_commit(REPO_PATH, BRANCH)
    remote_commit = get_remote_latest_commit(REPO_URL, BRANCH)
    compare_versions(local_commit, remote_commit)
