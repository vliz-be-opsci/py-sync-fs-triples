#! /usr/bin/env python
""" test_fname_ng_conversion
tests our expectations on translating filenames to named_graphs and back
"""
from typing import Iterable

import pytest
from conftest import TEST_FOLDER
from pyrdfstore import RDFStore
from util4tests import log, run_single_test

from syncfstriples.service import GraphNameMapper, sync_addition


def test_fname_to_ng():
    base: str = "urn:sync:"
    nmapper: GraphNameMapper = GraphNameMapper(base=base)

    # Test case 1: Valid filename
    fname = "example.txt"
    expected_ng = "urn:sync:example.txt"
    assert nmapper.key_to_ng(fname) == expected_ng

    # Test case 2: Filename with special characters
    fname = "file name with spaces.txt"
    expected_ng = "urn:sync:file%20name%20with%20spaces.txt"
    assert nmapper.key_to_ng(fname) == expected_ng

    # Test case 3: Empty filename
    fname = ""
    expected_ng = "urn:sync:"
    assert nmapper.key_to_ng(fname) == expected_ng

    # Add more test cases as needed


def test_ng_to_fname():
    base: str = "urn:sync:"
    nmapper: GraphNameMapper = GraphNameMapper(base=base)

    # Test case 1: Valid named graph URN
    ng = "urn:sync:example.txt"
    expected_fname = "example.txt"
    assert nmapper.ng_to_key(ng) == expected_fname

    # Test case 2: Named graph URN with special characters
    ng = "urn:sync:file%20name%20with%20spaces.txt"
    expected_fname = "file name with spaces.txt"
    assert nmapper.ng_to_key(ng) == expected_fname

    # Add more test cases as needed


@pytest.mark.usefixtures("rdf_stores")
def test_get_keys_in_store(rdf_stores: Iterable[RDFStore]):
    for rdf_store in rdf_stores:
        rdf_store_type: str = type(rdf_store).__name__
        # Test case 1: Empty store
        for key in rdf_store.keys:
            rdf_store.forget_graph_for_key(key)
        assert rdf_store.keys == []

        # Test case 2: Store with one named graph
        relative = "input/63523.ttl"
        sync_addition(rdf_store, TEST_FOLDER / relative, TEST_FOLDER)
        keys_in_store: Iterable[str] = rdf_store.keys
        assert keys_in_store == [relative]
        log.debug(f"{rdf_store_type} :: {keys_in_store=}")

        # Add more test cases as needed


if __name__ == "__main__":
    run_single_test(__file__)
