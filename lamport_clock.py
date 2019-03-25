def internal_event_adjustment(counter):
    return counter + 1

def send_event_adjustment(counter):
    return counter + 1
    
def recv_event_adjustment(counter, recv_counter):
    return max(counter, recv_counter) + 1