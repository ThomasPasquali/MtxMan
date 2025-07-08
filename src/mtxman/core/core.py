import csv
import os
import re
import subprocess
import yaml
from typing import List, Tuple, Union
from pathlib import Path
from bs4 import BeautifulSoup
from rich.console import Console
import requests
from dataclasses import dataclass

from mtxman.core.dependencies import MTX_TO_BMTX_CONVERTER
from mtxman.exceptions import ConfigurationFileNotFoundError, ConfigurationFormatError

console = Console()

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Union, Optional

@dataclass
class Graph500Matrix:
  scale: int
  edge_factor: int

@dataclass
class ConfigGraph500:
  scale: Union[List[int], int]
  edge_factor: Union[List[int], int]

  def get_matrices(self) -> List[Graph500Matrix]:
    scales = []
    edge_factors = []
    if isinstance(self.scale, list) and isinstance(self.edge_factor, list):
      scales = self.scale
      edge_factors = self.edge_factor
    elif isinstance(self.scale, int) and isinstance(self.edge_factor, list):
      scales = [self.scale] * len(self.edge_factor)
      edge_factors = self.edge_factor
    elif isinstance(self.scale, list) and isinstance(self.edge_factor, int):
      scales = self.scale
      edge_factors = [self.edge_factor] * len(self.scale)
    elif isinstance(self.scale, int) and isinstance(self.edge_factor, int):
      scales = [self.scale]
      edge_factors = [self.edge_factor]
    else:
      raise Exception(f"Combination of scale and edge_factor not allowed {self.scale=}, {self.edge_factor=}. Refer to the config.example.yaml file")
    
    return [Graph500Matrix(s, e) for s, e in zip(scales, edge_factors)]
  

@dataclass
class PaRMATMatrix:
  N: int
  M: int
  a: float
  b: float
  c: float
  noDuplicateEdges: bool
  undirected: bool
  noEdgeToSelf: bool
  sorted: bool

@dataclass
class PaRMATMatrixPartial:
  N: Optional[int] = None
  M: Optional[int] = None
  a: Optional[float] = None
  b: Optional[float] = None
  c: Optional[float] = None
  noDuplicateEdges: Optional[int] = None
  undirected: Optional[int] = None
  noEdgeToSelf: Optional[int] = None
  sorted: Optional[int] = None


@dataclass
class ConfigPaRMAT:
  _defaults: Optional[PaRMATMatrixPartial] = None
  _matrices: List[PaRMATMatrixPartial] = field(default_factory=list)

  def get_matrices(self) -> List[PaRMATMatrix]:
    """
    Combine the defaults with each matrix entry to produce complete PaRMATMatrix instances.

    Returns:
        List[PaRMATMatrix]: A list of fully-specified matrix configurations.
    """

    #   mtx_config = defaults.copy()
    #   for k, v in mtx.items():
    #       mtx_config[k] = v
    #   if 'N' not in mtx_config or 'M' not in mtx_config:
    #       raise Exception(f'Invalid PaRMAT configuration: N and M are required (not available in "{mtx_config}")')
    #   if ('a' in mtx_config or 'b' in mtx_config or 'c' in mtx_config) and not ('a' in mtx_config and 'b' in mtx_config and 'c' in mtx_config):
    #       raise Exception(f'Invalid PaRMAT configuration: You must either set all "a,b,c" or none of them ("{mtx_config}")')
    #   noDuplicateEdges = mtx_config.get('noDuplicateEdges', 0) == 1
    #   undirected = mtx_config.get('undirected', 0) == 1
    #   noEdgeToSelf = mtx_config.get('noEdgeToSelf', 0) == 1
    #   sorted = mtx_config.get('sorted', 0) == 1
    #   mtx_config['noDuplicateEdges'] = noDuplicateEdges
    #   mtx_config['undirected'] = undirected
    #   mtx_config['noEdgeToSelf'] = noEdgeToSelf
    #   mtx_config['sorted'] = sorted
    #   N = int(mtx_config['N'])
    #   M = int(mtx_config['M'])
    results = []
    for i, partial in enumerate(self._matrices):
      def get(field: str):
        val = getattr(partial, field)
        if val is not None:
          return val
        if self._defaults is not None:
          return getattr(self._defaults, field)
        return None

      N = get('N')
      M = get('M')
      a = get('a')
      b = get('b')
      c = get('c')

      if None in (N, M, a, b, c):
        raise ConfigurationFormatError(f"[red]PaRMAT Matrix {i} is missing required fields (N, M, a, b, c) after merging with defaults.\nDefaults: {self._defaults}\nFields: {partial}[/red]")

      matrix = PaRMATMatrix(
        N=N, M=M,
        a=a, b=b, c=c,
        noDuplicateEdges=get('noDuplicateEdges') or False,
        undirected=get('undirected') or False,
        noEdgeToSelf=get('noEdgeToSelf') or False,
        sorted=get('sorted') or False,
      )
      results.append(matrix)

    return results


@dataclass
class ConfigGenerators:
  graph500: Optional[ConfigGraph500] = None
  parmat: Optional[ConfigPaRMAT] = None


@dataclass
class ConfigSuiteSparseRange:
  min_nnzs: int
  max_nnzs: int
  limit: int


@dataclass
class ConfigCategory:
  generators: Optional[ConfigGenerators] = None
  suite_sparse_matrix_list: List[Tuple[str, str]] = field(default_factory=list)
  suite_sparse_matrix_range: Optional[ConfigSuiteSparseRange] = None


@dataclass
class Config:
  path: Path
  categories: Dict[str, ConfigCategory]

  def export_matrices_metadata_csv(self, output_csv: Union[Path, str]):
    """
    Generate a CSV file with metadata for all matrices listed in the config.

    Args:
        output_csv (Path | str): Name of the output CSV file.
    """
    self.path = self.path.resolve()
    output_csv = self.path / output_csv
    console.print(f"\n[green]Gathering matrices metadata[/green]")

    matrix_files = DatasetManager.all_matrices
    if len(matrix_files) <= 0:
      dataset_base_path = Path(self.path).resolve()
      matrix_list_txt = dataset_base_path / "matrices_list.txt"
      if not matrix_list_txt.exists():
        console.print(f"[red]Matrix list file not found at {matrix_list_txt}[/red]")
        return
      with matrix_list_txt.open("r") as f:
        matrix_files = [line.strip() for line in f.readlines() if line.strip()]

    fields = [
      "Name", "Category", "Group", "MatrixID", "NumRows", "NumCols",
      "Nonzeros", "Symmetric", "SparsityRatio", "Link", "ImageLink",
      "Source", "Params"
    ]
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with output_csv.open("w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(fields)

      for file in matrix_files:
        file_path = Path(file)
        if len(file_path.parts) < 2:
          continue

        category = file_path.resolve().relative_to(self.path).parts[0]  # user-defined category path
        source = file_path.parts[-2]  # Matrix type: SuiteSparse, Graph500, PaRMAT
        name = file_path.stem

        if source == "Graph500":
          matches = re.match(r'graph500_(\d+)_(\d+)', str(name))
          if not matches or len(matches.groups()) < 2:
            console.print(f'[red]Could not parse Graph500 matrix name "{name}"[/red]')
            continue
          scale = int(matches.group(1))
          edgefactor = int(matches.group(2))
          param_str = f"{scale=},{edgefactor=}"
          N = 2 ** scale
          M = N * edgefactor
          spr = float(M) / float(N * N)
          writer.writerow([name, category, "", "", N, N, M, "No", f"{spr:.10f}", "", "", "Graph500", param_str])
          console.print(f"[dim blue]Logged synthetic matrix (Graph500): {name}[/dim blue]")
          continue

        if source == "PaRMAT":
          matches = re.match(r'parmat_N(\d+)_M(\d+)_a(\d+)_b(\d+)_c(\d+)\w*', str(name))
          if not matches or len(matches.groups()) < 5:
            console.print(f'[red]Could not parse PaRMAT matrix name "{name}"[/red]')
            continue
          N = int(matches.group(1))
          M = int(matches.group(2))
          spr = float(M) / float(N * N)
          param_str = (
              f"{N=},{M=},a={matches.group(3)},b={matches.group(4)},c={matches.group(5)},"
              f"noDuplicateEdges={'noDup' in name},undirected={'undir' in name},"
              f"noEdgeToSelf={'noSelf' in name},sorted={'sorted' in name}"
          )
          spr = float(M) / float(N * N)
          writer.writerow([name, category, "", "", N, N, M, "No", f"{spr:.10f}", "", "", "PaRMAT", param_str])
          console.print(f"[dim blue]Logged synthetic matrix (PaRMAT): {name}[/dim blue]")
          continue

        # SuiteSparse
        group = file_path.parts[-3]
        full_name = f"{group}/{name}"
        url = f"https://sparse.tamu.edu/{full_name}"
        console.print(f"[dim blue]Fetching metadata for[/dim blue] {full_name}")

        try:
          response = requests.get(url)
          response.raise_for_status()
        except Exception as e:
          console.print(f"[red]Failed to fetch {url}: {e}[/red]")
          continue

        soup = BeautifulSoup(response.text, "html.parser")

        def extract_text_between(th_text):
          for th in soup.find_all("th"):
            if th_text.strip().lower() == th.get_text(strip=True).split("\n")[0].strip().lower():
              td = th.find_next("td")
              if td:
                return td.get_text(strip=True)
          return ""

        def extract_image_link():
          div = soup.find("div", class_="carousel-item active")
          if div and (a_tag := div.find("a", href=True)):
            return a_tag["href"]
          return ""

        name_field = extract_text_between("Name")
        group_field = extract_text_between("Group")
        matrix_id = extract_text_between("Matrix ID")
        num_rows = int(re.sub(",", "", extract_text_between("Num Rows")) or 0)
        num_cols = int(re.sub(",", "", extract_text_between("Num Cols")) or 0)
        nonzeros = int(re.sub(",", "", extract_text_between("Nonzeros")) or 0)
        spr = nonzeros / (num_rows * num_cols) if num_rows and num_cols else 0
        symmetric = extract_text_between("Symmetric")
        image_link = extract_image_link()

        writer.writerow([
          name_field, category, group_field, matrix_id,
          num_rows, num_cols, nonzeros, symmetric,
          f"{spr:.10f}", url, image_link,
          "SuiteSparse", ""
        ])
        console.print(f"[dim blue]Logged SuiteSparse matrix: {full_name}[/dim blue]")

    console.print(f"[green]CSV written to[/green] {output_csv}")


@dataclass
class Flags:
  """
  binary_mtx (bool): Whether to convert matrices to BMTX format.\n
  binary_mtx_double_vals (bool): Whether to use double values in BMTX.\n
  keep_mtx (bool): Whether to keep the original MTX files after conversion.\n
  keep_all_mtx (bool): Whether to keep all MTX files (not just the main one).\n
  """
  binary_mtx: bool
  binary_mtx_double_vals: bool
  keep_mtx: bool
  keep_all_files: bool


class DatasetManager:
  MATRICES_SUMMARY_FILENAME = "matrices_list.txt"
  # Static attribute to store all matrices generated or downloaded
  all_matrices: List[Path] = []

  def __init__(self, base_path: Path, category: str):
    self.base_path = base_path.resolve()
    self.base_path.mkdir(parents=True, exist_ok=True)
    self.category = category
    self.category_matrices = []

  def get_category_path(self) -> Path:
    """Returns the path for a dataset category folder."""
    path = self.base_path / self.category
    path.mkdir(parents=True, exist_ok=True)
    return path

  def get_suite_sparse_list_path(self) -> Path:
    """Returns the path for SuiteSparse matrices selected by explicit list."""
    return self.get_category_path()

  def get_suite_sparse_range_path(self, min_nnz: int, max_nnz: int, limit: int) -> Path:
    """Returns the path for SuiteSparse matrices selected by range."""
    subfolder = f"SuiteSparse_{min_nnz}_{max_nnz}_{limit}"
    path = self.get_category_path() / subfolder
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
  
  def get_graph500_path(self, matrix: Graph500Matrix) -> Path:
    """Returns the path for a Graph500 matrix."""
    subfolder = 'Graph500'
    mtx_file = f'graph500_{matrix.scale}_{matrix.edge_factor}.mtx'
    path = self.get_category_path() / subfolder / mtx_file
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
  
  def get_parmat_path_and_cli_args(self, matrix: PaRMATMatrix) -> Tuple[Path, List[str]]:
    """Returns the path for a PaRMAT matrix."""
    cli_args = ['-nVertices', matrix.N, '-nEdges', matrix.M]
    params = []
    # if 'a' not in mtx_config:
    #     mtx_config['a'] = mtx_config['b'] = mtx_config['c'] = 0.25
    # if 'a' in mtx_config and 'b' in mtx_config and 'c' in mtx_config:
    #     params.append(f"a{int(1000*mtx_config['a'])}_b{int(1000*mtx_config['b'])}_c{int(1000*mtx_config['c'])}")
    #     cli_args += ['-a', mtx_config['a'], '-b', mtx_config['b'], '-c', mtx_config['c']]
    params.append(f"a{int(1000*matrix.a)}_b{int(1000*matrix.b)}_c{int(1000*matrix.c)}")
    if matrix.noDuplicateEdges:
      params.append("noDup")
      cli_args.append("-noDuplicateEdges")
    if matrix.undirected:
      params.append("undir")
      cli_args.append("-undirected")
    if matrix.noEdgeToSelf:
      params.append("noSelf")
      cli_args.append("-noEdgeToSelf")
    if sorted:
      params.append("sorted")
      cli_args.append("-sorted")
    param_str = "_" + "_".join(params) if params else ""
    matrix_full_name = f"parmat_N{matrix.N}_M{matrix.M}{param_str}.mtx"

    subfolder = 'PaRMAT'
    path = self.get_category_path() / subfolder / matrix_full_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path, cli_args

  def register_matrix_path(self, path: Path, is_bmtx: bool):
    """Registers a matrix file path for tracking."""
    path = path.resolve().with_suffix('.bmtx' if is_bmtx else '.mtx')
    if path.is_file():
      self.category_matrices.append(path)
      self.all_matrices.append(path)
      console.print(f"➡️ [dim cyan]Registered matrix:[/dim cyan] [dim purple]{path}[/dim purple]")
    else:
      console.print(f"⚠️ [yellow]Ignored non-matrix file:[/yellow] [dim purple]{path}[/dim purple]")

  # def register_matrix_paths_from_dir(self, dir_path: Path):
  #   """Recursively registers all `.mtx` files under a directory."""
  #   for mtx_file in dir_path.rglob("*.mtx"):
  #     self.register_matrix_path(mtx_file)

  def write_category_summary(self):
    """Writes a summary of all category collected matrix paths to a file."""
    summary_file = self.base_path / self.category / DatasetManager.MATRICES_SUMMARY_FILENAME
    with open(summary_file, "w") as f:
      for matrix_path in self.category_matrices:
        rel_path = matrix_path.relative_to(self.base_path.parent)
        f.write(str(rel_path) + "\n")
    console.print(f"[green]✅ Summary written to:[/green] [purple]'{summary_file}'[/purple]")

  @staticmethod
  def write_global_summary(base_path: Path):
    """
    Write global summary at <base_path>/matrices_list.txt.
    """
    base_path = base_path.resolve()
    summary_file = base_path / DatasetManager.MATRICES_SUMMARY_FILENAME
    with summary_file.open("w") as f:
      for matrix_path in DatasetManager.all_matrices:
        rel_path = matrix_path.relative_to(base_path.parent)
        f.write(str(rel_path) + "\n")

    console.print(f"[bold cyan]Global summary written to:[/bold cyan] [purple]'{summary_file.absolute()}'[/purple]")

  def check_matrix_status(self, matrix_path: Path, flags: Flags, downloading: bool, matrix_full_name: str) -> Tuple[bool, bool]:
    """
    Check the status of a matrix: if needs to be downloaded/generated and converted.

    Args:
      matrix_path: the file extension will be automatically handled (depending on flags)
      downloading: if true, console logs will say that the matrix is being "downloaded", otherwise, "generated"
      matrix_full_name: just for console logs

    Returns:
      (to_download_or_generate, to_convert)
    """
    mtx_path = matrix_path.with_suffix('.mtx')
    bmtx_path = matrix_path.with_suffix('.bmtx')
    mtx_exists = mtx_path.is_file()
    bmtx_exists = bmtx_path.is_file()

    if flags.binary_mtx and bmtx_exists:
      console.print(f"[yellow]==> \"{matrix_full_name}\" already {'downloaded' if downloading else 'generated'} and converted, skipped[/yellow]")
      return False, False
    elif not flags.binary_mtx and mtx_exists:
      console.print(f"[yellow]==> \"{matrix_full_name}\" already {'downloaded' if downloading else 'generated'}, skipped[/yellow]")
      return False, False

    info = ''
    download = False
    convert = False

    if flags.binary_mtx and mtx_exists and not bmtx_exists:
      info = '==> Converting to BMTX'
      convert = True
    elif not flags.binary_mtx and not mtx_exists:
      info = f"==> {'Downloading' if downloading else 'Generating'}"
      download = True
    elif flags.binary_mtx and not mtx_exists:
      info = f"==> {'Downloading' if downloading else 'Generating'} and Converting to BMTX"
      download = True
      convert = True
    else:
      raise RuntimeError('Invalid state encountered in check_matrix_status')

    console.print(f"[bold cyan]{info} '{matrix_full_name}'[/bold cyan]")

    return download, convert

  def convert_to_bmtx(self, matrix_path: Path, flags: Flags, matrix_full_name: str):
    console.print(f"⚙️ Converting '{matrix_full_name}' to BMTX")
    subprocess.run([MTX_TO_BMTX_CONVERTER, matrix_path.resolve().absolute()] + (['-d'] if flags.binary_mtx_double_vals else []))
    if not flags.keep_mtx:
      os.remove(matrix_path.resolve())
      console.print('Deleted .mtx file')
    console.print('Converted!')


def load_config_file(path: Path) -> Config:
  if not path.exists():
    raise ConfigurationFileNotFoundError(f"YAML configuration cannot be found. File '{path.absolute()}' does not exist.")

  try:
    with open(path, 'r') as f:
        raw_cfg = yaml.safe_load(f)
  except yaml.YAMLError as e:
    console.print(f"[bold red]YAML parsing error:[/bold red] {e}")
    raise ConfigurationFormatError("The configuration file could not be parsed as valid YAML.")

  if not isinstance(raw_cfg, dict) or "path" not in raw_cfg:
    raise ConfigurationFormatError("Top-level YAML must include a 'path' field.")

  try:
    base_path = Path(raw_cfg['path'])
    categories = {}

    for cat_name, cat_data in raw_cfg.items():
      if cat_name == "path":
        continue

      if not isinstance(cat_data, dict):
        raise ConfigurationFormatError(f"Category '{cat_name}' must be a dictionary.")

      generators = cat_data.get("generators", {})
      graph500 = None
      parmat = None

      if "graph500" in generators:
        try:
          graph500 = ConfigGraph500(**generators["graph500"])
        except TypeError as e:
          raise ConfigurationFormatError(f"[{cat_name}] Invalid 'graph500' config: {e}")

      if "parmat" in generators:
        try:
          raw_parmat = generators["parmat"]
          defaults = None
          if "defaults" in raw_parmat:
            defaults = PaRMATMatrixPartial(**raw_parmat["defaults"])
          matrices = [PaRMATMatrixPartial(**m) for m in raw_parmat.get("matrices", [])]
          parmat = ConfigPaRMAT(_defaults=defaults, _matrices=matrices)
        except TypeError as e:
          raise ConfigurationFormatError(f"[{cat_name}] Invalid 'parmat' config: {e}")

      suite_range = None
      if "suite_sparse_matrix_range" in cat_data:
        try:
          suite_range = ConfigSuiteSparseRange(**cat_data["suite_sparse_matrix_range"])
        except TypeError as e:
          raise ConfigurationFormatError(f"[{cat_name}] Invalid 'suite_sparse_matrix_range': {e}")
        
      suite_list = cat_data.get("suite_sparse_matrix_list", [])
      parsed_suite_list = []
      for m in suite_list:
        ms = m.strip().split('/')
        if len(ms) != 2:
          raise ConfigurationFormatError(f"[{cat_name}] Invalid 'suite_sparse_matrix_list': this must be a list of string in the form 'mtx_group/mtx_name'.\nInvalid value '{m}'")
        parsed_suite_list.append((ms[0],ms[1]))

      category = ConfigCategory(
        generators=ConfigGenerators(graph500=graph500, parmat=parmat),
        suite_sparse_matrix_list=parsed_suite_list,
        suite_sparse_matrix_range=suite_range
      )

      categories[cat_name] = category

    return Config(path=base_path, categories=categories)

  except ConfigurationFormatError as e:
    console.print(f"[bold red]Configuration error:[/bold red] {e}")
    raise

  except Exception as e:
    console.print(f"[bold red]Unexpected error while loading config:[/bold red] {e}")
    raise ConfigurationFormatError("An unknown error occurred while loading the configuration.")

