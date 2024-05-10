from colorama import Fore, Style

# --- todo ----------------------------------------------------------------------------------------
# - line number is off by one
# - should include filename or source in error message
# 	- `Error:file.q:42`, `Error:import.q:22`, `Error:[string]:24` 
# - better parentheses and bracket mismatch errors reported at endscript
# 	- need more context? or just write the counts and the script name?


# -------------------------------------------------------------------------------------------------
def print_warning_message(message):
	print(F"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")


# -------------------------------------------------------------------------------------------------
def print_token_error_message(token):
	print('Error:')
	print(highlight_error_with_indicator(token['source'], token['index'], token['start'], token['end']))


# -------------------------------------------------------------------------------------------------
def highlight_error_with_indicator(line, line_index, start_index, end_index):
	"""
	Highlights an error in a given line of code, prefixes it with a line number, and
	creates a visual indicator pointing to the start of the error in the line below.
	
	Args:
	- line (str): The line of code.
	- line_index (int): The line number to prefix.
	- start_index (int): The start index of the error in the line.
	- end_index (int): The end index of the error in the line.
	
	Returns:
	- str: Formatted string with the line, error highlighted, and visual indicator below.
	"""
	# Highlight the error within the line
	highlighted_line = insert_color_and_reset(line, Fore.RED, start_index, end_index)
	
	# Prefix the line number
	line_with_number = f'{Fore.CYAN}{line_index+1:4}| {Style.RESET_ALL}{highlighted_line}'
	
	# Create the error indicator line
	# Uses spaces to align with the start of the error, then a dash line, ending with an arrow
	indicator_line = ' ' * (6 + start_index) + Fore.RED + '^' * (end_index - start_index) + Style.RESET_ALL
	
	return f'{line_with_number}\n{indicator_line}'


# -------------------------------------------------------------------------------------------------
def highlight_error_in_line(line, line_index, start_index, end_index):
	"""
	Highlights an error in a given line of code and prefixes it with a line number.
	
	Args:
	- line (str): The line of code.
	- line_index (int): The line number to prefix.
	- start_index (int): The start index of the error in the line.
	- end_index (int): The end index of the error in the line.
	
	Returns:
	- str: The line with the error highlighted and prefixed with the line number.
	"""
	# Highlight the error within the line
	highlighted_line = insert_color_and_reset(line, Fore.RED, start_index, end_index)
	
	# Prefix the line number
	line_with_number = f'{Fore.CYAN}{line_index+1:4}| {Style.RESET_ALL}{highlighted_line}'
	
	return line_with_number


# -------------------------------------------------------------------------------------------------
def insert_color_and_reset(text, color, start_index, end_index):
	"""
	Inserts a color at a specific index in a text and resets the color at another index.
	"""
	return text[:start_index] + color + text[start_index:end_index] + Style.RESET_ALL + text[end_index:]


# -------------------------------------------------------------------------------------------------
class CompilerError(Exception):

	# ---------------------------------------------------------------------------------------------
	def __init__(self, context, message):
		super().__init__(message)
		self.annotation = highlight_error_with_indicator(context['source'], context['index'], context['start'], context['end'])


# -------------------------------------------------------------------------------------------------
class InvalidFormatError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class InvalidTokenError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class TokenMismatchError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class KeywordMismatchError(Exception):
	pass


# -------------------------------------------------------------------------------------------------
class UnexpectedScopeError(Exception):
	pass
