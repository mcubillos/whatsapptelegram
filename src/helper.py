from src.static import DB

def db_agregar_contacto(nombre,numero):
	resultado = DB.contactos.insert_one(
		{
			'nombre' : nombre.lower(),
			'numero' : numero
		}
	)

	return resultado.inserted_id

def db_lista_contactos():
	contactos = DB.contactos.find()
	resultado = []
	
	def mapContact(nombre , numero):
		resultado.append((nombre, numero))
	
	return map(mapContact, contactos)

def db_eliminar_contacto(nombre):
	DB.contactos.delete_one({'nombre':nombre.lower()})

def get_contacto(numero):
	resultado = DB.contactos.find_one({"numero":numero})

	if not resultado:
		return None

	return resultado['nombre']

def get_numero(nombre):
	resultado = DB.contactos.find_one({"nombre":nombre.lower()})

	if not resultado:
		return None

	return resultado['numero']

def cast_seguro(val, tipo, default=None):
	try:
		return tipo(val)
	except (ValueError, TypeError):
		return default