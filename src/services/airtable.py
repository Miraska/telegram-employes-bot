from datetime import date
import requests
import logging
from config.settings import settings_config
import boto3


logger = logging.getLogger(__name__)

def upload_to_yandex_cloud(photo_path: str) -> str:
    # Создание клиента для Object Storage
    s3 = boto3.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

    # Имя бакета
    bucket_name = 'airtable-clone'

    # Загрузка фото
    local_photo_path = photo_path
    object_key = f'photos/{date.today()}_{photo_path}'
    s3.upload_file(local_photo_path, bucket_name, object_key)

    # Генерация временной ссылки на загруженный объект
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=3600 * 24 * 30  # Ссылка действительна 30 дней
    )
    print("Временная ссылка на 30 дней:", url)

    return url


def send_to_airtable(action: str, data: dict, photo_path: str = None):
    payload = {"action": action, **data}
    headers = {"Content-Type": "application/json"}

    if photo_path:
        photo_url = upload_to_yandex_cloud(photo_path)
        payload["photo_url"] = photo_url
        try:
            response = requests.post(settings_config.AIRTABLE_WEBHOOK, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Data sent to Airtable: {action}")
            return True
        except Exception as e:
            logger.error(f"Error sending to Airtable: {e}", exc_info=True)
            return False
    else:
        try:
            response = requests.post(settings_config.AIRTABLE_WEBHOOK, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Data sent to Airtable: {action}")
            return True
        except Exception as e:
            logger.error(f"Error sending to Airtable: {e}", exc_info=True)
            return False