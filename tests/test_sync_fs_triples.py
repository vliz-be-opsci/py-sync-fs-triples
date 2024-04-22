#! /usr/bin/env python
""" test_sync_fs_triples
tests concerning the service wrapper for sembench "SyncFsTriples"
"""
import shutil

import pytest
from conftest import TEST_INPUT_FOLDER
from util4tests import log, run_single_test

from syncfstriples import SyncFsTriples


@pytest.mark.usefixtures("store_builds", "syncfolders")
def test_service_wrapper(store_builds, syncfolders):
    base = "urn:sync:via-wrapper:"
    log.debug(f"{base=}")

    def inbase(ng):
        return ng.startswith(base)

    for store_build, syncpath in zip(store_builds, syncfolders):
        sft: SyncFsTriples = SyncFsTriples(
            str(syncpath), base, *store_build.store_info
        )

        # new instances are created inside the service wrapper,
        # no need to use the builder methods from the fixture
        rdf_store = sft.rdfstore

        sft.process()
        ng_set = set(filter(inbase, rdf_store.named_graphs))
        assert len(ng_set) == 0

        shutil.copytree(
            TEST_INPUT_FOLDER, syncpath / "input", dirs_exist_ok=True
        )
        file_set = set(TEST_INPUT_FOLDER.glob("**/*"))
        sft.process()
        ng_set = set(filter(inbase, rdf_store.named_graphs))
        log.debug(f"{set(rdf_store.named_graphs)=}")
        log.debug(f"{ng_set=}")
        assert len(ng_set) == len(file_set)


if __name__ == "__main__":
    run_single_test(__file__)
