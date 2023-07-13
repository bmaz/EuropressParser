import concurrent.futures
import json
from typing import List, Tuple

from europarser.models import FileToTransform, Output, Pivot, OutputType
from europarser.transformers.iramuteq import IramuteqTransformer
from europarser.transformers.csv import CSVTransformer
from europarser.transformers.pivot import PivotTransformer
from europarser.transformers.txm import TXMTransformer
from europarser.transformers.stats import StatsTransformer


def process(file: str, output: Output = "pivot", name: str = "file"):
    """
    utility function to process only one file at a time
    For multiple files, it's better to use the pipeline
    """
    return pipeline([FileToTransform(file=file, name=name)], output)


def pipeline(files: List[FileToTransform], output: Output = "pivot") -> Tuple[str, OutputType]:
    pivots: List[Pivot] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(PivotTransformer().transform, f) for f in files]
        for future in concurrent.futures.as_completed(futures):
            pivots = [*pivots, *future.result()]
        # undouble remaining doubles
        pivots = list(set(pivots))
    if output == "json":
        result = json.dumps({i: article.dict() for i, article in enumerate(pivots)}, ensure_ascii=False)
        result_type: OutputType = "json"
    elif output == "iramuteq":
        result = IramuteqTransformer().transform(pivots)
        result_type = "txt"
    elif output == "txm":
        result = TXMTransformer().transform(pivots)
        result_type = "xml"
    elif output == "csv":
        result = CSVTransformer().transform(pivots)
        result_type = "csv"
    elif output == "stats":
        result = json.dumps(StatsTransformer().transform(pivots), ensure_ascii=False, indent=2)
        result_type = "json"
    else:
        result = json.dumps([pivot.dict() for pivot in pivots], ensure_ascii=False)
        result_type: OutputType = "json"
    return result, result_type
