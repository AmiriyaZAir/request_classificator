import pychrome
import json 
import re
import time
import threading
import random 
from cdt_impl import CDTImplementation
import signal
import sys
from random import randint
from util import Preprocessor

#usage: python main.py url base_url_part mode(manual|auto) time(1000 default)

url = sys.argv[1]
base_url = sys.argv[2]
mode = sys.argv[3]
if len(sys.argv) == 5:
    sec = int(sys.argv[4])
else:
    sec = 100
browser = pychrome.Browser(url="http://127.0.0.1:9222")

tab = browser.new_tab()
tab.start()

     #call method
tab.Network.enable()
tab.Runtime.enable()
tab.DOM.enable()
tab.Page.enable()
tab.CSS.enable()
debugger_id = tab.Debugger.enable()

cdt = CDTImplementation(tab, base_url)


tab.Debugger.paused = cdt.debugger_paused

tab.Page.navigate(url=url, _timeout=6)


tab.wait(10)

#setting breakpoints
RequestPattern = {'urlPattern': '*', 'resourceType': 'XHR', 'requestStage': 'Response'}
patterns=[RequestPattern]
tab.Fetch.enable(patterns=patterns)

tab.DOMDebugger.setXHRBreakpoint(url = ".")

tab.Fetch.requestPaused = cdt.request_paused
signal.signal(signal.SIGINT, cdt.ctr_c_handler)


if (mode == 'manual'):
    print("You can start manual crawling!")

else:
    print("AUTO MODE ON")
    current_listeners_array = []
    listeners_array = []
    old_listeners_array = []
    request_identificators = []
    dom_identificators = []

    original_dom = tab.DOM.getDocument(depth=-1)
    dom_identificators = cdt.parse_nodes(original_dom)
    tab.DOM.documentUpdated = cdt.document_updated()

    buttons_array = []
    forms_array = []

    old_buttons_array = ["btn"]
    old_forms_array = []

    start_time = time.time()
    flag = 1

    while True:

        print("_______________________NEW CYCLE STARTED_________________________ ")

        end_time = time.time()
        print()
        if (end_time - start_time) >  5000:
                
            cdt.print_results(url)
            break

        if (end_time -start_time) >  2500 and flag :
            flag = 0
            tab.Page.navigate(url=url, _timeout=6)

        old_buttons_array = buttons_array
        old_forms_array = forms_array

        try: 
            preprocessor = Preprocessor();
            current_buttons = []
            preprocessor.preprocess_buttons(buttons_array, old_buttons_array, tab)
            current_forms = []
            preprocessor.preprocess_forms(forms_array, old_forms_array, tab)
            dom_identificators = cdt.parse_nodes(original_dom)

            try:
                for node_id in dom_identificators:
                    #get event listeners
                    dom_object = tab.DOM.resolveNode(nodeId = node_id)
                    object_id = dom_object.get("object").get("objectId")
                    listeners = tab.DOMDebugger.getEventListeners(objectId=object_id, depth = -1, pierce = True)
                    current_listeners_array = cdt.parse_listeners(listeners.get('listeners'), node_id)

                    #run all scripts and activate listeners
                    position = 0
                    while position < len(current_listeners_array):
                        res = cdt.run_script(current_listeners_array[position])
                        print(position)
                        tab.wait(2)
                        position += 1
            except:
                continue

            preprocessor.preprocess_links(base_url, tab)

        except Exception as e:
            print("exception in main ", e)
            tab.Page.navigate(url=url, _timeout=6)
            continue

tab.wait(sec)
cdt.print_results(url)

tab.stop()
browser.close_tab(tab)