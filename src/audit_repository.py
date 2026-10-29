"""Read-only GitHub candidate audit: secrets, size, links and protected paths."""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from inspect_data import ROOT


def git(*args, input_text=None):
    # A command-scoped trust exception for this explicit checkout only; never
    # writes global safe.directory configuration or trusts other repositories.
    run = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', *args],
                         cwd=ROOT, input=input_text, capture_output=True, text=True,
                         encoding='utf-8', check=True)
    return run.stdout


def main():
    names = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0')
    names = sorted(set(n for n in names if n))
    oversized, suspicious, broken = [], [], []
    patterns = {
        'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'github_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
        'aws_access_key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
        'credential_url': re.compile(r'(?i)(?:mysql|mariadb|postgres(?:ql)?)://[^\s:/]+:[^\s@]+@'),
        'literal_secret': re.compile(r'''(?i)\b(?:password|passwd|api_key|client_secret|access_token)\s*[:=]\s*["']([^\n"']{8,})["']'''),
    }
    text_extensions = {'.py', '.md', '.sql', '.json', '.pq', '.dax', '.txt', '.yml', '.yaml', '.toml', '.csv'}
    for name in names:
        path = ROOT/name
        if not path.is_file():
            continue
        if path.stat().st_size > 50_000_000:
            oversized.append(name)
        if path.suffix.lower() not in text_extensions and path.name != '.gitignore':
            continue
        content = path.read_text(encoding='utf-8-sig')
        for label, pattern in patterns.items():
            for match in pattern.finditer(content):
                if label == 'literal_secret' and any(s in match.group(1).upper() for s in ['YOUR_', 'EXAMPLE', 'PLACEHOLDER']):
                    continue
                suspicious.append({'file': name, 'pattern': label, 'line': content[:match.start()].count('\n')+1})
        if path.suffix.lower() == '.md':
            markdown = re.sub(r'```[\s\S]*?```|`[^`\n]*`', '', content)
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', markdown):
                target = target.strip('<>').split('#', 1)[0]
                if not target or re.match(r'^[a-zA-Z]+://', target) or target.startswith('mailto:'):
                    continue
                if not (path.parent/unquote(target)).exists():
                    broken.append({'file': name, 'target': target})
    protected = ['.venv/Scripts/python.exe', '.env', '.env.local', 'credentials.json',
                 'secrets.json', 'private.key', '.aws/credentials',
                 'data/raw/Online Retail.xlsx', 'online+retail/Online Retail.xlsx',
                 'data/processed/cleaning_example/completed_sales.csv',
                 'reports/analysis_example/sql_import.tsv', 'reports/analysis_example/customer_purchases.csv',
                 'dashboard/powerbi_example/data/FactSales.csv', 'dashboard/powerbi_example/power_query/pDataFolder.pq']
    ignored = set(git('check-ignore', '--stdin', '-z', input_text='\0'.join(protected)+'\0').split('\0'))
    unprotected = sorted(set(protected)-ignored)
    remotes = git('remote').splitlines()
    credential_files = []
    for folder, subfolders, files in os.walk(ROOT):
        subfolders[:] = [n for n in subfolders if n not in {'.git', '.venv', 'venv', '__pycache__'}]
        for name in files:
            if name == '.env.example':
                continue
            if re.fullmatch(r'(?:\.env(?:\..+)?|credentials(?:\..+)?|secrets(?:\..+)?|.*\.(?:pem|key|pfx|p12))', name, re.I):
                credential_files.append((Path(folder)/name).relative_to(ROOT).as_posix())
    result = {'generated_utc': datetime.now(timezone.utc).isoformat(),
              'candidate_file_count': len(names), 'candidate_bytes': sum((ROOT/n).stat().st_size for n in names if (ROOT/n).is_file()),
              'secret_pattern_hits': suspicious, 'files_over_50MB': oversized,
              'broken_local_markdown_links': broken, 'unprotected_paths': unprotected,
              'git_remotes': remotes,
              'credential_named_files_found': credential_files,
              'scope': 'Git candidate text files; common secret patterns only. Raw binaries, ignored local files and historical Git objects are not comprehensively secret-scanned. No history exists yet.',
              'ownership_note': 'Audit uses a command-scoped safe.directory for this exact checkout; no global trust settings are changed.'}
    out = ROOT/'reports/repository_audit.json'
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if suspicious or oversized or broken or unprotected or credential_files:
        raise SystemExit('Audit requires review: see reports/repository_audit.json')


if __name__ == '__main__':
    main()
