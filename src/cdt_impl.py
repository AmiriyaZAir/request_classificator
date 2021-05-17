from util import  callframe, flag, RequestIdentificator, ProcessedRequestIdentificator, RequestPartsArray, Listener
import urlparse
from deepdiff import DeepDiff
from genson import SchemaBuilder
import urllib
import pychrome
import json
import time
import sys

class CDTImplementation():

    def __init__(self, tab, url):
        self.request_flag = flag()
        self.current_call_frame = callframe("")
        self.request = RequestIdentificator()
        self.parsed_request_arr = []
        
        self.callframe_arr = []
        self.method_arr = []
        self.url_arr = []
        self.path_arr = []
        self.url_params_arr = []
        self.post_params_arr = []

        self.all_requests = RequestPartsArray()
        self.valuable_requests = RequestPartsArray()
        self.hint_requests = RequestPartsArray()
        self.useless_requests = RequestPartsArray()

        self.tab = tab
        self.url = url

        self.updated = 0

    def parse_call_frames(self, debbuger_info):
        initial_call_frames = debbuger_info.get("callFrames")
        result_call_frames = []
        for frame in initial_call_frames:
            frame.pop("scopeChain")
            frame.pop("this")
            frame.pop("callFrameId")
            frame["location"].pop("scriptId")
            try:
                frame.pop("functionLocation")
                frame.pop("returnValue")
            except:
                pass
            result_call_frames.append(str(frame))
        return result_call_frames


    def debugger_paused(self, **kwargs):
        if  (self.request_flag.get() == 0 or self.request_flag.get() == 2):
            self.current_call_frame.set(self.parse_call_frames(kwargs)) 
            self.request_flag.first()
            
        self.tab.Debugger.resume()
        return


    def request_paused(self, **kwargs):
        try:
            if self.request_flag.get() == 1:
                url = kwargs.get('request').get('url')
                method = kwargs.get('request').get('method') 
                responseCode = kwargs.get('responseStatusCode')

                try:
                    postData=kwargs.get('request').get("postData")
                except:
                    postData = ""

                self.request = RequestIdentificator(self.current_call_frame.get(), url, method, postData)
                self.process_request(self.request)


                self.request_flag.second()
        except Exception as e:
            print("Exception in request paused: ", e)

        return


    def process_request(self, request):
        parsed_request = ProcessedRequestIdentificator()
        parsed_request.set_method(request.get_method())
        url_parsed = urlparse.urlparse(request.get_url())

        if(url_parsed.netloc.find(self.url) == -1):
            print("nope", url_parsed.netloc, self.url)
            return
       
        parsed_request.set_url(url_parsed.netloc)
        parsed_request.set_path(url_parsed.path)
        
        #parse url params
        try:
            if (url_parsed.query):
                parsed_request.set_url_params(dict(urlparse.parse_qsl(url_parsed.query)))
                print("QUERY: ", parsed_request.get_url_params())
        except Exception as e:
            print("exception while parsing url get params: ", e)

        post_params = ""
        if (parsed_request.get_method() == "POST"):
            try:
                post_params = request.get_postData()
                post_params = str(post_params).encode('utf8', 'ignore').decode('utf8')
                
                if(post_params[0] == "{" or (post_params[0] == "[" and post_params[1] == "{")):
                    post_params = self.process_post_data(post_params)
                else:
                    post_params = dict(urlparse.parse_qsl(post_params))

                parsed_request.set_post_params(post_params)
           
            except Exception as e:
                print("exception while parsing url post params: ", e)
                print(post_params)
                #post_params = {str(post_params) : 0}
                #parsed_request.set_post_params(post_params)
            
        parsed_request.set_callFrames(request.get_callFrames())
        
        print "REQUEST DATA: " + str(parsed_request.get()) + "\n"
        self.parsed_request_arr.append(parsed_request)
        
        try:
            #self.add_request_detailes_to_arrays(parsed_request)
            self.remove_useless_parts(parsed_request)
            self.process_valuable_parts(parsed_request)
        except Exception as e:
            print("smth happend here: ", e)


    def process_post_data(self, data):
        data = json.loads(data)
        data = data[0]
        diff = DeepDiff({}, data, ignore_order=True, verbose_level=2).get('dictionary_item_added')
        result = {}
        reached_values = {}
        while diff != {}:
            try:
                reached_values = self.parse_json_diff(diff)
                result = dict(result.items() + reached_values.items()) 
            except Exception as e:
                print("exception in processing post data: ", e)

        #add keys to global array 
        #add values to global array 
        try:
            for key, value in result.items():
                result[key] = str(value).replace('"', '')
        except Exception as e:
            print("ERROR PROCESS POST DATA ")

        print(result)

        return result


    def process_json_scheme(self, data):
        builder = SchemaBuilder()
        #builder.add_schema({"type": "object"})
        builder.add_object(data)
        schema = builder.to_schema()
        return schema


    def parse_json_diff(self, diff):
        print("parsing json diff\n")
        reached_values = {}
        for key, value in diff.items():
            if (isinstance(value, str) and value[0]=="{"):
                value = json.loads(value)

            if isinstance(value, dict):
                value = dict(value)

                for key1, value1 in value.items():
                    new_key = key + '[' + "'"+str(key1)+"'" + ']'
                    value1 = json.dumps(value1)
                    diff[new_key] = value1
                
            else:
                reached_values[key] = value
            diff.pop(key)

        return reached_values


    def add_request_detailes_to_arrays(self, parsed_request):
       
        if (parsed_request.get_url() not in self.all_requests.url_arr):
            self.all_requests.url_arr.append(parsed_request.get_url())

        if (parsed_request.get_method() not in self.all_requests.method_arr):
            self.all_requests.method_arr.append(parsed_request.get_method())

        if (parsed_request.get_path() not in self.all_requests.path_arr):
            self.all_requests.path_arr.append(parsed_request.get_path())
 
        if (parsed_request.get_callFrames() not in self.all_requests.callframe_arr):
            self.all_requests.callframe_arr.append(parsed_request.get_callFrames())

        if (parsed_request.get_url_params() not in self.all_requests.url_params_arr):
            self.all_requests.url_params_arr.append(parsed_request.get_url_params())

        if (parsed_request.get_post_params() not in self.all_requests.post_params_arr):
            self.all_requests.post_params_arr.append(parsed_request.get_post_params())


    def remove_useless_parts(self, parsed_request):
        try:

            url_params = parsed_request.get_url_params()
            print ("REMOVED URL: ")
            for key, value in url_params.items():
                if key in self.useless_requests.url_params_arr :
                    url_params.pop(key)
                    print key
            parsed_request.set_url_params(url_params)

            post_params = parsed_request.get_post_params()
            print ("REMOVED POST: ")
            for key, value in post_params.items():
                if key in self.useless_requests.post_params_arr :
                    post_params.pop(key)
                    print key
            parsed_request.set_post_params(post_params)
        except Exception as e:
            print("exception in remove_useless_parts: ", e)
       
    def remove_repeated_callframes(self):
        for key, value in self.valuable_requests.url_params_arr.items() :
            num = value[0]
            if (num > 0 and len(value) == 2) or (num == (len(value) - 2)) :
                self.valuable_requests.url_params_arr.pop(key)
                self.useless_requests.url_params_arr[key] = value

        for key, value in self.valuable_requests.post_params_arr.items() :
            num = value[0]
            if (num > 0 and len(value) == 2) or (num == (len(value) - 2)) :
                self.valuable_requests.post_params_arr.pop(key)
                self.useless_requests.post_params_arr[key] = value



    def process_valuable_parts(self, parsed_request):

        try:
            method = parsed_request.get_method()
            url = parsed_request.get_url()
            path = parsed_request.get_path()
            url_params = parsed_request.get_url_params()
            post_params = parsed_request.get_post_params()
            call_frames = parsed_request.get_callFrames()
    
            if method not in self.valuable_requests.method_arr :
                self.save_valuable_info(method, url, path, url_params, post_params, call_frames)

            elif url not in self.valuable_requests.url_arr :
                self.save_valuable_info("", url, path, {}, {}, call_frames)
                self.save_hint_info("", "", "", url_params, post_params)

            elif path not in self.valuable_requests.path_arr :
                self.save_valuable_info("", "", path, {}, {}, call_frames)
                if path in self.hint_requests.path_arr :
                    self.hint_requests.path_arr.remove(path)

            else:
                self.save_valuable_info("", "", "", url_params, post_params, [])

                if call_frames not in self.valuable_requests.callframe_arr:
                    self.save_valuable_info("", "", "", {}, {}, call_frames)

                else:
                    for frame in self.parsed_request_arr:
                        if frame.get_callFrames == call_frames:
                            self.intersect_valuable_params(frame.get_url_params, frame.get_post_params, url_params, post_params)

        except Exception as e:
            print ("exception in processing valuable parts ", e)

       


       
    def save_valuable_info(self, method, url, path, url_params, post_params, call_frames):
        print ("SAVED VALUABLE: ", method, url, path, url_params, post_params)
        try:
            if method :
                self.valuable_requests.method_arr.append(method)
            
            if url :
                self.valuable_requests.url_arr.append(url)

            if path :
                self.valuable_requests.path_arr.append(path)

            if url_params :
                for key, value in url_params.items():
                    if key in self.hint_requests.url_params_arr:
                        self.hint_requests.url_params_arr.pop(key)

                    if key in self.valuable_requests.url_params_arr:
                        valuable_val = self.valuable_requests.url_params_arr[key]
                        if value not in valuable_val:
                            valuable_val.append(value)
                        valuable_val[0] += 1
                        self.valuable_requests.url_params_arr[key] = valuable_val
                    else:
                        self.valuable_requests.url_params_arr[key] = [0, value]

            if post_params :
                for key, value in post_params.items():
                    if key in self.hint_requests.post_params_arr:
                        self.hint_requests.post_params_arr.pop(key)

                    if key in self.valuable_requests.post_params_arr:
                        valuable_val = self.valuable_requests.post_params_arr[key]
                        if value not in valuable_val:
                            valuable_val.append(value)
                        valuable_val[0] += 1
                        self.valuable_requests.post_params_arr[key] = valuable_val
                    else:
                        self.valuable_requests.post_params_arr[key] = [0, value]

            if call_frames :
                self.valuable_requests.callframe_arr.append(call_frames)

        except Exception as e:
            print("exception in save valuable request: ", e)
                



    def save_hint_info(self, method, url, path, url_params, post_params):
     
        try:
            if method :
                self.hint_requests.method_arr.append(method)
            
            if url :
                self.hint_requests.url_arr.append(url)

            if path :
                self.hint_requests.path_arr.append(path)

            if url_params :
                for key, value in url_params.items():
                    self.hint_requests.url_params_arr[key] = value

            if post_params :
                for key, value in post_params.items():
                    self.hint_requests.post_params_arr[key] = value


        except Exception as e:
            print("exception in save hint request: ", e)
                

    def intersect_valuable_params(self, old_url_params, old_post_params, new_url_params, new_post_params):
        try:
            for key, value in new_url_params.items():
                if key not in old_url_params :
                    self.useless_requests.url_params_arr[key] = value
                    self.valuable_requests.url_params_arr.pop(key)
                elif value != old_url_params[key] :
                    self.useless_requests.url_params_arr[key] = value
                    self.valuable_requests.url_params_arr.pop(key)

            for key, value in new_post_params.items():
                if key not in old_post_params :
                    self.useless_requests.post_params_arr[key] = value
                    self.valuable_requests.post_params_arr.pop(key)
                elif value != old_post_params[key] :
                    self.useless_requests.post_params_arr[key] = value
                    self.valuable_requests.post_params_arr.pop(key)

        except Exception as e:
            print("exception in intersect valuable params: ", e)


    def print_parsed_requests(self):
        num = 0
        for i in self.parsed_request_arr :
            print("REQUEST " + str(num) + str(i.get()) + "\n")
            num += 1


    def ctr_c_handler(self, signal, frame):
        print("CTRL+C RECIEVED\n")
        self.print_parsed_requests()

        self.print_results(self.url)
        
        raise ValueError('A very specific bad thing happened')

        sys.exit(0)



    def document_updated (self):
        updated = 1
        return


    def parse_listeners(self, listeners, node_id):
        current_listeners_array = []
        for listener in listeners:
            if listener.get("type") != 'error' :
                listener_type  = listener.get("type")
                if listener_type != 'click' and listener_type != 'load' and listener_type != 'submit' and listener_type != 'scroll':
                    continue
                new_listener = Listener(listener.get("scriptId"),  listener.get("columnNumber"), listener.get("useCapture"),
                    listener.get("passive"), listener.get("lineNumber"),
                    listener.get("type"), listener.get("once"))
                if new_listener not in current_listeners_array:
                    current_listeners_array.append(new_listener)

        if  len(current_listeners_array):
            current_listeners_array.sort()
            
        return current_listeners_array

    def run_script(self, listener):
        result = ""
        script_id = listener.get()[0] 
        try:
            self.tab.Runtime.terminateExecution()
            self.tab.wait(2)
        except Exception as e:
            print("problem with termination", e)

        try:
            script = self.tab.Debugger.getScriptSource(scriptId = script_id)
            compiled_script = self.tab.Runtime.compileScript(expression = script.get("scriptSource"),sourceURL="*", persistScript = True)
            print("RUN SCRIPT WITH ID ", compiled_script.get("scriptId"))
            result = self.tab.Runtime.runScript(scriptId = compiled_script.get("scriptId"), includeCommandLineAPI = True, returnByValue = False)
            return str(result)
        except Exception as e:
            print("PROBLEM WITH SCRIPT", e)
            pass
        return str(result)


    def parse_nodes(self, dom):
        try: 
            full_dom = []
            full_dom.append(dom)
            nodes = []
            nodes.append(dom.get("root").get("nodeId"))
            old_nodes = []
            while old_nodes != nodes :
                old_nodes = nodes
                for node in full_dom:
        
                    if node.get("root").get("nodeId") not in nodes:
                        nodes.append(node.get("root").get("nodeId"))

                    children = node.get("children")
                    if children :
                        full_dom.append(children)
                    full_dom.remove(node)

        except Exception as e:
            print("PROBLEM WITH SCRIPT", e)

        return nodes



    def print_results (self, url):

        #self.print_parsed_requests()
        f = open("results"+self.url +".txt", 'a')

        self.remove_repeated_callframes()

        f.write(url)
        f.write("All valuable methods:")
        f.write(str(self.valuable_requests.method_arr))
        f.write("\n")

        print ("All valuable methods:")
        print(self.valuable_requests.method_arr)
        print()

        f.write("All valuable urls:")
        f.write(str(self.valuable_requests.url_arr))
        f.write("\n")

        print ("All valuable urls:")
        print(self.valuable_requests.url_arr)
        print()

        f.write("All valuable paths:")
        f.write(str(self.valuable_requests.path_arr))
        f.write("\n")

        print ("All valuable paths:")
        print(self.valuable_requests.path_arr)
        print()

        f.write("All valuable url_params:")
        f.write(str(self.valuable_requests.url_params_arr))
        f.write("\n")

        print ("All valuable url_params:")
        print(self.valuable_requests.url_params_arr)
        print()

        f.write("All valuable post_params:")
        f.write(str(self.valuable_requests.post_params_arr))
        f.write("\n")

        print ("All valuable post_params:")
        print(self.valuable_requests.post_params_arr)
        print()

        f.write("HINT\n")
        f.write(str(self.useless_requests.get()))
        
        print("USELESS\n")
        print(str(self.useless_requests.get()))

        f.close()
