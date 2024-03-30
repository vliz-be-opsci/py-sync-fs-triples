#! /usr/bin/env python
""" test_sync
tests concerning the actual core sync expectations
"""
from uuid import uuid4

import pytest
from conftest import make_sample_graph
from util4tests import log, run_single_test

from syncfstriples.service import (
    GraphFileNameMapper,
    format_from_filepath,
    perform_sync,
    relative_pathname,
)


@pytest.mark.usefixtures("rdf_stores", "syncfolders")
def test_perform_sync(rdf_stores, syncfolders):
    base = f"urn:test-sync:{uuid4()}"
    nmapper = GraphFileNameMapper(base)
    inbase = lambda ng: ng.startswith(base)

    extensions = ["ttl", "jsonld"]
    num = len(extensions)
    graphsize = 5
    graphs = [
        make_sample_graph(range(i * 10, i * 10 + graphsize))
        for i in range(1, 1 + num)
    ]
    sparql = "select * where {?s ?p ?o .}"

    for rdf_store, syncpath in zip(rdf_stores, syncfolders):
        rdf_store_type: str = type(rdf_store).__name__
        # 0. nothing there at the start
        assert len(nmapper.get_fnames_in_store(rdf_store)) == 0
        # now sync an empty folder
        log.debug(f"{rdf_store_type} :: sync empty folder")
        perform_sync(syncpath, rdf_store, nmapper)
        # still nothing
        assert len(nmapper.get_fnames_in_store(rdf_store)) == 0

        # 1. check addition -- so create some files
        relfpaths = list()
        for ext, g, n in zip(extensions, graphs, range(1, 1 + num)):
            fpath = syncpath / f"gen-{n:02d}.{ext}"
            g.serialize(
                destination=str(fpath), format=format_from_filepath(fpath)
            )
            relfpaths.append(relative_pathname(fpath, syncpath))
        # now sync again
        log.debug(f"{rdf_store_type} :: sync folder with test-content")
        perform_sync(syncpath, rdf_store, nmapper)
        # now stuff should be in store
        fnames_in_store = nmapper.get_fnames_in_store(rdf_store)
        assert len(fnames_in_store) == num
        log.debug(f"{rdf_store_type} :: {fnames_in_store=}")
        # the present graphs should match in both fname or ng format
        assert set(fnames_in_store) == set(relfpaths)
        ngs = [nmapper.fname_to_ng(fname) for fname in relfpaths]
        assert set(filter(inbase, rdf_store.named_graphs)) == set(ngs)
        # and we should be able to select and find those triples too
        for fname in relfpaths:
            ng = nmapper.fname_to_ng(fname)
            result = rdf_store.select(sparql, named_graph=ng)
            assert len(result) == graphsize

        # todo
        # 2. check removal -- so drop the last file in the run
        # 3. check update -- so add the triples from the last to the first


if __name__ == "__main__":
    run_single_test(__file__)
