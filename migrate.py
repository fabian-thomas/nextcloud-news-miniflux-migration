#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime, timedelta

import pymysql
import psycopg2
from psycopg2.extras import DictCursor

nc_db_config = {
    'password': sys.argv[1],
    'unix_socket': sys.argv[2],

    'user': 'nextcloud',
    'db': 'nextcloud',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

mf_db_config = {
    'user': 'miniflux',
    'host': '/run/postgresql',
    'dbname': 'miniflux'
}

# Get the uid of user miniflux. This is needed later to connect to the miniflux database.
miniflux_uid = int(subprocess.check_output(['id', '-u', 'miniflux']), 10)



def nc_feeds_to_mf(nc_feeds):
    mf_feeds = []
    for nc_feed in nc_feeds:
        mf_feed = {}
        mf_feed["id"] = nc_feed["id"]
        mf_feed["title"] = nc_feed["title"]
        mf_feed["feed_url"] = nc_feed["url"]
        mf_feed["site_url"] = nc_feed["link"]

        mf_feed["user_id"] = 1

        mf_feed["category_id"] = 1 if nc_feed["folder_id"] == None else nc_feed["folder_id"]

        mf_feed["etag_header"] = ""

        mf_feed["last_modified_header"] = ""
        mf_feed["parsing_error_msg"] = ""
        mf_feed["scraper_rules"] = ""
        mf_feed["rewrite_rules"] = ""
        mf_feed["user_agent"] = ""
        mf_feed["blocklist_rules"] = ""
        mf_feed["keeplist_rules"] = ""
        mf_feed["cookie"] = ""
        mf_feed["url_rewrite_rules"] = ""

        mf_feed["parsing_error_count"] = 0

        mf_feed["crawler"] = False
        mf_feed["disabled"] = False
        mf_feed["ignore_http_cache"] = False
        mf_feed["fetch_via_proxy"] = False
        mf_feed["allow_self_signed_certificates"] = False
        mf_feed["hide_globally"] = False

        mf_feed["username"] = ""
        mf_feed["password"] = ""

        current_time = datetime.now()
        five_minutes_ago = current_time - timedelta(minutes=5)
        mf_feed["next_check_at"] = five_minutes_ago
        mf_feed["checked_at"] = five_minutes_ago
        mf_feeds.append(mf_feed)

    return mf_feeds

def nc_items_to_mf(nc_items, mf_feeds):
    mf_items = []
    for nc_item in nc_items:
        mf_item = {}
        mf_item["id"] = nc_item["id"]
        mf_item["feed_id"] = nc_item["feed_id"]

        if nc_item["pub_date"] < 0:
            mf_item["published_at"] = datetime.now()
        else:
            mf_item["published_at"] = datetime.fromtimestamp(nc_item["pub_date"])
        mf_item["title"] = nc_item["title"]
        mf_item["author"] = "" if nc_item["author"] == None else nc_item["author"]
        url = nc_item["url"]
        if url == None:
            url = list(filter(lambda feed: feed["id"] == nc_item["feed_id"], mf_feeds))[0]["site_url"]
        mf_item["url"] = url
        mf_item["content"] = nc_item["body"]
        mf_item["status"] = "unread" if nc_item["unread"] == 1 else "read"
        mf_item["starred"] = nc_item["starred"] == 1

        mf_item["comments_url"] = ""

        mf_item["tags"] = []

        mf_item["user_id"] = 1

        mf_item["document_vectors"] = "'4.83':38B '48.8':37B 'a':6B 'additional':54B 'an':24B 'android':65B 'app':26B,44B 'changes':68B 'check':48B 'custom':57B 'default':4B 'different':46B 'directly':32B 'displayed':19B 'documentation':50B 'each':43B 'enter':10B 'feilen':20B 'fixes':59B 'for':35B,53B 'from':64B 'geo':36B 'harshad1':11B 'history':15B 'home':42B 'icons':58B 'if':23B 'improvements':12B 'information':55B 'installed':25B 'is':18B 'it':31B 'keyboard':17B 'kiss':62B 'link':60B 'manifest':52B 'marunjar':56B 'matches':27B 'my':41B 'on':9B 'open':30B 'option':2B 'or':51B 'preferences':63B 'provides':45B 's':40B 'search':8B,22B 'searching':34B 'show':14B 'system':66B 'that':39B 'the':28B 'their':49B 'to':3B,5B,13B,61B 'translation':67B 'try':33B 'uri':21B,29B,47B 'v3.16.10':1A 'web':7B 'when':16B"

        mf_item["share_code"] = ""

        mf_item["reading_time"] = 1

        current_time = datetime.now()
        mf_item["changed_at"] = current_time
        mf_item["created_at"] = current_time

        to_hash = nc_item["guid"] if nc_item["guid"] != "" else nc_item["url"]
        import hashlib
        mf_item["hash"] = hashlib.sha256(to_hash.encode()).hexdigest()

        mf_items.append(mf_item)

    return mf_items

def nc_folders_to_mf(nc_folders):
    mf_folders = []
    for nc_folder in nc_folders:
        mf_folder = {}
        mf_folder["id"] = nc_folder["id"]
        mf_folder["title"] = nc_folder["name"]

        mf_folder["user_id"] = 1

        mf_folder["hide_globally"] = False

        mf_folders.append(mf_folder)

    return mf_folders



##################### Get items from nextcloud #####################
nc_news_con = pymysql.connect(**nc_db_config)

try:
    with nc_news_con.cursor() as cursor:
        # Get feeds
        query = "SELECT * FROM oc_news_feeds;"
        cursor.execute(query)
        nc_feeds = cursor.fetchall()

        # Migrate feeds
        mf_feeds = nc_feeds_to_mf(nc_feeds)

        # Get items
        query = "SELECT * FROM oc_news_items;"
        cursor.execute(query)
        nc_items = cursor.fetchall()

        # Migrate items
        mf_items = nc_items_to_mf(nc_items, mf_feeds)

        # Get folders
        query = "SELECT * FROM oc_news_folders;"
        cursor.execute(query)
        nc_folders = cursor.fetchall()

        # Migrate folders
        mf_folders = nc_folders_to_mf(nc_folders)

finally:
    nc_news_con.close()



##################### Write to miniflux db #####################
os.seteuid(miniflux_uid)

def insert(l, table):
    query = f"DELETE FROM {table};"
    cursor.execute(query)
    for entry in l:
        columns = ', '.join(entry.keys())
        placeholders = ', '.join(['%s'] * len(entry))
        if table == "entries":
            placeholders = "%s, %s, %s, %s, %s, %s, %s, CAST(%s AS entry_status), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"
        cursor.execute(query, list(entry.values()))

try:
    connection = psycopg2.connect(**mf_db_config)

    cursor = connection.cursor(cursor_factory=DictCursor)

    insert(mf_folders, "categories")
    insert(mf_feeds, "feeds")
    insert(mf_items, "entries")

    connection.commit()
    print("Commited {} feeds, {} items and {} folders.".format(len(mf_feeds), len(mf_items), len(mf_folders)))

    cursor.close()
    connection.close()

except psycopg2.Error as e:
    print("Error:", e)
