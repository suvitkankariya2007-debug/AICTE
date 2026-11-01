"""Single-process demo worker. Run separately; database uniqueness prevents repeated alerts."""
import argparse,time,logging
from sqlalchemy.exc import IntegrityError
from .db import setup
from .engine import sweep
parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
engine,Factory=setup()
while True:
    try:
        with Factory.begin() as db: print(f'Deadline worker: {sweep(db)} new simulated deliveries',flush=True)
    except IntegrityError: logging.info('Another worker already recorded this alert; rolled back, retrying next interval')
    if args.once: break
    time.sleep(60)
