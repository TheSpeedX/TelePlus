
from telethon.sync import TelegramClient as TClient
from telethon.errors.rpcerrorlist import ApiIdInvalidError, PeerFloodError, UserPrivacyRestrictedError

class TelegramClient:
    def __init__(self,api_id,api_hash,phone):
        self.api_id=api_id
        self.api_hash=api_hash
        self.phone=phone
        self.client=TClient(self.phone, self.api_id, self.api_hash)
        
    
    async def auth(self,code=None,phone_code=None):
        await self.client.connect()
        if code:
            await self.client.sign_in(self.phone,code,phone_code_hash=phone_code)
        # else:
        #     self.client = TClient(self.phone, self.api_id, self.api_hash)
        #     await self.client.connect()
        flag = await self.client.is_user_authorized()
        if not flag:
            try:
                return await self.client.send_code_request(self.phone)
            except ApiIdInvalidError:
                return None
        return True

    def scrap(self):
        pass

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
    
    def add(self,telegram_client):
        self.client_store.append(telegram_client)
    
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