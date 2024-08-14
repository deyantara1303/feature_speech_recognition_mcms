from enum import Enum
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import wave
import requests
import time

CHANNELS = 1
CHUNK = 1024
FRAME_RATE = 16000
RECORD_SECONDS = 10
AUDIO_FORMAT = pyaudio.paInt16
SAMPLE_SIZE = 2
WAVE_OUTPUT_FILENAME = "file.wav"

class SpeechState(Enum):
    idle = 0
    mode_long = 1
    mode_short = 2
    stop = 3
    error = 4

class SpeechController:
    def __init__(self, logger, command_queue) -> None:
        self.__logger = logger
        self.__currentstate = SpeechState.idle
        self.__previousstate = SpeechState.idle
        self.__model = Model(model_name="vosk-model-small-en-us-0.15")
        self.__rec = KaldiRecognizer(self.__model, FRAME_RATE)
        self.__frames = []
        self.command_queue = command_queue

    def get_current_state(self) -> SpeechState:
        return self.__currentstate

    def start_mode_long(self, ip_addr, port):
        start_time = time.time()
        self.__logger.info("Command recognized: Activated Long Massage mode, %s", self.__currentstate)
        file_path = "assets/sample_long.json"
        url = f"http://{ip_addr}:{port}/sequence/1"
        headers = {'Content-Type': 'application/json'}
        try:
            with open(file_path, "r") as file:
                json_data = file.read()
            response = requests.put(url, headers=headers, data=json_data)
            url = f"{url}/start"
            response = requests.put(url)
            self.__logger.info("Sequence status %d -- %s", response.status_code, response.text)
        except Exception as err:
            self.__logger.warning('Error: %s----Cannot start mode long, current state is %s', err, self.__currentstate.name)
  
        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time of long mode: {execution_time:.2f} seconds")

    def start_mode_short(self, ip_addr, port):
        start_time = time.time()
        self.__logger.info("Command recognized: Activated Short Massage mode, %s", self.__currentstate)
        file_path = "assets/sample_short.json"
        url = f"http://{ip_addr}:{port}/sequence/2"
        headers = {'Content-Type': 'application/json'}
        try:
            with open(file_path, "r") as file:
                json_data = file.read()            
            response = requests.put(url, headers=headers, data=json_data)
            url = f"{url}/start"
            response = requests.put(url)
            self.__logger.info("Sequence status %d %s", response.status_code, response.text)
        except Exception as err:
            self.__logger.warning('Error: %s----Cannot start mode short, current state is %s', err, self.__currentstate.name)
    
        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time of short mode: {execution_time:.2f} seconds")

    def stop_mode(self, ip_addr, port):
        start_time = time.time()
        if self.__previousstate == SpeechState.mode_long:
            url = f"http://{ip_addr}:{port}/sequence/1"
        elif self.__previousstate == SpeechState.mode_short:
            url = f"http://{ip_addr}:{port}/sequence/2"
        else:
            return
        try:
            self.__logger.info("Stop mode. %s", self.__currentstate)
            url = f"{url}/stop"
            response = requests.put(url)
            self.__logger.info("Sequence status %d %s", response.status_code, response.text)
        except Exception as err:
            self.__logger.warning('Error: %s----Cannot stop mode, current state is %s', err, self.__currentstate.name)

        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time of stop mode: {execution_time:.2f} seconds")


    def recognize_speech(self) -> None:
        self.__logger.info("Running MCMS Speech Recognition using Vosk LLM multi-threading") 
        self.__frames = []   
        self.__rec.SetWords(True)
        try:
            self.__audio = pyaudio.PyAudio()
            self.__stream = self.__audio.open(format=AUDIO_FORMAT,
                                          channels=CHANNELS,
                                          rate=FRAME_RATE,
                                          input=True,
                                          input_device_index=0,
                                          frames_per_buffer=CHUNK)
            self.__logger.info("Recording on mic .....using Vosk") 

            # Record speech frames from microphone for RECORD_SECONDS
            for i in range(0, int(FRAME_RATE / CHUNK * RECORD_SECONDS)):
                data = self.__stream.read(CHUNK)
                self.__frames.append(data)
            self.__logger.info("Finished recording")

            start_time = time.time()
            # Transcribe using Kaldi recognizer
            self.__rec.AcceptWaveform(b''.join(self.__frames))
            result = self.__rec.Result()
            text = json.loads(result)["text"]
            print(text)
        
            # Check if the recognized command identifies "long"     
            if "long" in text:
                self.command_queue.put(SpeechState.mode_long)
                self.__currentstate = SpeechState.mode_long
            # Check if the recognized command identifies "short"
            elif "short" in text:
                self.command_queue.put(SpeechState.mode_short)
                self.__currentstate = SpeechState.mode_short
            # Check if the recognized command identifies "stop"
            elif "stop" in text:
                self.command_queue.put(SpeechState.stop)
                self.__currentstate = SpeechState.stop
            else:
                self.__logger.warning("Command not recognized, Current state is %s, previous state was %s", 
                                      self.__currentstate, self.__previousstate)
                self.__currentstate = SpeechState.idle
        except Exception as e:
            self.__logger.error(f"Could not request results; {e}")
            self.command_queue.put(SpeechState.error)
        
        finally:
            if self.__stream:
                self.__stream.stop_stream()
                self.__stream.close()
            if self.__audio:
                self.__audio.terminate()

        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time of transcription: {execution_time:.2f} seconds")

        if self.__currentstate == SpeechState.mode_long or self.__currentstate == SpeechState.mode_short:
            self.__previousstate = self.__currentstate;
