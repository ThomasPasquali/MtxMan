import os
import sys
import subprocess
import shutil

import colors
import utils


def set_env(file_name):
    os.environ["REUSEFILE"] = "1"
    os.environ["TMPFILE"] = file_name
    os.environ["SKIP_BFS"] = "1"


def unset_env():
    del os.environ["REUSEFILE"]
    del os.environ["TMPFILE"]
    del os.environ["SKIP_BFS"]


def read_graph_500_config(config, category):
    if not category in config:
        raise Exception(
            f"{colors.color_red('category')} key is not configured properly. Refer to the config.example.yaml file"
        )

    if not "generators" in config[category]:
        raise Exception(
            f"{colors.color_red('generators')} key is not configured properly. Refer to the config.example.yaml file"
        )

    if not "graph500" in config[category]["generators"]:
        raise Exception(
            f"{colors.color_red('graph500')} key is not configured properly. Refer to the config.example.yaml file"
        )

    graph_500_config = config[category]["generators"]["graph500"]

    if not "scale" in graph_500_config:
        raise Exception(
            f"{colors.color_red('scale')} key is required. Refer to the config.example.yaml file"
        )
    if not "edge_factor" in graph_500_config:
        raise Exception(
            f"{colors.color_red('edge_factor')} key is required. Refer to the config.example.yaml file"
        )

    scale, edge_factor = graph_500_config["scale"], graph_500_config["edge_factor"]

    if isinstance(scale, list) and isinstance(edge_factor, list):
        return scale, edge_factor
    elif isinstance(scale, int) and isinstance(edge_factor, list):
        return [scale] * len(edge_factor), edge_factor
    elif isinstance(scale, list) and isinstance(edge_factor, int):
        return scale, [edge_factor] * len(scale)
    elif isinstance(scale, int) and isinstance(edge_factor, int):
        return [scale], [edge_factor]
    else:
        raise Exception(
            f"Combination of scale and edge_factor not allowed {scale=}, {edge_factor=}. Refer to the config.example.yaml file"
        )


def generate(config, category):
    graph500_dir_path = "generators/graph500"
    if not os.listdir(graph500_dir_path):
        raise Exception(
            "graph 500 submodule is required: remember to run 'git submodule update --init --recursive'"
        )

    (scales, edge_factors) = read_graph_500_config(config, category)

    for scale, edge_factor in zip(scales, edge_factors):
        file_name = f"graph500_{scale}_{edge_factor}"
        set_env(file_name)

        working_dir_path = f"{graph500_dir_path}/src"

        try:
            print(f"Start compiling graph500_reference_bfs...")
            print()
            subprocess.run(
                ["make", "graph500_reference_bfs"], cwd=working_dir_path, check=True
            )
            print()
        except subprocess.CalledProcessError as e:
            print(f"Compilation failed: {e}")
            sys.exit(1)

        try:
            print(
                f"Start generating a graph with {colors.color_green(f'(scale, edge factor) = ({scale}, {edge_factor})')}"
            )
            print()
            subprocess.run(
                ["mpirun", "./graph500_reference_bfs", f"{scale}", f"{edge_factor}"],
                cwd=working_dir_path,
                check=True,
            )
            print()
        except subprocess.CalledProcessError as e:
            print(f"Graph generation failed: {e}")
            sys.exit(1)

        utils.create_datasets_dir(config, category)
        unset_env()

        data_dir_path = utils.get_datasets_dir_path(config)
        source_path = f"{working_dir_path}/{file_name}"
        destination_path = f"{data_dir_path}/{file_name}"

        print(colors.color_green(f"Graph generated in {source_path}"))
        print(colors.color_green(f"Copying to {destination_path}"))

        # if the file is big then it will take a long time to move, so it is safer to copy it first so that, if the copy operation fails, we can repeat the copy operation later and then delete it
        shutil.copy2(source_path, destination_path)
        os.remove(source_path)
