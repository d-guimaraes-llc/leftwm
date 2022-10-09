#!/usr/bin/env python

import subprocess
import os
import re
from collections import deque
from pprint import pprint as pp


FILEPATH = "/home/danielg/.config/leftwm"
FILE = "config.ron"
NUM_BACKUPS = 5
BACKUPS_DIR = os.path.join(FILEPATH, "config_backups")


def get_current_config_file() -> str:
    command1 = ["/usr/bin/ls", "-l", os.path.join(FILEPATH, FILE)]
    command2 = ["awk", "{print $11}"]
    res = get_output_from_piped_command(command1, command2)
    if len(res) == 1:
        return res[0]
    else:
        raise RuntimeError("Unable to get current config, check stdout warning messages")


def get_config_file_names() -> list:
    config_files = []
    files = os.listdir(FILEPATH)
    for file in files:
        if re.search(r"^config\..*\.ron$", file):
            config_files.append(file)
    return config_files


def load_config_file(file_name: str) -> str:
    if FILEPATH not in file_name:
        file_name = f"{FILEPATH}/{file_name}"
    with open(file_name) as file:
        return file.readlines()


def load_configs(all_config_files: list) -> dict:
    all_configs = {}
    for config_file in all_config_files:
        config = load_config_file(config_file)
        all_configs[config_file] = config
    return all_configs


def extract_keybinds_from_current(config_dict: dict, current: str) -> list:
    keybinds = []
    for config_name, config in config_dict.items():
        if config_name in current:
            extract = False
            for line in config:
                if extract:
                    keybinds.append(line)
                elif "keybind" in line:
                    extract = True
    return keybinds


def update_keybinds_to_other_configs(config_dict: dict, keybinds: list, current: str):
    for config_name, config in config_dict.items():
        if config_name not in current:
            overwrite = False
            new_config = []
            for line in config:
                if overwrite:
                    config_dict[config_name] = new_config + keybinds
                    break  # inner for, continue outer for
                elif "keybind" in line:
                    overwrite = True
                new_config.append(line)


def find_keybind_idx(config: list) -> int:
    for idx, line in enumerate(config):
        if "keybind" in line:
            return idx


def validate_configs(config_dict: dict, current: str) -> tuple:
    valid = False
    errors = []
    current_config = load_config_file(current)
    for config_name, config in config_dict.items():
        if config_name not in current:
            current_keybind_idx = find_keybind_idx(current_config)
            to_validate_config_idx = find_keybind_idx(config)
            while current_keybind_idx < len(current_config):
                if current_config[current_keybind_idx] != config[to_validate_config_idx]:
                    errors.append({
                        "line": to_validate_config_idx,
                        "config": config_name,
                    })
                    break
                current_keybind_idx += 1
                to_validate_config_idx += 1
    if len(errors) == 0:
        valid = True
    return (valid, errors)


def get_output_from_piped_command(c1: list, c2: list) -> list:
    try:
        p1 = subprocess.Popen(c1, stdout=subprocess.PIPE)
        p2 = subprocess.check_output(c2, stdin=p1.stdout)
        return p2.decode("utf-8").strip().split("\n")
    except subprocess.CalledProcessError as e:
        pp(f"WARNING: {e}")
        return []


def delete_oldest_backup(backups: deque):
    # The oldest file will be first
    backup = backups.popleft()
    os.remove(os.path.join(BACKUPS_DIR, backup.split(" ")[-1]))


def backup_old_configs(config_dict: list, current: str) -> bool:
    success = False
    for config_name, config in config_dict.items():
        if config_name not in current:
            command1 = ["ls", "-ltr", BACKUPS_DIR]
            command2 = ["grep", config_name]
            backups = deque(get_output_from_piped_command(command1, command2))
            while len(backups) > NUM_BACKUPS:
                delete_oldest_backup(backups)
            p_date = subprocess.check_output(["date", "+%Y%m%d%H%M%S"])
            date = p_date.decode("utf-8").strip()
            filename = f"{date}_{config_name}"
            with open(os.path.join(BACKUPS_DIR, filename), "w") as file:
                file.writelines(config)
    return success


def write_new_configs(config_dict: dict, current: str):
    for config_name, config in config_dict.items():
        if config_name not in current:
            with open(os.path.join(FILEPATH, config_name), "w") as file:
                file.writelines(config)


if __name__ == "__main__":
    current_config_file = get_current_config_file()
    all_config_files = get_config_file_names()
    config_dict = load_configs(all_config_files)
    keybinds = extract_keybinds_from_current(config_dict, current_config_file)
    backup_old_configs(config_dict, current_config_file)
    update_keybinds_to_other_configs(config_dict, keybinds, current_config_file)
    (valid, errors) = validate_configs(config_dict, current_config_file)
    if valid:
        write_new_configs(config_dict, current_config_file)
    else:
        pp(f"errors: {errors}")
