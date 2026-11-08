from dataclasses import dataclass


@dataclass
class Techniques:
    repo_map: bool = True
    slice_reads: bool = True
    patch_edits: bool = True
    trim_tool_output: bool = True
    compaction: bool = True
    tiered_models: bool = True
    short_outputs: bool = True
    dedupe: bool = True
    stable_prefix: bool = True
