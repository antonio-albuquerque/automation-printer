import os
import subprocess
from time import sleep
import requests
import slack

SLACK_CHANNEL=os.environ['SLACK_CHANNEL']
USER_TOKEN=os.environ['USER_TOKEN']
POOLING=int(os.environ['POOLING'])

def get_client(user_token):
    return slack.WebClient(token=user_token)

def get_messages_that_carries_some_file_to_print(client, channel):
    return list(
        filter(
            lambda message: 'reactions' not in message and 'files' in message,
            client.conversations_history(channel=channel)['messages']
        )
    )

def get_download_links_of_files_to_get_printed(messages):
    return list(
        map(
            lambda message: list(map(lambda file: file['url_private_download'],message['files'])),
            messages
        )
    )

def get_files_to_print(links, user_token):
    for link in links:
        file = requests.get(link[0], headers={'Authorization': 'Bearer ' + user_token})
        filename = link[0].split('/')[-1]
        open(filename, 'wb').write(file.content)
        print_file(filename)

def set_downloaded_messages_thumbs_up(client, channel, messages):
    for message in messages:
        timestamp = message['ts']
        client.reactions_add(
            channel=channel,
            timestamp=timestamp,
            name='thumbsup'
        )
        client.chat_postMessage(
            channel=channel,
            text="Mandei pra fila de impressão. PIN para acessar o arquivo na impressora: 5002",
            thread_ts=timestamp,
            # reply_broadcast=True
        )

def print_file(filename):
    subprocess.call(['lp', filename])

def main(user_token, channel):
    client = get_client(user_token)
    messages = get_messages_that_carries_some_file_to_print(client, channel)
    download_links = get_download_links_of_files_to_get_printed(messages)
    get_files_to_print(download_links, user_token)
    set_downloaded_messages_thumbs_up(client, channel, messages)

while True:
    main(USER_TOKEN, SLACK_CHANNEL)
    sleep(POOLING)