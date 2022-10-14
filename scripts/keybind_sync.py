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
    """This gets the symlink config.ron and determines the file it is pointing at

    Raises:
        RuntimeError: This raises when the command is uable to determine a result
        Maybe there is not symlink?

    Returns:
        str: _description_
    """
    command1 = ["/usr/bin/ls", "-l", os.path.join(FILEPATH, FILE)]
    command2 = ["awk", "{print $11}"]
    res = get_output_from_piped_command(command1, command2)
    if len(res) == 1:
        return res[0]
    else:
        raise RuntimeError(
            "Unable to get current config, check stdout warning messages.\n"
            "Do you have a config.ron symlink?"
        )


def get_config_file_names() -> list:
    """This function finds all of the configs.  Configs have the following name convention:
    config.*.ron

    Returns:
        list: A list of the config files found
    """
    config_files = []
    files = os.listdir(FILEPATH)
    for file in files:
        if re.search(r"^config\..*\.ron$", file):
            config_files.append(file)
    return config_files


def load_config_file(file_name: str) -> list:
    """This loads a config file into a list

    Args:
        file_name (str): The file to load

    Returns:
        list: a list of the lines of the file
    """
    if FILEPATH not in file_name:
        file_name = f"{FILEPATH}/{file_name}"
    with open(file_name) as file:
        return file.readlines()


def load_configs() -> dict:
    """This loads each of the configs into a dict with the filename as the key

    Returns:
        dict: The contents of the config files with their filename as a key
    """
    all_configs = {}
    all_config_files = get_config_file_names()
    for config_file in all_config_files:
        config = load_config_file(config_file)
        all_configs[config_file] = config
    return all_configs


def extract_section_from_current(config_dict: dict, current: str, section: str) -> list:
    """This extracts the contents of a specific section from the currently active (symlinked)
    config

    Args:
        config_dict (dict): A dict of each config file
        current (str): The fqdn of the current file
        section (str): The section name i.e. keybind ...

    Returns:
        list: This is the contents of the section as a list of strings
    """
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
    """This will write the extracted section to each of the inactive configs

    Args:
        config_dict (dict): A dict of each config, the filename is the key
        data (list): The section that was extracted from the active confing
        current (str): the fqdn of the active config
        section (str): The section header, i.e. keybind, ...
    """
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
    """This finds the start index of the section.  It is the line after the section header

    Args:
        config (list): The config to search
        section (str): The header we are looking for

    Returns:
        int: _description_
    """
    for idx, line in enumerate(config):
        if re.fullmatch(rf"\s+{section}: \[\n$", line):
            return idx + 1  # start on next line


def find_end_idx(config: list, idx: int):
    """This finds the ending sequence of the current section

    Args:
        config (list): The config to search
        idx (int): The index to start looking from

    Returns:
        _type_: _description_
    """
    while True:
        idx += 1
        if re.fullmatch(r"^\s+],\n$", config[idx]):
            return idx


def validate_section(
    current_config: dict, config: dict, config_name: str, section: str, current: str
) -> dict:
    """This function validates an actual section in the main config vs the updated config

    Args:
        current_config (dict): The currently active config
        config (dict): The updated inactive config
        config_name (str): The file name of the inactgi
        section (str): The section to validate
        current (str): The file name of the current config

    Returns:
        dict: A dict of errors in the copy
    """
    errors = []
    current_config_idx = find_start_idx(current_config, section)
    end_config_idx = find_end_idx(current_config, current_config_idx)
    to_validate_config_idx = find_start_idx(config, section)
    while current_config_idx < end_config_idx:
        if current_config[current_config_idx] != config[to_validate_config_idx]:
            errors.append(
                {
                    "config-current": current,
                    "config-to-validate": config_name,
                    "value-current": current_config[current_config_idx],
                    "value-to-validate": config[to_validate_config_idx],
                }
            )
            break
        current_config_idx += 1
        to_validate_config_idx += 1
    return errors


def validate_configs(config_dict: dict, current: str) -> tuple:
    """This function validates each updated section in the inactive configs

    Args:
        config_dict (dict): This is the main data source with all the configs
        current (str): The filename of the currently active config

    Returns:
        tuple: A tuple with bool (valid, not valid), and a dict of errors
    """
    valid = False
    errors = []
    current_config = load_config_file(current)
    for section in SYNC_SECTIONS:
        for config_name, config in config_dict.items():
            if config_name not in current:
                errors += validate_section(
                    current_config, config, config_name, section, current
                )
        if len(errors) == 0:
            valid = True
    return (valid, errors)


def get_output_from_piped_command(c1: list, c2: list) -> list:
    """This runs two commands on the linux shell, the first is piped into the second.

    Args:
        c1 (list): This is a list of the command part typically [command, flag, value, ...]
        c2 (list): This is the cmmand that the output of the first command will get piped into

    Returns:
        list: A list of the results of the running of the commadn
    """
    try:
        p1 = subprocess.Popen(c1, stdout=subprocess.PIPE)
        p2 = subprocess.check_output(c2, stdin=p1.stdout)
        return p2.decode("utf-8").strip().split("\n")
    except subprocess.CalledProcessError as e:
        pp(f"WARNING: {e}")
        return []


def delete_oldest_backup(backups: deque):
    """This deletes the first (oldest) backup from a list

    Args:
        backups (deque): A deque so we can pop_left and send that data for deletion
    """
    # The oldest file will be first
    backup = backups.popleft()
    os.remove(os.path.join(BACKUPS_DIR, backup.split(" ")[-1]))


def create_backups_dir():
    """This makes sure the backups dir is there
    """
    if not os.path.exists(BACKUPS_DIR):
        os.mkdir(BACKUPS_DIR)


def backup_old_configs(config_dict: dict, current: str) -> bool:
    """The purpose of this function is to backup old configs before we write new ones.  Best to
    keep a known good config on file

    Args:
        config_dict (dict): A dictionay of all the configs, the filename is the key
        current (str): The fqdn of the current config

    Returns:
        bool: True if backup successful, else False
    """
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
    """This simply writes the updated configs to disk

    Args:
        config_dict (dict): A dictionay of all the configs, the filename is the key
        current (str): The fqdn of the current config
    """
    for config_name, config in config_dict.items():
        file_name = os.path.join(FILEPATH, config_name)
        if config_name not in current:
            with open(file_name, "w") as file:
                file.write("".join(config))


if __name__ == "__main__":
    current_config_file_name = get_current_config_file()
    config_dict = load_configs()
    if backup_old_configs(config_dict, current_config_file_name):
        for section in SYNC_SECTIONS:
            data = extract_section_from_current(
                config_dict, current_config_file_name, section
            )
            update_section_to_other_configs(
                config_dict, data, current_config_file_name, section
            )
        (valid, errors) = validate_configs(config_dict, current_config_file_name)
        if valid:
            write_new_configs(config_dict, current_config_file_name)
        else:
            pp(f"errors: {errors}")
