
# -------------------------------------------------------------------------------------------------
def count_chunks_of_type(chunks, chunk_type):
	return sum(1 for chunk in chunks if chunk.get_type() == chunk_type)


# -------------------------------------------------------------------------------------------------
def find_chunks_by_type(chunks, chunk_type):
	return [chunk for chunk in chunks if chunk.get_type() == chunk_type]


# -------------------------------------------------------------------------------------------------
def find_first_chunk_of_type(chunks, chunk_type):
	return next((chunk for chunk in chunks if chunk.get_type() == chunk_type), None)
