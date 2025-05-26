#![allow(unused_imports)]
#![allow(dead_code)]

#[macro_use]
extern crate lazy_static;
extern crate regex;
extern crate sysinfo;

use std::{sync::{Arc, Mutex}, thread, process::Command, str, env};
use sysinfo::{System, CpuRefreshKind, MemoryRefreshKind, ProcessRefreshKind, Networks, Disks};
use regex::Regex;

// Constantes matemáticas
const _KB: u64 = 1024;
const _KB_MB: u64 = _KB * _KB;
const _KB_GB: u64 = _KB_MB * _KB;

// Constantes del sistema de archivos del servidor Linux
lazy_static! {
  static ref _SYSTEM_DIRS_REGEX: Regex = Regex::new(
    r"^/(bin|sbin|lib|lib64|etc|boot|var/lib/dpkg|var/lib/apt/lists|var/cache/apt/archives|usr/lib|usr/sbin|sys|proc|dev|run|etc/init.d|etc/systemd|root)(/|$)"
  ).unwrap();
  static ref _PS_PID: Arc<Mutex<Vec<u32>>> = Arc::new( Mutex::new( Vec::new() ) );
  static ref SYS: Arc<Mutex<System>> = Arc::new( Mutex::new( System::new() ) );
}

fn main() {

  let args: Vec<String> = env::args().collect();

  // Dependiendo del parámetro insertado, ejecutaremos un módulo u otro
  if args.len() > 1 {
    match args[1].as_str() {
      "process"    => process(),
      "subprocess" => subprocess(),
      &_           => todo!()
    }
  }
}

fn process() {

  // Ejecutamos los módulos en hilos separados
  let handle_pc = thread::spawn( get_pc );
  let handle_ps = thread::spawn( get_ps );
  let handle_os = thread::spawn( get_os );
  // let handle_services = thread::spawn( get_services );

  // Esperamos a que todos los hilos terminen
  handle_pc.join().unwrap();
  handle_ps.join().unwrap();
  handle_os.join().unwrap();
  // handle_services.join().unwrap();

}

fn subprocess() {

  // Ejecutamos los módulos en hilos separados
  let handle_pc = thread::spawn( get_pc );
  let handle_ps = thread::spawn( get_ps );

  // Esperamos a que todos los hilos terminen
  handle_pc.join().unwrap();
  handle_ps.join().unwrap();

}

fn get_pc() {
  
  // Clonamos la instancia de System mediante una referencia
  let sys_pc = Arc::clone( &SYS );

  // RAM CPU | Refrescamos los datos y los mostramos por pantalla
  let handle_pc = thread::spawn( move || {

    // Bloqueamos el Mútex y recibimos la instancia System
    let mut sys_inner = match sys_pc.lock() {
      Ok( inner ) => inner,
      Err(_) => {
        return;
      }
    };

    // Refresco de datos
    sys_inner.refresh_memory_specifics( MemoryRefreshKind::new().with_ram() );
    sys_inner.refresh_cpu_specifics( CpuRefreshKind::everything().without_frequency() );

    // Inicializamos el array de Cores y el índice
    let mut cores = Vec::new();
    let mut core_index = 0;

    // Iteramos cada núcleo y calculamos si debe ser insertado en el array
    for cpu in sys_inner.cpus() {
      let usage = ( cpu.cpu_usage() * 100.0 ).trunc() / 100.0;
      cores.push( format!( "Core {}: {:.2}", core_index, usage ) );
      core_index += 1;
    }  

    // Inicializamos el array de la memoria
    let mut memory_arr = Vec::new();
    memory_arr.push( format!( "MemTotal: {}MB,",  ( sys_inner.total_memory() / _KB_MB ) ) );
    memory_arr.push( format!( "MemUsed: {}MB,",   ( sys_inner.used_memory()  / _KB_MB ) ) );
    memory_arr.push( format!( "SwapTotal: {}MB,", ( sys_inner.total_swap()   / _KB_MB ) ) );
    memory_arr.push( format!( "SwapUsed: {}MB",  ( sys_inner.used_swap()    / _KB_MB ) ) );

    // Refrescamos los datos de los discos duros
    let disks = Disks::new_with_refreshed_list();
    for disk in disks.list() {

      println!(
          "DISK * {:?} * Capacity: {}GB/{}GB | "
        , disk.name()
        , ( disk.available_space() / _KB_GB )
        , ( disk.total_space() / _KB_GB )
      );
    }

    // Inicializamos la lista de redes del ordenador
    // Possteriormente, actualizamos sus datos
    let mut networks = Networks::new_with_refreshed_list();
    networks.refresh();

    // Iteramos la referencia de las redes
    for ( _interface_name, network ) in &networks {

      // Capturamos el total_received
      let total_received: u32 = match network.total_received().try_into() {
        Ok( result ) => result,
        Err( _ ) => {
          continue;
        }
      };

      if total_received > 0 {
        println!(
            "NET * {} * Rcv: {}B, Tx: {}B, Pkt Rcv: {}, Pkt Tx: {}, Err Rcv: {}, Err Tx: {} | "
          , _interface_name
          , network.total_received()
          , network.total_transmitted()
          , network.total_packets_received()
          , network.total_packets_transmitted()
          , network.total_errors_on_received()
          , network.total_errors_on_transmitted()
        );
      }
      else {
        continue;
      }        
    }

    println!( "RAM * Usage * {} | ", memory_arr.join( " " ) );
    println!( "CPU * Usage * {} | ", cores.join( ", " ) );
  } );

  // Cerramos los hilos
  match handle_pc.join(){
    Ok( result ) => result,
    Err( _ ) => {
      return;
    }
  };

}

fn get_ps() {

  // Clonamos la instancia de los directorios
  let ps_pid_clon = Arc::clone( &_PS_PID );

  // Clonamos la instancia de System y generamos un hilo
  let sys_ps    = Arc::clone( &SYS );
  let handle_ps = thread::spawn( move || {

    // Bloqueamos el Mútex y recibimos la instancia System
    let mut sys_inner = match sys_ps.lock() {
      Ok( inner ) => inner,
      Err(_) => {
        return;
      }
    };

    sys_inner.refresh_processes_specifics( ProcessRefreshKind::everything().with_cpu() );

    // Inicializamos un buffer de datos
    let mut buffer = Vec::new();

    // Por cada proceso refrescado
    for ( _, process ) in sys_inner.processes() {

      // Si el proceso es ejecutado por un usuario de Sistema, nos lo saltamos
      if let Some( uid ) = process.effective_user_id() {
        if **uid < 1000 {
          continue;
        }
      }

      // Comprobamos que consume mucha memoria y si no lo hemos declarado en el buffer de procesos
      if process.memory() > 100 * _KB_MB && process.cpu_usage() > 0.00 {

        // Evluación de procesos
        if !buffer.iter().any( | ( _, item ): &( u32, [String; 4] ) | item[0] == process.name() ) {

          if let Some( _exe_path ) = process.exe() {

            // Si la ruta se trata de una del propio sistema, no incluímos el proceso
            let is_system_process = _SYSTEM_DIRS_REGEX.is_match( &_exe_path.to_string_lossy() );

            // Si no es un proceso de sistema, lo añadimos al buffer
            if !is_system_process {
              let _temp_pid: u32 = process.pid().as_u32();

              // Insertamos los datos en el array
              buffer.push( (
                _temp_pid,
                [
                  process.name().to_string(),
                  _exe_path.to_string_lossy().into_owned(),
                  process.memory().to_string(),
                  process.cpu_usage().to_string()
                ],
              ) );
            } else {
              continue;
            }
          }

          // Instanciamos la constante del historial
          let mut ps_pid = match ps_pid_clon.lock() {
            Ok( result ) => result,
            Err( _ ) => {
              continue
            }
          };

          // Si no ha sido añadido antes al historial, lo añadimos
          if !ps_pid.contains( &process.pid().as_u32() ) {
            ps_pid.push( process.pid().as_u32() );
          }
          
        }
      }
    }

    // Iteramos los datos del buffer
    // Capturamos el id y el envoltorio de la ruta y el nombre del proceso a valorar
    for ( pid, data ) in buffer {
      println!(
        "PROCESS * PID: {:?}, Name: {:?}, Exe: {:?}, Memory {:?}, CPU_Usage {:?} | ",
        pid, data[0], data[1], data[2], data[3]
      );
    }
  });

  // Cerramos el hilo
  match handle_ps.join(){
    Ok( result ) => result,
    Err(_) => {
      return;
    }
  };
}

fn get_os() {

  // Clonamos la instancia de System e inicializamos un hilo
  let sys_os    = Arc::clone( &SYS );
  let handle_os = thread::spawn( move || {

    // Iniciamos la sesión de os_info para capturar los datos del sistema
    let info = os_info::get();

    // Bloqueamos el hilo para impedir condiciones de carrera
    let mut sys_inner = match sys_os.lock() {
      Ok( result ) => result,
      Err( _ ) => {
        return;
      }
    };

    sys_inner.refresh_all();

    // Calculamos los campos a devolver
    let pc_name  = System::name();
    let kernel_v = System::kernel_version();
    let os_v     = System::os_version();

    // Imprimimos los resultados
    println!( "OS * {}, Kernel Version {}, OS Version {}, Bitness {}, Architecture {:?} | "
      , pc_name.expect("REASON").to_string()
      , kernel_v.expect("REASON").to_string()
      , os_v.expect("REASON").to_string()
      , info.bitness()
      , info.architecture()
    );
    
  } );

  // Cerramos el hilo de ejecución
  match handle_os.join() {
    Ok( result ) => result,
    Err(_) => {
      return;
    }
  };
}


fn get_services() {

let mut services = Vec::new();

  // Ejecutamos el comando
  let cmd_output = Command::new( "sh" )
    .arg( "-c" )
    .arg( "systemd-cgtop --batch --iterations=1 --order=memory" )
    .output()
    .expect( "Failed" );

  // Si el comando es correcto
  if cmd_output.status.success() {
    let cmd_output_str = str::from_utf8( &cmd_output.stdout ).unwrap();

    // Iteramos cada proceso
    for item in cmd_output_str.lines() {

      // Formateo de campos
      let service_name = item.split_whitespace().next().unwrap();

      // Si el array de procesos no contiene, lo añadimos
      if !services.contains( &service_name.to_string() ) {
        services.push( service_name.to_string() );
      }
      
    }
  }

  println!( "SERVICE * {:?} | ", services );
}