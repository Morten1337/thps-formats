# -------------------------------------------------------------------------------------------------
def count_chunks_with_type(chunks, target_type):
	"""
	Counts the number of chunks with the specified type.

	Args:
		chunks (list): List of chunks to search.
		target_type (ChunkType): The target type to count.

	Returns:
		int: The count of chunks with the specified type.
	"""
	return sum(1 for chunk in chunks if chunk.get_type() == target_type)


# -------------------------------------------------------------------------------------------------
def find_chunks_with_type(chunks, target_type):
	"""
	Finds all chunks with the specified type.

	Args:
		chunks (list): List of chunks to search.
		target_type (ChunkType): The target type to filter.

	Returns:
		list: List of chunks matching the specified type.
	"""
	return [chunk for chunk in chunks if chunk.get_type() == target_type]


# -------------------------------------------------------------------------------------------------
def find_first_chunk_with_type(chunks, target_type):
	"""
	Finds the first chunk with the specified type.

	Args:
		chunks (list): List of chunks to search.
		target_type (ChunkType): The target type to search for.

	Returns:
		object: The first chunk with the specified type or None if not found.
	"""
	return next((chunk for chunk in chunks if chunk.get_type() == target_type), None)
