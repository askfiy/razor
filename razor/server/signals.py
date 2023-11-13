from blinker import signal

request_start = signal("request_started")
request_finish = signal("request_finished")
