import pychrome
import random

class num():
    def __init__(self):
        self.num = 0

    def add(self):
        self.num += 1
        return self.num
    def get(self):
        return self.num 


class callframe():
    def __init__(self, frame):
        self.frame = frame

    def get(self):
        return self.frame

    def set(self, new_frame):
        self.frame = new_frame        


class flag():
    def __init__(self):
        self.flag = 0

    def first(self):
        self.flag = 1

    def second(self):
        self.flag = 2

    def get(self):
        return self.flag


class RequestIdentificator:
    def __init__(self, callFrames = [], url = "", method = "" ,  postData=""):
        self.callFrames = callFrames
        self.url = url
        self.method = method
        self.postData = postData

    def get(self):
        arr = []
        arr.append(self.callFrames)
        arr.append(self.url)
        arr.append(self.method)
        arr.append(self.postData)
        return arr

    def get_url(self):
        return self.url

    def get_method(self):
        return self.method

    def get_postData(self):
        return self.postData

    def get_callFrames(self):
        return self.callFrames

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return ( self.callFrames, self.url, self.method, self.postData)  ==  (
            other.callFrames, other.url, other.method,  other.postData)
        

class Listener:
    def __init__(self, scriptid, columnnumber, usecapture, passive, linenumber, eventtype, once):
        self.scriptId = scriptid
        self.columnNumber = columnnumber
        self.useCapture = usecapture
        self.passive = passive
        self.lineNumber = linenumber
        self.eventType = eventtype
        self.once = once

    def get(self):
        arr = []
        arr.append(self.scriptId)
        arr.append(self.columnNumber)
        arr.append(self.useCapture)
        arr.append(self.passive)
        arr.append(self.lineNumber)
        arr.append(self.eventType)
        arr.append(self.once)
        return arr

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return (self.scriptId, self.columnNumber, self.useCapture, self.passive, 
            self.lineNumber, self.eventType, self.once) == (other.scriptId, other.columnNumber,
            other.useCapture, other.passive, other.lineNumber, other.eventType, other.once)


class ProcessedRequestIdentificator:
    def __init__(self, method = "" , url = "", path = "",  url_params={}, callFrames = [], graphQL = "", post_params = {}):
        self.method = method
        self.url = url
        self.path = path
        self.url_params = url_params
        self.graphQL = graphQL
        self.callFrames = callFrames
        self.post_params = post_params

        
    def get(self):
        arr = []
        arr.append(self.method)
        arr.append(self.url)
        arr.append(self.path)
        arr.append(self.url_params)
        arr.append(self.graphQL)
        arr.append(self.callFrames)
        arr.append(self.post_params)
        return arr

    def get_method(self):
        return str(self.method)

    def get_url(self):
        return str(self.url)

    def get_path(self):
        return str(self.path)

    def get_url_params(self):
        return self.url_params
   
    def get_graphQL(self):
        return self.graphQL

    def get_callFrames(self):
        return self.callFrames

    def get_post_params(self):
        return self.post_params    


    def set_method(self, method):
        self.method = str(method)

    def set_url(self, url):
        self.url = str(url)

    def set_path(self, path):
        self.path = str(path)

    def set_url_params(self, url_params):
        self.url_params = url_params
   
    def set_graphQL(self, graphQL):
        self.graphQL = graphQL

    def set_callFrames(self, callFrames):
        self.callFrames = callFrames

    def set_post_params(self, post_params):
        self.post_params = post_params   



    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return ( self.callFrames, self.url, self.method, self.path, self.url_params, self.graphQL)  ==  (
            other.callFrames, other.url, other.method, other.path, other.url_params, other.graphQL)


class RequestPartsArray:

    def __init__(self):

        self.callframe_arr = []
        self.method_arr = []
        self.url_arr = []
        self.path_arr = []
        self.url_params_arr = {}
        self.post_params_arr = {}

    def get(self):
        arr = []
        arr.append(self.method_arr)
        arr.append(self.url_arr)
        arr.append(self.path_arr)
        arr.append(self.url_params_arr)
        arr.append(self.post_params_arr)
        return arr


class Listener:
    def __init__(self, scriptid, columnnumber, usecapture, passive, linenumber, eventtype, once):
        self.scriptId = scriptid
        self.columnNumber = columnnumber
        self.useCapture = usecapture
        self.passive = passive
        self.lineNumber = linenumber
        self.eventType = eventtype
        self.once = once

    def get(self):
        arr = []
        arr.append(self.scriptId)
        arr.append(self.columnNumber)
        arr.append(self.useCapture)
        arr.append(self.passive)
        arr.append(self.lineNumber)
        arr.append(self.eventType)
        arr.append(self.once)
        return arr

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return (self.scriptId, self.columnNumber, self.useCapture, self.passive, 
            self.lineNumber, self.eventType, self.once) == (other.scriptId, other.columnNumber,
            other.useCapture, other.passive, other.lineNumber, other.eventType, other.once)

class Preprocessor:
    def __init__(tab):
        self.tab = tab

    def preprocess_buttons(self, buttons_array, old_buttons_array):
        res = self.tab.Runtime.evaluate(expression = "res = document.querySelectorAll('button'); ", includeCommandLineAPI = True)
        num = int(re.findall('\d+', res.get("result").get("description"))[0])
           
        r = list(range(num))
        random.shuffle(r)
        for i in r:
            expression = "res["+str(i)+"]"
            res = self.tab.Runtime.evaluate(expression = expression, includeCommandLineAPI = True)
            current_buttons.append(res.get("result").get("description"))
            res = self.tab.Runtime.evaluate(expression = expression + ".click()", includeCommandLineAPI = True)
            self.tab.wait(3)

        for button in current_buttons:
            if button not in buttons_array:
                buttons_array.append(button)
                    

    def preprocess_forms(self, forms_array, old_forms_array):
        res = self.tab.Runtime.evaluate(expression = "res = document.querySelectorAll('form');", includeCommandLineAPI = True)
        num = int(re.findall('\d+', res.get("result").get("description"))[0])

        for i in range (0, num):
            expression = "res["+str(i)+"]"
            res = self.tab.Runtime.evaluate(expression = expression, includeCommandLineAPI = True)
            current_forms.append(res.get("result").get("description"))
            res = self.tab.Runtime.evaluate(expression = expression + ".submit()", includeCommandLineAPI = True)
            self.tab.wait(1)

            for form in current_forms:
                if form not in forms_array:
                    forms_array.append(form)

    def preprocess_links(self, base_url):
        res = self.tab.Runtime.evaluate(expression = "res = document.links", includeCommandLineAPI = True)
        num = int(re.findall('\d+', res.get("result").get("description"))[0])
        link_num = randint(1, num - 1)
        res = self.tab.Runtime.evaluate(expression = "res = res["+ str(link_num) +"].href", includeCommandLineAPI = True)
        next_url = res.get("result").get("value")
                    
        if (next_url.find(base_url) != -1):
            self.tab.Runtime.evaluate(expression = "res = res[" + str(link_num) + "].click()", includeCommandLineAPI = True)
            self.tab.wait(4)

