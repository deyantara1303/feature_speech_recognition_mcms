import speech_recognition as sr
from enum import Enum
import requests
import time

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
        self.__recognizer = sr.Recognizer()

    def get_current_state(self) -> SpeechState:
        '''
        Returns the current state of the SpeechController.
        '''
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
        except RuntimeError as err:
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
        except RuntimeError as err:
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
        except RuntimeError as err:
            self.__logger.warning('Error: %s----Cannot stop mode, current state is %s', err, self.__currentstate.name)

        end_time = time.time()
        execution_time = end_time - start_time
        self.__logger.info(f"Execution time of stop mode: {execution_time:.2f} seconds")

    def recognize_speech(self) -> SpeechState:
        self.__logger.info("Running MCMS Speech Recognition using Google Cloud") 
        with sr.Microphone() as source:
            self.__logger.info("Listening on mic ....")
            self.__recognizer.adjust_for_ambient_noise(source)
            audio = self.__recognizer.listen(source)

            try:
                start_time = time.time()
                # Recognize speech using Google Speech Recognition
                command = self.__recognizer.recognize_google(audio)

                # Check if the recognized command identifies "long"  
                if "long" in command.lower():
                    self.__currentstate = SpeechState.mode_long

                # Check if the recognized command identifies "short"
                elif "short" in command.lower():
                    self.__currentstate = SpeechState.mode_short

                # Check if the recognized command identifies "stop"
                elif "stop" in command.lower():
                    self.__currentstate = SpeechState.stop

                else:
                    self.__logger.warning("Command not recognized, previous state was %s. Setting current staate to idle", 
                                          self.__previousstate)
                    self.__currentstate = SpeechState.idle

            except sr.UnknownValueError:
                print("Mic is listening, but could not understand")
                self.__currentstate = SpeechState.idle
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                self.__currentstate = SpeechState.error

            end_time = time.time()
            execution_time = end_time - start_time
            self.__logger.info(f"Execution time of transcription: {execution_time:.2f} seconds")

            if self.__currentstate == SpeechState.mode_long or self.__currentstate == SpeechState.mode_short:
                self.__previousstate = self.__currentstate;
            
            return self.__currentstate