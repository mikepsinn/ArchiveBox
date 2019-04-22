__package__ = 'archivebox.legacy'

import os
import re
import sys
import django
import getpass
import shutil

from typing import Optional
from subprocess import run, PIPE, DEVNULL

# ******************************************************************************
# Documentation: https://github.com/pirate/ArchiveBox/wiki/Configuration
# Use the 'env' command to pass config options to ArchiveBox.  e.g.:
#     env USE_COLOR=True CHROME_BINARY=chromium archivebox add < example.html
# ******************************************************************************

IS_TTY =                 sys.stdout.isatty()
USE_COLOR =              os.getenv('USE_COLOR',              str(IS_TTY)        ).lower() == 'true'
SHOW_PROGRESS =          os.getenv('SHOW_PROGRESS',          str(IS_TTY)        ).lower() == 'true'

OUTPUT_DIR =             os.getenv('OUTPUT_DIR',             '')
ONLY_NEW =               os.getenv('ONLY_NEW',               'False'            ).lower() == 'true'
TIMEOUT =                int(os.getenv('TIMEOUT',            '60'))
MEDIA_TIMEOUT =          int(os.getenv('MEDIA_TIMEOUT',      '3600'))
OUTPUT_PERMISSIONS =     os.getenv('OUTPUT_PERMISSIONS',     '755'              )
FOOTER_INFO =            os.getenv('FOOTER_INFO',            'Content is hosted for personal archiving purposes only.  Contact server owner for any takedown requests.',)
URL_BLACKLIST =          os.getenv('URL_BLACKLIST',          None)

FETCH_WGET =             os.getenv('FETCH_WGET',             'True'             ).lower() == 'true'
FETCH_WGET_REQUISITES =  os.getenv('FETCH_WGET_REQUISITES',  'True'             ).lower() == 'true'
FETCH_PDF =              os.getenv('FETCH_PDF',              'True'             ).lower() == 'true'
FETCH_SCREENSHOT =       os.getenv('FETCH_SCREENSHOT',       'True'             ).lower() == 'true'
FETCH_DOM =              os.getenv('FETCH_DOM',              'True'             ).lower() == 'true'
FETCH_WARC =             os.getenv('FETCH_WARC',             'True'             ).lower() == 'true'
FETCH_GIT =              os.getenv('FETCH_GIT',              'True'             ).lower() == 'true'
FETCH_MEDIA =            os.getenv('FETCH_MEDIA',            'True'             ).lower() == 'true'
FETCH_FAVICON =          os.getenv('FETCH_FAVICON',          'True'             ).lower() == 'true'
FETCH_TITLE =            os.getenv('FETCH_TITLE',            'True'             ).lower() == 'true'
SUBMIT_ARCHIVE_DOT_ORG = os.getenv('SUBMIT_ARCHIVE_DOT_ORG', 'True'             ).lower() == 'true'

CHECK_SSL_VALIDITY =     os.getenv('CHECK_SSL_VALIDITY',     'True'             ).lower() == 'true'
RESOLUTION =             os.getenv('RESOLUTION',             '1440,2000'        )
GIT_DOMAINS =            os.getenv('GIT_DOMAINS',            'github.com,bitbucket.org,gitlab.com').split(',')
WGET_USER_AGENT =        os.getenv('WGET_USER_AGENT',        'ArchiveBox/{VERSION} (+https://github.com/pirate/ArchiveBox/) wget/{WGET_VERSION}')
COOKIES_FILE =           os.getenv('COOKIES_FILE',           None)
CHROME_USER_DATA_DIR =   os.getenv('CHROME_USER_DATA_DIR',   None)
CHROME_HEADLESS =        os.getenv('CHROME_HEADLESS',        'True'             ).lower() == 'true'
CHROME_USER_AGENT =      os.getenv('CHROME_USER_AGENT',      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36')
CHROME_SANDBOX =         os.getenv('CHROME_SANDBOX',         'True'             ).lower() == 'true'

USE_CURL =               os.getenv('USE_CURL',               'True'             ).lower() == 'true'
USE_WGET =               os.getenv('USE_WGET',               'True'             ).lower() == 'true'
USE_CHROME =             os.getenv('USE_CHROME',             'True'             ).lower() == 'true'

CURL_BINARY =            os.getenv('CURL_BINARY',            'curl')
GIT_BINARY =             os.getenv('GIT_BINARY',             'git')
WGET_BINARY =            os.getenv('WGET_BINARY',            'wget')
YOUTUBEDL_BINARY =       os.getenv('YOUTUBEDL_BINARY',       'youtube-dl')
CHROME_BINARY =          os.getenv('CHROME_BINARY',          None)

# ******************************************************************************

### Terminal Configuration
TERM_WIDTH = lambda: shutil.get_terminal_size((100, 10)).columns
ANSI = {
    'reset': '\033[00;00m',
    'lightblue': '\033[01;30m',
    'lightyellow': '\033[01;33m',
    'lightred': '\033[01;35m',
    'red': '\033[01;31m',
    'green': '\033[01;32m',
    'blue': '\033[01;34m',
    'white': '\033[01;37m',
    'black': '\033[01;30m',
}
if not USE_COLOR:
    # dont show colors if USE_COLOR is False
    ANSI = {k: '' for k in ANSI.keys()}

def stderr(*args):
    sys.stderr.write(' '.join(str(a) for a in args) + '\n')

USER = getpass.getuser() or os.getlogin()
ARCHIVEBOX_BINARY = sys.argv[0]

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
if OUTPUT_DIR:
    OUTPUT_DIR = os.path.abspath(os.path.expanduser(OUTPUT_DIR))
else:
    OUTPUT_DIR = os.path.abspath(os.curdir)

SQL_INDEX_FILENAME = 'index.sqlite3'
JSON_INDEX_FILENAME = 'index.json'
HTML_INDEX_FILENAME = 'index.html'
ARCHIVE_DIR_NAME = 'archive'
SOURCES_DIR_NAME = 'sources'
LOGS_DIR_NAME = 'logs'
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, ARCHIVE_DIR_NAME)
SOURCES_DIR = os.path.join(OUTPUT_DIR, SOURCES_DIR_NAME)
LOGS_DIR = os.path.join(OUTPUT_DIR, LOGS_DIR_NAME)

PYTHON_DIR = os.path.join(REPO_DIR, 'archivebox')
LEGACY_DIR = os.path.join(PYTHON_DIR, 'legacy')
TEMPLATES_DIR = os.path.join(LEGACY_DIR, 'templates')

if COOKIES_FILE:
    COOKIES_FILE = os.path.abspath(os.path.expanduser(COOKIES_FILE))

if CHROME_USER_DATA_DIR:
    CHROME_USER_DATA_DIR = os.path.abspath(os.path.expanduser(CHROME_USER_DATA_DIR))

URL_BLACKLIST_PTN = re.compile(URL_BLACKLIST, re.IGNORECASE) if URL_BLACKLIST else None

########################### Environment & Dependencies #########################

VERSION = open(os.path.join(REPO_DIR, 'VERSION'), 'r').read().strip()
GIT_SHA = VERSION.split('+')[-1] or 'unknown'
HAS_INVALID_DEPENDENCIES = False

### Check system environment
if USER == 'root':
    stderr('{red}[!] ArchiveBox should never be run as root!{reset}'.format(**ANSI))
    stderr('    For more information, see the security overview documentation:')
    stderr('        https://github.com/pirate/ArchiveBox/wiki/Security-Overview#do-not-run-as-root')
    raise SystemExit(1)

### Check Python environment
PYTHON_BINARY = sys.executable
PYTHON_VERSION = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
if float(PYTHON_VERSION) < 3.6:
    stderr('{}[X] Python version is not new enough: {} (>3.6 is required){}'.format(ANSI['red'], PYTHON_VERSION, ANSI['reset']))
    stderr('    See https://github.com/pirate/ArchiveBox/wiki/Troubleshooting#python for help upgrading your Python installation.')
    raise SystemExit(1)

if sys.stdout.encoding.upper() not in ('UTF-8', 'UTF8'):
    stderr('[X] Your system is running python3 scripts with a bad locale setting: {} (it should be UTF-8).'.format(sys.stdout.encoding))
    stderr('    To fix it, add the line "export PYTHONIOENCODING=UTF-8" to your ~/.bashrc file (without quotes)')
    stderr('    Or if you\'re using ubuntu/debian, run "dpkg-reconfigure locales"')
    stderr('')
    stderr('    Confirm that it\'s fixed by opening a new shell and running:')
    stderr('        python3 -c "import sys; print(sys.stdout.encoding)"   # should output UTF-8')
    stderr('')
    stderr('    Alternatively, run this script with:')
    stderr('        env PYTHONIOENCODING=UTF-8 ./archive.py export.html')
    raise SystemExit(1)

# ******************************************************************************
# ***************************** Helper Functions *******************************
# ******************************************************************************

def bin_version(binary: str) -> Optional[str]:
    """check the presence and return valid version line of a specified binary"""

    global HAS_INVALID_DEPENDENCIES
    binary = os.path.expanduser(binary)
    try:
        if not shutil.which(binary):
            raise Exception

        version_str = run([binary, "--version"], stdout=PIPE, cwd=REPO_DIR).stdout.strip().decode()
        # take first 3 columns of first line of version info
        return ' '.join(version_str.split('\n')[0].strip().split()[:3])
    except Exception:
        HAS_INVALID_DEPENDENCIES = True
        stderr('{red}[X] Unable to find working version of dependency: {}{reset}'.format(binary, **ANSI))
        stderr('    Make sure it\'s installed, then confirm it\'s working by running:')
        stderr('        {} --version'.format(binary))
        stderr()
        stderr('    If you don\'t want to install it, you can disable it via config. See here for more info:')
        stderr('        https://github.com/pirate/ArchiveBox/wiki/Install')
        stderr()
        return None


def find_chrome_binary() -> Optional[str]:
    """find any installed chrome binaries in the default locations"""
    # Precedence: Chromium, Chrome, Beta, Canary, Unstable, Dev
    # make sure data dir finding precedence order always matches binary finding order
    default_executable_paths = (
        'chromium-browser',
        'chromium',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        'google-chrome',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'google-chrome-stable',
        'google-chrome-beta',
        'google-chrome-canary',
        '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
        'google-chrome-unstable',
        'google-chrome-dev',
    )
    for name in default_executable_paths:
        full_path_exists = shutil.which(name)
        if full_path_exists:
            return name
    
    stderr('{red}[X] Unable to find a working version of Chrome/Chromium, is it installed and in your $PATH?'.format(**ANSI))
    stderr()
    return None


def find_chrome_data_dir() -> Optional[str]:
    """find any installed chrome user data directories in the default locations"""
    # Precedence: Chromium, Chrome, Beta, Canary, Unstable, Dev
    # make sure data dir finding precedence order always matches binary finding order
    default_profile_paths = (
        '~/.config/chromium',
        '~/Library/Application Support/Chromium',
        '~/AppData/Local/Chromium/User Data',
        '~/.config/google-chrome',
        '~/Library/Application Support/Google/Chrome',
        '~/AppData/Local/Google/Chrome/User Data',
        '~/.config/google-chrome-stable',
        '~/.config/google-chrome-beta',
        '~/Library/Application Support/Google/Chrome Canary',
        '~/AppData/Local/Google/Chrome SxS/User Data',
        '~/.config/google-chrome-unstable',
        '~/.config/google-chrome-dev',
    )
    for path in default_profile_paths:
        full_path = os.path.expanduser(path)
        if os.path.exists(full_path):
            return full_path
    return None


def setup_django(out_dir: str=OUTPUT_DIR, check_db=False):
    import django
    sys.path.append(PYTHON_DIR)
    os.environ.setdefault('OUTPUT_DIR', out_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

    if check_db:
        assert os.path.exists(os.path.join(out_dir, SQL_INDEX_FILENAME)), (
            f'No database file {SQL_INDEX_FILENAME} found in OUTPUT_DIR: {out_dir}')

# ******************************************************************************
# ************************ Environment & Dependencies **************************
# ******************************************************************************

try:
    ### Get Django version
    DJANGO_BINARY = django.__file__.replace('__init__.py', 'bin/django-admin.py')
    DJANGO_VERSION = '{}.{}.{} {} ({})'.format(*django.VERSION)

    ### Make sure curl is installed
    if USE_CURL:
        USE_CURL = FETCH_FAVICON or SUBMIT_ARCHIVE_DOT_ORG
    else:
        FETCH_FAVICON = SUBMIT_ARCHIVE_DOT_ORG = False
    CURL_VERSION = None
    if USE_CURL:
        CURL_VERSION = bin_version(CURL_BINARY)

    ### Make sure wget is installed and calculate version
    if USE_WGET:
        USE_WGET = FETCH_WGET or FETCH_WARC
    else:
        FETCH_WGET = FETCH_WARC = False
    WGET_VERSION = None
    WGET_AUTO_COMPRESSION = False
    if USE_WGET:
        WGET_VERSION = bin_version(WGET_BINARY)
        WGET_AUTO_COMPRESSION = not run([WGET_BINARY, "--compression=auto", "--help"], stdout=DEVNULL, stderr=DEVNULL).returncode
        
    WGET_USER_AGENT = WGET_USER_AGENT.format(
        VERSION=VERSION,
        WGET_VERSION=WGET_VERSION or '',
    )

    ### Make sure git is installed
    GIT_VERSION = None
    if FETCH_GIT:
        GIT_VERSION = bin_version(GIT_BINARY)

    ### Make sure youtube-dl is installed
    YOUTUBEDL_VERSION = None
    if FETCH_MEDIA:
        YOUTUBEDL_VERSION = bin_version(YOUTUBEDL_BINARY)

    ### Make sure chrome is installed and calculate version
    if USE_CHROME:
        USE_CHROME = FETCH_PDF or FETCH_SCREENSHOT or FETCH_DOM
    else:
        FETCH_PDF = FETCH_SCREENSHOT = FETCH_DOM = False
    
    if not CHROME_BINARY:
        CHROME_BINARY = find_chrome_binary() or 'chromium-browser'
    CHROME_VERSION = None

    if USE_CHROME:
        if CHROME_BINARY:
            CHROME_VERSION = bin_version(CHROME_BINARY)
            # stderr('[i] Using Chrome binary: {}'.format(shutil.which(CHROME_BINARY) or CHROME_BINARY))

            if CHROME_USER_DATA_DIR is None:
                CHROME_USER_DATA_DIR = find_chrome_data_dir()
            elif CHROME_USER_DATA_DIR == '':
                CHROME_USER_DATA_DIR = None
            else:
                if not os.path.exists(os.path.join(CHROME_USER_DATA_DIR, 'Default')):
                    stderr('{red}[X] Could not find profile "Default" in CHROME_USER_DATA_DIR:{reset} {}'.format(CHROME_USER_DATA_DIR, **ANSI))
                    stderr('    Make sure you set it to a Chrome user data directory containing a Default profile folder.')
                    stderr('    For more info see:')
                    stderr('        https://github.com/pirate/ArchiveBox/wiki/Configuration#CHROME_USER_DATA_DIR')
                    if 'Default' in CHROME_USER_DATA_DIR:
                        stderr()
                        stderr('    Try removing /Default from the end e.g.:')
                        stderr('        CHROME_USER_DATA_DIR="{}"'.format(CHROME_USER_DATA_DIR.split('/Default')[0]))
                    raise SystemExit(1)
            # stderr('[i] Using Chrome data dir: {}'.format(os.path.abspath(CHROME_USER_DATA_DIR)))


    ### Summary Lookup Dicts
    FOLDERS = {
        'REPO_DIR': {
            'path': os.path.abspath(REPO_DIR),
            'enabled': True,
            'is_valid': os.path.exists(os.path.join(REPO_DIR, '.github')),
        },
        'PYTHON_DIR': {
            'path': os.path.abspath(PYTHON_DIR),
            'enabled': True,
            'is_valid': os.path.exists(os.path.join(PYTHON_DIR, '__main__.py')),
        },
        'LEGACY_DIR': {
            'path': os.path.abspath(LEGACY_DIR),
            'enabled': True,
            'is_valid': os.path.exists(os.path.join(LEGACY_DIR, 'util.py')),
        },
        'TEMPLATES_DIR': {
            'path': os.path.abspath(TEMPLATES_DIR),
            'enabled': True,
            'is_valid': os.path.exists(os.path.join(TEMPLATES_DIR, 'static')),
        },
        'OUTPUT_DIR': {
            'path': os.path.abspath(OUTPUT_DIR),
            'enabled': True,
            'is_valid': os.path.exists(os.path.join(OUTPUT_DIR, 'index.json')),
        },
        'SOURCES_DIR': {
            'path': os.path.abspath(SOURCES_DIR),
            'enabled': True,
            'is_valid': os.path.exists(SOURCES_DIR),
        },
        'LOGS_DIR': {
            'path': os.path.abspath(LOGS_DIR),
            'enabled': True,
            'is_valid': os.path.exists(LOGS_DIR),
        },
        'ARCHIVE_DIR': {
            'path': os.path.abspath(ARCHIVE_DIR),
            'enabled': True,
            'is_valid': os.path.exists(ARCHIVE_DIR),
        },
        'CHROME_USER_DATA_DIR': {
            'path': CHROME_USER_DATA_DIR and os.path.abspath(CHROME_USER_DATA_DIR),
            'enabled': USE_CHROME and CHROME_USER_DATA_DIR,
            'is_valid': os.path.exists(os.path.join(CHROME_USER_DATA_DIR, 'Default')) if CHROME_USER_DATA_DIR else False,
        },
        'COOKIES_FILE': {
            'path': COOKIES_FILE and os.path.abspath(COOKIES_FILE),
            'enabled': USE_WGET and COOKIES_FILE,
            'is_valid': COOKIES_FILE and os.path.exists(COOKIES_FILE),
        },
    }

    DEPENDENCIES = {
        'PYTHON_BINARY': {
            'path': PYTHON_BINARY,
            'version': PYTHON_VERSION,
            'enabled': True,
            'is_valid': bool(DJANGO_VERSION),
        },
        'DJANGO_BINARY': {
            'path': DJANGO_BINARY,
            'version': DJANGO_VERSION,
            'enabled': True,
            'is_valid': bool(DJANGO_VERSION),
        },
        'CURL_BINARY': {
            'path': CURL_BINARY and shutil.which(CURL_BINARY),
            'version': CURL_VERSION,
            'enabled': USE_CURL,
            'is_valid': bool(CURL_VERSION),
        },
        'WGET_BINARY': {
            'path': WGET_BINARY and shutil.which(WGET_BINARY),
            'version': WGET_VERSION,
            'enabled': USE_WGET,
            'is_valid': bool(WGET_VERSION),
        },
        'GIT_BINARY': {
            'path': GIT_BINARY and shutil.which(GIT_BINARY),
            'version': GIT_VERSION,
            'enabled': FETCH_GIT,
            'is_valid': bool(GIT_VERSION),
        },
        'YOUTUBEDL_BINARY': {
            'path': YOUTUBEDL_BINARY and shutil.which(YOUTUBEDL_BINARY),
            'version': YOUTUBEDL_VERSION,
            'enabled': FETCH_MEDIA,
            'is_valid': bool(YOUTUBEDL_VERSION),
        },
        'CHROME_BINARY': {
            'path': CHROME_BINARY and shutil.which(CHROME_BINARY),
            'version': CHROME_VERSION,
            'enabled': USE_CHROME,
            'is_valid': bool(CHROME_VERSION),
        },
    }

    CHROME_OPTIONS = {
        'TIMEOUT': TIMEOUT,
        'RESOLUTION': RESOLUTION,
        'CHECK_SSL_VALIDITY': CHECK_SSL_VALIDITY,
        'CHROME_BINARY': CHROME_BINARY,
        'CHROME_HEADLESS': CHROME_HEADLESS,
        'CHROME_SANDBOX': CHROME_SANDBOX,
        'CHROME_USER_AGENT': CHROME_USER_AGENT,
        'CHROME_USER_DATA_DIR': CHROME_USER_DATA_DIR,
    }

    # PYPPETEER_ARGS = {
    #     'headless': CHROME_HEADLESS,
    #     'ignoreHTTPSErrors': not CHECK_SSL_VALIDITY,
    #     # 'executablePath': CHROME_BINARY,
    # }
    
except KeyboardInterrupt:
    raise SystemExit(1)

except Exception as e:
    stderr()
    stderr('{red}[X] Error during configuration: {} {}{reset}'.format(e.__class__.__name__, e, **ANSI))
    stderr('    Your archive data is unaffected.')
    stderr('    Check your config or environemnt variables for mistakes and try again.')
    stderr('    For more info see:')
    stderr('        https://github.com/pirate/ArchiveBox/wiki/Configuration')
    stderr()
    raise


def check_dependencies() -> None:
    if HAS_INVALID_DEPENDENCIES:
        stderr('{red}[X] Missing some required dependencies.{reset}'.format(**ANSI))
        raise SystemExit(1)
        
def check_data_folder() -> None:
    if not os.path.exists(os.path.join(OUTPUT_DIR, 'index.json')):
        stderr('{red}[X] No archive data was found in:{reset} {}'.format(OUTPUT_DIR, **ANSI))
        stderr('    Are you running archivebox in the right folder?')
        stderr('        cd path/to/your/archive/folder')
        stderr('        archivebox [command]')
        stderr()
        stderr('    To create a new archive collection in this folder, run:')
        stderr('        archivebox init')
        raise SystemExit(1)