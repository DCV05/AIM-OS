from modules.llm.llm import LLM
from modules.ldi.ldi import LDI
from modules.sci.sci import SCI
from modules.metacommands.metacommands import METACOMMANDS

# Funciones generales
from lib.lib import *

import asyncio
import os

# Variables de entorno
from dotenv import load_dotenv
load_dotenv()
assistand_id = os.getenv( 'ASSISTANT_ID' ) 

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

# Función pricipal del main
async def main():
  
  global ldi
  
  # Consulta al usuario
  await ldi.terminal_interaction()

if __name__ == '__main__':
  
  try:
    
    # Iniciamos una conversación con el LLM
    llm    = LLM( assistand_id )
    thread = llm.llm_create_thread()
    
    # Instanciamos el intérprete de comandos, la interfaz de datos y el módulo de metacomandos
    sci = SCI( llm, thread.id )
    ldi = LDI( llm, thread.id, sci )
    metacommands = METACOMMANDS( ldi )

    # Inicialización del LDI
    ldi.initialize( metacommands )
        
    # Añadimos los metacomandos al contexto de la conversación
    metacommands_list = '\n'.join( [f"- {key}: {details['meaning']}" for key, details in metacommands.metacommands_instructions().items()] )
    llm.llm_message_thread( thread.id, metacommands_list )
    
    loop = asyncio.run( main() )
      
  except KeyboardInterrupt:
    print( 'Interrupted' )
    exit( 0 )