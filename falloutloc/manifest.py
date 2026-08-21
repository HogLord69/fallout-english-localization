"""Record of what an install actually did, so it can be undone exactly.

`.orig` backups alone are not enough: most dialogue overrides are files the
installer *creates*, with no previous version to back up. Reverting has to
delete those, and only those -- so the install writes down which paths it
created and which it replaced.

The manifest lives in the install root and accumulates across runs.
"""
import json
import os

NAME = ".falloutloc-manifest.json"


class Manifest:
    def __init__(self, install):
        self.install = install
        self.path = os.path.join(install, NAME)
        self.created = set()
        self.replaced = set()
        if os.path.exists(self.path):
            try:
                data = json.load(open(self.path, encoding="utf-8"))
                self.created = set(data.get("created", []))
                self.replaced = set(data.get("replaced", []))
            except (ValueError, OSError):
                pass

    def _rel(self, path):
        return os.path.relpath(path, self.install).replace("\\", "/")

    def note(self, path, existed):
        """Record a write. `existed` is whether the file was there beforehand."""
        rel = self._rel(path)
        if existed:
            # A path we once created and now replace is still ours to delete.
            if rel not in self.created:
                self.replaced.add(rel)
        else:
            self.created.add(rel)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"created": sorted(self.created),
                       "replaced": sorted(self.replaced)}, f, indent=1)
