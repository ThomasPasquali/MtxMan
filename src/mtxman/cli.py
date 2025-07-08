import importlib
from pathlib import Path
import typer
from typing_extensions import Annotated
from typing import List, Optional
from rich.console import Console

from mtxman.exceptions import MtxManError
import mtxman.core.core as core
import mtxman.core.dependencies as dependencies
import mtxman.generators.graph500 as graph500_generator
import mtxman.generators.parmat as parmat_generator
import mtxman.downloaders.suite_sparse as suite_sparse_downloader

app = typer.Typer(help="A utility that simplifies the download and generation of Matrix Market (`.mtx`) files.", add_completion=True)
console = Console()

def version_callback(value: bool):
  if not value:
    return
  try:
    console.print(f"MtxMan version: [bold cyan]{importlib.metadata.version('mtxman')}[/bold cyan]")
  except importlib.metadata.PackageNotFoundError:
    console.print("[bold red]Error:[/bold red] Could not determine the version. Is MtxMan installed correctly?")
    raise typer.Exit(1)
  raise typer.Exit()

@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True, help="Show the version and exit."),
  ):
  """
  MtxMan CLI main callback.
  Handles global exceptions.
  """
  try:
    # This is a placeholder for any pre-command logic.
    # The actual command execution happens after this.
    pass
  except MtxManError as e:
    console.print(f"[bold red]{e}[/bold red] ")
    raise typer.Exit(code=1)

@app.command()
def sync(
  file: Annotated[str, typer.Argument(help='Path to the YAML configuration file')],
  skip: list[str] = typer.Option([], "--skip", "-s", help="List of categories to skip (e.g., '--skip category1 --skip category2')."),
  keep_all_files: bool = typer.Option(False, "--keep_all_files", "-ka", help="Keep all files in SuiteSparse archives."),
  binary_mtx: bool = typer.Option(False, "--binary-mtx", "-bmtx", help="Generate binary '.bmtx' files."),
  keep_mtx: bool = typer.Option(False, "--keep-mtx", "-kmtx", help="(Used with --binary-mtx) Keep original '.mtx' files."),
  binary_mtx_double_vals: bool = typer.Option(False, "--binary-mtx-double-vals", "-bmtxd", help="(Used with --binary-mtx) Store values using 8 bytes instead of 4."),
  skip_metadata: bool = typer.Option(False, "--skip-metadata", "-nometa", help="If set, the 'matrices_metadata.csv' file will not be generated.")
):
  """
  Synchronizes the matrices configured via '[FILE]'
  """
  config = core.load_config_file(Path(file))
  flags = core.Flags(
    binary_mtx=binary_mtx,
    binary_mtx_double_vals=binary_mtx_double_vals,
    keep_mtx=keep_mtx,
    keep_all_files=keep_all_files,
  )
  
  if binary_mtx:
    dependencies.download_and_build_mtx_to_bmtx_converter()
    
  for category_name, category_config in config.categories.items():
    if category_name in skip:
      console.print(f'[bold yellow]>> Skipping category "{category_name}"[/bold yellow]')
      continue

    console.print(f'[bold green]>> Syncing category "{category_name}"...[/bold green]')

    category_datasets_manager = core.DatasetManager(config.path, category_name)

    parmat_generator.generate(
      config=category_config,
      flags=flags,
      dataset_manager=category_datasets_manager,
    )
    graph500_generator.generate(
      config=category_config,
      flags=flags,
      dataset_manager=category_datasets_manager
    )
    suite_sparse_downloader.download_list(
      config=category_config,
      flags=flags,
      dataset_manager=category_datasets_manager
    )
    suite_sparse_downloader.download_range(
      config=category_config,
      flags=flags,
      dataset_manager=category_datasets_manager
    )

    category_datasets_manager.write_category_summary()

    console.print(f'[bold green]>> Category "{category_name}", up to date![/bold green]\n')

  core.DatasetManager.write_global_summary(config.path)

  if not skip_metadata:
    config.export_matrices_metadata_csv('matrices_metadata.csv')

pipe_sep = '|'
@app.command('update-deps')
def update_deps(
  deps: List[str] = typer.Option(None, help=f'Available options "{pipe_sep.join([d.value for d in dependencies.DEPS])}". Default: all. Example: "--deps {dependencies.DEPS.DISTRIBUTED_MMIO.value} --deps {dependencies.DEPS.GRAPH500.value}"')
):
  """
  Explicitly Build or Rebuild dependencies.
  """
  if not deps:
    deps = [d.value for d in dependencies.DEPS]
  for d in deps:
    match dependencies.DEPS(d):
      case dependencies.DEPS.DISTRIBUTED_MMIO:
        dependencies.download_and_build_mtx_to_bmtx_converter(force=True)
      case dependencies.DEPS.GRAPH500:
        dependencies.download_and_build_graph500_generator(force=True)
      case dependencies.DEPS.PARMAT:
        dependencies.download_and_build_parmat_generator(force=True)


if __name__ == "__main__":
  app()
