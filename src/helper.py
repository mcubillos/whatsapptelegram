from src.static import DB

def cast_seguro(val, tipo, default=None):
	try:
		return tipo(val)
	except (ValueError, TypeError):
		return default