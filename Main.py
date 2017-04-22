import requests
import sys
import json
import configparser
import psycopg2
import random
import subprocess
import os


config = configparser.ConfigParser()
ini = config.read('conf2.ini')
RED_HOST = config.get('Redshift Creds', 'host')
RED_PORT = config.get('Redshift Creds', 'port')
RED_USER = config.get('Redshift Creds', 'user')
RED_PASSWORD = config.get('Redshift Creds', 'password')


def get_weak_words():
    url = "https://api.busuu.com/vocabulary/saved/fr"

    querystring = {"uid": "32767377", "ck": "1487691895548",

                   "access-token": "09080ba2c38ae0b51fb79bc35a8720ba55daddb054d11f00d3bd53c5d6f3def0|c457a87a59304e7c1c1330c18082696b.3332373637333737"}

    # Connect to RedShift
    conn_string = "dbname=%s port=%s user=%s password=%s host=%s" % (RED_USER, RED_PORT, RED_USER, RED_PASSWORD, RED_HOST)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    try:
        response = requests.request("GET", url,  params=querystring)

        assert response.status_code ==200, "Toto won't let you in"

        vocabulary = json.loads(response.content)["vocabulary"]

        weak_words = []
        for words in vocabulary:
            if words["strength"] < 2:
                weak_word = words["entity_id"]
                cursor.execute("select english, french from content_entities ent inner join content_strings str on str.str_name = ent.phrase where entity = '%s';" % weak_word)
                answer = cursor.fetchone()
                weak_words.append(answer)

        conn.commit()
        conn.close()

        return random.choice(weak_words)


    except Exception as e:
        print e


def create_new_learning_session(weak_words):

    weak_words_string = "Your weak word for this tea break is:  '%s' which means '%s'" % (weak_words[1], weak_words[0])

    with open('IOT_Screen.ino', 'r') as ino_file_read:
        with open('IOT_Kettle/src/IOT_Screen.ino', 'w') as ino_file_write:
            template_file = ino_file_read.read()
            template_file = str(template_file).replace('"paramtobereplaced";', weak_words_string)

            ino_file_write.write(template_file)
    return True


def upload_non_learning_session():

    subprocess.Popen(['ino', 'upload'], cwd="IOT_Kettle/IOT_Kettle_Template")


def upload_learning_session():

    subprocess.Popen(['ino', 'upload'], cwd="IOT_Kettle/IOT_Kettle")


def main(argv):

    weak_words = get_weak_words()
    result = create_new_learning_session(weak_words)

    print result



if __name__ == '__main__':
    main(sys.argv)