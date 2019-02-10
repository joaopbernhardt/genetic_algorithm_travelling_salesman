from multiprocessing import cpu_count
from multiprocessing.connection import Connection
from typing import Union


def get_last_message(connection: Connection) -> dict:
    message = {}
    try:
        while connection.poll():
            message = connection.recv()
    except EOFError:
        pass
    return message


def get_pipes_messages(pipe_conns: list) -> list:
    messages = []
    for conn in pipe_conns:
        this_message = get_last_message(conn)
        if this_message:
            messages.append(this_message)
    return messages


def any_process_alive(processes: list) -> bool:
    for process in processes:
        if process.is_alive():
            return True
    return False

def validate_and_get_num_processes(num_processes: Union[int, str]):
    error_string = 'num_processes should be either "max" or a positive integer.'
    if isinstance(num_processes, int):
        if num_processes < 1:
            raise ValueError(error_string)
        return num_processes
    elif isinstance(num_processes, str):
        if not num_processes == "max":
            raise ValueError(error_string)
        # leave one CPU as handler
        return cpu_count() - 1
    else:
        raise ValueError(error_string)
