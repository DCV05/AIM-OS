import os
import json
import sys
from lib.lib import *
from rich.console import Console

# Variables de entorno
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv( 'OPENAI_API_KEY' )

from openai import OpenAI
client = OpenAI()
from typing_extensions import override
from openai import AssistantEventHandler

# Clase LLM
class LLM:
  
  def __init__( self, assistant_id ):
    self.assistant_id = assistant_id
    self.console      = Console()

  # LLM | Crear un thread en LLM
  def llm_create_thread( self ):
    thread = client.beta.threads.create()
    return thread

  # LLM | Añadir un mensaje al thread
  def llm_message_thread( self, thread_id, text_message ):

    # Añadimos el mensaje al thread
    message = client.beta.threads.messages.create(
        thread_id = thread_id
      , role      = 'user'
      , content   = text_message
    )
    
    return message

  # LLM | Ejecutar mensaje de thread con un assistant específico
  def llm_run_thread( self, thread_id ):

    # Instancia del event_handler
    handler = event_handler()

    # Ejecutamos el thread y los mensajes que contiene
    with client.beta.threads.runs.create_and_stream(
        thread_id         = thread_id
      , assistant_id      = self.assistant_id
      , temperature       = 0.0
      , max_prompt_tokens = 1500
      , event_handler     = handler
    ) as stream:
      stream.until_done()

    # Capturamos el mensaje final y lo retornamos
    answer_llm = handler.get_answer_llm()
    json_answer = json.loads( answer_llm )

    if json_answer['response_type'] == 'text':
      print( "\n\n" )
      rich_formatter( json_answer['response'], self.console )

    return json_answer

# Mediador entre el mensaje streaming y la aplicación
class event_handler( AssistantEventHandler ):
  
  # Constructor
  def __init__( self ):
    super().__init__()
    self.answer_llm_parts = ''

  @override
  def on_text_created( self, text ) -> None:
    print( f'---------------------------\nLLM: ', end = "", flush = True )

  # Mensaje streaming
  @override
  def on_text_delta( self, delta, snapshot ):
    self.answer_llm_parts += delta.value
    print( delta.value, end = "", flush = True )

  # Captura mensaje final
  def get_answer_llm( self ):
    return self.answer_llm_parts