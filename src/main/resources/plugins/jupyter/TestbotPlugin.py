"""
Copyright (c) 2016 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Apache License, Version 2.0 (the "License").
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
The code, technical concepts, and all information contained herein, are the property of
Cisco Technology, Inc. and/or its affiliated entities, under various laws including copyright,
international treaties, patent, and/or contract. Any use of the material herein must be in
accordance with the terms of the License.
All rights not expressly granted by the License are reserved.

Unless required by applicable law or agreed to separately in writing, software distributed under
the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied.

Purpose:    CDH whitebox tests, proxied through CM API

"""

import time
import json
import argparse
import eventlet
import requests

from pnda_plugin import PndaPlugin
from pnda_plugin import Event

TIMESTAMP_MILLIS = lambda: int(round(time.time() * 1000))

TestbotPlugin = lambda: JupyterNotebook() # pylint: disable=invalid-name


class JupyterNotebook(PndaPlugin):

    def __init__(self):
        pass

    def read_args(self, args):
        """
        This class argument parser.
        This shall come from main runner in the extra arg
        """
        parser = argparse.ArgumentParser(prog=self.__class__.__name__, \
         usage='%(prog)s [options]', description='Key metrics from CDH cluster')
        parser.add_argument('--jnbendpoint', default='http://localhost:8080', \
         help='JupyterNotebook endpoint e.g. http://localhost:8080')

        return parser.parse_args(args)

    def runner(self, args, display=True):
        """
        Main section.
        """
        plugin_args = args.split() \
        if args is not None and (len(args.strip()) > 0) \
        else ""

        options = self.read_args(plugin_args)

        values = []
        health, cause = "OK", None
        cookies = ""
        service_running = False
        notebooks_available_count, available_kernels_count = -1, -1
        running_notebooks_count, active_sessions_count = -1, -1
        notebook_creation, notebook_deletion = False, False
        try:
            login_url = "%s/hub/login" % (options.jnbendpoint)
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.post(login_url, data={'username': 'pnda', 'password': 'pnda'}, allow_redirects=False, timeout=20)
            req.raise_for_status()
            end = TIMESTAMP_MILLIS()
            cookies = req.cookies

            req_xsrf = requests.get('%s/user/pnda/tree/' % (options.jnbendpoint), cookies=cookies)
            xsrf_cookie = req_xsrf.cookies['_xsrf']
            cookies['_xsrf'] = xsrf_cookie

            service_running = True
            service_running_count_ms = end - start
            values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                                "jupyter_notebook.jupyterhub_service_running_ms",
                                [], service_running_count_ms))
        except Exception:
            cause = "Unable to connect to Jupyter Server"

        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                            "jupyter_notebook.jupyterhub_service_running", [], service_running))

        try:
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.get("%s/user/pnda/api/contents" % (options.jnbendpoint), cookies=cookies, timeout=20)
            end = TIMESTAMP_MILLIS()
            contents = req.json().get('content', [])
            notebooks_available_count = len(contents)
            notebooks_available_count_ms = end-start
            values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                                "jupyter_notebook.notebooks_available_ms",
                                [], notebooks_available_count_ms))
        except Exception:
            cause = "Unable to connect to Jupyter Server"

        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                            "jupyter_notebook.notebooks_available_count", [], notebooks_available_count))

        try:
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.get("%s/user/pnda/api/kernelspecs" % (options.jnbendpoint), cookies=cookies, timeout=20)
            end = TIMESTAMP_MILLIS()
            kernelspecs = req.json().get('kernelspecs', [])
            available_kernels_count = len(kernelspecs)
            available_kernels_count_ms = end-start
            values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                                "jupyter_notebook.kernels_count_ms",
                                [], available_kernels_count_ms))
        except Exception:
            cause = "Unable to connect to Jupyter Server"

        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                            "jupyter_notebook.kernels_count", [], available_kernels_count))
        try:
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.get("%s/user/pnda/api/kernels" % (options.jnbendpoint), cookies=cookies, timeout=20)
            end = TIMESTAMP_MILLIS()
            running_notebooks_count = len(req.json())
            running_notebooks_count_ms = end - start
            values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                                "jupyter_notebook.running_notebooks_count_ms",
                                [], running_notebooks_count_ms))
        except Exception:
            cause = "Unable to connect to Jupyter Server"
        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                            "jupyter_notebook.running_notebook_count", [], running_notebooks_count))
        try:
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.get("%s/user/pnda/api/sessions" % (options.jnbendpoint), cookies=cookies, timeout=20)
            end = TIMESTAMP_MILLIS()
            active_sessions_count = len(req.json())
            active_sessions_count_ms = end - start
            values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                                "jupyter_notebook.active_sessions_count_ms",
                                [], active_sessions_count_ms))
        except Exception:
            cause = "Unable to connect to Jupyter Server"

        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                            "jupyter_notebook.active_sessions_count", [], active_sessions_count))

        try:
            start = TIMESTAMP_MILLIS()
            payload = {'type': 'notebook'}
            headers = {'content-type': 'application/json', 'X-XSRFToken': cookies['_xsrf']}
            with eventlet.Timeout(100):
                req = requests.post("%s/user/pnda/api/contents" % (options.jnbendpoint), data=json.dumps(payload),
                                    headers=headers, cookies=cookies, timeout=20)
            end = TIMESTAMP_MILLIS()

            check_req = requests.get("%s/user/pnda/api/contents/Untitled.ipynb" % (options.jnbendpoint),
                                     headers=headers, cookies=cookies, timeout=20)
            print ">>>>>>>>>>>>>>>>>>>>",check_req.json().keys()
            if 'message' not in check_req.json().keys():
                notebook_creation = True
                notebook_creation_ms = end - start
                values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook", "jupyter_notebook.notebook_creation_ms",
                                    [], notebook_creation_ms))
            else:
                cause = "Unable to create notebook"
        except Exception as err:
            cause = "Unable to connect to Jupyter Server"

        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook", "jupyter_notebook.notebook_creation",
                            [], notebook_creation))

        try:
            start = TIMESTAMP_MILLIS()
            with eventlet.Timeout(100):
                req = requests.delete("%s/user/pnda/api/contents/Untitled.ipynb"
                                      % (options.jnbendpoint), cookies=cookies,
                                      headers={'X-XSRFToken': cookies['_xsrf']}, timeout=20)
            end = TIMESTAMP_MILLIS()
            check_req = requests.get("%s/user/pnda/api/contents/Untitled.ipynb" \
                                % (options.jnbendpoint), headers=headers, cookies=cookies, timeout=20)

            if 'message' in check_req.json().keys():
                notebook_deletion = True
                notebook_deletion_ms = end - start
                values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook",
                                    "jupyter_notebook.notebook_deletion_ms",
                                    [], notebook_deletion_ms))
            else:
                cause = "Unable to delete notebook"
        except Exception as err:
            cause = "Unable to connect to Jupyter Server"

        values.append(Event(TIMESTAMP_MILLIS(), "jupyter_notebook", "jupyter_notebook.notebook_deletion",
                            [], notebook_deletion))
        if cause:
            health = "ERROR"

        values.append(Event(TIMESTAMP_MILLIS(), 'jupyter_notebook',
                            'jupyter_notebook.health', [cause], health))

        if display:
            self._do_display(values)

        return values
