import argparse
import utils
import colors
import graph500_generator
import suite_sparse_matrix_downloader

def sync_all(args, config):
    matrices_paths = []
    base_path = utils.get_datasets_dir_path(config)
    for category in config.keys():
        if category == 'path' or category in args.skip:
            continue
        matrices_paths_category = []

        print(colors.color_green(f'\n>> Syncing "{category}"...'))
        # FIXME graph500_generator.generate(config, category)
        matrices_paths_category += suite_sparse_matrix_downloader.download_list(config, category)
        matrices_paths_category += suite_sparse_matrix_downloader.download_range(config, category)
        
        # Remove base path
        matrices_paths_category = [p[len(base_path)+1:] for p in matrices_paths_category]

        utils.write_mtx_summary_file(config, matrices_paths_category, category)
        matrices_paths += matrices_paths_category
    
    utils.write_mtx_summary_file(config, matrices_paths)

def main(args):
    config = utils.read_config_file()
    sync_all(args, config)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MtxMan - simple download and generation of Matrix Market files")
    # parser.add_argument("--interactive", "-i", action="store_true", help="Starts the CLI tool that will guide you")
    parser.add_argument("--skip", "-s", nargs="+", required=False, help="A list of 'categories' to skip", default=[])

    # TODO implement
    parser.add_argument("--matrix-market", "-mm", action="store_true", help="If set, the script will not generate the binary '.bmtx' files")
    # TODO implement
    parser.add_argument("--keep-mtx", "-k", action="store_true", help="If set, the script will keep the '.mtx' files")
    # TODO implement
    parser.add_argument("--keep-all-mtx", "-ka", action="store_true", help="If set, the script will keep the '.mtx' files")
    
    args = parser.parse_args()

    main(args)
