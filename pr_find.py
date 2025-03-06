import requests
import json
import os
import time
import subprocess
import argparse
import re
import pr_ignore
import datetime
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    if os.name == 'nt':
        subprocess.run(['pip', 'install', 'pandas'])
        subprocess.run(['pip', 'install', 'openpyxl'])
    else:
        subprocess.run(['pip3', 'install', 'pandas'])
        subprocess.run(['pip3', 'install', 'openpyxl'])
    import pandas as pd


cur_dir = os.path.dirname(os.path.abspath(__file__))


def is_invalid_pr(pr):
    return any(label['name'] == 'spam' or label['name'] == 'duplicate' or label['name'] == 'invalid' for label in pr.get('labels', []))


def fetch_dont_merged_prs():
    cache = 'pull_requests.json'

    if os.path.exists(cache) and (time.time() - os.path.getmtime(cache)) < 3600 * 24 * 1:
        return json.load(open(cache))

    pull_requests = []
    page = 1

    while True:
        response = requests.get('https://api.github.com/repos/yt-dlp/yt-dlp/pulls', params={'page': page, 'per_page': 100, 'state': 'all'})

        if response.status_code != 200:
            response.raise_for_status()

        page_pull_requests = response.json()
        if not page_pull_requests:
            break
        page += 1
        pull_requests.extend([pr for pr in page_pull_requests if (pr['state'] != 'closed' or not pr.get('merged_at')) and not is_invalid_pr(pr)])

    json.dump(pull_requests, open('pull_requests.json', 'w'), indent=4)

    return pull_requests


def fetch_domains(file_path, fileters, fetch_name):
    df = pd.read_excel(file_path)

    for fileter in fileters:
        if '<' in fileter:
            (name, value) = fileter.split('<')
            df = df[df[name] < float(value)]
        elif '>' in fileter:
            (name, value) = fileter.split('>')
            df = df[df[name] > float(value)]
        elif '=' in fileter:
            (name, value) = fileter.split('=')
            df = df[df[name] == float(value)]

    domains = df[fetch_name].tolist()
    if len(domains) > 1 and '.' not in domains[0]:
        domains = domains[1:]
    return domains


_exectror_files = {}


def _all_exctoror_files():
    global _exectror_files

    if _exectror_files:
        return _exectror_files

    _exectror_files = {}

    for filename in os.listdir(os.path.join(cur_dir, 'yt_dlp', 'extractor')):
        if not filename.endswith('.py') or filename.startswith('_') or filename == 'generic':
            continue
        _exectror_files[filename] = Path(os.path.join(cur_dir, 'yt_dlp', 'extractor', filename)).read_text(encoding='utf-8')
    return _exectror_files


def exist_pr_valid_re(pr):
    ie = get_ie(pr['title'])
    for filename, content in _all_exctoror_files().items():
        if re.search(rf'http:.*{ie}.*', content):
            return filename
    return False


def pr2fpr(pr):
    return {
        'title': pr['title'],
        'url': pr['html_url'],
        'reject': (pr['state'] == 'closed' and not pr.get('merged_at')) or any(label['name'] == 'do-not-merge' for label in pr.get('labels', [])),
        'has_valid_re': exist_pr_valid_re(pr),
        'illegal': any(label['name'] == 'piracy/illegal' for label in pr.get('labels', [])),
        'date': pr['created_at'] or pr['updated_at'],
        'updated_at': pr['updated_at'],
    }


def fprs_sort(frps):
    if not frps:
        return
    frps.sort(key=lambda pr: not pr['has_valid_re'])
    frps.sort(key=lambda pr: datetime.datetime.fromisoformat(pr['date']).timestamp())
    frps.sort(key=lambda pr: not pr['reject'])
    frps.sort(key=lambda pr: not pr['illegal'])


def find_prs(filter_func, pull_requests, ignore_invalid_pr=True):
    pull_requests = [pr for pr in pull_requests if (pr['html_url'] not in pr_ignore.ignore_prs) and (not is_invalid_pr(pr) if ignore_invalid_pr else True)]
    pull_requests = [pr for pr in pull_requests if all(black not in pr['title'] for black in pr_ignore.black_domain)]

    fprs = []
    for pr in pull_requests:
        filter_result = filter_func(pr)
        if filter_result:
            if isinstance(filter_result, dict):
                filter_result.update(pr2fpr(pr))
                fprs.append(filter_result)
            else:
                fprs.append(pr2fpr(pr))
    fprs_sort(fprs)
    return fprs


def get_ie(title):
    title = title.lower()
    ie = ''
    rs = [r'\[ie/(.+?)\]',
          r'\[extractor/(.+?)\]',
          r'\[(.+?)\]',
          r'extractor for \s*([^\s]+)',
          r'add support for \s*([^\s]+)',
          r'add \s*([^\s]+?)\s+support',
          r'\s*([^\s]+?)\s+extractor',
          r'fix \s*([^\s]+)',
          ]
    for r in rs:
        g = re.search(r, title)
        if g:
            ie = g.group(1).lower().strip()
            break
    if not ie:
        ie = title
    if ie.endswith(('.com', '.org', '.net')):
        ie = ie[:-4]
    if ie.startswith('www.'):
        ie = ie[4:]
    return ie


def is_match_domain_pr(domain, pr):
    origi_domain = domain
    if domain.count('.') > 1:
        domain = domain.split('.', 1)[1]

    if len(domain.partition('.')[0]) != 1:
        domain = domain.partition('.')[0]

    title = pr['title'].lower()
    if domain.lower() not in title:
        return False

    ie = get_ie(title)
    if bool(ie.lower() == domain.lower() or ie.lower() == origi_domain.lower()):
        return True
    return len(domain) > 3 and domain in ie


def find_domains_prs(domains, pull_requests):
    def filter_pr(pr):
        for domain in domains:
            if domain in pr_ignore.black_domain:
                continue
            if is_match_domain_pr(domain, pr):
                if 'add' in pr['title'].lower() and has_pr_extractor(pr):
                    continue
                return {
                    'domain': domain.lower(),
                }
        return False

    fpr_map = {}
    for fpr in find_prs(filter_pr, pull_requests, ignore_invalid_pr=False):
        domain = fpr['domain']
        if domain not in fpr_map:
            fpr_map[domain] = []
        fpr_map[domain].append(fpr)

    for fprs in fpr_map.values():
        fprs_sort(fprs)
    return fpr_map


def has_pr_extractor(pr):
    def _is_exist(name: str):
        if not name:
            return False
        name = name.replace('.', '')
        return os.path.exists(os.path.join(cur_dir, 'yt_dlp', 'extractor', f'{name}.py'))

    return _is_exist(get_ie(pr['title']))


def is_only_add_ie_pr(pr):
    if any(label['name'] == 'site-request' for label in pr.get('labels', [])):
        return True
    title = pr['title'].lower()
    return 'add' in title and ('extractor' in title or 'extraction' in title or 'extract' in title)


def main():
    parser = argparse.ArgumentParser(description='Command Line Parser')

    subparsers = parser.add_subparsers(dest='command')
    find = subparsers.add_parser('find', help='call command')
    find.add_argument('--excel', type=str, help='file path')
    find.add_argument('--filter', type=str, nargs='+', help='filter')
    find.add_argument('--domain-column', type=str, help='domain column')

    args = parser.parse_args()

    if args.command == 'find':
        domains = fetch_domains(args.excel, args.filter, args.domain_column)
        if not domains:
            print('No domains found')
            return
        prs = fetch_dont_merged_prs()
        fprs = find_domains_prs(domains, prs)
    else:
        prs = fetch_dont_merged_prs()

        def filter_prs(pr):
            return is_only_add_ie_pr(pr) and not has_pr_extractor(pr)
        fprs = find_prs(filter_prs, prs)

    if fprs:
        print(json.dumps(fprs, indent=4))
        print('count:', len(fprs))
    else:
        print('PRs Empty')


if __name__ == '__main__':
    main()
