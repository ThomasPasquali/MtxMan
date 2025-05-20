import argparse
import utils
import colors
import graph500_generator
import suite_sparse_matrix_downloader
from collections import defaultdict

def sync_all(args, config):
    matrices_paths = []
    base_path = utils.get_datasets_dir_path(config)
    for category in config.keys():
        if category == 'path' or category in args.skip:
            continue
        matrices_paths_category = {}

        print(colors.color_green(f'\n>> Syncing "{category}"...'))

        matrices_paths_category_dd = defaultdict(list)
        for d in [
            graph500_generator.generate(args, config, category),
            suite_sparse_matrix_downloader.download_list(args, config, category),
            suite_sparse_matrix_downloader.download_range(args, config, category)
        ]:
            for k, v in d.items():
                matrices_paths_category_dd[k].append(v)

        matrices_paths_category = dict(matrices_paths_category_dd)
        matrices_paths_category = [item[len(base_path)+1:] for sublist in matrices_paths_category.values() for item in sublist]

        utils.write_mtx_summary_file(config, matrices_paths_category, category)
        matrices_paths += matrices_paths_category
    
    utils.write_mtx_summary_file(config, matrices_paths)

def main(args):
    config = utils.read_config_file()

    if args.binary_mtx:
        utils.build_mtx_to_bmtx_converter()

    sync_all(args, config)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MtxMan - simple download and generation of Matrix Market files.")
    # parser.add_argument("--interactive", "-i", action="store_true", help="Starts the CLI tool that will guide you")
    parser.add_argument("--skip", "-s", nargs="+", required=False, help="A list of 'categories' to skip.", default=[])
    parser.add_argument("--keep-all-mtx", "-ka", action="store_true", help="Archives downloaded from SuiteSparse may contain more files. If --keep-all-mtx is set, the script will keep the '<matrix_name>.mtx' file.")

    parser.add_argument("--binary-mtx", "-bmtx", action="store_true", help="If set, the script will not generate the binary '.bmtx' files.")
    parser.add_argument("--keep-mtx", "-kmtx", action="store_true", help="(Has effect only if --binary-mtx is set) If set, the script will keep the '.mtx' files.")
    parser.add_argument("--binary-mtx-double-vals", "-bmtxd", action="store_true", help="(Has effect only if --binary-mtx|-bmtx is set) If set, the bmtx converter will store values using 8 bytes (instead of 4). Note: this has no effect on 'pattern' matrices.")
    
    args = parser.parse_args()

    main(args)
