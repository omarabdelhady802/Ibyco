import threading

_listener_started = False
_lock = threading.Lock()


def post_fork(server, worker):
    """Start the Redis listener once in the first worker only."""
    global _listener_started
    with _lock:
        if not _listener_started:
            _listener_started = True
            from service.redis_worker import start_redis_listener
            t = threading.Thread(target=start_redis_listener, daemon=True)
            t.start()
            server.log.info("[SYSTEM] Redis Listener started in worker %s", worker.pid)
