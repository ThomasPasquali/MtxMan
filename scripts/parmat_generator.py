import os
import re
from typing import Any
import colors
import subprocess

import utils

def read_parmat_config(config, category) -> tuple[dict[str,Any], list[dict[str,Any]]]:
    if not category in config:
        raise Exception(f"{colors.color_red('category')} key is not configured properly. Refer to the config.example.yaml file")

    if "generators" not in config[category] or "parmat" not in config[category]["generators"]:
        return ({},[])

    parmat_config = config[category]["generators"]["parmat"]

    return parmat_config.get('defaults', {}), parmat_config.get('matrices', [])


def generate(args, config, category) -> dict:
    matrices_paths = {}

    parmat_dir_path = "generators/PaRMAT"
    parmat_gen_dir_path = f'{parmat_dir_path}/Release'

    if not os.path.isdir(parmat_dir_path):
        raise Exception("PaRMAT submodule is required: remember to run 'git submodule update --init --recursive'")
    
    if not os.path.isfile(f'{parmat_gen_dir_path}/PaRMAT'):
        try:
            print(f"Compiling PaRMAT generator...")
            subprocess.run('make', cwd=parmat_gen_dir_path, check=True)
            print(f"PaRMAT Generator compiled!")
        except subprocess.CalledProcessError as e:
            print(f"Compilation failed: {e}")
            exit(1)

    defaults, matrices = read_parmat_config(config, category)
    utils.create_datasets_dir(config, category)

    for mtx in matrices:
        mtx_config = defaults.copy()
        for k, v in mtx.items():
            mtx_config[k] = v
        if 'N' not in mtx_config or 'M' not in mtx_config:
            raise Exception(f'Invalid PaRMAT configuration: N and M are required (not available in "{mtx_config}")')
        if ('a' in mtx_config or 'b' in mtx_config or 'c' in mtx_config) and not ('a' in mtx_config and 'b' in mtx_config and 'c' in mtx_config):
            raise Exception(f'Invalid PaRMAT configuration: You must either set all "a,b,c" or none of them ("{mtx_config}")')
        noDuplicateEdges = mtx_config.get('noDuplicateEdges', 0) == 1
        undirected = mtx_config.get('undirected', 0) == 1
        noEdgeToSelf = mtx_config.get('noEdgeToSelf', 0) == 1
        sorted = mtx_config.get('sorted', 0) == 1
        mtx_config['noDuplicateEdges'] = noDuplicateEdges
        mtx_config['undirected'] = undirected
        mtx_config['noEdgeToSelf'] = noEdgeToSelf
        mtx_config['sorted'] = sorted
        N = int(mtx_config['N'])
        M = int(mtx_config['M'])

        cli_args = ['-nVertices', N, '-nEdges', M]
        params = []
        if 'a' not in mtx_config:
            mtx_config['a'] = mtx_config['b'] = mtx_config['c'] = 0.25
        if 'a' in mtx_config and 'b' in mtx_config and 'c' in mtx_config:
            params.append(f"a{int(1000*mtx_config['a'])}_b{int(1000*mtx_config['b'])}_c{int(1000*mtx_config['c'])}")
            cli_args += ['-a', mtx_config['a'], '-b', mtx_config['b'], '-c', mtx_config['c']]
        if noDuplicateEdges:
            params.append("noDup")
            cli_args.append("-noDuplicateEdges")
        if undirected:
            params.append("undir")
            cli_args.append("-undirected")
        if noEdgeToSelf:
            params.append("noSelf")
            cli_args.append("-noEdgeToSelf")
        if sorted:
            params.append("sorted")
            cli_args.append("-sorted")
        param_str = "_" + "_".join(params) if params else ""
        file_name = f"parmat_N{N}_M{M}{param_str}"
        data_dir_path = utils.get_datasets_dir_path(config)
        destination_path = os.path.join(data_dir_path, category, 'PaRMAT')
        os.makedirs(destination_path, exist_ok=True)

        print(f"\tChecking matrix: {file_name}")

        destination_path = os.path.join(destination_path, file_name)
        destination_path_mtx = f"{destination_path}.mtx"
        destination_path_bmtx = f"{destination_path}.bmtx"

        mtx_exists = os.path.isfile(destination_path_mtx)
        bmtx_exists = os.path.isfile(destination_path_bmtx)

        file_name += '.bmtx' if args.binary_mtx else '.mtx'
        destination_path = os.path.join(data_dir_path, category, 'PaRMAT', file_name)
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
                try:
                    print(f"Generating PaRMAT matrix using {colors.color_green(mtx_config)}")
                    cli_args = [str(v) for v in (['./PaRMAT'] + cli_args + ['-output', destination_path_mtx])]
                    print(' '.join(cli_args))
                    subprocess.run(cli_args, cwd=parmat_gen_dir_path, check=True)
                    with open(destination_path_mtx, 'r+') as f:
                        content = f.read()
                        lines = content.split('\n')
                        coords = []
                        for line in lines:
                            line = re.sub(r'\s+', ' ', line)
                            rc = line.split(' ')
                            if len(rc) == 2:
                                r, c = rc
                                coords.append(f'{int(r)+1} {int(c)+1}')
                        f.seek(0, 0)
                        f.write('%%MatrixMarket matrix coordinate pattern general\n')
                        f.write(f'{N} {N} {M}\n')
                        f.write('\n'.join(coords))
                except subprocess.CalledProcessError as e:
                    print(f"Graph generation failed: {e}")
                    continue
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

        matrices_paths[str(mtx_config)] = str(os.path.join(data_dir_path, category, 'PaRMAT', file_name))
        
    return matrices_paths
