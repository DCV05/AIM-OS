import asyncio
import aioconsole
import traceback
import os
from typing import Dict, Any
from lib.lib import *

class LDI:
    
  def __init__( self, llm, thread_id, sci ):
    self.llm          = llm
    self.thread_id    = thread_id
    self.sci          = sci
    self.metacommands = None
    self.index        = 0
    
    # Información del ordenador
    self.pc_data: Dict[str, Dict[str, Any]] = {
        'DISK': {}
      , 'NET': {}
      , 'RAM': {}
      , 'CPU': {}
    }

  def initialize( self, metacommands ):
    self.metacommands = metacommands
                
  # ------------------------------------------------------------
  # LLM
  # ------------------------------------------------------------

  async def llm_call( self ):

    """
    Maneja la llamada al modelo LLM, ejecuta comandos Unix si es necesario y procesa los metacomandos.

    :param user_question: La pregunta realizada por el usuario.
    :param llm_answer: La respuesta proporcionada por el modelo LLM (opcional).
    :param is_web: Indica si la llamada se realiza desde la web.
    :return: Una lista con los resultados de la ejecución.
    """

    # Llamada al LLM
    llm_answer = self.llm.llm_run_thread( self.thread_id )
    try:

      # Si es un comando de Unix, lo ejecutamos
      if llm_answer['response_type'] == 'linux_command':
        await self.sci.analize_cmd( llm_answer['response'], bool( llm_answer['dangerous_command'] ) )

      # Si detectamos un metacomando, lo analizamos y ejecutamos
      if len( llm_answer['metacommand'] ) > 0: 
        # Analizar y ejecutar el metacomando
        metacommand_result    = await analyze_metacommand(
            metacommand_name  = llm_answer['metacommand']
          , metacommands      = self.metacommands
        )

        return metacommand_result

    except Exception as e:
      print( 'LC Error: ', traceback.format_exc() )
        
      
  # ------------------------------------------------------------
  # DAEMON
  # ------------------------------------------------------------
        
  # Diagnóstico de recursos usados
  async def execute_daemon( self ):

    """
    Ejecuta un Daemon Rust para obtener información del sistema y procesa su salida.

    :return: Cadena de texto con la salida del Daemon.
    """

    try:      
      output = ''
      
      # Calculamos la ruta del Daemon
      daemon_path = __file__.replace( '/ldi/ldi.py', '/sys_info' )
      cmd = [f'{daemon_path}/target/debug/sysinfo', 'subprocess']
      
      # Ejecución de Daemon Rust
      process_pc = await asyncio.create_subprocess_exec(
          *cmd
        , stdout = asyncio.subprocess.PIPE
      )
      
      # Procesamos cada línea del output
      async for line in process_pc.stdout:
        line = line.decode().strip()
        output += line

    except Exception as e:
      print( 'GD Error:', traceback.format_exc() )
      
    finally:
      return output
      
        
  async def process_pc_data( self, pc_data_str ):
    """
    Procesa datos de hardware provenientes de una cadena de texto y calcula índices de variación.
    Si el índice de variación supera el 10%, se añade la información a llm_data.

    :param pc_data_str: Cadena de texto con los datos del hardware.
    :return: Cadena de texto con los datos relevantes para el LLM.
    """
    
    llm_data = ''
  
    # Procesamos el output del Rust
    for item in pc_data_str.split( '|' ):
      item_data = item.strip().split( ' * ' )
      
      # Si hay datos, los insertamos en el atributo pc_data
      if len( item_data ) > 2 and item_data[0] in self.pc_data:
        hw_name, hw_property, components_str = item_data[0], item_data[1], item_data[2]
        
        # Desenvolvemos los datos
        for component in components_str.split( ', ' ):
          component_data_type, component_data_details = component.split( ': ' )

          # Si no existe ni el componente, lo creamos
          if hw_property not in self.pc_data[hw_name]:
            self.pc_data[hw_name][hw_property] = {}
        
          # Si no existen sus propiedades, las creamos y calculamos el índice de variación
          if component_data_type not in self.pc_data[hw_name][hw_property]:
            self.pc_data[hw_name][hw_property][component_data_type] = {}
          else:
            
            # Creamos un índice de variación de datos para decidir si pasarlo al LLM
            try:
              old_data = int( self.pc_data[hw_name][hw_property][component_data_type] )
              new_data = int( component_data_details )
              
              # Cálculo del índice de variación
              if old_data != 0:
                variation_index = round( abs( ( new_data - old_data ) / old_data ) * 10000, 3 )
                
                # Si el índice de variación supera 10%, lo añadimos al String a devolver
                if variation_index > 10:
                  llm_data += f" {hw_name}: {hw_property} - {component_data_type} = {component_data_details} "
            
            except ( ValueError, ZeroDivisionError ):
              continue
          
          # Rellenamos los datos
          self.pc_data[hw_name][hw_property][component_data_type] = component_data_details

    return llm_data   

  # Función de interacción con el usuario
  async def terminal_interaction( self ):
    """
    Interacción con el usuario, ejecución comandos Linux.
    Formulación de una consulta para el modelo LLM con el contexto adecuado.
    """
    
    # Palabras bloqueantes
    STOPWORDS = ['close', 'exit']

    while True:
      try:
          
        query = await aioconsole.ainput( "\n> " )
        query = query.strip().lower()
          
        # Si el input está en las STOPWORDS, cerramos el programa
        if query in STOPWORDS or len( query ) < 1:
          exit( 1 )
          
        # Detectamos si es un comando de Linux a ejecutar
        if find_linux_cmd( query ):
          await self.sci.analize_cmd( [ query ] )
          continue

        # En la primera consulta, enviamos todo el contexto. Después, solo la variación entre datos antiguos y nuevos.
        daemon_output = await self.execute_daemon()
        if self.index > 0:
          daemon_output = await self.process_pc_data( daemon_output )
        
        # Formulamos el prompt y lo añadimos al contexto
        llm_question = f'CONTEXT: {daemon_output} QUESTION: {query}' if len( daemon_output ) > 0 else f'QUESTION: {query}'
        self.llm.llm_message_thread( self.thread_id, llm_question )
        await self.llm_call()
        
      except Exception as e:
        print( 'TI Error:', traceback.format_exc() )