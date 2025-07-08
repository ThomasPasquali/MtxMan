import os
import subprocess
from pathlib import Path

import ssgetpy
from rich.console import Console

from mtxman.core.core import ConfigCategory, DatasetManager, Flags
from mtxman.core.dependencies import MTX_TO_BMTX_CONVERTER

console = Console()

class SuiteSparseMatrixHandler:
  def __init__(
    self,
    base_path: Path,
    dataset_manager: DatasetManager,
    flags: Flags,
  ):
    """
    Handles downloading and converting SuiteSparse matrices.

    Args:
        
        dataset_manager (DatasetManager): Manages dataset file paths.
        category (str): Dataset category for configuration and path structure.
    """
    self.flags = flags
    self.dm = dataset_manager
    self.base_path = base_path

  def _get_matrix_paths(self, matrix) -> tuple[str, Path, Path, Path]:
      full_name = f"{matrix.group}/{matrix.name}"
      group_dir = self.base_path / matrix.group
      matrix_dir = group_dir / matrix.name
      matrix_dir.mkdir(parents=True, exist_ok=True)

      mtx_path = matrix_dir / f"{matrix.name}.mtx"
      bmtx_path = matrix_dir / f"{matrix.name}.bmtx"

      return full_name, group_dir, matrix_dir, mtx_path

  def sync_matrix(self, matrix):
    """
    Download and convert a SuiteSparse matrix if necessary.

    Args:
      matrix: A SuiteSparse matrix object returned from ssgetpy.

    Returns:
      bool: True if the matrix was downloaded or converted, False otherwise.
    """
    full_name, group_dir, matrix_dir, mtx_path = self._get_matrix_paths(matrix)

    download, convert = self.dm.check_matrix_status(mtx_path, self.flags, True, full_name)

    if download:
      matrix_url = matrix.url('MM')
      tar_file_path = group_dir / f"{matrix.name}.tar.gz"

      os.system(f"wget -O {tar_file_path} {matrix_url}")
      os.system(f"tar -xzf {tar_file_path} -C {group_dir}")

      extracted_mtx = group_dir / f"{matrix.name}.mtx"
      if extracted_mtx.exists():
        extracted_mtx.rename(mtx_path)

      tar_file_path.unlink()

    if not self.flags.keep_all_files:
      for file in matrix_dir.glob("*.mtx"):
        if file.name != f"{matrix.name}.mtx":
          file.unlink()

    if convert and self.flags.binary_mtx:
      self.dm.convert_to_bmtx(mtx_path, self.flags, full_name)
      
    self.dm.register_matrix_path(mtx_path, self.flags.binary_mtx)

def download_list(
  config: ConfigCategory,
  flags: Flags,
  dataset_manager: DatasetManager,
):
  """
  Download a configured list of SuiteSparse matrices.

  Returns:
      dict: Mapping of matrix full names to file paths.
  """
  matrix_list = config.suite_sparse_matrix_list

  handler = SuiteSparseMatrixHandler(
    base_path=dataset_manager.get_suite_sparse_list_path(),
    dataset_manager=dataset_manager,
    flags=flags,
  )

  for group, name in matrix_list:
    full_name = f'{group}/{name}'
    console.print(f"[cyan]🔎 Checking matrix: \"{full_name}\"[/cyan]")
    matrices = ssgetpy.search(name=name, limit=1)

    if not matrices:
      console.print(f"[red]{full_name} not found in SuiteSparse, skipped[/red]")
      continue

    matrix = matrices[0]
    if matrix.name == name:
      handler.sync_matrix(matrix)
    else:
      console.print(f"[red]{name} matched but was not an exact match, skipped[/red]")


def download_range(
  config: ConfigCategory,
  flags: Flags,
  dataset_manager: DatasetManager,
):
  """
  Download a range of SuiteSparse matrices based on NNZ constraints.

  Returns:
      dict: Mapping of matrix full names to file paths.
  """
  if not config.suite_sparse_matrix_range:
    return
  
  range = config.suite_sparse_matrix_range

  matrices = ssgetpy.fetch(nzbounds=(range.min_nnzs, range.max_nnzs), limit=range.limit, dry_run=True)
  handler = SuiteSparseMatrixHandler(
    base_path=dataset_manager.get_suite_sparse_range_path(range.min_nnzs, range.max_nnzs, range.limit),
    dataset_manager=dataset_manager,
    flags=flags,
  )

  for matrix in matrices:
    handler.sync_matrix(matrix)

