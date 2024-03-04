import logging
import os
import signal
import sys
from datetime import datetime, timezone
from time import sleep
from flask import Flask, request, render_template
import threading
from aw_client import ActivityWatchClient
from aw_core.log import setup_logging
from aw_core.models import Event
from multiprocessing import Queue
from flask import jsonify
import requests


from .config import parse_args
from .exceptions import FatalError
from .lib import get_current_window

logger = logging.getLogger(__name__)
manual_input_queue = Queue()

# run with LOG_LEVEL=DEBUG
log_level = os.environ.get("LOG_LEVEL")
if log_level:
    logger.setLevel(logging.__getattribute__(log_level.upper()))

# Global variable to store bucket_id
global_bucket_id = None

def kill_process(pid):
    logger.info("Killing process {}".format(pid))
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        logger.info("Process {} already dead".format(pid))

app = Flask(__name__)

def create_data_dict(name_value):
    return {"title": name_value}

def run_flask():
    app.run(port=5000, debug=False)

def main():
    global global_bucket_id  # Accessing the global variable
    args = parse_args()

    if sys.platform.startswith("linux") and (
        "DISPLAY" not in os.environ or not os.environ["DISPLAY"]
    ):
        raise Exception("DISPLAY environment variable not set")

    setup_logging(
        name="aw-watcher-window",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    client = ActivityWatchClient(
        "aw-watcher-window", host=args.host, port=args.port, testing=args.testing
    )

    bucket_id = f"{client.client_name}_{client.client_hostname}"
    event_type = "currentwindow"

    client.create_bucket(bucket_id, event_type, queued=True)
    
    # Assigning bucket_id to global variable
    global_bucket_id = bucket_id

    logger.info("aw-watcher-window started")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    sleep(1)  # wait for the server to start
    with client:
        heartbeat_loop(
            client,
            bucket_id,
            poll_time=args.poll_time,
            strategy=args.strategy,
            exclude_title=args.exclude_title,
        )

import time

def heartbeat_loop(client, bucket_id, poll_time, strategy, exclude_title=False):
    while True:
        if os.getppid() == 1:
            logger.info("window-watcher stopped because the parent process died")
            break

        # Check for manual input
        if not manual_input_queue.empty():
            manual_input_event = manual_input_queue.get()
            client.heartbeat(bucket_id, manual_input_event, pulsetime=1.0, queued=True)

        current_window = None
        try:
            current_window = get_current_window(strategy)
            print("Heartbeat")
            print(bucket_id)
            logger.debug(current_window)
        except (FatalError, OSError):
            # Fatal exceptions should quit the program
            try:
                logger.exception("Fatal error, stopping")
            except OSError:
                pass
            break
        except Exception:
            # Non-fatal exceptions should be logged
            try:
                # If stdout has been closed, this exception-print can cause (I think)
                #   OSError: [Errno 5] Input/output error
                # See: https://github.com/ActivityWatch/activitywatch/issues/756#issue-1296352264
                #
                # However, I'm unable to reproduce the OSError in a test (where I close stdout before logging),
                # so I'm in uncharted waters here... but this solution should work.
                logger.exception("Exception thrown while trying to get active window")
            except OSError:
                break

        if current_window is None:
            logger.debug("Unable to fetch window, trying again on the next poll")
        else:
            if exclude_title:
                current_window["title"] = "excluded"

            now = datetime.now(timezone.utc)
            current_window_event = Event(timestamp=now, data=current_window)

            client.heartbeat(
                bucket_id, current_window_event, pulsetime=poll_time + 1.0, queued=True
            )

        sleep(poll_time)
        
@app.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    global global_bucket_id  # Accessing the global variable
    response_data = None
    message = None
    if request.method == 'POST':
        # Obtenha os dados do formulário enviado
        date_value = request.form.get('date')
        time_value = request.form.get('time')
        end_time = request.form.get('endTime')
        name_value = request.form.get('title')

        start_datetime = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
        start_datetime_utc = start_datetime.astimezone(timezone.utc)

        end_datetime = datetime.strptime(f"{date_value} {end_time}", "%Y-%m-%d %H:%M")
        end_datetime_utc = end_datetime.astimezone(timezone.utc)

        duration_in_seconds = int((end_datetime - start_datetime).total_seconds())

        data_dict = create_data_dict(name_value)

        # Construa a URL com os parâmetros de data e hora
        url = f"http://localhost:5600/api/0/buckets/{global_bucket_id}/events"
        params = {
            'start': start_datetime_utc.strftime("%Y-%m-%d %H:%M:%S%z"),
            'end': end_datetime_utc.strftime("%Y-%m-%d %H:%M:%S%z")
        }
        
        # Faça a solicitação GET usando requests
        response = requests.get(url, headers={'accept': 'application/json'}, params=params)
        print(response)
        if response.status_code == 200:
            # Processar a resposta
            response_data = response.json()
            message = "Existem eventos no período selecionado."

            if not response_data:
                # Coloque manual_input_event na queue
                manual_input_event = Event(timestamp=start_datetime_utc, duration=duration_in_seconds, data=data_dict)
                manual_input_queue.put(manual_input_event)
                message = "Evento adicionado no ActivityWatch!"

    return render_template('manual_input.html', response_data=response_data, message=message)
