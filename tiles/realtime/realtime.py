import logging
import multiprocessing as mp
import os
import queue as qu
import sched as sc
import threading as th
import time
from collections import defaultdict
from typing import Any, Callable, Iterable, List, Mapping, NamedTuple, Type, Union


class message(NamedTuple):
    identifier: Any
    value: Any

def _module_executor(func, sched, queue, *args, **kwargs) -> None:
    logging.debug(f"Task recieved with function {func} with arguments {args} and keyword arguments {kwargs}")

    if "files" in kwargs:
        logging.info(f"Opening required files for task")
        kwargs.update({"files": {x : open(x) for x in kwargs.pop('files')}})
        logging.info(f"The following files were opened: {', '.join(kwargs['files'])}")

    logging.debug(f"Starting scheduler for task with function {func} with arguments {args} and keyword arguments {kwargs}")
    try:
        for t, identifier in sched.next_timing():
            result = func(*args, **kwargs)
            for e in identifier:
                queue.put(message(e, result))
            time.sleep(t)
    except BaseException as e:
        logging.critical(f"Exception occurred in task with function {func} with arguments {args} and keyword arguments {kwargs}:\n{e}")

class _tmp_exec():
    def __init__(self, executed, func, func_args, func_kwargs, *args, **kwargs) -> None:
        self.exec = executed
        self.func = func
        self.args = func_args
        self.kwargs = func_kwargs

class execution():
    """
    Things to consider when using a `native` execution mode:
    - If the rendering of other tiles is slow, it may be because the system forces the evaluation of the function. Consider switching the execution method to `threaded` or `process`
    """
    def __init__(self, func: Callable[..., Any], func_args: Iterable[Any], func_kwargs: Mapping[str, Any], instance, return_type: Union[Callable[[], None], Type], store_results: bool = False, *args, **kwargs) -> None:
        self.func = func
        self.args = func_args
        self.kwargs = func_kwargs

        if store_results:
            self._base_storage = list
        else:
            self._base_storage = return_type

        self.instances = []
        self.mapping = defaultdict(self._base_storage)

        self.add_instance(instance)

    def fetch(self, identifier) -> Any:
        raise NotImplementedError

    def add_instance(self, o) -> None:
        self.instances.append(o)
        self.mapping[id(o)] = self._base_storage()

    def start(self) -> None:
        return

    @staticmethod
    def procure(tile, executed: str = "native", *args, **kwargs) -> None:
        for e in _existing_executions:
            if e == _tmp_exec(executed, *args, **kwargs):
                logging.debug("Found a similar task. Grouping them together")
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
            self.mapping[id(identifier)].append(result)
        else:
            self.mapping[id(identifier)] = result

        return self.mapping[id(identifier)]

class concurrent_execution(execution):
    def __init__(self, *args, **kwargs) -> None:
        self.started = False
        self.remote: Union[th.Thread, mp.Process]

        super(concurrent_execution, self).__init__(*args, **kwargs)

    def add_instance(self, o) -> None:
        assert self.started == False, "Cannot add a new instance once the concurrent execution has started."
        super(concurrent_execution, self).add_instance(o)

    def start(self) -> None:
        assert self.started == False, "Cannot start concurrent execution twice."
        self.started = True

        logging.info(f"Starting concurrent execution of function {self.func} with arguments {self.args} and keyword arguments {self.kwargs}")

        if isinstance(self, thread_execution):
            self.remote = th.Thread
            self.queue = qu.Queue()
        elif isinstance(self, process_execution):
            self.remote = mp.Process
            self.queue = mp.Queue()
        else:
            raise NotImplementedError

        self.kwargs.update({"func": self.func, "queue": self.queue, "sched": sc.scheduler([(a, id(b)) for x in self.instances for a, b in x.timing()])})

        self.remote = self.remote(target=_module_executor, args=self.args, kwargs=self.kwargs, daemon=True)

        self.remote.start()

    def fetch(self, identifier) -> Any:
        assert self.started == True, "Cannot fetch data before the concurrent execution has started."

        try:
            while not self.queue.empty():
                e: message = self.queue.get()
                if type(self._base_storage) != type(None) and "append" in self._base_storage.__dict__:
                    self.mapping[e.identifier].append(e.value)
                else:
                    self.mapping[e.identifier] = e.value

            return self.mapping[id(identifier)]
        except BaseException as e:
            logging.critical(f"Exception occured between processes with pids {os.getpid()} and {self.remote.pid}:\n{e}")

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
