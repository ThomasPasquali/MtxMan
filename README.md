# MtxMan 🔢

This is a utility that simplifies the download and generation of Matrix Market (`.mtx`) files.

* Files are downloaded from `SuiteSparse` (https://sparse.tamu.edu/)
* Supported generators:
    * [Graph500](https://github.com/graph500/graph500) (Kronecker graphs)
    * [PaRMAT](https://github.com/farkhor/PaRMAT) (Customizable RMATs)

## Requirements

- `gcc`: to build dependencies:
    - `distributed_mmio` to convert matrices to BMTX format.
    - `Graph500` and `PaRMAT` generators.
- `python3`/`pip`/`pipx` to download and setup MtxMan.

## Setup

First, setup you Python environment (if needed).

### Virtual Environment Setup

```bash
# If you don't already have one, create and activate a venv
python3 -m venv .venv
source .venv/bin/activate

pip install pipx
pipx ensurepath
```

You may need to restart your terminal for the changes to take effect.

## MtxMan Installation

Once `pipx` is installed, you can install MtxMan from [PyPI](https://pypi.org/project/mtxman/):

```bash
# Install MtxMan CLI
pipx install mtxman
```

Great, you now have MtxMan installed! You can check out the available commands by running:

```bash
mtxman --help
```

## Developer Installation

```bash
# Clone the repository
git clone git@github.com:ThomasPasquali/MtxMan.git
cd MtxMan
# Install the project in editable mode
pip install -e .
```

Now the `mtxman` command should use the local version of the package.  
Any changes you make to the code will be reflected immediately when you run the command.

## Usage: matrices download/generation

Once you have the MtxMan available on your system.

1) Create your own YAML configuration file (check out the example below for the syntax)
2) Run the following command:

```bash
mtxman sync <your_config_file>.yaml
```

By default this command will download/generate all the configured matrices.

For more details, run `mtxman sync --help`.

### Example Configuration File

```yaml
# This is the base folder for storing the Matrix Market files
path: ./datasets

# This is an example subfolder/category of matrices
matrices_category_1:

  # Generators configuration
  generators:
    # Graph500 Kronecker
    graph500:
      # This will generate two graphs:
      # 1) Scale 4, Edge-factor 5
      # 2) Scale 6, Edge-factor 10
      scale:
        - 4
        - 6
      edge_factor:
        - 5
        - 10

    # PaRMAT generator
    parmat:
    # Parameters:
    # N - Number of veritces
    # M - Number of edges
    # a,b,c - RMAT probabilities. "d" will be deduced automatically. (defaulf: a,b,c=0.25)
    # noDuplicateEdges, undirected, noEdgeToSelf, sorted - Flags. To enable a flag, please set it to 1. (default: 0)
      defaults: # This is optional
        N: 32
        a: 0.25
        b: 0.25
        c: 0.25
        undirected: 1
        noDuplicateEdges: 1
      matrices: # Specify the list of matrices. Default parametes can be overwritten
        - { M: 64 }
        - { M: 128 }
        - { N: 64, M: 64, a: 0.7, b: 0.1, c: 0.1, noEdgeToSelf: 1 } # Overriding defaults

  # List of matrices to be downloaded from SuiteSparse
  # Format: "<group>/<matrix_name>"
  suite_sparse_matrix_list:
    - HB/ash219
    - HB/arc130
    - Averous/epb0
  
  # This allows to download matrices based on their metadata
  # Internally, these options will be passed to the `ssgetpy` package
  suite_sparse_matrix_range:
    min_nnzs: 100
    max_nnzs: 1000
    limit: 4

# This is ANOTHER example subfolder/category of matrices
# The configuration structure is as above
# Keys 'generators', 'suite_sparse_matrix_list' and 'suite_sparse_matrix_range' are OPTIONAL
matrices_category_2:
  suite_sparse_matrix_list:
    - Simon/olafu

matrices_category_3:
  generators:
    graph500:
      # This will generate three graphs:
      # 1) Scale 6, Edge-factor 5
      # 2) Scale 8, Edge-factor 5
      # 3) Scale 9, Edge-factor 5
      edge_factor: 5
      scale:
        - 6
        - 8
        - 9
```

## Files Structure

The downloaded/generated files are structured as follows:

```
<config.path>
├── <category_0>
│   ├── <SuiteSparse_group_0> # Matrices from SuiteSparse "list"
│   │   └── <matrix_0>
│   │       └── <matrix_0>.mtx
│   ├── <SuiteSparse_group_1>
│   │   ├── <matrix_0>
│   │   │   └── <matrix_0>.mtx
│   │   └── <matrix_1>
│   │       └── <matrix_1>.mtx
|   ...
|   |
|   ├── Graph500
│   │   ├── graph500_<scale_0>_<edge_factor0>
│   │   ├── graph500_<scale_1>_<edge_factor1>
│   │   ...
|   |
|   ├── PaRMAT
│   │   ├── parmat_N<N_0>_M<M_0>_<other parmat parameters 0>
│   │   ├── parmat_N<N_1>_M<M_1>_<other parmat parameters 1>
│   │   ...
|   |
│   └── SuiteSparse_<min_nnz>_<max_nnz>_<limit> # Matrices from SuiteSparse "range"
|   │   ├── <SuiteSparse_group_0> # Matrices from SuiteSparse "list"
|   │   │   └── <matrix_0>
|   │   │       └── <matrix_0>.mtx
|   |   ...
|   └── matrices_list.txt # Summary file, contains all matrices paths for <category_0>
├── <category_1>
│   |
|   ... # Same structure
...
└── matrices_list.txt # Summary file, contains all matrices paths
└── matrices_metadata.csv # Summary file, contains all matrices metadata (number of rows, columns, non-zeros etc.)
```

## Optimize Required Disk Space and Read Time

To optimize space requirements, run the `sync` command as follows:
```bash
mtxman sync <your_config_file>.yaml --binary-mtx
```

This will convert `.mtx` files to `.bmtx` saving 50 to 80% disk space.  
The reading of `.bmtx` files is handled by [https://github.com/HicrestLaboratory/distributed_mmio](https://github.com/HicrestLaboratory/distributed_mmio). Check it out!
