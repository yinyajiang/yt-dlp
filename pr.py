import subprocess
import argparse
import os


def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_directory)

    parser = argparse.ArgumentParser(description='Command Line Parser')
    parser.add_argument('--git', default='', help='Special Config')
    parser.add_argument('--branch', default='', help='signature is not required')
    parser.add_argument('--commitid', default='', help='signature is not required')
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


if __name__ == '__main__':
    main()
