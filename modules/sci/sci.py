import re
import aioconsole
import os
import traceback
from rich.console import Console
from rich.markdown import Markdown
from lib.lib import *

# Constantes
CRIT_CMD  = [
  'rm',
  'su',
  'dd',
  'fdisk',
  'mkfs',
  'wget',
  'curl',
  'chmod',
  'chown',
  'shutdown',
  'reboot',
  'halt',
  'kill',
  'pkill',
  'iptables',
  'userdel'
]

# Ejecución de Scripts
SCRIPT_CMD = [
  'java',
  'python',
  'python3',
  'php',
  'ruby',
  'perl',
  'node',
  'npm',
  'go run',
  'dotnet run'
]

class SCI:
  
  def __init__( self, llm, thread_id: str ):
    self.llm        = llm
    self.thread_id  = thread_id
    self.console    = Console()
    
  # Función para ejecutar un comando
  async def analize_cmd( self, cmd: list[str], is_dangerous: bool = False ):
    """
    Ejecuta un comando recibido, pidiendo confirmación para comandos críticos o scripts.

    :param cmd: Comando a ejecutar.
    :param is_dangerous: Indica si el comando es peligroso o no
    :return: Lista con los resultados de la ejecución.
    """
    
    cmd_outputs = []
    try:

      # Separación por partes
      for part in cmd:
        part = part.strip()
        items = part.split( ' ' )

        # Determinamos si son comandos peligrosos o de ejecución de scripts
        is_critical = ( any( item in CRIT_CMD for item in items ) or is_dangerous )
        is_script   = any( item in SCRIPT_CMD for item in items )
        
        # Si es un script o un comando peligroso
        if is_critical or is_script:
          
          # Pedimos por consola una confirmación
          input_response = await aioconsole.ainput( f"\nAre you sure you want to execute: '{part}'? (y/n) " )
          input_response = input_response.strip().lower()
          if input_response != 'y':
            return
      
        # Ejecutamos el comando
        output = await self.run_cmd( part )
        
        cmd_outputs.append( {
            'input': part
          , 'output': output
          , 'pwd': os.getcwd()
        } )
          
    except Exception as e:
      print( 'ECW Error: ', traceback.format_exc() )
      
    finally:
      return cmd_outputs
    
  async def run_cmd( self, cmd ):
    """
    Ejecuta un comando en la CLI, manejando permisos sudo si es necesario.

    :param cmd: Comando a ejecutar.
    :return: Tupla con la salida del comando y un indicador de éxito.
    """
    
    try:
      # Construimos el comando
      temp_cmd = f'{cmd} && echo "@$(pwd)@"'
      
      linux_result = subprocess.run(
          temp_cmd
        , text           = True
        , shell          = True
        , capture_output = True
        , check          = True
      )
      
      # Cambiamos el puntero del proceso Python
      pointer = os.getcwd()
      pwd_pattern = re.compile( r'\@(.*?)\@' )
      new_pointer = pwd_pattern.findall( linux_result.stdout )
      
      # Si el puntero actual es diferente al comparado, cambiamos la ruta del puntero
      if new_pointer and new_pointer[0] != pointer:
        pointer = new_pointer[0]
        os.chdir( pointer )
      linux_result.stdout = linux_result.stdout.replace( f"@{pointer}@", '' )
      
      # Calculamos el output a devolver
      success_text = "Command execution successful" if not len( linux_result.stdout ) > 0 else linux_result.stdout[0:1024]
      
      # Añadimos el output al contexto
      self.console.print(
          f"\n-------------------------------------------------\n"
        + f"CMD -> {cmd}"
        + f"\n-------------------------------------------------\n"
        + f"\n{success_text}"
        + f"-------------------------------------------------"
      )
      self.llm.llm_message_thread( self.thread_id, cmd + ' | ' + success_text + f"\n{pointer}" )
      
      return success_text
    
    # En caso de error, mostramos el error por consola
    except Exception as e:
      error_text = f"CLI-Error: \n{str( e )[0:1024]}"
      self.console.print(
          f"\n-------------------------------------------------\n"
        + f"CMD -> {cmd}"
        + f"\n-------------------------------------------------\n"
        + f"\n{error_text}"
        + f"-------------------------------------------------"
      )

      self.llm.llm_message_thread( self.thread_id, cmd + ' | ' + error_text )
      
      return error_text, False