from dataclasses import dataclass
import shutil
import subprocess
import zipfile
import requests
from pathlib import Path
from rich.console import Console
from typing import Optional, List, Tuple, Union

from mtxman.exceptions import DependencyError

console = Console()

DEPS_DIR = Path(__file__).resolve().parent.parent / 'deps'

MTX_TO_BMTX_CONVERTER = DEPS_DIR / 'distributed_mmio/build/mtx_to_bmtx'

@dataclass
class DependencyManager:
  @staticmethod
  def install(
    name: str,
    url: str,
    subdir: Optional[str] = None,
    branch: str = "main",
    build_commands: Optional[List[Union[Tuple[Path, List[str]], List[str]]]] = None,
    force: bool = False,
  ) -> Path:
    """
    Downloads and builds a dependency.

    Parameters:
    - name: folder name to extract to
    - url: base GitHub URL (e.g., https://github.com/user/repo)
    - subdir: optional subdirectory inside the archive to treat as root
    - branch: git branch to download from
    - build_commands: list of commands to run for building (e.g., [["make"]])
    - force: if True, re-download and rebuild
    """
    DEPS_DIR.mkdir(exist_ok=True, parents=True)
    target_dir = DEPS_DIR / name

    if force and target_dir.exists():
      console.print(f"[yellow]Removing existing dependency '{name}'...[/yellow]")
      shutil.rmtree(target_dir)

    if target_dir.exists():
      # console.print(f"[green]✓ Dependency '{name}' already exists.[/green]")
      return target_dir

    zip_url = f"{url}/archive/refs/heads/{branch}.zip"
    zip_path = DEPS_DIR / f"{name}.zip"

    console.print(f"📦 [blue]Downloading '{name}' from {zip_url}...[/blue]")
    try:
      response = requests.get(zip_url)
      response.raise_for_status()
      with open(zip_path, "wb") as f:
          f.write(response.content)
    except Exception as e:
      raise DependencyError(f"Failed to download {name} from {zip_url}: {e}")

    console.print(f"📁 [cyan]Extracting '{name}'...[/cyan]")
    try:
      with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(DEPS_DIR)
    except zipfile.BadZipFile as e:
      raise DependencyError(f"Failed to extract ZIP archive for {name}: {e}")
    finally:
      zip_path.unlink(missing_ok=True)

    extracted_dir = DEPS_DIR / f"{url.rstrip('/').split('/')[-1]}-{branch}"
    if subdir:
      extracted_dir = extracted_dir / subdir

    if not extracted_dir.exists():
      raise DependencyError(f"Extracted directory '{extracted_dir}' not found")

    extracted_dir.rename(target_dir)

    if build_commands:
      console.print(f"🔧 [yellow]Building '{name}'...[/yellow]")
      for command in build_commands:
        try:
          if isinstance(command, tuple):
            subprocess.run(command[1], cwd=target_dir / command[0], check=True, stdout=subprocess.DEVNULL)
          else:
            subprocess.run(command, cwd=target_dir, check=True, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise DependencyError(f"Build failed for {name}: {e}")

      console.print(f"[green]✓ Build complete for '{name}'.[/green]")

    return target_dir

def download_and_build_mtx_to_bmtx_converter():
  DependencyManager.install(
    name="distributed_mmio",
    url="https://github.com/HicrestLaboratory/distributed_mmio",
    build_commands=[
      ["cmake", "-B", "build"],
      (Path('build'), ["make", "mtx_to_bmtx"]),
    ],
  )