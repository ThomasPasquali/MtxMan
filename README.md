# MtxMan

This is a utility repository that simplifies the download and generation of Matrix Market (`.mtx`) files.

* Files are downloaded from `SuiteSparse` (https://sparse.tamu.edu/)
* Supported generators:
    * `Graph500` (Kronecker graphs)

## Cloning

To clone this repo with all the git submodules initialized run the following command

```
git clone --recurse-submodules https://github.com/HicrestLaboratory/distributed_mmio.git
```

If you already cloned the repo and initialize recursively the submodules

```
git submodule update --init --recursive
```

## Python Environment

If `conda` is available on your system, all the required packages and configuration are in the `environment.yml` file. Just run:

```bash
conda env create -f environment.yml
```

Alternatively, use `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generators

If you want to use the `graph500` generator then you should have the `gcc` available on your system.

## Dataset download/generation

Once the environment is ready, it is time to customize the condiguration file.

1) Create your own `config.yaml` file (based on the `config.example.yaml` format)
2) Run the following command:

```bash
python3 scripts/sync_datasets.py
```

By default this command will download/generate all the configured matrices.

For more details, run the script with the `-h` or `--help` flag.

The downloaded/generated files are structured as follows:

```bash
<config.path>
├── <category_0>
│   ├── <group_0> # Matrices from SuiteSparse "list"
│   │   └── <matrix_0>
│   │       └── <matrix_0>.mtx
│   ├── <group_1>
│   │   ├── <matrix_0>
│   │   │   └── <matrix_0>.mtx
│   │   └── <matrix_1>
│   │       └── <matrix_1>.mtx
|   ...
|   |
│   └── SuiteSparse_<min_nnz>_<max_nnz>_<limit> # Matrices from SuiteSparse "range"
|   │   ├── <group_0> # Matrices from SuiteSparse "list"
|   │   │   └── <matrix_0>
|   │   │       └── <matrix_0>.mtx
|   |   ...
|   └── matrices_list.txt # Summary file, contains all matrices paths for <category_0>
├── <category_1>
│   |
|   ... # Same structure
...
└── matrices_list.txt # Summary file, contains all matrices paths
```

> **IMPORTANT.** To minimize space requirements, run the script as
> ```bash
> python3 scripts/sync_datasets.py --binary-mtx
> ```
> This will convert `.mtx` files to `.bmtx` saving 80 to 50% disk space. The reading of `.bmtx` files is handled by [https://github.com/HicrestLaboratory/distributed_mmio](https://github.com/HicrestLaboratory/distributed_mmio). Check it out!
> Before running make sure `distributed_mmio` git submodule is cloned
> ```bash
> git submodule init
> git submodule update distributed_mmio
> ```


## Utilities 

Once you have downloaded/generated your matrices, you can generate a CSV containing all your matrices metadata.

> This will only add matrices from SuiteSparse.

```bash
utils/get_mtx_metadata.sh # This will generate the matrix_info.csv file
```