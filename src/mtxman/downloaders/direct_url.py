import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from mtxman.core.core import ConfigCategory, DatasetManager, Flags
import shutil
import urllib.parse

console = Console()    

def download_url_list(
  config: ConfigCategory,
  flags: Flags,
  dataset_manager: DatasetManager,
):
  """
  Download a list of matrices from the provided URLs.
  """
  urls = config.direct_urls
  if not urls:
    return
  
  allowed_extensions = ('.mtx', '.bmtx', '.zip', '.tar', '.tar.gz', '.tgz')

  for url_dict in urls:
    url = url_dict['url']
    filename = url_dict['filename']
    rename = url_dict.get('rename')
    
    parsed_url = urllib.parse.urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc):
        console.print(f"[red]Invalid URL:[/red] {url}")
        continue
    if not any(parsed_url.path.endswith(ext) for ext in allowed_extensions):
        console.print(f"[red]URL does not point to a supported file type:[/red] {url}")
        continue

    mtx_path = dataset_manager.get_direct_url_matrix_path(filename, rename)
    download, convert = dataset_manager.check_matrix_status(mtx_path, flags, True, mtx_path.stem)

    if download:
      scratch_path = Path(config.scratch_path)
      download_filename = Path(Path(parsed_url.path).parts[-1])
      download_filepath = scratch_path / download_filename

      os.system(f"wget -O '{download_filepath}' '{url}'")
      # Uncompress if needed
      if download_filename.suffix in ['.zip', '.gz', '.tgz', '.tar']:
        if download_filename.name.endswith('.zip'):
          os.system(f"unzip -o '{download_filepath}' -d '{scratch_path}'")
        elif download_filename.name.endswith('.tar.gz') or download_filename.name.endswith('.tgz'):
          os.system(f"tar -xzf '{download_filepath}' -C '{scratch_path}'")
        elif download_filename.name.endswith('.tar'):
          os.system(f"tar -xf '{download_filepath}' -C '{scratch_path}'")
          
        if download_filepath.exists():
          download_filepath.unlink()
          
        # Remove all suffixes from download_filename
        base_name = download_filename.name.split('.')[0]
        downloaded_file = scratch_path / base_name / filename
      else:
        downloaded_file = scratch_path / filename
        
      if (not downloaded_file.with_suffix('.mtx').exists()) and (not downloaded_file.with_suffix('.bmtx').exists()):
        console.print(f"[yellow]Warning: Downloaded file '{filename}.{{mtx|bmtx}}' not found in '{downloaded_file.parent}'.[/yellow]")
        continue
      else:
        if rename:
          new_path = downloaded_file.parent / rename
          downloaded_file.rename(new_path)
          console.print(f"[green]Renamed '{filename}' to '{rename}'.[/green]")

      if not flags.keep_all_files:
        for file in downloaded_file.parent.glob("*.{mtx,bmtx}"):
          if file.name != f"{downloaded_file.name}.mtx" and file.name != f"{downloaded_file.name}.bmtx":
            file.unlink()
    
      # Move the downloaded file (or its folder) to match mtx_path
      target_path = mtx_path.parent
      target_path.mkdir(parents=True, exist_ok=True)
      
      if downloaded_file.parent.name == scratch_path.name:
        downloaded_file.replace(mtx_path)
      else:
        # Move all contents from the downloaded folder to target_path
        for item in downloaded_file.parent.iterdir():
          dest = target_path / item.name
          if item.is_file():
            item.replace(dest)
          elif item.is_dir():
            shutil.move(str(item), str(dest))
        # Remove the now-empty downloaded folder
        downloaded_file.parent.rmdir()

    if convert and flags.binary_mtx:
      dataset_manager.convert_to_bmtx(mtx_path, flags, mtx_path.stem)
      
    dataset_manager.register_matrix_path(mtx_path, flags.binary_mtx)