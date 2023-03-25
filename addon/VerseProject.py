
from ast import Str
import json
from typing_extensions import Self
from urllib.parse import urlencode,urljoin
from Loader import load,LoadType,normalize_path

class UserInfo:
    def __init__(self) -> None:
        self.token='17b36eb006e07a153859ee9c36f7ca9dc8e746ac'
        pass

class VerseProject:
    def __init__(self) -> None:
        self.rootpath= 'https://develop-maker.layaverse.com/'
        self.userinfo = UserInfo()
        pass

    def _getUserInfo(self,uid:Str,password:Str):
        pass

    def open(self,gameid:int):
        self._getUserInfo('13693364578','guozhaokui')
        self._getProjectInfo(gameid,self.userinfo.token)
        pass

    
    def _getProjectInfo(self,gameid:int,token:Str):
        app = 'game/gameAndHistory'
        data = {'game_id':gameid, 'client':20,'access_token':token}
        my_query_params = '?'+urlencode(data)
        full_url = urljoin( urljoin(self.rootpath, app, my_query_params),my_query_params)
        data = load(full_url,LoadType.TEXT)
        pass

    def loadScene(self,scepath:Str):
        #scepath='https://develop-layaverse-1.layaverse.com/scenes_game/367318/scenes/0/scene_1670305604172_view.dat'
        data = load(scepath,LoadType.BIN)
        bflen = len(data)
        pass

if __name__ == "__main__":
    p = VerseProject()
    #p.open(10000)
    p.loadScene('https://develop-layaverse-1.layaverse.com/scenes_game/367318/scenes/0/scene_1670305604172_view.dat')
