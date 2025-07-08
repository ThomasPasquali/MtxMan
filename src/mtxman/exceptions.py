class MtxManError(Exception):
  """Base exception for MtxMan."""
  pass

class ConfigurationFileNotFoundError(MtxManError):
  """Raised when the YAML configuration cannot be found."""
  def __init__(self, message):
    self.message = message
    super().__init__(self.message)

class ConfigurationFormatError(MtxManError):
  """Raised when the YAML configuration file is not formatted properly."""
  def __init__(self, message):
    self.message = message
    super().__init__(self.message)

class DependencyError(MtxManError):
  """Raised when a dependency fails to download or build."""
  def __init__(self, message):
    self.message = message
    super().__init__(self.message)