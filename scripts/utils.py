import os
import yaml
import colors
import subprocess

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
        raise Exception(f"{colors.color_red('path')} key is required. Refer to the config.example.yaml file")

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

def build_mtx_to_bmtx_converter():
    subfolder = os.path.join(os.path.dirname(__file__), "..", "distributed_mmio")
    subfolder = os.path.abspath(subfolder)
    if os.path.exists(os.path.join(subfolder, 'build', 'mtx_to_bmtx')):
        return

    print(colors.color_green('Building mtx_to_bmtx converter...'))
    
    if not os.path.exists(subfolder):
        raise Exception(f"{colors.color_red('distributed_mmio')} submodule not found. Please sync the git submodule.")

    build_dir = os.path.join(subfolder, "build")
    try:
        subprocess.run(
            ["cmake", "-B", "build"],
            cwd=subfolder,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["make", "mtx_to_bmtx"],
            cwd=build_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        raise Exception(
            f"{colors.color_red('Failed to build distributed-mmio. Please sync the git submodule and ensure CMake is available.')}\nError: {e}"
        )
    print(colors.color_green('mtx_to_bmtx converter compiled!'))


# def remove_other_mtx(matrices: dict[str, str]):
#     """
#     For each matrix, remove all files in its subfolder except <matrix_name>.mtx.
#     """
#     for matrix_name, matrix_path in matrices.items():
#         folder = os.path.dirname(matrix_path)
#         for filename in os.listdir(folder):
#             file_path = os.path.join(folder, filename)
#             if filename != f"{matrix_name}.mtx" and os.path.isfile(file_path):
#                 os.remove(file_path)
    
