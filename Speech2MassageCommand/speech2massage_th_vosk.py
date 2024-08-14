import logging, socket, psutil, threading, queue
from   include.SpeechController_Vosk_Th import SpeechController
from   include.SpeechController_Vosk_Th import SpeechState

# --------------------------------------------------
# *  Section:  Main - Subroutines                  *
# --------------------------------------------------
def mainReturnLogger(name:str, level:str):
    logging.basicConfig(format='%(asctime)s  [%(filename)-16s] [%(levelname)-7s] [%(funcName)-20s]  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return(logger)


def mainGetLocalIpAddress() -> str:
    '''
    Returns the local ip address of the machine the programm is running on.
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def find_service_ip_by_port(port_number):
    for conn in psutil.net_connections():
        if conn.status == psutil.CONN_LISTEN and conn.type == socket.SOCK_STREAM and conn.laddr.port == port_number:
            ip_address = conn.laddr.ip
            return ip_address
    return None


def recognize_speech_thread(sc):
    logger.info('Starting recognize speech thread')
    while True:
        sc.recognize_speech()


def process_command_thread(sc, restIp, restPort):
    logger.info('Starting process command thread')
    while True:
        speechstate = sc.command_queue.get()
        if speechstate == SpeechState.mode_long:
            sc.start_mode_long(restIp, restPort)
        elif speechstate == SpeechState.mode_short:
            sc.start_mode_short(restIp, restPort)
        elif speechstate == SpeechState.stop:
            sc.stop_mode(restIp, restPort)
        elif speechstate == SpeechState.error:
            sc.__logger.error("Error %s", speechstate)
            break

if __name__ == '__main__':

    name = "speech2Massage"
    logger = mainReturnLogger(name, logging.INFO)
    logger.info('------------------------------------------------------------')
    logger.info(f'***  {name}                                  ***')
    logger.info('------------------------------------------------------------')

    restPort = 50000
    restIp = find_service_ip_by_port(restPort)

    command_queue = queue.Queue()
    sc = SpeechController(logger, command_queue)

    recognize_thread = threading.Thread(target=recognize_speech_thread, args=(sc,))
    process_thread = threading.Thread(target=process_command_thread, args=(sc, restIp, restPort))

    recognize_thread.start()
    process_thread.start()

    recognize_thread.join()
    process_thread.join()