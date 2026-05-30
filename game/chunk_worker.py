def generate_and_validate(index, entry_row, stop_shm_name=None):
    #subprocess never touches arcade/opengl
    import os
    import time as _time
    from multiprocessing.shared_memory import SharedMemory
    from level.generator import generate_raw_chunk
    from validation.pipeline import validate
    pid = os.getpid()
    t0 = _time.perf_counter()
    shm = None
    if stop_shm_name:
        try:
            shm = SharedMemory(name=stop_shm_name, create=False)
        except Exception:
            pass
    try:
        for attempt in range(1, 1501):
            if shm is not None and shm.buf[0]:
                return None, attempt, _time.perf_counter() - t0, pid
            chunk = generate_raw_chunk(index=index, entry_row=entry_row)
            if validate(chunk):
                return chunk, attempt, _time.perf_counter() - t0, pid
    finally:
        if shm is not None:
            shm.close()
    return None, 1500, _time.perf_counter() - t0, pid
