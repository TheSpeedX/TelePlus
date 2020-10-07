
from TGClient import *
import glob
import os
import json

class Group:
    def __init__(self,path,name,id,members):
        self.path=path
        self.filename=os.path.split(path)[1]
        self.name=name
        self.id=id
        self.members=members

    def save(self):
        config={"name":self.name,
                "id":self.id,
                "members":self.members}
        save_group(self.filename[:-5],config)
    
    def split(self,n,total_split=False):
        members=[member for subgroup in self.members for member in subgroup]
        if total_split:
            mod=len(members)//n
            self.members =[members[i*mod:(i+1)*mod] if (i+2)*mod<=len(members) else members[i*mod:] for i in range(n)]
        else:
            self.members = [members[i:i+n] if (i+n)<=len(members) else members[i:] for i in range(0,len(members),n)]
        self.save()
        return self.members
    
    def todict(self):
        count=sum([len(subgroup) for subgroup in self.members])
        result= {attr: getattr(self,attr) for attr in ["id","name","filename"]}
        result.update({"count":count})
        return result

    def chooser_config(self):
        count=sum([len(subgroup) for subgroup in self.members])
        result= {attr: getattr(self,attr) for attr in ["id","name"]}        
        result.update({"memcount":{ i:len(k) for i,k in enumerate(self.members)}})
        return result

    def __str__(self):
        print_attr=[ attr+"="+str(atval) for attr,atval in self.todict().items() ]
        return "<"+", ".join(print_attr)+">"

class GroupStore:


    def __init__(self):
        self.group_store=[]
    
    def load(self):
        self.group_store=[]
        group_path = os.path.join("data","groups","*.json")
        for path in glob.glob(group_path):
            with open(path,"r",encoding="UTF-8") as group_file:
                group_json=json.load(group_file)
                self.group_store.append(Group(path,**group_json))

    def pop(self,index=None):
        if index:
            return self.group_store.pop(index)
        else:
            return self.group_store.pop()

    def get(self,**kwargs):
        for i,group in enumerate(self.group_store):
            flag=True
            for attr in kwargs:
                if not str(kwargs[attr])==str(getattr(group,attr)):
                    flag=False
                    break
            if flag:
                return group
        return None

    def get_index(self,**kwargs):
        for i,group in enumerate(self.group_store):
            flag=True
            for attr in kwargs:
                if not str(kwargs[attr])==str(getattr(group,attr)):
                    flag=False
                    break
            if flag:
                return i
        return -1
    
    
    def add(self,group):
        index = self.get_index(id=group.id)
        if not index==-1:
            self.pop(index)
        self.group_store.append(group)

    def toconfig(self):
        return [group.todict() for group in self.group_store]
    
    def chooser_config(self):
        return [group.chooser_config() for group in self.group_store]

    def __str__(self):
        return str([str(group) for group in self.group_store])