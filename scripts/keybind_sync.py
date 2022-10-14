#!/usr/bin/env python


import os
import re
import subprocess
from collections import deque
from pprint import pprint as pp

FILEPATH = os.path.abspath(
    os.path.join(os.path.realpath(__file__), os.pardir, os.pardir)
)
FILE = "config.ron"
NUM_BACKUPS = 5
BACKUPS_DIR = os.path.join(FILEPATH, "config_backups")
SYNC_SECTIONS = ["keybind", "tags", "window_rules"]


def get_current_config_file() -> str:
    command1 = ["/usr/bin/ls", "-l", os.path.join(FILEPATH, FILE)]
    command2 = ["awk", "{print $11}"]
    res = get_output_from_piped_command(command1, command2)
    if len(res) == 1:
        return res[0]
    else:
        raise RuntimeError(
            "Unable to get current config, check stdout warning messages"
        )


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


def load_configs() -> dict:
    all_configs = {}
    all_config_files = get_config_file_names()
    for config_file in all_config_files:
        config = load_config_file(config_file)
        all_configs[config_file] = config
    return all_configs


def extract_section_from_current(config_dict: dict, current: str, section: str) -> list:
    data = []
    for config_name, config in config_dict.items():
        if config_name in current:
            start_idx = find_start_idx(config, section)
            end_idx = find_end_idx(config, start_idx)
            for i in range(start_idx, end_idx):
                data.append(config[i])
    return data


def update_section_to_other_configs(
    config_dict: dict, data: list, current: str, section: str
):
    for config_name, config in config_dict.items():
        if config_name not in current:
            start_idx = find_start_idx(config, section)
            end_idx = find_end_idx(config, start_idx)
            new_config = []
            for i in range(0, start_idx):
                new_config.append(config[i])
            for item in data:
                new_config.append(item)
            for i in range(end_idx, len(config)):
                new_config.append(config[i])
            config_dict[config_name] = new_config


def find_start_idx(config: list, section: str) -> int:
    for idx, line in enumerate(config):
        if section in line:
            return idx + 1  # start on next line


def find_end_idx(config: list, idx: int):
    while True:
        idx += 1
        if re.fullmatch(r"^\s+],\n$", config[idx]):
            return idx


def validate_configs(config_dict: dict, current: str) -> tuple:
    valid = False
    errors = []
    current_config = load_config_file(current)
    for section in SYNC_SECTIONS:
        for config_name, config in config_dict.items():
            if config_name not in current:
                current_config_idx = find_start_idx(current_config, section)
                end_config_idx = find_end_idx(current_config, current_config_idx)
                to_validate_config_idx = find_start_idx(config, section)
                while current_config_idx < end_config_idx:
                    if current_config[current_config_idx] != config[to_validate_config_idx]:
                        errors.append(
                            {
                                "line": to_validate_config_idx,
                                "config": config_name,
                            }
                        )
                        break
                    current_config_idx += 1
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


def create_backups_dir():
    if not os.path.exists(BACKUPS_DIR):
        os.mkdir(BACKUPS_DIR)


def backup_old_configs(config_dict: list, current: str) -> bool:
    success = False
    create_backups_dir()
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
            success = True
            if not success:
                break
    return success


def write_new_configs(config_dict: dict, current: str):
    print("Writing new configs")
    for config_name, config in config_dict.items():
        file_name = os.path.join(FILEPATH, config_name)
        print(f"New config file: {file_name}")
        if config_name not in current:
            with open(file_name, "w") as file:
                file.write("".join(config))


if __name__ == "__main__":
    current_config_file_name = get_current_config_file()
    config_dict = load_configs()
    if backup_old_configs(config_dict, current_config_file_name):
        print("Backup successful")
        for section in SYNC_SECTIONS:
            data = extract_section_from_current(
                config_dict, current_config_file_name, section
            )
            update_section_to_other_configs(
                config_dict, data, current_config_file_name, section
            )
        (valid, errors) = validate_configs(
            config_dict, current_config_file_name
        )
        if valid:
            write_new_configs(config_dict, current_config_file_name)
        else:
            pp(f"errors: {errors}")
