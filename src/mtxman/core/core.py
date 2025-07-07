import yaml
from typing import List, Tuple, Union
from pathlib import Path
from rich.console import Console
from dataclasses import dataclass

from mtxman.exceptions import ConfigurationFileNotFoundError, ConfigurationFormatError

console = Console()

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Union, Optional

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
    path.mkdir(parents=True, exist_ok=True)
    return path

  def register_matrix_path(self, path: Path):
    """Registers a matrix file path for tracking."""
    path = path.resolve()
    if path.is_file() and path.suffix == ".mtx":
      self.category_matrices.append(path)
      self.all_matrices.append(path)
      console.print(f"[dim cyan]↪ Registered matrix:[/dim cyan] {path}")
    else:
      console.print(f"[yellow]⚠️ Ignored non-matrix file:[/yellow] {path}")

  def register_matrix_paths_from_dir(self, dir_path: Path):
    """Recursively registers all `.mtx` files under a directory."""
    for mtx_file in dir_path.rglob("*.mtx"):
      self.register_matrix_path(mtx_file)

  def write_category_summary(self):
    """Writes a summary of all category collected matrix paths to a file."""
    summary_file = self.base_path / DatasetManager.MATRICES_SUMMARY_FILENAME
    with open(summary_file, "w") as f:
      for matrix_path in self.category_matrices:
        rel_path = matrix_path.relative_to(self.base_path.parent)
        f.write(str(rel_path) + "\n")
    console.print(f"[green]✓ Summary written to:[/green] {summary_file}")

  @staticmethod
  def write_global_summary(base_path: Path):
    """
    Write global summary at <base_path>/matrices_list.txt.
    """
    summary_file = base_path / DatasetManager.MATRICES_SUMMARY_FILENAME
    with summary_file.open("w") as f:
      for p in DatasetManager.all_matrices:
        f.write(str(p) + "\n")

    console.print(f"\n[bold cyan]Matrix file paths written to '{summary_file.absolute()}'[/bold cyan]")

@dataclass
class ConfigGraph500:
  scale: Union[List[int], int]
  edge_factor: Union[List[int], int]


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

