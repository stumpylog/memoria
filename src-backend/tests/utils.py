from contextlib import contextmanager


@contextmanager
def disable_signal(sig, receiver, sender):
    try:
        sig.disconnect(receiver=receiver, sender=sender)
        yield
    finally:
        sig.connect(receiver=receiver, sender=sender)
