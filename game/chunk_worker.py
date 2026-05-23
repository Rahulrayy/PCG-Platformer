def generate_and_validate(index, entry_row):
    #subprocess never touches arcade/opengl
    from level.generator import generate_raw_chunk
    from validation.pipeline import validate
    for attempt in range(1, 601):
        chunk = generate_raw_chunk(index=index, entry_row=entry_row)
        if validate(chunk):
            return chunk, attempt
    return None, 600
