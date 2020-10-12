import json
import os
from quart import Quart, render_template, request, jsonify, make_response,redirect,url_for,session
from TGClient import *
from TGGroup import GroupStore
from datetime import datetime
import asyncio
import logging
import traceback
from threading import Thread 

logging.basicConfig(level=logging.ERROR)

app = Quart(__name__)

SETTINGS = json.load(open("settings.json"))

client_store = ClientStore()
group_store = GroupStore()
group_store.load()
loop = asyncio.get_event_loop()

for config in json.load(open(SETTINGS.get("config_path"))):
    client_store.add(TGClient(loop,**config))

def save_settings():
    with open("settings.json","w") as setting_file:
        json.dump(SETTINGS,setting_file,indent=4)

def save_config():
    with open(SETTINGS.get("config_path"),"w") as config_file:
        json.dump(client_store.toconfig(),config_file,indent=4)


@app.route('/')
async def home():
    # print("CONFIG: ",client_store.toconfig())
    # print("Home Request: ",client_store)
    session["config"]=client_store.toconfig()
    if len(session["config"])==0:
        return await render_template("default.html",type="guest",info={})
    elif not session.get("current"):
        session["current"] = session.get("config")[0]
    session["phone"]= json.load(open(build_phone_path(session["current"]["phone"])))
    if session["phone"].get("status"):
        return await render_template("default.html",type="active",info=session["phone"])
    else:
        return await render_template("default.html",type="inactive",info=session["phone"])
    

@app.route('/adduser',methods=["GET","POST"])
async def login():
    if request.method=="GET":
        return await render_template("login.html")
    else:
        data=await request.get_json()

        # if client_store.get(phone=data["phone"]):
        #     return {"success":False,"ask_code":False,"message":"Account Already Exists"}
        new_client = TGClient(loop,data["api_id"],data["api_hash"],data["phone"])

        if data.get("code"):
            flag=await new_client.auth(code=data["code"],phone_code=session["phone_code_hash"])
        else:
            flag=await new_client.auth()
        if flag==True:
            config_data= dict(status=False,target_group="",message="",count=0,total=0,timestamp=datetime.now().timestamp())
            save_phone(config_data,phone=new_client.phone)
            client_store.add(new_client)
            session["config"]=client_store.toconfig()
            await change_number(data["api_id"])
            save_config()
            return {"success":True}
        elif flag==None:
            return {"success":False,"ask_code":False,"message":"Invalid API ID/API HASH "}
        else:
            session["phone_code_hash"]=flag.phone_code_hash
            return {"success":False,"ask_code":True,"message":"Enter Code"}


@app.route('/settings', methods=['GET', 'POST'])
async def change_settings():
    if request.method == "GET":
        return await render_template("settings.html", settings=SETTINGS)
    else:
        data=await request.get_json()
        SETTINGS.update(data)
        save_settings()
        return {"success":True}


@app.route('/logout')
async def logout():
    client_store.pop(client_store.get_index(api_id=session["current"]["api_id"]))
    session["config"]=client_store.toconfig()
    save_config()
    if session["config"]:
        session["current"] = session.get("config")[0]
        session["phone"]= json.load(open(build_phone_path(session["current"]["phone"])))
    return redirect("/")
    

@app.route('/stop')
async def stop_add():
    client = client_store.get(api_id=session["current"]["api_id"])
    client.terminate()
    return redirect("/")

    
@app.route('/change/<api_id>')
async def change_number(api_id):
    session["current"] = client_store.get(api_id=api_id).todict()
    session["phone"]= json.load(open(build_phone_path(session["current"]["phone"])))
    return session["current"]

@app.route("/scrap/<int:index>")
async def scrap_group(index):
    client = client_store.get(phone=session["current"]["phone"])
    if index<len(client.groups):
        data = await client.scrap(index)
        group_store.load()
        return {"success":True,"members":len(data["members"][0])}
    return {"success":False}

@app.route("/split/<int:id>",methods=["POST"])
async def split_group(id):
    group = group_store.get(id=id)
    data=await request.get_json()
    if group:
        members = group.split(data["parts"],total_split=data["total_parts"])
        return {"success":True,"members":len(members)}
    return {"success":False}


@app.route("/split")
async def split_view():
    group_store.load()
    # print(group_store)
    return await render_template("splitter.html",groups=group_store.toconfig())

@app.route('/list')
async def list_groups():
    client = client_store.get(phone=session["current"]["phone"])
    # print(client)
    flag = await client.auth()
    if flag:
        if len(client.groups)==0:
            await client.list_groups()
        return await render_template("listing.html",flag=False,groups=client.groups_title)
    else:
        return await render_template("login.html",data=client.todict())

@app.route('/chooser/<int:id>/<int:part>/<int:index>')
async def add_group(id,part,index):
    client =  client_store.get(phone=session["current"]["phone"])
    from_group = group_store.get(id=id)
    members = from_group.members[part]
    target_group = client.groups[index]
    config=dict(status=True,target_group=target_group.title,message="Started Bot...",count=0,total=len(members),timestamp=datetime.now().timestamp()+10)
    save_phone(config,client.phone)
    try:
        thread = Thread(target=client.start_add,args=(loop,target_group,members,),daemon=True)
        thread.start()
    except:
        traceback.print_exc()
    return {"success":True}

@app.route('/chooser')
async def chooser_view():
    group_store.load()
    data = group_store.chooser_config()
    client = client_store.get(phone=session["current"]["phone"])
    flag = await client.auth()
    if flag:
        if len(client.groups)==0:
            await client.list_groups()
        return await render_template("selection.html",groups=data,all_groups=client.groups_title)
    else:
        return await render_template("login.html",data=client.todict())
    
def main():
    if not SETTINGS.get("secret_key"):
        SETTINGS.update({"secret_key":os.urandom(32).hex()})
        save_settings()
    app.secret_key = SETTINGS.get("secret_key",os.urandom(32).hex())
    app.run(host="0.0.0.0",port=SETTINGS.get("port",5000),debug=True,loop=loop)
    
if __name__ == '__main__':
    main()