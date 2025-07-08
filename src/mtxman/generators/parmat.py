import os
import re
import subprocess
from rich.console import Console

from mtxman.core import dependencies
from mtxman.core.core import ConfigCategory, DatasetManager, Flags

console = Console()

def generate(
  config: ConfigCategory,
  flags: Flags,
  dataset_manager: DatasetManager,
):
  if not config.generators or not config.generators.parmat:
    return
  
  matrices = config.generators.parmat.get_matrices()

  if len(matrices) > 0:
    dependencies.download_and_build_parmat_generator()

  for matrix in matrices:
    mtx_path, cli_args = dataset_manager.get_parmat_path_and_cli_args(matrix)
    generate, convert = dataset_manager.check_matrix_status(mtx_path, flags, False, mtx_path.stem)
      
    if generate:
      try:
        console.print(f"==> ⚙️ Generating PaRMAT matrix \"{mtx_path.stem}\"")
        output_path = os.path.relpath(mtx_path.resolve(), dependencies.PARMAT_GENERATOR.parent)
        cli_args = [str(v) for v in ([f'./{dependencies.PARMAT_GENERATOR.stem}'] + cli_args + ['-output', output_path])]
        print(' '.join(cli_args))
        subprocess.run(cli_args, cwd=dependencies.PARMAT_GENERATOR.parent, check=True)
        with open(mtx_path.resolve().absolute(), 'r+') as f:
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
          f.write(f'{matrix.N} {matrix.N} {matrix.M}\n')
          f.write('\n'.join(coords))
      except subprocess.CalledProcessError as e:
        print(f"Matrix generation failed: {e}")
        continue
      print('==> Generated!')

    if convert and flags.binary_mtx:
      dataset_manager.convert_to_bmtx(mtx_path, flags, mtx_path.stem)

    dataset_manager.register_matrix_path(mtx_path, flags.binary_mtx)

