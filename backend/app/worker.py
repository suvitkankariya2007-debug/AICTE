"""Single-process demo worker with persistent health status."""
import argparse,time,logging
from datetime import datetime,timezone
from sqlalchemy.exc import IntegrityError,OperationalError
from .db import WorkerHeartbeat,setup
from .engine import sweep
parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
engine,Factory=setup()
while True:
    started=datetime.now(timezone.utc).isoformat()
    try:
        with Factory.begin() as db:
            heartbeat=db.get(WorkerHeartbeat,1)
            if not heartbeat: heartbeat=WorkerHeartbeat(id=1)
            heartbeat.last_started=started
            heartbeat.last_error=''
            db.add(heartbeat)
        with Factory.begin() as db:
            count=sweep(db)
        with Factory.begin() as db:
            heartbeat=db.get(WorkerHeartbeat,1)
            heartbeat.last_completed=datetime.now(timezone.utc).isoformat()
            heartbeat.processed=count
            print(f'Deadline worker: {count} new simulated deliveries',flush=True)
    except IntegrityError:
        logging.info('Another worker already recorded this alert; rolled back, retrying next interval')
    except OperationalError as exc:
        logging.exception('Deadline worker iteration failed')
        with Factory.begin() as db:
            heartbeat=db.get(WorkerHeartbeat,1)
            if heartbeat:
                heartbeat.last_error=str(exc)[:500]
    if args.once: break
    time.sleep(60)
