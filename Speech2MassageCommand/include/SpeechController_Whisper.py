from enum import Enum
import whisper
import pyaudio
import wave
import requests
import time

CHANNELS = 2
CHUNK = 1024
FRAME_RATE = 44100
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
    def __init__(self, logger) -> None:
        self.__logger = logger
        self.__currentstate = SpeechState.idle
        self.__previousstate = SpeechState.idle
        self.__model = whisper.load_model("base")
        self.__audio = None
        self.__frames = []
        self.__stream = None 

    def get_current_state(self) -> SpeechState:
        '''
        Returns the current state of the SpeechController.
        '''
        return self.__currentstate
    
    
    def start_mode_long(self, ip_addr, port):
        start_time = time.time()
        self.__logger.info("Command recognized: Activated Long Massage mode, %s", self.__currentstate)

        file_path = "assets/shop_massage_long.json"
        url = f"http://{ip_addr}:{port}/sequence/1"
        headers = {'Content-Type': 'application/json'}

        try: 
            with open(file_path, "r") as file:
                json_data = file.read()
            response = requests.put(url, headers=headers, data=json_data)
            url = f"{url}/start"
            response = requests.put(url)
            self.__logger.info("Sequence status %d -- %s", response.status_code, response.text)
        except RuntimeError as err:
            self.__logger.warning('Error: %s----Cannot start mode long, current state is %s', err, self.__currentstate.name)
    
        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time: {execution_time:.2f} seconds")
    
    def start_mode_short(self, ip_addr, port):
        start_time = time.time()
        self.__logger.info("Command recognized: Activated Short Massage mode, %s", self.__currentstate)

        file_path = "assets/shop_massage_short.json"
        url = f"http://{ip_addr}:{port}/sequence/2"
        headers = {'Content-Type': 'application/json'}

        try: 
            with open(file_path, "r") as file:
                json_data = file.read()            
            response = requests.put(url, headers=headers, data=json_data)
            url = f"{url}/start"
            response = requests.put(url)
            self.__logger.info("Sequence status %d %s", response.status_code, response.text)
        except RuntimeError as err:
            self.__logger.warning('Error: %s----Cannot start mode short, current state is %s', err, self.__currentstate.name)
    
        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time: {execution_time:.2f} seconds")

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
        except RuntimeError as err:
            self.__logger.warning('Error: %s----Cannot stop mode, current state is %s', err, self.__currentstate.name)

        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time: {execution_time:.2f} seconds")


    def recognize_speech(self) -> SpeechState:
        start_time = time.time()
        self.__logger.info("Running MCMS Speech Recognition using Whisper LLM single-threaded") 
        self.__frames = []  
        try: 
            self.__audio = pyaudio.PyAudio()
            self.__stream = self.__audio.open(format=AUDIO_FORMAT,
                        channels=CHANNELS,
                        rate=FRAME_RATE,
                        input=True,
                        input_device_index=1,
                        frames_per_buffer=CHUNK) 
            self.__logger.info("Recording on mic .....")            
            # Start recording
            for i in range(0, int(FRAME_RATE/CHUNK * RECORD_SECONDS)):
                data = self.__stream.read(CHUNK)
                self.__frames.append(data)
            self.__logger.info("Finished recording")

            # Write to new .wav file
            with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wavFile:
                wavFile.setnchannels(CHANNELS)
                wavFile.setsampwidth(self.__audio.get_sample_size(AUDIO_FORMAT))
                wavFile.setframerate(FRAME_RATE)
                wavFile.writeframes(b''.join(self.__frames))
                wavFile.close()

            result = self.__model.transcribe(WAVE_OUTPUT_FILENAME)
            print(result)

            # Check if the recognized command matches "activate mode long"
            if "long" in result['text'].lower():
                self.__currentstate = SpeechState.mode_long

            # Check if the recognized command matches "activate mode short"
            elif "short" in result['text'].lower():
                self.__currentstate = SpeechState.mode_short

            # Check if the recognized command matches "stop"
            elif "stop" in result['text'].lower():
                self.__currentstate = SpeechState.stop

            else:
                self.__logger.warning("Command not recognized, previous state was %s. \
                                      Setting current state to idle", self.__currentstate)
                self.__currentstate = SpeechState.idle
        
        except Exception as e:
            print(f"Could not request results; {e}")
            self.__currentstate = SpeechState.error

        finally:    
            if self.__stream:
                # Stop recording
                self.__stream.stop_stream()
                self.__stream.close()
            if self.__audio:
                self.__audio.terminate()

        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time: {execution_time:.2f} seconds")

        if self.__currentstate == SpeechState.mode_long or self.__currentstate == SpeechState.mode_short:        
            self.__previousstate = self.__currentstate;
        
        return self.__currentstate
    