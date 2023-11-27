from flask import Flask
from threading import Thread
import azuredevops
from loadenv import download_ssh_keys_from_s3

app = Flask(__name__)


download_ssh_keys_from_s3()


@app.route('/young-sheldon/review')
def review_cron():
    thread = Thread(target=manual_review)
    thread.start()

    return "Disparado com sucesso!"


@app.route('/young-sheldon/manualReview')
def manual_review():
    azuredevops.review_process()


if __name__ == "__main__":
    manual_review()
