import base64
import json
import logging
import os
import zoneinfo
from datetime import datetime
from pprint import pformat

import google.cloud.logging
import requests

# 標準 Logger の設定
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)
logger = logging.getLogger()

# Cloud Logging ハンドラを logger に接続
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

# setup_logging() するとログレベルが INFO になるので DEBUG に変更
logger.setLevel(logging.DEBUG)


WEBHOOK_URL = os.environ['WEBHOOK_URL']
ICON_IMAGE_URL = os.environ['ICON_IMAGE_URL']
JST = zoneinfo.ZoneInfo('Asia/Tokyo')


def monitoring_notify(event, context):
    try:
        logger.info('===== START cloud monitoring notifier =====')
        logger.debug(f'event={pformat(event)}')
        logger.debug(f'context={pformat(context)}')

        logger.info('----- get pubsub event data -----')
        event_data_json = base64.b64decode(event['data']).decode('utf-8')
        logger.debug(f'event_data={event_data_json}')
        event_data = json.loads(event_data_json)['incident']

        logger.info('----- create post content -----')
        headers = {'Content-Type': 'application/json'}
        content = f'''**Incident is ongoing**
Policy: {event_data['policy_name']}
Severity: {event_data["severity"]}
'''
        embeds = [
            {
                'title': 'Incident details',
                'url': event_data["url"],
                'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                'color': 16711680,
                'footer': {
                    'text': "Cloud Monitoring Notifier",
                    'icon_url': ICON_IMAGE_URL
                },
                'author': {
                    'name': '@Google Cloud',
                    'url': f'https://console.cloud.google.com/home/dashboard?hl=ja&project={event_data["scoping_project_id"]}',
                    'icon_url': 'https://avatars.slack-edge.com/2019-10-30/817024818759_0abdf89bb617c3003b21_512.png'
                },
                'fields': [
                    {
                        'name': 'Summary',
                        'value': event_data['summary'],
                    },
                    {
                        'name': 'Policy name',
                        'value': event_data['policy_name'],
                        'inline': True
                    },
                    {
                        'name': 'Severity',
                        'value': event_data["severity"],
                        'inline': True
                    },
                    {
                        'name': 'Started at',
                        'value': datetime.fromtimestamp(event_data['started_at'], JST).strftime('%Y-%m-%d %H:%M:%S'),
                    },
                    {
                        'name': 'Log query',
                        'value': event_data['condition']['conditionMatchedLog']['filter'],
                    },
                ]
            },
        ]

        body = {
            'username': 'Cloud Monitoring Notifier',
            'avatar_url': ICON_IMAGE_URL,
            'content': content,
            'embeds': embeds
        }

        logger.debug(f'webhook_url={WEBHOOK_URL}')
        logger.debug(f'headers={pformat(headers)}')
        logger.debug(f'body={pformat(body)}')

        logger.info('----- post message -----')
        response = requests.post(WEBHOOK_URL, json.dumps(body), headers=headers)

        logger.debug(f'response.status={pformat(response.status_code)}')
        logger.info('===== END cloud monitoring notifier =====')
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    monitoring_notify('', '')
