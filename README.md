## telegram-employes-bot

### Инструкция - сначала нужно запустить venv, или создать если его нет. Затем нужно установить все зависимости которых нет, в requirements.txt они есть, затем нужно перейти в папку src и написать вот эту команду: "python -m bot.main".


#### Создайте конфигурацию для настройки бакета от облака яндекс:
For macOS and Linux:
mkdir ~/.aws/

For Windows:

mkdir C:\Users\<username>\.aws\

In the .aws directory, create a file named credentials, copy the credentials you got earlier, and paste them into it:

[default]
aws_access_key_id = <static_key_ID>
aws_secret_access_key = <secret_key>

Create a file named config with the default region settings and copy the following information to it:

[default]
region = ru-central1
endpoint_url = https://storage.yandexcloud.net