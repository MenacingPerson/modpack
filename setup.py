#!/usr/bin/env python


"""
Main pack creation tool for the modpack.
Use the stuff in ./scripts/ instead of this.
$1 = config directory
Refer to config.json for configuration info.
"""

import glob
import shutil
import sys
import os
import core.base
import core.packwiz
import core.pack_editions
from core.base import (echo, ODIR, runcmd, toml_read,
                       toml_write, json_read, json_write,
                       config, base_conf, chodir)
from core.pack_editions import run_in, run_separately_in_all

os.chdir(ODIR)

# logic (functions)


def modify_packtoml(pack: dict):
    """Modify the pack.toml to contain modpack branding"""
    echo(f'Modifying pack.toml file for {pack["edition"]}')
    pack_toml = toml_read('./pack.toml')
    pack_toml['name'] = base_conf['pack_name']
    pack_toml['author'] = base_conf['pack_author']
    pack_toml['version'] = pack['fullver']
    toml_write(pack_toml, './pack.toml')


def copy_over(_pack: dict, src_name: str, dest_name: str):
    """Copy over folder from config to pack edition"""
    shutil.copytree(f'{ODIR}/conf/{sys.argv[1]}/{src_name}', f'./{dest_name}', dirs_exist_ok=True)


def mark_mods_optional(pack: dict, optional_mods_key: str):
    """Mark mods as optional in pack edition"""
    echo(f'Marking optional mods using {optional_mods_key} for {pack["edition"]}')
    for mod in config[optional_mods_key]:
        print(f'Marked {mod} as optional')
        mod_toml = toml_read(f'mods/{mod}.pw.toml')
        mod_toml['option'] = {
            'optional': True
        }
        toml_write(mod_toml, f'mods/{mod}.pw.toml')


def cp_pwignore(pack: dict):
    """Copy pwignore to the edition"""
    with open(f'{ODIR}/conf/demo/.packwizignore', 'r') as file:
        with open('./.packwizignore', 'a') as pwign:
            pwign.write('\n' + file.read())


def fix_mmc_config(pack: dict):
    """Fix Main Menu Credit json file to include branding"""
    echo(f'Fixing Main Menu Credits config for {pack["edition"]}')
    mmc_conf_json = json_read('./config/isxander-main-menu-credits.json')
    mmc_conf_json = {
        'main_menu': {
            'bottom_left': [
                {
                    'text': f'{base_conf["pack_name"]} {base_conf["pack_version"]}',
                    'clickEvent': {
                        'action': 'open_url',
                        'value': base_conf['pack_url']
                    }
                }
            ]
        }
    }
    json_write(mmc_conf_json, './config/isxander-main-menu-credits.json')


def change_modloader_ver(pack: dict) -> None:
    """Change version of specified modloader"""
    modloader = pack['modloader']
    if core.pack_editions.loader_is_valid(modloader):
        echo(f"Updating {modloader} to {base_conf['modloaders'][modloader]['version']} for {pack['edition']}")
        pack_toml = toml_read('./pack.toml')
        pack_toml['versions'][modloader] = base_conf['modloaders'][modloader]['version']
        toml_write(pack_toml, './pack.toml')
    else:
        print(f'{i} is not a valid modloader!')
        exit(1)


def forge_additive_fixer(pack: dict) -> None:
    """Clean up forge edition"""
    echo(f'Cleaning up extra files for {pack["edition"]}')
    for folder in glob.glob('mods_*'):
        shutil.rmtree(folder)


# Reset to certain hash to avoid unwanted changes
echo('Updating Additive to specified hash')
runcmd('git submodule update --recursive --init --remote')
os.chdir(f'{ODIR}/forgified-Additive/')
runcmd('git pull origin main')
runcmd('git reset --hard', base_conf["forgified-Additive_hash"])
os.chdir(f'{ODIR}/Additive/')
runcmd('git pull origin main')
runcmd('git reset --hard', base_conf["Additive_hash"])
core.base.if_exists_rm(f'{ODIR}/forgified-Additive/Modified')
core.base.if_exists_rm(f'{ODIR}/forgified-Additive/packs')
core.base.if_exists_rm(f'{ODIR}/Additive/Modified')
core.base.if_exists_rm(f'{ODIR}/Additive/packs')
os.chdir(ODIR)
runcmd('git add Additive/ forgified-Additive/')

# Recreate modified pack
echo("Removing previous modified packs")
core.base.if_exists_rm(f'{ODIR}/Modified')
core.base.if_not_exists_create_dir(f'{ODIR}/packs')


for loader in config['modloaders']:
    if not core.pack_editions.loader_is_valid(loader):
        print("Invalid loader in conf, exiting!")
        exit(1)
    os.makedirs(f'{ODIR}/Modified/versions/{loader}')
    chodir()
    for i in os.listdir(f'{ODIR}/{core.packwiz.modloaders[loader]["additive_version"]}/versions/{loader}'):
        if i == config['game_version']:
            shutil.copytree(f'{ODIR}/{core.packwiz.modloaders[loader]["additive_version"]}/versions/{loader}/{i}', f'{loader}/{i}')

run_in('all', cp_pwignore)

run_in('all', core.packwiz.pw_refresh)

run_separately_in_all(copy_over, 'mods_[ml]', 'mods')

run_separately_in_all(copy_over, 'resourcepacks_[ml]', 'resourcepacks')

run_separately_in_all(copy_over, 'shaderpacks_[ml]', 'shaderpacks')

run_separately_in_all(copy_over, 'config_[ml]', 'config')

run_separately_in_all(mark_mods_optional, 'mods_optional_[ml]')

run_separately_in_all(core.packwiz.pw_rm_mods, 'mods_removed_[ml]')

run_in('all', modify_packtoml)

run_in('all', fix_mmc_config)

for i in core.packwiz.modloaders:
    run_in(i, change_modloader_ver)

run_in('forge', forge_additive_fixer)

run_in('all', core.packwiz.pw_refresh)

run_in('all', core.packwiz.pw_export_pack)

echo('Packed files located in packs folder:')
print('  '.join(os.listdir(f'{ODIR}/packs')))
