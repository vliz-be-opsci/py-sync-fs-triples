import os
import pathlib

import pytest
from pyrdfstore.store import RDFStore
from rdflib import Graph
from util4tests import run_single_test


def test_fname_to_ng():
    from syncfstriples.service import fname_to_ng

    # Test case 1: Valid filename
    fname = "example.txt"
    expected_ng = "urn:sync:example.txt"
    assert fname_to_ng(fname) == expected_ng

    # Test case 2: Filename with special characters
    fname = "file name with spaces.txt"
    expected_ng = "urn:sync:file%20name%20with%20spaces.txt"
    assert fname_to_ng(fname) == expected_ng

    # Test case 3: Empty filename
    fname = ""
    expected_ng = "urn:sync:"
    assert fname_to_ng(fname) == expected_ng

    # Add more test cases as needed


def test_ng_to_fname():
    from syncfstriples.service import ng_to_fname

    # Test case 1: Valid named graph URN
    ng = "urn:sync:example.txt"
    expected_fname = "example.txt"
    assert ng_to_fname(ng) == expected_fname

    # Test case 2: Named graph URN with special characters
    ng = "urn:sync:file%20name%20with%20spaces.txt"
    expected_fname = "file name with spaces.txt"
    assert ng_to_fname(ng) == expected_fname

    # Add more test cases as needed


@pytest.mark.usefixtures("memorystore")
def test_get_fnames_in_store_ttl(memorystore):
    from syncfstriples.service import get_fnames_in_store

    # Test case 1: Empty store
    expected_result = []
    assert get_fnames_in_store(memorystore) == expected_result

    # Test case 2: Store with one named graph
    # add a graph to the memorystore
    to_add_file = os.path.join(os.path.dirname(__file__), "input", "63523.ttl")
    memorystore.insert(
        Graph().parse(to_add_file, format="turtle"), "urn:sync:63523.ttl"
    )

    assert get_fnames_in_store(memorystore) == ["63523.ttl"]

    # Add more test cases as needed

@pytest.mark.usefixtures("memorystore")
def test_get_fnames_in_store_jsonld(memorystore):
    from syncfstriples.service import get_fnames_in_store

    # Test case 1: Empty store
    expected_result = []
    assert get_fnames_in_store(memorystore) == expected_result

    # Test case 2: Store with one named graph
    # add a graph to the memorystore
    to_add_file = os.path.join(os.path.dirname(__file__), "input", "3293.jsonld")
    memorystore.insert(
        Graph().parse(to_add_file, format="json-ld"), "urn:sync:3293.jsonld"
    )

    assert get_fnames_in_store(memorystore) == ["3293.jsonld"]

    # Add more test cases as needed

    
@pytest.mark.usefixtures("memorystore")
def test_perform_sync(memorystore):
    from syncfstriples.service import get_fnames_in_store, perform_sync
    
    path_test = pathlib.Path(os.path.dirname(__file__), "input")
    # list all files with full path
    file_names = [str(p) for p in path_test.glob("**/*") if p.is_file()]
    # perform_sync(path_test, memorystore)
    perform_sync(path_test, memorystore)
    
    assert get_fnames_in_store(memorystore) == file_names

    

if __name__ == "__main__":
    run_single_test(__file__)
