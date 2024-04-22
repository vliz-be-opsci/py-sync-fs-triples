#!/usr/bin/env python
""" test_main_cli
tests concerning the cli call functioning
"""
import shutil
from uuid import uuid4

import pytest
from conftest import TEST_INPUT_FOLDER
from util4tests import log, run_single_test

from syncfstriples.__main__ import main


@pytest.mark.usefixtures("store_builds", "syncfolders")
def test_main(store_builds: tuple, syncfolders: tuple):
    base: str = f"urn:sync:test-main:{uuid4()}:"
    for store_build, syncpath in zip(store_builds, syncfolders):
        root_path = syncpath / "input"
        shutil.copytree(TEST_INPUT_FOLDER, root_path, dirs_exist_ok=True)
        argsline: str = f"--root {str(root_path)} --base {base}"
        store_info: tuple = store_build.store_info
        store_part = " ".join(store_info)
        if (len(store_part)) > 0:
            argsline += f" --store {store_part}"

        log.debug(f"testing equivalent of python -msyncfstriples {argsline}")
        args_list: list = argsline.split(" ")
        main(*args_list)  # pass as individual arguments

        # TODO consider some extra assertions on the result


if __name__ == "__main__":
    run_single_test(__file__)
