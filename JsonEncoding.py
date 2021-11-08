from flask.json import JSONEncoder

#JSON 인코더 - json 변환시에 set자료형을 list로 만들어서 변환함
class CustomJSONEncoder(JSONEncoder):
    
    def default(self,obj):
        if isinstance(obj,set):
            return list(obj)
        
        return JSONEncoder.default(self,obj)
    