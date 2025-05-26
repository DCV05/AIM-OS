import lib.lib
import json
import traceback

class METACOMMANDS:
  
  def __init__( self, ldi ):
    self.ldi = ldi
  
  # Función para devolver los metacommands del json
  def metacommands_instructions( self ):
    
    dir = __file__.replace( 'metacommands.py', '' )
    try:
      # Leemos el JSON
      with open( f"{dir}/metacommands.json", 'r' ) as f:
        return json.loads( f.read() )
      
    except Exception as e:
      print( traceback.format_exc() )
      return None
  
  async def meta_return( self, **kwargs ):
    # Consulta al LLM
    return await self.ldi.llm_call()