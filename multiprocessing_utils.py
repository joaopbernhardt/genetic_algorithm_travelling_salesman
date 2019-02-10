from multiprocessing.connection import Connection


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
