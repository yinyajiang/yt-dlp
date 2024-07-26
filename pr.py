import subprocess
import argparse
import os


def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_directory)

    parser = argparse.ArgumentParser(description='Command Line Parser')
    parser.add_argument('--git', default='', help='git url is required')
    parser.add_argument('--branch', default='', help='git branch is required')
    parser.add_argument('--commitid', default='', help='git commit id is optional')
    args = parser.parse_args()
    subprocess.run(['git', 'remote', '-v']).check_returncode()
    subprocess.run(['git', 'remote', 'add', args.branch, args.git]).check_returncode()
    subprocess.run(['git', 'fetch', args.branch]).check_returncode()
    if args.commitid:
        subprocess.run(['git', 'cherry-pick', args.commitid]).check_returncode()
    else:
        subprocess.run(['git', 'merge', args.branch + '/' + args.branch]).check_returncode()
    subprocess.run(['git', 'remote', 'rm', args.branch]).check_returncode()
    subprocess.run(['git', 'remote', '-v']).check_returncode()

    subprocess.run(['ruff', 'check', './yt-dlp', '--fix', '--unsafe-fixes']).check_returncode()
    subprocess.run(['autopep8', '-i', './yt-dlp']).check_returncode()


if __name__ == '__main__':
    main()
