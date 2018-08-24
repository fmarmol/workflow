import os
import luigi

class DirectoryTarget(luigi.Target):
    """
    Subclass of luigi.Target to manage directory
    """
    def __init__(self, path):
        self.path = path
        self.targets = []

    def exists(self):
        return os.path.exists(self.path)

    def get_targets(self):
        """
        Return all files in the directory as luigi.LocalTarget
        """
        targets = []
        for dirpath, dirname, files in os.walk(self.path):
            for filename in files:
                filepath = os.path.join(dirpath, filename)
                targets.append(luigi.LocalTarget(path=filepath, format=luigi.format.Nop))
        return targets
