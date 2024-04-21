#! /usr/bin/env python
""" test_sync
tests concerning the actual core sync expectations
"""
import random

import pytest
from conftest import make_sample_graph
from util4tests import log, run_single_test

from syncfstriples.service import (
    format_from_filepath,
    perform_sync,
    relative_pathname,
)


@pytest.mark.usefixtures("base", "nmapper", "rdf_stores", "syncfolders")
def test_perform_sync(base, nmapper, rdf_stores, syncfolders):
    def inbase(ng):
        return ng.startswith(base)

    # there should at least be 2 for the logic of the test to hold
    extensions = ["ttl", "jsonld", "turtle", "json"]
    random.shuffle(extensions)
    num = len(extensions)
    assert num >= 2
    graphsize = 5
    sparql = "select * where {?s ?p ?o .}"

    for rdf_store, syncpath in zip(rdf_stores, syncfolders):
        rdf_store_type: str = type(rdf_store).__name__
        assert nmapper == rdf_store._nmapper
        # note since we manipulate these along the way, we need them freshly made per rdf_store
        graphs = [
            make_sample_graph(range(i * 10, i * 10 + graphsize))
            for i in range(1, 1 + num)
        ]
        # 0. nothing there at the start
        assert len(rdf_store.keys) == 0
        # now sync an empty folder
        log.debug(f"{rdf_store_type} :: sync empty folder")
        perform_sync(syncpath, rdf_store)
        # still nothing
        assert len(rdf_store.keys) == 0

        # 1. check addition -- so create some files
        relfpaths = list()
        for ext, g, n in zip(extensions, graphs, range(1, 1 + num)):
            fpath = syncpath / f"gen-{n:02d}.{ext}"
            log.debug(f"creating file for sync {fpath=}")
            g.serialize(
                destination=str(fpath), format=format_from_filepath(fpath)
            )
            relfpaths.append(relative_pathname(fpath, syncpath))
        # now sync again
        log.debug(f"{rdf_store_type} :: sync folder with test-content")
        perform_sync(syncpath, rdf_store)
        log.debug(f"{rdf_store_type} :: after first sync {rdf_store.keys=}")
        # now stuff should be in store
        fnames_in_store = rdf_store.keys
        assert len(fnames_in_store) == num
        log.debug(f"{rdf_store_type} :: {fnames_in_store=}")
        # the present graphs should match in both fname or ng format
        assert set(fnames_in_store) == set(relfpaths)
        ngs = [nmapper.key_to_ng(fname) for fname in relfpaths]
        assert set(filter(inbase, rdf_store.named_graphs)) == set(ngs)
        # and we should be able to select and find those triples too
        for fname in relfpaths:
            ng = nmapper.key_to_ng(fname)
            result = rdf_store.select(sparql, named_graph=ng)
            assert len(result) == graphsize

        # 2. check removal -- so drop the last file in this sequence
        rm_fname = relfpaths.pop()
        rm_fpath = syncpath / rm_fname
        log.debug(f"removing file {rm_fpath=}")
        rm_fpath.unlink()
        # also grab the change-time on the first
        first_ng = nmapper.key_to_ng(relfpaths[0])
        first_store_lastmod = rdf_store.lastmod_ts(first_ng)
        log.debug(
            f"{rdf_store_type} :: "
            f"lastmod at key {relfpaths[0]} leads to ng {first_ng} "
            f"that has lastmod={first_store_lastmod}"
        )
        # now sync again
        log.debug(f"{rdf_store_type} :: sync folder after file delete")
        perform_sync(syncpath, rdf_store)
        log.debug(
            f"{rdf_store_type} :: after sync after delete {rdf_store.keys =}"
        )
        # there should be one less in store
        fnames_in_store = rdf_store.keys
        assert len(fnames_in_store) == num - 1
        # the other one should not have been changed
        log.debug(
            f"{rdf_store_type} :: "
            f"lastmod at key {relfpaths[0]} leads to ng {first_ng} "
            f"that used to have lastmod={first_store_lastmod} "
            f"and now has lastmod={rdf_store.lastmod_ts(first_ng)} "
        )
        assert rdf_store.lastmod_ts(first_ng) == first_store_lastmod

        # 3. check update -- so add the triples from the last to the first
        first_graph = graphs[0]
        last_graph = graphs[-1]
        first_graph += last_graph
        # save that back out
        fpath = syncpath / relfpaths[0]
        log.debug(f"updating file for sync {fpath=}")
        first_graph.serialize(
            destination=str(fpath), format=format_from_filepath(fpath)
        )
        # then resync
        log.debug(f"{rdf_store_type} :: sync folder after file update")
        perform_sync(syncpath, rdf_store)
        log.debug(
            f"{rdf_store_type} :: after sync after update {rdf_store.keys =}"
        )
        # still same amount of files in store
        fnames_in_store = rdf_store.keys
        assert len(fnames_in_store) == num - 1
        # but the first should have been updated
        assert rdf_store.lastmod_ts(first_ng) > first_store_lastmod


if __name__ == "__main__":
    run_single_test(__file__)
