#! /usr/bin/env python
""" test_sync_fs_triples
tests concerning the service wrapper for sembench "SyncFsTriples"
"""
import os
import shutil

import pytest
from conftest import TEST_INPUT_FOLDER
from pyrdfstore.store import URIRDFStore
from util4tests import log, run_single_test

from syncfstriples import SyncFsTriples


@pytest.mark.usefixtures("rdf_stores", "syncfolders")
def test_service_wrapper(rdf_stores, syncfolders):
    base = "urn:sync:via-wrapper:"
    log.debug(f"{base=}")
    inbase = lambda ng: ng.startswith(base)

    for rdf_store, syncpath in zip(rdf_stores, syncfolders):
        read_uri, write_uri = None, None
        if isinstance(rdf_store, URIRDFStore):
            read_uri = os.getenv("TEST_SPARQL_READ_URI", None)
            write_uri = os.getenv("TEST_SPARQL_WRITE_URI", read_uri)
        sft: SyncFsTriples = SyncFsTriples(
            str(syncpath), base, read_uri, write_uri
        )

        # new instances are created inside the service wrapper, the fixtures are ignored!
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
        assert len(ng_set) == len(file_set)


if __name__ == "__main__":
    run_single_test(__file__)
