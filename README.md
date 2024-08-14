The feature development has been done in Python. Python was chosen for its extensive libraries and frameworks that simplify rapid development of speech processing functionalities. Following the research phase, the chosen speech recognition libraries viz., Google Cloud Speech-to-text API, Whisper offline API and Vosk API, were used to implement the voice command feature into the existing software.

The following libraries were used for the implementation:
•	Vosk: The Vosk library is used for converting spoken language into text. It provides an easy-to-use interface for integrating speech recognition into Python applications and supports various languages and models. The Kaldi recognizer model ‘vosk-model-small-en-us-0.15’ is accessed through Vosk library here.
•	Whisper: Whisper API library allows multilingual speech recognition and translation by loading a single model ‘tiny’ or ‘base’. There are also. en models for English-only usage. The speech frames captured through PyAudio are written to a .wav file, and this file is transcribed using transcribe method.
•	PyAudio: PyAudio is used to capture audio from a microphone. It facilitates interaction with audio streams, enabling the application to record speech in real-time.
•	SpeechRecognition: The SpeechRecognition library is used to capture and transcribe spoken words into text and it provides an interface to Google Web Speech API, which is also used in the alternative implementation.
•	Requests: The Requests library is used to make HTTP requests to a remote REST server to start or stop specific modes based on recognized speech commands.
•	JSON: JSON is used to handle data formats when interacting with external services, particularly for sending and receiving data.
•	Queue: The Queue module is used to manage a thread-safe queue for handling commands and communication between different threads of the application.
•	Logging: The Logging library is used to track errors, warnings, and status messages.
•	Psutil:  Psutil is used to find services listening on specific ports, which helps in identifying the IP and port for the REST server.

Design
------

The SpeechController class manages the system's state transitions through the SpeechState enum. This class contains the following components: 
*	a Logger for logging 
*	a Model (in English language) from the vosk library for speech recognition
*	a queue.Queue for managing command execution
*	pyaudio for audio processing
*	wave for file handling
*	requests for HTTP requests
*	time library for latency calculation. 
It also implements methods to recognize speech and activate specific modes (long or short) by communicating with RESTful API services through HTTP requests. The main script initializes the SpeechController, sets up a multithreading environment with threading.Thread to concurrently run speech recognition and command processing. It retrieves the REST service port address using find_service_ip_by_port().


Here is a step-by-step explanation of the sequence diagram:
•	The user starts the main program, initiating the speech recognition system.
•	The main program initializes the logger and sets up network configurations. It creates a SpeechController instance and a command queue.
•   The main program starts two threads: recognize_speech_thread() and process_command_thread().
    recognize_speech_thread() records audio input from the microphone using PyAudio. The microphone listens iteratively a certain time assigned to the RECORD_SECONDS variable. It identifies commands (e.g., "long," "short," or "stop") from the transcribed text [18].
    process_command_thread() retrieves commands from the command queue and invokes methods on the SpeechController to send HTTP requests to the REST API.
•	The Vosk Kaldi recognizer transcribes the recorded audio into text.
•	The REST API executes the appropriate massage sequence based on the command and updates the state: mode_long, mode_short, or stop.
•	If an error occurs, the system logs the error and updates the state accordingly. 

