import multiprocessing as mp
import threading as th
import readerwriterlock as rwl
from typing import Any, Callable, Iterable, List, Mapping, TypedDict, Union

import sched as sc

class execution():
    """
    Things to consider when using a `native` execution mode:
    - The function has to return the value otherwise the tile wont know what to render.
    - If the rendering of other tiles is slow, it may be because the system forces the evaluation of the function. Consider switching the execution method to `threaded` or `process`
    """
    def __init__(self, func: Callable[..., None], func_args: Iterable[Any], *args, **kwargs) -> None:
        self.func = func
        self.args = func_args

    def fetch(self) -> Any:
        raise NotImplementedError

    @staticmethod
    def procure(executed: str = "native", *args, **kwargs):
        return _execution_types.get(executed, execution)(*args, **kwargs)

    def __eq__(self, o: object) -> bool:
        return self.func == o.func and self.args == o.args and type(self) == type(o)

    def __ne__(self, o: object) -> bool:
        return not self == o

class native_execution(execution):
    def __init__(self, *args, **kwargs) -> None:
        super(native_execution, self).__init__(*args, **kwargs)

    def fetch(self) -> Any:
        return self.func(*self.args)

class concurrent_execution(execution):
    def __init__(self, frequencies: Union[int, Iterable[int]], *args, **kwargs) -> None:
        # raise NotImplementedError
        super(concurrent_execution, self).__init__(*args, **kwargs)
        self.freq_data = {} #defaultdict(type(return_type))
        if isinstance(frequencies, Iterable):
            freqs = [(x, self.func) for x in frequencies]
        else:
            freqs = [(frequencies, self.func)]

        self.sched = sc.scheduler(freqs)

    def __eq__(self, o: object) -> bool:
        """
        Things that may differ:
        - Stuff like function and arguments
        - The place of execution (native, threaded, and as a separate process)
        """
        return super(concurrent_execution, self).__eq__(o) and True

class thread_execution(concurrent_execution):
    def __init__(self, *args, **kwargs) -> None:
        super(thread_execution, self).__init__(*args, **kwargs)

class process_execution(concurrent_execution):
    def __init__(self, *args, **kwargs) -> None:
        super(process_execution, self).__init__(*args, **kwargs)

_execution_types: Mapping[str, execution] = {
    "native": native_execution,
    "thread": thread_execution,
    "process": process_execution,
}
