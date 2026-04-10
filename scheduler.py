import time

from app import app
from db import remove_expired_contacts


def run_minute_job():
    with app.app_context():
        removed_count = remove_expired_contacts()
        print(f'SCHEDULER: removed {removed_count} expired contacts')


def main():
    while True:
        run_minute_job()
        time.sleep(60)


if __name__ == '__main__':
    main()
