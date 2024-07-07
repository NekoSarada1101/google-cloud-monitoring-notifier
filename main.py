import base64
import json
import logging
import os
from pprint import pformat

import google.cloud.logging
import requests

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
    try:
        logger.info('===== START cloud monitoring notifier =====')
        logger.debug(f'event={pformat(event)}')
        logger.debug(f'context={pformat(context)}')

        logger.info('----- get pubsub event data -----')
        event_data_json = base64.b64decode(event['data']).decode('utf-8')
        logger.debug(f'event_data={event_data_json}')
        event_data = json.loads(event_data_json)['incident']

        logger.info('----- create post content -----')
        webhook_url = os.environ['WEBHOOK_URL']
        headers = {'Content-Type': 'application/json'}
        content = f'''**Incident is ongoing**
{event_data["condition_name"]}
**Severity:** {event_data["severity"]}'''
        embeds = [
            {
                'title': 'Incident details',
                'description': event_data["summary"],
                'url': event_data["url"],
                'color': 8782097
            },
            {
                'title': event_data['policy_name'],
                'description': event_data['condition']['conditionMatchedLog']['filter'],
                'url': f'https://console.cloud.google.com/monitoring/alerting/policies/{event_data["condition"]["name"].split("/")[3]}?project={event_data["scoping_project_id"]}',
                'color': 8421504
            },
        ]

        body = {
            'username': 'Cloud Monitoring Notifier',
            'avatar_url': os.environ['ICON_IMAGE_URL'],
            'content': content,
            'embeds': embeds
        }

        logger.debug(f'webhook_url={webhook_url}')
        logger.debug(f'headers={pformat(headers)}')
        logger.debug(f'body={pformat(body)}')

        logger.info('----- post message -----')
        response = requests.post(webhook_url, json.dumps(body), headers=headers)

        logger.debug(f'response.status={pformat(response.status_code)}')
        logger.info('===== END cloud monitoring notifier =====')
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    monitoring_notify('', '')
