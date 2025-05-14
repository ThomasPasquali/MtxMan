import os
import yaml
import colors

config_file_url = "config.yaml"

def read_config_file():
    if not os.path.exists(config_file_url):
        raise Exception(
            f"{colors.color_red('config.yaml')} is not present. Refer to the config.example.yaml file to generate your custom config.yaml file"
        )

    with open(config_file_url, "r") as config_file:
        config = yaml.safe_load(config_file)

    return config


def create_datasets_dir(config, category):
    if not "path" in config:
        raise Exception(
            f"{colors.color_red('path')} key is required. Refer to the config.example.yaml file"
        )

    data_dir_path = f'{config["path"]}/{category}'
    os.makedirs(data_dir_path, exist_ok=True)


def get_datasets_dir_path(config):
    if not "path" in config:
        raise Exception(
            f"{colors.color_red('path')} key is required. Refer to the config.example.yaml file"
        )
    return config["path"]


def write_mtx_summary_file(config, matrices_paths, category=None):
    datasets_dir_path = get_datasets_dir_path(config)
    category_folder_path = f"{datasets_dir_path}/{category}" if category else datasets_dir_path
    os.makedirs(category_folder_path, exist_ok=True)
    output_file_path = f"{category_folder_path}/matrices_list.txt"

    with open(output_file_path, "w") as f:
        for matrix_path in matrices_paths:
            f.write(f"{matrix_path}\n")

    print(f"\n{colors.color_yellow(f'Matrix file paths written to {output_file_path}')}")
