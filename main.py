import os
import threading
import subprocess
import time

from pyrogram import Client
from pyrogram import filters

from pyrogram.types import Message, CallbackQuery
import mdisk
import split
from split import TG_SPLIT_SIZE
from config import API_ID, API_HASH, BOT_TOKEN
from database import collection

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot_token = BOT_TOKEN
api_hash = API_HASH
api_id = API_ID
app = Client("my_bot",api_id=api_id, api_hash=api_hash,bot_token=bot_token)


@app.on_message(filters.command(["start"]))
def echo(client, message):
    app.send_message(message.chat.id, 'Send link like this >> /mdisk link')


def status(folder,message):
    length = len(folder)
    
    # wait for the folder to create
    while True:
        if os.path.exists(folder + "/vid.mp4.part-Frag0"):
            break
    
    while os.path.exists(folder + "/" ):
        result = subprocess.run(["du", "-hs", f"{folder}/"], capture_output=True, text=True)
        size = result.stdout[:-(length+2)]
        try:
            app.edit_message_text(message.chat.id, message.id, f"Downloaded : {size}")
            time.sleep(10)
        except:
            time.sleep(5)


def upstatus(statusfile,message):

    while True:
        if os.path.exists(statusfile):
            break
        
    txt = "0%"    
    while os.path.exists(statusfile):
        with open(statusfile,"r") as upread:
            txt = upread.read()
        try:
            app.edit_message_text(message.chat.id, message.id, f"Uploaded : {txt}")
            time.sleep(10)
        except:
            time.sleep(5)


def progress(current, total, message):
    with open(f'{message.id}upstatus.txt',"w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")


@app.on_message(filters.command(["log"]))
def log_channel_handler(client, m:Message):
    log = collection.find_one({ "tag": "log_channel" })
    if len(m.command) == 2:
        log_channel_id = m.command[1]

        if log_channel_id == "remove":
            log_channel_id = None
        else:
            log_channel_id = int(log_channel_id)

        myquery = { "tag": "log_channel" }
        newvalues = { "$set": { "value": log_channel_id } }

        collection.update_one(myquery, newvalues, True)
        m.reply_text("log_channel updated")
    else:
        id = log['value'] if log and log['value'] else None
        m.reply_text(f"/log -100xx\nCurrent Log: {id}") 


@app.on_message(filters.command(["setthumb"]))
def thumbnail_handler(client, m:Message):
    if m.reply_to_message and m.reply_to_message.photo:
        fileid = m.reply_to_message.photo.file_id
        txt = m.reply_text("Downloading Thumbnail....")
        file = client.download_media(fileid, file_name="thumb.jpeg")

        myquery = { "tag": "thumbnail" }
        newvalues = { "$set": { "value": file } }

        collection.update_one(myquery, newvalues, True)

        txt.edit("Thumbnail has been set")


@app.on_message(filters.command(["showthumb"]))
def show_thumbnail_handler(client, m:Message):
    thumb = (collection.find_one({"tag": "thumbnail"}))
    m.reply_photo(thumb["value"]) if thumb and thumb["value"] else m.reply_text("None")


@app.on_message(filters.command(["delthumb"]))
def del_thumbnail_handler(client, m:Message):

    myquery = { "tag": "thumbnail" }
    newvalues = { "$set": { "value": None } }

    collection.update_one(myquery, newvalues, True)
    m.reply_text("Deleted")

@app.on_message(filters.command(["mode"]))
def doc_video_handler(client, m:Message):
    REPLY_MARKUP  = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Doc', callback_data=f'mode_doc'),
            InlineKeyboardButton('Video', callback_data='mode_video')
        ],

    ])

    mode = collection.find_one({"tag": "mode"})
    mode = mode["value"] if mode and mode["value"] else None

    m.reply_text(f"Current Mode: {mode}", reply_markup=REPLY_MARKUP)

@app.on_message(filters.command(["custom"]))
def custom_filename_handler(client, m:Message):
    if len(m.command) != 1:
        print(m.text)
        custom = m.text.replace("/custom ", "")

        if "remove" in custom:
            custom = None
        
        myquery = { "tag": "custom" }
        newvalues = { "$set": { "value": custom } }

        collection.update_one(myquery, newvalues, True)

        m.reply_text(f"Custom Filename has been Updated to {custom}")
    else:
        mode = collection.find_one({"tag": "custom"})
        mode = f'{mode["value"]} ' if mode and mode["value"] else ""
        txt = m.reply_text(f"/custom @ur channel username\nCurrent: {mode}")


@app.on_callback_query(filters.regex("mode"))
def doc_video_cb_handler(client, m:CallbackQuery):
    mode = m.data.split("_")[1]

    myquery = { "tag": "mode" }
    newvalues = { "$set": { "value": mode } }

    collection.update_one(myquery, newvalues, True)
    m.edit_message_text("Changed", reply_markup=None)

def down(message,link):
    msg = app.send_message(message.chat.id, 'Downloading...', reply_to_message_id=message.id)
    sta = threading.Thread(target=lambda:status(str(message.id),msg),daemon=True)
    sta.start()

    file = mdisk.mdow(link,message)

    size = split.get_path_size(file)

    upsta = threading.Thread(target=lambda:upstatus(f'{message.id}upstatus.txt',msg),daemon=True)
    upsta.start()

    if(size > TG_SPLIT_SIZE):
        app.edit_message_text(message.chat.id, msg.id, "Splitting...")
        flist = split.split_file(file,size,file,".", TG_SPLIT_SIZE)
        os.remove(file)
        app.edit_message_text(message.chat.id, msg.id, "Uploading...")
        i = 1
        for ele in flist:
            app.send_document(message.chat.id,document=ele,caption=f"part {i}", reply_to_message_id=message.id, progress=progress, progress_args=[message])
            i = i + 1
            os.remove(ele)
    else:
        app.edit_message_text(message.chat.id, msg.id, "Uploading...")
        try:

            try:
                thumb = (collection.find_one({"tag": "thumbnail"}))["value"]
            except:
                thumb = None

            mode = collection.find_one({"tag": "mode"})
            mode = mode["value"] if mode and mode["value"] else None

            if (mode and mode == "doc") or not mode:
                temp_file = app.send_document(message.chat.id, thumb=thumb, document=file, reply_to_message_id=message.id, progress=progress, progress_args=[message])
            elif mode and mode == "video":
                temp_file = app.send_video(message.chat.id, thumb=thumb, document=file, reply_to_message_id=message.id, progress=progress, progress_args=[message])

            log_channel = collection.find_one({ "tag": "log_channel" })
            if log_channel and log_channel["value"]:
                temp_file.copy(log_channel["value"])

        except Exception as e:
            app.send_message(message.chat.id,e)
        os.remove(file)

    os.remove(f'{message.id}upstatus.txt')
    app.delete_messages(message.chat.id,message_ids=[msg.id])


@app.on_message(filters.command("mdisk"))
def echo(client, message):
    try:
        links = message.text.replace("mdisk ", "").split()

        if len(links) > 1:
            message.reply_text("Multiple Links found")

        for link in links:
            if "mdisk" in link:
                d = threading.Thread(target=lambda:down(message,link),daemon=True)
                d.start()
    except:
        app.send_message(message.chat.id, 'send only mdisk link with command followed by link')


print("Bot Running")
app.run()    
