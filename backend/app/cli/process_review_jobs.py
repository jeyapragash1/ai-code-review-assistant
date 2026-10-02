from app.models import ReviewJob
from app.services.job_worker import main

if __name__ == "__main__":
    raise SystemExit(main(ReviewJob))
