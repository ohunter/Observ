import multiprocessing as mp
import threading as th
import readerwriterlock as rwl
from typing import Any, Callable, Iterable, List, Mapping, NamedTuple, TypedDict, Union
from collections import defaultdict

import sched as sc

class _tmp_exec():
    def __init__(self, executed, func, func_args, func_kwargs, *args, **kwargs) -> None:
        self.exec = executed
        self.func = func
        self.args = func_args
        self.kwargs = func_kwargs

class execution():
    """
    Things to consider when using a `native` execution mode:
    - The function has to return the value otherwise the tile wont know what to render.
    - If the rendering of other tiles is slow, it may be because the system forces the evaluation of the function. Consider switching the execution method to `threaded` or `process`
    """
    def __init__(self, func: Callable[..., None], func_args: Iterable[Any], func_kwargs: Mapping[str, Any], instance, store_results: Union[Callable[[], None], bool] = False, *args, **kwargs) -> None:
        self.func = func
        self.args = func_args
        self.kwargs = func_kwargs

        if isinstance(store_results, bool):
            self._base_storage = None if not store_results else list
        if isinstance(store_results, Callable):
            self._base_storage = store_results

        self.instances = defaultdict(self._base_storage)

        self.add_instance(instance)

    def fetch(self, identifier) -> Any:
        raise NotImplementedError

    def add_instance(self, o):
        self.instances[o] = type(self._base_storage)()

    @staticmethod
    def procure(tile, executed: str = "native", *args, **kwargs):
        for e in _existing_executions:
            if e == _tmp_exec(executed, *args, **kwargs):
                e.add_instance(tile)
                return e

        kwargs.update({"instance" : tile})

        _existing_executions.append(_execution_types.get(executed, execution)(*args, **kwargs))
        return _existing_executions[-1]

    def __eq__(self, o: Union[object, _tmp_exec]) -> bool:
        if isinstance(o, _tmp_exec):
            return self.func == o.func and self.args == o.args and self.kwargs == o.kwargs and type(self).__name__.split('_')[0] == o.exec
        else:
            return self.func == o.func and self.args == o.args and self.kwargs == o.kwargs and type(self) == type(o)

    def __ne__(self, o: Union[object, _tmp_exec]) -> bool:
        return not self == o

class native_execution(execution):
    def __init__(self, *args, **kwargs) -> None:
        super(native_execution, self).__init__(*args, **kwargs)

    def fetch(self, identifier) -> Any:
        result = self.func(*self.args, **self.kwargs)

        if type(self._base_storage) != type(None) and "append" in self._base_storage.__dict__:
            self.instances[identifier].append(result)
        else:
            self.instances[identifier] = result

        return result

class concurrent_execution(execution):
    def __init__(self, frequencies: Union[int, Iterable[int]], *args, **kwargs) -> None:
        super(concurrent_execution, self).__init__(*args, **kwargs)

        remote = None
        if isinstance(self, thread_execution):
            remote = th.Thread
        elif isinstance(self, process_execution):
            remote = mp.Process

        self.remote = remote(target=self.func, args=self.args, kwargs=self.kwargs, daemon=True)

        self.started = False

    def add_instance(self, o):
        assert self.started == False, "Cannot add a new instance once the concurrent execution has started."
        super(concurrent_execution, self).add_instance(o)

    def start(self):
        self.started = True

        self.remote.start()

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

_existing_executions: List[execution] = []