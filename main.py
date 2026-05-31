import base64
import json
import logging
import os
from datetime import datetime, timezone
import zoneinfo
from pprint import pformat
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


WEBHOOK_URL = os.environ['WEBHOOK_URL']
ICON_IMAGE_URL = os.environ['ICON_IMAGE_URL']
JST = zoneinfo.ZoneInfo('Asia/Tokyo')


def monitoring_notify(event, context):
    try:
        logger.info('===== START cloud monitoring notifier =====')

        # 1. Pub/Sub ペイロードのデコード
        event_data_json = base64.b64decode(event['data']).decode('utf-8')
        event_data = json.loads(event_data_json).get('incident')

        if not event_data:
            logger.error("Payload does not contain 'incident' data.")
            return

        # 2. インシデントのレベル
        incident_level = event_data.get("severity", 'Unknown')
        color = 8421504  # 灰色
        if incident_level == 'Error' or incident_level == "Emergency":
            color = 16711680  # 赤
        elif incident_level == 'Warning':
            color = 16776960  # 黄

        logger.info(f'Incident state: {incident_level}')

        # 4. Discord ペイロードの構築
        content = f"**[ALERT - {incident_level}]** {event_data.get('policy_name')}"

        started_at = event_data.get('started_at')
        started_at_str = datetime.fromtimestamp(started_at, JST).strftime(
            '%Y-%m-%d %H:%M:%S') if started_at else 'Unknown'

        embeds = [
            {
                'title': 'Incident details',
                'url': event_data.get("url"),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'color': color,
                'footer': {
                    'text': "Cloud Monitoring Notifier",
                    'icon_url': ICON_IMAGE_URL
                },
                'fields': [
                    {
                        'name': 'Severity',
                        'value': incident_level,
                    },
                    {
                        'name': 'Policy name',
                        'value': event_data.get('policy_name', 'Unknown'),
                    },
                    {
                        'name': 'Started at (JST)',
                        'value': started_at_str,
                        'inline': True
                    },
                    {
                        'name': 'Condition',
                        'value': event_data.get('condition_name', 'Unknown'),
                        'inline': True
                    },
                ]
            }
        ]

        body = {
            'username': 'Cloud Monitoring Notifier',
            'avatar_url': ICON_IMAGE_URL,
            'content': content,
            'embeds': embeds
        }

        # 5. メッセージの送信と厳格なエラーハンドリング
        logger.info('----- post message -----')
        response = requests.post(
            WEBHOOK_URL,
            json=body,
            headers={'Content-Type': 'application/json'},
            timeout=10  # 無限ハングアップ防止
        )

        # HTTPエラー（4xx, 5xx）の場合は例外を発生させ、Pub/Subにリトライを要求する
        response.raise_for_status()

        logger.info('===== END cloud monitoring notifier =====')
    except requests.exceptions.RequestException as re:
        # ネットワーク層・HTTPステータスエラー
        logger.error(f"Discord Webhook API Error: {re}")
        raise  # リトライさせるために再送出
    except Exception as e:
        # その他の予期せぬエラー
        logger.error(f"Unexpected Error: {e}")
        logger.debug(f"Event payload: {pformat(event)}")
        raise


if __name__ == '__main__':
    monitoring_notify('', '')
