#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
'''
# ---------------------#
# EZNV BACKUP RESTORE  #
# -------------------- #

Downloads backup information generated by `eznv_backup.sh` script gist and
re-installs packages/apps/etc based on contents of "*.install" files saved in
that gist.

ARGS:       gist_id (string) - ID of gist to get
   

INSTALLER CONFIG
----------------
You can add more installer configurations to this script to handle installing
from more "*.install" files. Installer configs for the "*.install" files in the
gist are set up in the `restore_installers.json` file in this script's dir in
the following way:

  {
      "[* in *.install file]": {
           "sh_item_command": "[command to run with '{item}' in format string]"
       },
       ...
  }
'''

__author__ = "Arjun Ray"
__email__ = "deconstructionalism@gmail.com"
__license__ = "GNU GPLv3"
__maintainer__ = "Arjun Ray"
__status__ = "Development"
__version__ = "0.0.1"

import crayons
import json
import requests
import sys
from subprocess import Popen, PIPE

# colored print functions
p_err = lambda x: print(crayons.red(x))
p_suc = lambda x: print(crayons.green(x))
p_war = lambda x: print(crayons.yellow(x))
p_bol = lambda x: print(crayons.white(x, bold=True))

def get_gist(gist_id):
    ''' 
    Get gist files a given gist.

    ARGS:       gist_id (string) - ID of gist to get
    RETURNS:    files (dict) - files in gist of format 
                               {[file name]: [file contents]}
    '''

    gist_url = f'https://api.github.com/gists/{gist_id}'

    r = requests.get(gist_url)
    if not r.status_code == 200:
        p_err(f'REQUEST TO {gist_url} FAILED WITH HTTP CODE {r.status_code}!')
        sys.exit(1)

    res = json.loads(r.text)
    files = {k: v['content'] for k, v in res['files'].items()}
    return files


def load_installers(json_file_name='restore_installers.json'):
    try:
        with open(json_file_name, 'r') as f:
            installers = json.load(f)
        return installers
    except IOError:
        p_err(f'ERROR: NO INSTALLER CONFIG FILE "{json_file_name}" found in script directory!')
        sys.exit(1)


def run_installers(files, installers):
    '''
    Run installers for each "*.install" file in gist given the config
    specified in `installers` dict.

    ARGS:  files (dict)      - files dict returned from `get_gist`
           installers (dict) - installer config dict set up as specified in 
                               "INSTALLER CONFIG: section of main script doc.
    '''

    install_file_names = [k for k, v in files.items() if k.endswith('.install')]
    file_to_list = lambda x:  list(filter(None, x.split('\n')))

    for f in install_file_names:
        key = f.rstrip('.install')
        try:
            config = installers[key]
        except KeyError:
            p_war(f'WARNING: INSTALL CONFIG FOR "{f}" NOT IN THIS SCRIPT!\n')
            continue

        install_list = file_to_list(files[f])
        
        if 'sh_item_command' in config:
            p_bol(f'RUNNING INSTALL FOR "{f}" \n{ "-" * 80 }')
            for item in install_list:
                cmd = config['sh_item_command'].format(item=item)
                run_sh_command(cmd)
        else:
            p_war(f'WARNING: NO INSTALL COMMAND FOR "{f}" IN INSTALL CONFIG IN THIS SCRIPT!\n')


def run_sh_command(command):
    '''
    Run shell command, color print output.

    ARGS:   command (string or list) - shell command string or shell command
                                       split on spaces into list
    '''

    cmd_list = command if isinstance(command, list) else command.split(' ')

    proc = Popen(cmd_list, stdout=PIPE, stderr=PIPE)

    result = proc.communicate()
    output, error = map(lambda x: x.decode(), result)
    if output: p_suc(output)
    if error and 'error' in error.lower():
        p_err(f'ERROR:\n{error}')
    elif error:
            p_war(f'WARNING:\n {error}')


def main(gist_id):
    '''
    Get install backup from gist and install from them locally.

    ARGS:       gist_id (string) - ID of gist to get
    '''

    files = get_gist(gist_id)

    installers = load_installers()
    run_installers(files, installers)


if __name__ == '__main__':

    # clear screen
    print('\033[H\033[J')

    try:
        gist_id = sys.argv[1]
    except: 
        p_err('ERROR: YOU MUST PASS A GIST ID FOR A "system_backup.sh" GENERATED GIST AS FIRST ARGUMENT!')
        sys.exit(0)

    main(gist_id)