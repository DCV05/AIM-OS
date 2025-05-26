import psutil
import os
import math
import subprocess
import asyncio
import traceback

from dotenv import load_dotenv
import os

load_dotenv()

_MB = pow( 1024, 2 )
_GB = pow( 1024, 3 )

class OS_INFO:

  # -------------------------------------------------------------------------------------
  # Funciones generales de formato de datos
  # -------------------------------------------------------------------------------------

  # Función para pasar de Bytes a Megabytes 
  def b_mb( self, b ):
    return math.trunc( b / _MB )
  
  # Función para pasar de Bytes a Gigabytes 
  def b_gb( self, b ):
    return math.trunc( b / _GB )
    
  # -------------------------------------------------------------------------------------
  # CPU
  # -------------------------------------------------------------------------------------

  def get_cpu( self ):

    # Calculamos el uso de CPU de 1, 5 y 15 minutos
    load_1, load_5, load_15 = psutil.getloadavg()

    # Calculamos la carga de la CPU en relación con el número de núcleos
    cpu_count   = psutil.cpu_count()
    load_per_1  = ( load_1  / cpu_count ) * 100
    load_per_5  = ( load_5  / cpu_count ) * 100
    load_per_15 = ( load_15 / cpu_count ) * 100
    
    # Calculamos el uso de CPU
    cpu_usage = psutil.cpu_percent()
    average_usage = ( cpu_usage / cpu_count )

    cpu_threads = subprocess.run(
          'ps -eLf | wc -l'
      ,   text           = True
      ,   shell          = True
      ,   capture_output = True
      ,   check          = True
    )

    return (
      f"{average_usage},"     # Average CPU Usage (%)
      f"{load_1:.2f},"        # Load Average Over 1' (%)
      f"{load_per_1:.2f},"    # Load Average Percentage Over 1' (%)
      f"{load_5:.2f},"        # Load Average Over 5' (%)
      f"{load_per_5:.2f},"    # Load Average Percentage Over 5' (%)
      f"{load_15:.2f},"       # Load Average Over 15' (%)
      f"{load_per_15:.2f},"   # Load Average Percentage Over 15' (%)
      f"{cpu_threads.stdout}" # Threads
    )
    
  # -------------------------------------------------------------------------------------
  # RAM
  # -------------------------------------------------------------------------------------
  
  def get_ram( self ):
    
    # Calculamos los datos de la memoria RAM y del swap
    memory_data = psutil.virtual_memory()
    swap_data   = psutil.swap_memory()
    
    # Capturamos los datos a valorar y les otorgamos un formato específico
    ram_total      = self.b_mb( memory_data.total   )
    ram_used       = self.b_mb( memory_data.used    )
    ram_buffers    = self.b_mb( memory_data.buffers )
    ram_total_swap = self.b_mb( swap_data.total     )
    ram_used_swap  = self.b_mb( swap_data.used      )
    
    return f"{ram_used},{ram_total},{ram_buffers},{ram_used_swap},{ram_total_swap}"
    
  # -------------------------------------------------------------------------------------
  # DISKS
  # -------------------------------------------------------------------------------------  
    
  def get_disks( self ):
    
    # Capturamos la lista de datos de los discos del servidor
    disks = psutil.disk_partitions()
    for disk in disks:
      
      # Calculamos los datos del disco
      disk_info = psutil.disk_usage( disk.mountpoint )
      
      # Formateo de campos
      disk_total   = self.b_gb( disk_info.total )
      disk_used    = self.b_gb( disk_info.used  )
      disk_free    = self.b_gb( disk_info.free  )
      disk_percent = disk_info.percent
      
      # Disk Space (GB), Disk Free Space (GB) y Disk Percent Used (%)
      disk_information = f"{disk_used},{disk_total},{disk_free},{disk_percent}"
      return disk_information
      
  # -------------------------------------------------------------------------------------
  # Networks
  # -------------------------------------------------------------------------------------
  
  def get_networks( self ):
    
    interfaces_arr = []
    
    # Según el tráfico, e capturarán loss datos de una interfaz u otra
    # Si no ha tenido una red tráfico, nos la saltamos
    traffic = psutil.net_io_counters( pernic = True )
    for interface, counter in traffic.items():
      if not counter.bytes_sent > 0 or not counter.bytes_recv > 0:
        interfaces_arr.append( interface )
        
    # Evaluamos los datos de las redes
    interfaces = psutil.net_if_addrs()
    for interface, details in interfaces.items():
      
      # Nos saltamos aquellas redes que no tienen tráfico de entrada o salida
      if interface in interfaces_arr:
        continue
      
      # Imprimimos los datos de aquellas redes que tengan algún tipo de tráfico
      net_information = f'{interface},'
      
      for info in details:
        net_information += f"{info.address},{info.netmask}"
        
      net_information += f'|'
    return net_information
        
  # -------------------------------------------------------------------------------------
  # OS
  # -------------------------------------------------------------------------------------
   
  def get_os( self ):
    
    # Calculamos la ruta del Daemon
    bash_path = __file__.replace( 'os_info/os_info.py', '/sys_info' )
    
    try:
      linux_result = subprocess.run(
            f'sh {bash_path}/info.sh'
        ,   text           = True
        ,   shell          = True 
        ,   capture_output = True
        ,   check          = True
      )
      
      return linux_result.stderr if linux_result.stderr else linux_result.stdout

    # Captura de excepciones
    except Exception as e:
      print( 'GO Error:', traceback.format_exc() )
      
  # -------------------------------------------------------------------------------------
  # Processes
  # -------------------------------------------------------------------------------------
      
  def get_ps( self ):
    
    process_dict = {}
    
    # Iteramos todos los procesos en ejecución
    for process in psutil.process_iter( [ 'pid', 'name', 'status', 'cpu_percent', 'memory_info' ] ):
      
      try:
        
        # Filtramos por los procesos que no estén inactivos o en estado 'sleep'
        if process.info['status'] in [ 'idle' ] or not self.b_mb( process.info['memory_info'].rss ) > 100.00:
          continue
        
        # Añadimos el proceso al array final
        process_data = {
            'pid': process.info['pid']
          , 'status': process.info['status']
          , 'cpu_percent': process.info['cpu_percent']
          , 'memory_rss': int ( self.b_mb( process.info['memory_info'].rss ) )
        }
        
        if process.info['name'] in process_dict:
          process_dict[ process.info['name'] ]['memory_rss'] += int( process_data['memory_rss'] )
        else:
          process_dict[ process.info['name'] ] = process_data
        
      except ( psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess ):
        continue
    
    process_arr = [
        f"{data['pid']},{name},{data['status']},{data['cpu_percent']},{data['memory_rss']}|"
        for name, data in process_dict.items()
    ]

    return "".join( process_arr )
    
  # -------------------------------------------------------------------------------------
  # MySQL
  # -------------------------------------------------------------------------------------  
  
  def get_mysql( self ):
    
    # Capturamos la contraseña de MySQL
    mysql_password = os.getenv( 'MYSQL_PASSWORD' )
    
    try: 
      mysql_result = subprocess.run(
            f'mysql -u root -p\'{mysql_password}\' -e "SELECT * FROM information_schema.processlist WHERE TIME > 1 and COMMAND != \'Sleep\'"'
          ,   text           = True
          ,   shell          = True
          ,   capture_output = True
          ,   check          = True
      )
      
      '''
      Id      User    Host       db     Command   Time  State     Info                    Progress
      62      root    localhost  NULL   Query     0     starting  SHOW FULL PROCESSLIST   0.000
      '''
        
      if mysql_result.stderr:
        return mysql_result.stderr
      else:
        # Separamos los registros
        lines = mysql_result.stdout.split('\n')
        lines = [ line.replace( '\t', ',' ) for line in lines ]
        return "|".join( lines )

    # Captura de excepciones
    except Exception as e:
      print( 'GO Error:', traceback.format_exc() )
    
  # -------------------------------------------------------------------------------------
  # Servicios
  # -------------------------------------------------------------------------------------  
    
  def get_services( self ):
    
    # Listado completo de servicios activos del sistema
    command = "systemctl list-units --type=service --state=running --no-legend --no-pager | awk '{print $1}' | sed 's/.service//g' | head -n 10"
    result = subprocess.run( command, shell = True, stdout = subprocess.PIPE, text = True )
    
    # Separar la salida en líneas y devolver la lista de nombres de servicios
    service_names = result.stdout.strip().replace( '\n', '|' )
    return service_names