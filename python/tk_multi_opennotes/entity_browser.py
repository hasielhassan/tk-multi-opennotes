# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import os
import sys
import threading
from datetime import datetime
from tank.platform.qt import QtCore, QtGui

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

class EntityBrowserWidget(browser_widget.BrowserWidget):

    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)
        
        # only load this once!
        self._current_user = None
        self._current_user_loaded = False
        self._initTime = datetime.now()
        

    def get_data(self, data):

        self._current_user = tank.util.get_shotgun_user(self._app.shotgun)
        notes = self._app.shotgun.find("Note", 
                                       [ ["project", "is", self._app.context.project], 
                                         ["note_links", "in", self._app.context.entity]], 
                                         ["subject","sg_status_list","tasks","note_links","type","user","created_at","content","replies","attachments"],
                                         [{'field_name':'updated_at','direction':'desc'}]
                                       )
        userDict = dict()

        for note in notes:
            if 'user' in note:
                if not note['user']['name'] in userDict:
                    userDict[note['user']['name']] = self._app.shotgun.find_one("HumanUser",[['id','is',note['user']['id']]], ['image'])

        return {"data": notes,
                "users": userDict,
                "curTime": datetime.now()}

    def process_result(self, result):

        if len(result.get("data")) == 0:
            self.set_message("No notes found!")
            return
        contextTask = self._app.context.task
        if not contextTask:
            temp = self.add_item(browser_widget.ListHeader)
            temp.set_title("<FONT COLOR='#FF0000'>NO TASK PRESENT IN THE CONTEXT THIS IS BAD PLEASE US THE SETCONTEXT APPS</FONT COLOR='#FF0000'>")
        if result['users']:
            icons = result['users']

        for e,note in enumerate(result.get("data")):
            if e == 0:
                userBanner = self.add_item(browser_widget.ListHeader)
                userBanner.set_title("Notes from %s" % (note['user']['name']))
                self.setData(note, result, contextTask)
                currUser = note['user']['name']
            else:
                if note['user']['name'] == currUser:
                    self.setData(note, result, contextTask)
                else:
                    userBanner = self.add_item(browser_widget.ListHeader)
                    userBanner.set_title("Notes from %s" % (note['user']['name']))
                    self.setData(note, result, contextTask)
                    currUser = note['user']['name']
                    
    def setData(self,note,result,contextTask):
        overview = self.add_item(browser_widget.ListItem)
        image = result['users'][note['user']['name']]['image']
        if 'tasks' in note:
            tasks = note['tasks']
            retTasks = list()
            for task in tasks:
                if 'name' in task:
                    retTasks.append(task['name'])
        if contextTask:
            if self._app.context.task['name'] in retTasks:
                details = "<FONT COLOR='#65D552'><b>%s</b><br>from %s<br>status: %s<br>tasks: <b>%s</b></FONT COLOR='#65D552'>" % (note.get("subject"), 
                                                  note.get("created_at"), 
                                                  note.get('sg_status_list'),
                                                  ", ".join(retTasks))
            else:
                details = "<b>%s</b><br>from %s<br>status: %s<br>tasks: <b>%s</b>" % (note.get("subject"), 
                                                  note.get("created_at"), 
                                                  note.get('sg_status_list'),
                                                  ", ".join(retTasks))
        else:
            details = "<b>%s</b><br>from %s<br>status: %s<br>tasks: <b>%s</b>" % (note.get("subject"), 
                                              note.get("created_at"), 
                                              note.get('sg_status_list'),
                                              ", ".join(retTasks))
                
        overview.set_details(details)
        note['curTime'] = result['curTime']
        overview.sg_data = note
        if image:
            overview.set_thumbnail(image)
            note['user']['image'] = image
            overview.sg_data = note
        else:
            note['user']['image'] = None
            overview.sg_data = note