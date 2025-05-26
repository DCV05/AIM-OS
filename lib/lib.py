from rich.syntax import Syntax
from rich.table import Table
from rich import box

import re
import asyncio
import traceback
import subprocess
import re
import time

# Comprobación de comandos Linux
import shutil

def find_linux_cmd( cmd_text: str ) -> bool:
  """
  Verifica si un comando dado es un comando válido de Linux.

  Args:
    cmd_text (str): La cadena de texto que representa el comando a verificar.
                    Puede incluir el comando y sus argumentos, pero solo el
                    nombre del comando será evaluado.

  Returns:
    bool: True si el comando es un comando válido de Linux, False en caso contrario.

  Ejemplos:
    >>> find_linux_cmd("ls -l")
    True
    >>> find_linux_cmd("fakecommand")
    False
  """

  linux_commands = [
    "ls", "cd", "mv", "cp", "rm", "echo", "cat", "grep", "find",
    "chmod", "chown", "sudo", "apt-get", "mkdir", "rmdir", "touch",
    "nano", "vi", "vim", "ps", "kill", "df", "du", "free", "top", "htop",
    "ifconfig", "ip", "netstat", "ss", "ping", "systemctl", "service",
    "dmesg", "journalctl", "tar", "gzip", "gunzip", "zip", "unzip", "wget",
    "curl", "ssh", "scp", "rsync", "mount", "umount", "fdisk", "parted",
    "chkconfig", "yum", "dnf", "rpm", "apt", "dpkg", "snap", "flatpak", "ufw",
    "firewalld", "iptables", "crontab", "at", "alias", "unalias", "bg", "fg",
    "jobs", "killall", "watch", "lsof", "nc", "traceroute", "dig", "who", "whoami",
    "last", "useradd", "usermod", "userdel", "groupadd", "groupdel", "passwd",
    "chmod", "chown", "locate", "updatedb", "man", "info", "which", "whereis",
    "history", "cmp", "diff", "patch", "ac", "ar", "as", "bc", "dc", "dd", "ed",
    "sed", "awk", "sort", "uniq", "cut", "paste", "join", "comm", "expand", "unexpand",
    "fold", "pax", "cpio", "bzip2", "xz", "make", "gcc", "g++", "git", "svn", "make",
    "nm", "objdump", "strace", "ltrace", "gdb", "perf", "getent", "stat", "touch", "test", "pwd",
    "pip"
  ]
  
  # Obtenemos el primer componente del comando
  cmd = cmd_text.split()[0]
  
  # Comprobamos si es un comando Linux
  return cmd in linux_commands or shutil.which( cmd ) is not None

# Función para detectar un comando UNIX
def find_metacommands( text ):
  """
  Detecta un metacomando en una cadena de texto.

  Args:
    text (str): La cadena de texto que se va a analizar para encontrar metacomandos.

  Returns:
    str: El metacomando encontrado en la cadena de texto si existe, 
          en el formato "#comando#", o None si no se encuentra ningún metacomando.

  Ejemplos:
    >>> find_metacommands("Este es un #metacomando# de ejemplo.")
    '#metacomando#'
    >>> find_metacommands("Texto sin metacomando.")
    None
  """
  
  metacommand_pattern = r"#([^@]+)#"
  match = re.search( metacommand_pattern, text )
  return match.group() if match is not None else None

# Función para detectar un comando UNIX
def find_unix_cmd( text ) -> bool:
  """
  Detecta un comando UNIX en una cadena de texto.

  Args:
      text (str): La cadena de texto que se va a analizar para encontrar comandos UNIX.

  Returns:
      bool: True si se encuentra un comando UNIX en el formato "@comando@", False en caso contrario.

  Ejemplos:
      >>> find_unix_cmd("Este es un @comando@ UNIX.")
      True
      >>> find_unix_cmd("Texto sin comando UNIX.")
      False
  """
  unix_pattern = r"@([^@]+)@"
  return bool( re.search( unix_pattern, text ) )

# Análisis y ejecución de metacomandos
async def analyze_metacommand( **kwargs ):
  """
  Analiza y ejecuta un metacomando si está presente en los argumentos.

  Args:
    **kwargs: Argumentos clave-valor que deben incluir:
      - metacommand_name (str): El nombre del metacomando a ejecutar.
      - metacommands (obj): Un objeto que contiene las definiciones de los metacomandos como métodos.

  Returns:
    Any: El resultado de la ejecución del metacomando si se encuentra y se ejecuta, None en caso contrario.

  Ejemplos:
    >>> class Metacommands:
    ...     async def meta_test(self, **kwargs):
    ...         return "Test executed"
    >>> metacommands = Metacommands()
    >>> result = await analyze_metacommand(metacommand_name="#test#", metacommands=metacommands)
    >>> print(result)
    'Test executed'
  """
  
  if kwargs.get( 'metacommand_name' ):
    metacommand_name = kwargs.get( 'metacommand_name' ).replace( '#', '' )
    metacommands = kwargs.get( 'metacommands' )
  
    # Ejecutamos el metacomando
    function_name = f"meta_{metacommand_name}"
    if hasattr( metacommands, function_name ):
      function = getattr( metacommands, function_name )

      metacommand_result = await function( **kwargs )
      return metacommand_result
  
  else:
    return None
  
# -------------------------------------------------------------------------------------------
# Control de servicios
# -------------------------------------------------------------------------------------------

async def turn_off_service( service_name, sudo_password ):

  try:
    
    result = subprocess.run(
          f'echo "{sudo_password}" | sudo -S systemctl stop {service_name}'
      ,   text           = True
      ,   shell          = True
      ,   capture_output = True
      ,   check          = True
    )
    
    print( f"Service {service_name} stopped" )
    
  # Captura de excepciones
  except Exception as e:
    print( 'TOS Error:', traceback.format_exc() )

async def turn_on_service( service_name, sudo_password ):

  try:
    
    result = subprocess.run(
          f'echo "{sudo_password}" | sudo -S systemctl start {service_name}'
      ,   text           = True
      ,   shell          = True
      ,   capture_output = True
      ,   check          = True
    )
    
    print( f"Service {service_name} started" )
    
  # Captura de excepciones
  except Exception as e:
    print( 'TOS Error:', traceback.format_exc() )

async def restart_service( service_name, sudo_password ):

  try:
    
    result = subprocess.run(
          f"echo '{sudo_password}' | sudo -S systemctl restart {service_name}"
      ,   text           = True
      ,   shell          = True
      ,   capture_output = True
      ,   check          = True
    )
    
    print( f"Service {service_name} restarted" )
    
  # Captura de excepciones
  except Exception as e:
    print( 'TOS Error:', traceback.format_exc() )


def convert_markdown_to_rich( text ):
  text = re.sub( r"\*\*(.*?)\*\*", r"[bold]\1[/bold]", text )
  text = re.sub( r"__(.*?)__", r"[underline]\1[/underline]", text )
  text = re.sub( r"~~(.*?)~~", r"[strike]\1[/strike]", text )
  text = re.sub( r"\*(.*?)\*", r"[italic]\1[/italic]", text )
  return text

def rich_formatter( response_text, console ):
  response_fragments = response_text[0].split( "\n\n" )

  try:
    for frag in response_fragments:
      if "```" in frag:
        sections = frag.split( "```" )
        for i, section in enumerate( sections ):
          section = section.replace( '```rich', '```python' )
          if i % 2 == 0:
            # Detectar tablas o texto con Rich Markup
            if "|" in section and "\n" in section:
              render_table( section, console )
            else:
              # Convertir ** a [bold] y __ a [underline]
              section = convert_markdown_to_rich( section )
              console.print( section.strip() )  # Aquí utilizamos Rich Markup
          else:
            # Procesar bloques de código
            syntax = Syntax( section.strip(), "python", theme = "monokai" )
            console.print( syntax )
        console.print( "\n" )
        console.file.flush()
      else:
        if "|" in frag and "\n" in frag:
          console.print( "\n" )
          render_table( frag, console )
          console.print( "\n" )
        else:
          # Convertir ** a [bold] y __ a [underline]
          frag = convert_markdown_to_rich( frag )
          console.print( frag.strip() )  # Aquí utilizamos Rich Markup
        console.file.flush()

  except BlockingIOError:
    time.sleep( 0.1 )
    console.print( response_text.strip() )
    console.file.flush()

def render_table( text, console ):
  lines = text.strip().split( "\n" )
  
  # Crear la tabla con título y estilo mejorado
  table = Table(
    box=box.ROUNDED,  # Estilo de borde
    show_lines=True  # Mostrar líneas entre filas
  )

  # Agregar columnas (encabezados)
  headers = lines[0].split( "|" )
  for header in headers:
    table.add_column( header.strip(), justify="center", style="bold yellow" )

  # Agregar las filas con un estilo zebra (alternando colores)
  for i, line in enumerate( lines[1:] ):
    row = line.split( "|" )
    row_style = "dim" if i % 2 == 0 else ""
    table.add_row( *[cell.strip() for cell in row], style=row_style )

  # Imprimir la tabla en la consola
  console.print( table )
