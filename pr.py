import subprocess
import argparse
import os
import requests


def get_pr_info(owner, repo, pr_number):
    response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}')
    if response.status_code == 200:
        pr_data = response.json()
        git, branch = (pr_data['head']['repo']['clone_url'], pr_data['head']['ref'])
        if not git or not branch:
            raise Exception('pr info fail')
        return (git, branch)
    else:
        raise Exception('pr pulls fail')


def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_directory)

    parser = argparse.ArgumentParser(description='Command Line Parser')
    parser.add_argument('--pr', default='', help='pr number', type=int)
    parser.add_argument('--git', default='', help='git url')
    parser.add_argument('--branch', default='', help='git branch')
    parser.add_argument('--commitid', default='', help='git commit id is optional')
    args = parser.parse_args()
    if args.pr:
        args.git, args.branch = get_pr_info('yt-dlp', 'yt-dlp', args.pr)

    subprocess.run(['git', 'remote', '-v']).check_returncode()
    subprocess.run(['git', 'remote', 'add', args.branch, args.git]).check_returncode()
    subprocess.run(['git', 'fetch', args.branch]).check_returncode()
    if args.commitid:
        subprocess.run(['git', 'cherry-pick', args.commitid]).check_returncode()
    else:
        subprocess.run(['git', 'merge', args.branch + '/' + args.branch]).check_returncode()
    subprocess.run(['git', 'remote', 'rm', args.branch]).check_returncode()
    subprocess.run(['git', 'remote', '-v']).check_returncode()

    subprocess.run(['ruff', 'check', './yt_dlp', '--fix', '--unsafe-fixes']).check_returncode()
    subprocess.run(['autopep8', '-i', './yt_dlp']).check_returncode()


if __name__ == '__main__':
    main()
