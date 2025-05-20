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
        raise Exception(f"{colors.color_red('category')} key is not configured properly. Refer to the config.example.yaml file")

    if not "generators" in config[category]:
        return ([],[])

    if not "graph500" in config[category]["generators"]:
        raise Exception(f"{colors.color_red('graph500')} key is not configured properly. Refer to the config.example.yaml file")

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


def generate(args, config, category):
    matrices_paths = {}

    graph500_dir_path = "generators/graph500"
    graph500_gen_dir_path = f'{graph500_dir_path}/generator'
    graph500_gen_main_filename = 'graph500_generator_main.c'

    if not os.path.isdir(graph500_dir_path):
        raise Exception("graph 500 submodule is required: remember to run 'git submodule update --init --recursive'")

    if not os.path.isfile(os.path.join(graph500_gen_dir_path, graph500_gen_main_filename)):
        shutil.copy2(
            os.path.join("generators", "custom", graph500_gen_main_filename),
            os.path.join(graph500_gen_dir_path, graph500_gen_main_filename)
        )

    try:
        print(f"Compiling graph500 generator...")
        subprocess.run((f'gcc -O3 -I ./ -o graph500_gen {graph500_gen_main_filename} make_graph.c splittable_mrg.c graph_generator.c utils.c -lm -w').split(), cwd=graph500_gen_dir_path, check=True)
        print(f"Graph500 Generator compiled!")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

    (scales, edge_factors) = read_graph_500_config(config, category)
    utils.create_datasets_dir(config, category)

    for scale, edge_factor in zip(scales, edge_factors):
        file_name = f"graph500_{scale}_{edge_factor}"
        data_dir_path = utils.get_datasets_dir_path(config)
        destination_path = os.path.join(data_dir_path, category, 'Graph500')
        os.makedirs(destination_path, exist_ok=True)
        destination_path = os.path.join(destination_path, file_name)
        destination_path_mtx = f"{destination_path}.mtx"
        destination_path_bmtx = f"{destination_path}.bmtx"

        mtx_exists = os.path.isfile(destination_path_mtx)
        bmtx_exists = os.path.isfile(destination_path_bmtx)

        file_name += '.bmtx' if args.binary_mtx else '.mtx'
        destination_path = os.path.join(data_dir_path, category, 'Graph500', file_name)
        destination_path = os.path.abspath(destination_path)
        destination_path_mtx = os.path.abspath(destination_path_mtx)
        destination_path_bmtx = os.path.abspath(destination_path_bmtx)

        if args.binary_mtx and bmtx_exists:
            print(f"\t\t{colors.color_yellow(file_name)} was already generated and converted, skipped")
        elif not args.binary_mtx and mtx_exists:
            print(f"\t\t{colors.color_yellow(file_name)} was already generated, skipped")
        else:
            info = ''
            generate = False
            convert = False
            if args.binary_mtx and mtx_exists and not bmtx_exists:
                info = 'Converting to BMTX'
                convert = True
            elif not args.binary_mtx and not mtx_exists:
                info = 'Generating'
                generate = True
            elif args.binary_mtx and not mtx_exists:
                info = 'Generating and Converting to BMTX'
                generate = True
                convert = True
            else:
                raise Exception('This should not happen')
            
            print(f"\t\t{info} {colors.color_green(file_name)}")
            print(100 * "=")

            if generate:
                set_env(file_name)  # This is probably not needed anymore
                try:
                    print(f"Generating Graph500 graph with {colors.color_green(f'(scale, edge factor) = ({scale}, {edge_factor})')}")
                    subprocess.run(['./graph500_gen', str(scale), str(edge_factor), str(destination_path_mtx)], cwd=graph500_gen_dir_path, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Graph generation failed: {e}")
                    unset_env()
                    continue
                unset_env()
                print('Generated!')

            if convert and args.binary_mtx:
                mtx_to_bmtx_bin_path = os.path.join(os.path.dirname(__file__), '..', 'distributed_mmio', 'build', 'mtx_to_bmtx')
                mtx_to_bmtx_bin_path = os.path.abspath(mtx_to_bmtx_bin_path)
                subprocess.run([mtx_to_bmtx_bin_path, destination_path_mtx] + (['-d'] if args.binary_mtx_double_vals else []))
                if not args.keep_mtx:
                    os.remove(destination_path_mtx)

            print((100 * "=")+'\n')

            # source_path = os.path.join(graph500_gen_dir_path, file_name)
            # print(colors.color_green(f"Graph generated in {source_path}"))
            # print(colors.color_green(f"Copying to {destination_path}"))
            # shutil.copy2(source_path, destination_path)
            # os.remove(source_path)

        matrices_paths[(scale, edge_factor)] = str(os.path.join(data_dir_path, category, 'Graph500', file_name))
        
    return matrices_paths
