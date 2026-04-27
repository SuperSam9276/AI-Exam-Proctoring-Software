import time, threading, redis, os
from app.penalty import (
    DECAY_RATE,
    DECAY_INTERVAL_SECS,
    FLOOR_SCORE,
    STATE_FLOOR_SCORE
    )
from dotenv import load_dotenv
load_dotenv()

redis_cl = redis.from_url(os.getenv("REDIS_URL"))
def decay_loop():
    """Background thread that periodically decays penalty scores for all active sessions in Redis"""
    while True:
        time.sleep(DECAY_INTERVAL_SECS)
        
        keys = redis_cl.keys("session:*")
        
        for key in keys:
            try:    
                data = redis_cl.hgetall(key)
                if not data:
                    continue

                state = data.get(b"state", b"CLEAR").decode("utf-8")
                score = int(data.get(b"penalty_score", 0))

                if state == "TERMINATED":
                    continue

                if score <= FLOOR_SCORE:
                    continue
                
                state_floor = STATE_FLOOR_SCORE[state]
                new_score = max(score - DECAY_RATE, state_floor)
                redis_cl.hset(
                    key, mapping= {
                    "penalty_score": new_score, 
                    "state": state
                    }
                    )
            


            except Exception as e:
                print(f"Error in decay loop: {e}")


# Start the decay loop in a background thread
def start_decay_thread():
    thread = threading.Thread(target=decay_loop, daemon=True, name="ScoreDecay")
    thread.start()
    print(
        f"[decay] Score Decacy Thread started -"
        f" Decay every {DECAY_INTERVAL_SECS} seconds, "
        f"Decay by {DECAY_RATE} points \n "
        f"Floor score per state: {STATE_FLOOR_SCORE}"
    )