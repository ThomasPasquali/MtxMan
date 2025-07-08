import subprocess
from rich.console import Console

from mtxman.core import dependencies
from mtxman.core.core import ConfigCategory, DatasetManager, Flags

console = Console()

# def set_env(file_name):
#   os.environ["REUSEFILE"] = "1"
#   os.environ["TMPFILE"] = file_name
#   os.environ["SKIP_BFS"] = "1"


# def unset_env():
#   del os.environ["REUSEFILE"]
#   del os.environ["TMPFILE"]
#   del os.environ["SKIP_BFS"]


def generate(
  config: ConfigCategory,
  flags: Flags,
  dataset_manager: DatasetManager,
):
  if not config.generators or not config.generators.graph500:
    return
  
  matrices = config.generators.graph500.get_matrices()
  
  if len(matrices) > 0:
    dependencies.download_and_build_graph500_generator()

  for matrix in matrices:
    mtx_path = dataset_manager.get_graph500_path(matrix)

    generate, convert = dataset_manager.check_matrix_status(mtx_path, flags, False, mtx_path.stem)
    
    if generate:
      # set_env(file_name)  # This is probably not needed anymore
      try:
        console.print(f"==> ⚙️ Generating Graph500 graph with (scale, edge factor) = ({matrix.scale}, {matrix.edge_factor})")
        subprocess.run([f'./{dependencies.GRAPH500_GENERATOR.stem}', str(matrix.scale), str(matrix.edge_factor), str(mtx_path.resolve().absolute())], cwd=dependencies.GRAPH500_GENERATOR.parent, check=True)
      except subprocess.CalledProcessError as e:
        console.print(f"[red]Graph generation failed:[/red] {e}")
        # unset_env()
        continue
      # unset_env()
      console.print('==> Generated!')

    if convert and flags.binary_mtx:
      dataset_manager.convert_to_bmtx(mtx_path, flags, mtx_path.stem)

    dataset_manager.register_matrix_path(mtx_path, flags.binary_mtx)
      