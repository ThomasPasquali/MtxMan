import os

import ssgetpy
import utils
import colors

def download_matrix(matrix, matrix_location):
    matrix_url = matrix.url('MM')
    tar_file_path = f"{matrix_location}/{matrix.name}.tar.gz"
    os.system(f"wget -O {tar_file_path} {matrix_url}")
    os.system(f"tar -xzf {tar_file_path} -C {matrix_location}")
    
    # Ensure the .mtx file is in a subfolder
    subfolder_path = f"{matrix_location}/{matrix.name}"
    if not os.path.isdir(subfolder_path):
        os.makedirs(subfolder_path, exist_ok=True)
        os.rename(f"{matrix_location}/{matrix.name}.mtx", f"{subfolder_path}/{matrix.name}.mtx")
    
    os.remove(tar_file_path)

def read_sparse_matrix_list_config(config, category):
    if not category in config:
        raise Exception(
            f"{colors.color_red('category')} key is not configured properly. Refer to the config.example.yaml file"
        )

    if not "suite_sparse_matrix_list" in config[category]:
        return []

    suite_sparce_matrix_list = config[category]["suite_sparse_matrix_list"]

    if suite_sparce_matrix_list is None:
        raise Exception(
            f"{colors.color_red('suite_sparse_matrix_list')} is empty. Refer to the config.example.yaml file"
        )

    processed_suite_sparse_matrix_list = []

    for group_and_name in suite_sparce_matrix_list:
        if isinstance(group_and_name, str):
            parts = group_and_name.split("/")
            if len(parts) == 2:
                processed_suite_sparse_matrix_list.append(
                    (group_and_name, parts[0], parts[1])
                )
            else:
                print(
                    f"{colors.color_red(group_and_name)} has an invalid format. Refer to the config.example.yaml file"
                )

    return processed_suite_sparse_matrix_list


def download_list(config, category)-> list[str]:
    processed_suite_sparse_matrix_list = read_sparse_matrix_list_config(config, category)
    error_matrices = []
    matrices_paths = []

    utils.create_datasets_dir(config, category)
    datasets_dir_path = utils.get_datasets_dir_path(config)

    for full_name, group_name, matrix_name in processed_suite_sparse_matrix_list:
        print(f"\tChecking matrix: {full_name}")

        matrices = ssgetpy.search(name=matrix_name, limit=3000)

        if not matrices:
            print(
                f"\t\t{colors.color_red(full_name)} not found in SuiteSparse, skipped"
            )
            error_matrices.append(full_name)
            continue

        found = False
        for matrix in matrices:
            if matrix.name == matrix_name:
                matrix_location = f"{datasets_dir_path}/{category}/{group_name}"
                if os.path.isdir(f"{datasets_dir_path}/{category}/{full_name}"):
                    print(
                        f"\t\t{colors.color_yellow(full_name)} was already downloaded, skipped"
                    )
                else:
                    os.makedirs(matrix_location, exist_ok=True)
                    print(f"\t\tDownloading {colors.color_green(full_name)}")
                    print(100 * "=")
                    # This is slow... matrix.download(destpath=matrix_location, extract=True)
                    download_matrix(matrix, matrix_location)
                    print(100 * "=")

                matrices_paths.append(f'{matrix_location}/{matrix_name}/{matrix_name}.mtx')
                found = True
                break

        if not found:
            print(
                f"{colors.color_red('matrix_name')} returned, but exact match not found"
            )
            error_matrices.append(matrix_name)

    if error_matrices:
        print()
        print(
            f"{colors.color_red('Error')}: The following matrices were not found or mismatched:"
        )
        for m in error_matrices:
            print(f"\t{m}")
    else:
        print(colors.color_green(f'All "{category}" matrices were sync successfully <<'))

    return matrices_paths


def read_sparse_matrix_range_config(config, category):
    if not category in config:
        raise Exception(
            f"{colors.color_red('category')} key is not configured properly. Refer to the config.example.yaml file"
        )

    if not "suite_sparse_matrix_range" in config[category]:
        return None

    if not "min_nnzs" in config[category]["suite_sparse_matrix_range"]:
        raise Exception(
            f"{colors.color_red('min_nnzs')} key is not configured properly. Refer to the config.example.yaml file"
        )

    min_nnzs = config[category]["suite_sparse_matrix_range"]["min_nnzs"]

    if min_nnzs <= 0:
        raise Exception(
            f"{colors.color_red('min_nnzs')} value should be strictly positive. Refer to the config.example.yaml file"
        )

    if not "max_nnzs" in config[category]["suite_sparse_matrix_range"]:
        raise Exception(
            f"{colors.color_red('max_nnzs')} key is not configured properly. Refer to the config.example.yaml file"
        )

    max_nnzs = config[category]["suite_sparse_matrix_range"]["max_nnzs"]

    if max_nnzs <= 0:
        raise Exception(
            f"{colors.color_red('max_nnzs')} value should be strictly positive. Refer to the config.example.yaml file"
        )

    if min_nnzs > max_nnzs:
        raise Exception(
            f"{colors.color_red('max_nnzs > max_nnzs')} is not valid. Refer to the config.example.yaml file"
        )

    if not "limit" in config[category]["suite_sparse_matrix_range"]:
        raise Exception(
            f"{colors.color_red('limit')} key is not configured properly. Refer to the config.example.yaml file"
        )

    limit = config[category]["suite_sparse_matrix_range"]["limit"]

    if limit <= 0:
        raise Exception(
            f"{colors.color_red('limit')} value should be strictly positive. Refer to the config.example.yaml file"
        )

    return (min_nnzs, max_nnzs, limit)


def download_range(config, category) -> list[str]:
    mtx_range = read_sparse_matrix_range_config(config, category)

    if not mtx_range:
        return []
    (min_nnzs, max_nnzs, limit) = mtx_range

    matrices = ssgetpy.fetch(nzbounds=(min_nnzs, max_nnzs), limit=limit, dry_run=True)
    skipped_matrices = []
    matrices_paths = []

    if not matrices:
        raise Exception(
            f"{colors.color_red('Error')} : matrices with min_nnzs: {min_nnzs}, max_nnzs: {max_nnzs}, limit: {limit} were not found in SuiteSparse"
        )

    utils.create_datasets_dir(config, category)
    datasets_dir_path = utils.get_datasets_dir_path(config)
    matrices_dir_name = f"SuiteSparse_{min_nnzs}_{max_nnzs}_{limit}"

    for matrix in matrices:
        matrix_location = f"{datasets_dir_path}/{category}/{matrices_dir_name}/{matrix.group}"
        full_name = f"{matrix.group}/{matrix.name}"
        if os.path.isdir(f"{matrix_location}/{matrix.name}"):
            print(f"\t\t{colors.color_yellow(full_name)} was already downloaded, skipped")
            skipped_matrices.append(full_name)
        else:
            os.makedirs(matrix_location, exist_ok=True)
            print(f"\t\tDownloading {colors.color_green(full_name)}")
            print(100 * "=")
            # This is slow... matrix.download(destpath=matrix_location, extract=True)
            download_matrix(matrix, matrix_location)
            print(100 * "=")
        
        matrices_paths.append(f'{matrix_location}/{matrix.name}/{matrix.name}.mtx')

    if skipped_matrices:
        print()
        print(f"{colors.color_yellow('Warning')}: The following matrices were skipped:")
        for full_name in skipped_matrices:
            print(f"\t{full_name}")
    else:
        print(colors.color_green(f'All "{category}" matrices were downloaded successfully <<'))

    return matrices_paths
    
