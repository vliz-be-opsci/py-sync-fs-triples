from datetime import UTC as UTC_tz
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Dict, Iterable
from urllib.parse import quote, unquote

from pyrdfstore import create_rdf_store
from pyrdfstore.store import RDFStore
from rdflib import Graph

log = getLogger(__name__)

SUFFIX_TO_FORMAT = {
    ".ttl": "turtle",
    ".turtle": "turtle",
    ".jsonld": "json-ld",
    ".json-ld": "json-ld",
    ".json": "json-ld",
}
SUPPORTED_RDF_DUMP_SUFFIXES = [sfx for sfx in SUFFIX_TO_FORMAT]
DEFAULT_URN_BASE = "urn:sync:"


class GraphFileNameMapper:
    """Helper class to convert filenames into graph-names."""

    def __init__(self, base: str = DEFAULT_URN_BASE) -> None:
        """constructor

        :param base: base_uri to apply, defaults to DEFAULT_URN_BASE = 'urn:sync:'
        :type base: str
        """
        self._base = str(base)

    def fname_to_ng(self, fname: str) -> str:
        """converts local filename to a named_graph

        :param fname: local file-name
        :type fname: str
        :returns: urn representing the filename to be used as named-graph
        :rtype: str
        """
        return f"{self._base}{quote(fname)}"

    def ng_to_fname(self, ng: str) -> str:
        """converts named_graph urn back into local filename

        :param fname: local file-name
        :type fname: str
        :returns: urn representing the filename to be used as named-graph
        :rtype: str
        """
        assert ng.startswith(self._base), (
            f"Unknown {ng=}. " f"It should start with {self._base=}"
        )
        return unquote(ng[len(self._base) :])

    def get_fnames_in_store(self, store: RDFStore) -> Iterable[str]:
        """selects those named graphs in the store.named_graphs under our base
        and converts them into filenames

        :param store: the store to grab & filter the named_graphs from
        :type store: RDFStore
        :returns: list of filenames in that store, based on the found
        :rtype: List[str]
        """
        return [
            self.ng_to_fname(ng)
            for ng in store.named_graphs
            if ng.startswith(self._base)
        ]  # filter and convert the named_graphs to file_names we handle


def get_lastmod_by_fname(from_path: Path) -> Dict[str, datetime]:
    """lists all files in path with their lastmod timestamp

    :param from_path: root to list contents from
    :type from_path: Path
    :returns: dict of fnames + their lastmod on disk
    :rtype: Dict[ str, datetime ]
    """
    return {
        str(p): datetime.fromtimestamp(p.stat().st_mtime, UTC_tz)
        for p in from_path.glob("**/*")
        if p.is_file() and p.suffix in SUPPORTED_RDF_DUMP_SUFFIXES
    }


def format_from_filepath(fpath: Path) -> str:
    """extracts the rdflib file format from the suffix of the file in fpath

    :param fpath: path of file to inspect
    :type fpath: Path
    :returns: value for rdflib format=  for that file
    :rtype: str
    """
    suffix = fpath.suffix.lower()
    return SUFFIX_TO_FORMAT.get(suffix, None)


def load_graph_fpath(fpath: Path, format: str = None) -> Graph:
    """loads content of file at fpath into a graph
    :param fpath: path of file to load
    :type fpath: Path
    :param format: rdflib format to apply when parsing the file
        optional - if left None, autodetected base on file-extension
    :type format: str
    :returns: the graph containing the triples from the file
    :rtype: Graph
    """
    format = format or format_from_filepath(fpath)
    graph: Graph = Graph().parse(location=str(fpath), format=format)
    return graph


def relative_pathname(subpath: Path, ancestorpath: Path) -> str:
    """gives the relative part pointing to the subpath from the ancestorpath"""
    return str(subpath.absolute().relative_to(ancestorpath.absolute()))


def sync_removal(
    store: RDFStore, fpath: Path, rootpath: Path, nmapper: GraphFileNameMapper
) -> None:
    """Handles removal event triggered when file on disk got removed.
    (i.e. has a matching graph in store, but no longer exists).
    Resolution should ensure removal of the matching graph in the store

    :param store: target store where removal should happen
    :type store: RDFStore
    :param fpath: file-path of file that no longer exists
    :type fpath: Path
    :param rootpath: root containing the sub fpath
    :type rootpath: Path
    :param nmapper: convertor between fnames and graphnames to be used
    :type nmapper: GraphFileNameMapper
    :rtype: None
    """
    ng = nmapper.fname_to_ng(relative_pathname(fpath, rootpath))
    store.drop_graph(ng)
    store.forget_graph(ng)


def sync_addition(
    store: RDFStore, fpath: Path, rootpath: Path, nmapper: GraphFileNameMapper
) -> None:
    """Handles addition event triggered when a new file on disk appeared.
    (i.e. has not yet a matching graph in store).
    Resolution should ensure addition of the matching graph in the store

    :param store: target store where addition should happen
    :type store: RDFStore
    :param fpath: file-path of file that was added
    :type fpath: Path
    :param rootpath: root containing the sub fpath
    :type rootpath: Path
    :param nmapper: convertor between fnames and graphnames to be used
    :type nmapper: GraphFileNameMapper
    :rtype: None
    """
    ng = nmapper.fname_to_ng(relative_pathname(fpath, rootpath))
    g = load_graph_fpath(fpath)
    store.insert(g, ng)


def sync_update(
    store: RDFStore, fpath: Path, rootpath: Path, nmapper: GraphFileNameMapper
) -> None:
    """Handles update event triggered when a file on disk was changed
    (i.e. has a more recent lastmod then matching graph in store).
    Resolution should ensure addition of the matching graph in the store

    :param store: target store where update should happen
    :type store: RDFStore
    :param fpath: file-pathname of file that was updated
    :type fpath: Path
    :param rootpath: root containing the sub fpath
    :type rootpath: Path
    :param nmapper: convertor between fnames and graphnames to be used
    :type nmapper: GraphFileNameMapper
    :rtype: None
    """
    ng = nmapper.fname_to_ng(relative_pathname(fpath, rootpath))
    store.drop_graph(ng)
    g = load_graph_fpath(fpath)
    store.insert(g, ng)


def perform_sync(
    from_path: Path, to_store: RDFStore, nmapper: GraphFileNameMapper
) -> None:
    """synchronizes found rdf-dump files in the from_path to the RDFStore specified

    :param from_path: folder path to sync from
    :type from_path: Path
    :param to_store: rdf store target for the sync operation
    :type to_store: RDFStore
    :param nmapper: convertor between fnames and graphnames to be used
    :type nmapper: GraphFileNameMapper
    :rtype: None
    """
    known_relnames_in_store = nmapper.get_fnames_in_store(to_store)
    current_lastmod_by_fname = get_lastmod_by_fname(from_path)
    log.debug(f"current_lastmod_by_fname: {current_lastmod_by_fname}")
    for relname in known_relnames_in_store:
        fname = str(from_path / relname)
        if fname not in current_lastmod_by_fname:
            log.debug(f"old file {fname} no longer exists")
            sync_removal(to_store, Path(fname), from_path, nmapper)
    for fname, lastmod in current_lastmod_by_fname.items():
        relname = relative_pathname(Path(fname), from_path)
        if relname not in known_relnames_in_store:
            log.debug(f"new file {fname} with lastmod {lastmod}")
            sync_addition(to_store, Path(fname), from_path, nmapper)
        else:
            ng = nmapper.fname_to_ng(relname)
            known_lastmod = to_store.lastmod_ts(ng).astimezone(UTC_tz)
            log.debug(
                f"known file {relname} - check file {lastmod} >= {known_lastmod}"
            )
            if lastmod >= known_lastmod:
                log.debug(f"updated file {fname} with lastmod {lastmod}")
                sync_update(to_store, Path(fname), from_path, nmapper)
            else:
                log.debug(
                    f"skip file {fname} with lastmod {lastmod} - unchanged"
                )


class SyncFsTriples:
    """Process-wrapper-pattern for easy inclusion in other contexts."""

    def __init__(
        self,
        fpath: str,
        named_graph_base: str = DEFAULT_URN_BASE,
        read_uri: str = None,
        write_uri: str = None,
    ):
        """Creates the process-wrapper instance

        :param fpath: path to te folder to check for nested rdf dump files to be synced up.
        :type fpath: str
        :param named_graph_base: the base to be used for building named_graphs in the conversion
            optional - defaults to DEFAULT_URN_BASE = "urn:sync:"
        :type named_graph_base: str
        :param read_uri: uri to the triple-store to sync to
            optional - defaults to None - leading to using an in-MemoryStore
        :type read_uri: str
        :param write_uri: uri for write operations to the triple store
            optional - defaults to None - leading to a store that can only be read from
        :type write_uri: str
        """
        self.source_path: Path = Path(fpath)
        assert self.source_path.exists(), (
            "cannot sync a source-path " + str(fpath) + " that does not exist."
        )
        assert self.source_path.is_dir(), (
            "source-path " + str(fpath) + " should be a folder."
        )
        self.nmapper = GraphFileNameMapper(base=named_graph_base)
        self.rdfstore: RDFStore = create_rdf_store(read_uri, write_uri)

    def process(self) -> None:
        """executes the SyncFs command"""
        perform_sync(
            from_path=self.source_path,
            to_store=self.rdfstore,
            nmapper=self.nmapper,
        )
