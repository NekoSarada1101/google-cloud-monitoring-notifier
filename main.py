# This example requires the 'message_content' intent.

import os
import requests
import json
from pprint import pformat
import google.cloud.logging
import logging

# 標準 Logger の設定
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s] %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger()


# Cloud Logging ハンドラを logger に接続
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

# setup_logging() するとログレベルが INFO になるので DEBUG に変更
logger.setLevel(logging.DEBUG)


def monitoring_notify(event, context):
    logger.info('===== START cloud monitoring notifier =====')
    logger.debug(f'event={pformat(event)}')

    webhook_url = os.environ['WEBHOOK_URL']
    headers = {'Content-Type': 'application/json'}
    body = {
        'username': 'Cloud Monitoring Notifier',
        'avatar_url': os.environ['ICON_IMAGE_URL'],
        'content': 'テキスト'
    }

    logger.debug(f'webhook_url={webhook_url}')
    logger.debug(f'headers={pformat(headers)}')
    logger.debug(f'body={pformat(body)}')

    response = requests.post(webhook_url, json.dumps(body), headers=headers)

    logger.debug(f'response.status={pformat(response.status_code)}')
    logger.info('===== END cloud monitoring notifier =====')


if __name__ == '__main__':
    monitoring_notify('', '')
