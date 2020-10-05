
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ApiIdInvalidError, PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser

import re
import os
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('telethon').setLevel(level=logging.DEBUG)

def build_group_path(group):
    group=re.sub("[^a-zA-Z0-9]","-",group)
    return os.path.join("data","groups",group+".json")


def save_group(group,data):
    with open(build_group_path(group),"w",encoding='UTF-8') as config_file:
        json.dump(data,config_file,indent=4)

class TGClient:

    def __init__(self,loop,api_id,api_hash,phone):
        self.api_id=api_id
        self.api_hash=api_hash
        self.phone=phone
        self.groups=[]
        self.groups_title=[]
        self.auth_check=None
        self.client=TelegramClient(self.phone, self.api_id, self.api_hash, loop=loop)
        
    async def auth(self,code=None,phone_code=None):
        print("before connection")
        await self.client.connect()
        if self.auth_check:
            if (datetime.now()-self.auth_check).seconds<600:
                return True
        if code:
            await self.client.sign_in(self.phone,code,phone_code_hash=phone_code)
        print("on connection")
        flag = await self.client.is_user_authorized()
        
        if not flag:
            try:
                return await self.client.send_code_request(self.phone)
            except ApiIdInvalidError:
                return None
        print("after connection")
        self.auth_check=datetime.now()
        return True

    async def list_groups(self):
        chunk_size=200
        print("Started Listing...")
        result = await self.client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash = 0
            ))
        chats = result.chats
        for chat in chats:
            try:
                if chat.megagroup:
                    self.groups.append(chat)
                    self.groups_title.append(chat.title)
            except:
                continue
        return len(self.groups)==len(self.groups_title)


    async def scrap(self,index):
        target_group=self.groups[index]
        all_participants = []
        all_participants = await self.client.get_participants(target_group)

        group_data=dict(name=target_group.title,id=target_group.id)
        final_data=[]
        for user in all_participants:
            username = user.username if user.username else ""
            first_name = user.first_name if user.first_name else ""
            last_name = user.last_name if user.last_name else ""
            name= (first_name + ' ' + last_name).strip()
            final_data.append(dict(username=username,name=name,id=user.id,access_hash=user.access_hash))
        group_data["members"]=[final_data]
        save_group((target_group.title+"-"+str(target_group.id)),group_data)
        return group_data

    def add(self):
        pass

    def todict(self):
        return {attr: getattr(self,attr) for attr in ["api_id","api_hash","phone"]}

    def __str__(self):
        print_attr=[ attr+"="+atval for attr,atval in self.todict().items() ]
        return "<"+",".join(print_attr)+">"


class ClientStore:
    def __init__(self):
        self.client_store=[]
    
    
    def pop(self,index=None):
        if index:
            return self.client_store.pop(index)
        else:
            return self.client_store.pop()
    def get(self,**kwargs):
        for i,client in enumerate(self.client_store):
            flag=True
            for attr in kwargs:
                if not str(kwargs[attr])==str(getattr(client,attr)):
                    flag=False
                    break
            if flag:
                return client
        return None
    
    def add(self,telegram_client):
        index = self.get_index(phone=telegram_client.phone)
        if not index==-1:
            self.pop(index)
        self.client_store.append(telegram_client)

    def get_index(self,**kwargs):
        for i,client in enumerate(self.client_store):
            flag=True
            for attr in kwargs:
                if not str(kwargs[attr])==str(getattr(client,attr)):
                    flag=False
                    break
            if flag:
                return i
        return -1
    
    def toconfig(self):
        return [client.todict() for client in self.client_store]
    def __str__(self):
        return str([str(client) for client in self.client_store])

    