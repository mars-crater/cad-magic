"""Rebuild both Lesson 2 models and verify their exported geometry."""
from pathlib import Path

import cadquery as cq

import keychain
import terrain


def main():
    for exercise in (terrain, keychain):
        path = Path(__file__).with_name(f"{exercise.__name__}.step")
        cq.exporters.export(exercise.build(), str(path))
        part = cq.importers.importStep(str(path))
        assert part.val().isValid() and len(part.solids().vals()) == 1
        exercise.verify(part)
        print(f"{path.name}: valid solid; reference and feature checks passed")


if __name__ == "__main__":
    main()
