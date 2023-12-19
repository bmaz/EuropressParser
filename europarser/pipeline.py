from __future__ import annotations

import concurrent.futures
from typing import Tuple

from tqdm import tqdm

from europarser.models import Output, FileToTransform, OutputFormat, Pivot, TransformerOutput, Params
from europarser.transformers.csv import CSVTransformer
from europarser.transformers.iramuteq import IramuteqTransformer
from europarser.transformers.json import JSONTransformer
from europarser.transformers.markdown import MarkdownTransformer
from europarser.pivot import PivotTransformer
from europarser.transformers.txm import TXMTransformer
from europarser.transformers.stats import StatsTransformer

transformer_factory = {
    "json": JSONTransformer().transform,
    "txm": TXMTransformer().transform,
    "iramuteq": IramuteqTransformer().transform,
    "gephi": None,
    "csv": CSVTransformer().transform,
    "stats": "get_stats",
    "processed_stats": "get_processed_stats",
    "plots": "get_plots",
    "markdown": MarkdownTransformer().transform
}

stats_outputs = {"stats", "processed_stats", "plots", "markdown"}


def pipeline(files: list[FileToTransform], outputs: list[Output], params: Params) -> list[TransformerOutput]:
    """
    main function that transforms the files into pivots and then in differents required ouptputs
    """

    transformer = PivotTransformer(params)
    pivots = transformer.transform(files_to_transform=files)

    to_process = []
    st = None
    if stats_outputs.intersection(outputs):
        st = StatsTransformer()
        st.transform(pivots)

    for output in outputs:
        if output in stats_outputs and output != "markdown":
            func = getattr(st, transformer_factory[output])
            to_process.append((func, []))

        else:
            func = transformer_factory[output]
            args = [pivots]
            to_process.append((func, args))

    results: list[TransformerOutput] = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(func, *args) for func, args in to_process]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            res = future.result()
            results.append(res)

    return results


def process(*args, **kwargs) -> list[TransformerOutput]:
    return pipeline(*args, **kwargs)
