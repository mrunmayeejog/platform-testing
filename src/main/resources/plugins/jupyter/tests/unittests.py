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

Purpose:    Unit testing

"""
import json
import unittest

import requests
from mock import patch, MagicMock
from plugins.jupyter.TestbotPlugin import JupyterNotebook

class TestJupyterWhitebox(unittest.TestCase):
    @patch('requests.post')
    @patch('requests.get')
    @patch('requests.delete')
    def test_normal_use(self, requests_mock_post, requests_mock_get, requests_mock_delete):
        response = MagicMock()
        response.json.return_value = json.loads('{}')
        requests_mock_post.return_value = response
        requests_mock_get.return_value = response
        requests_mock_delete.return_value = response

        plugin = JupyterNotebook()
        values = plugin.runner("--jnbendpoint http://localhost", True)
        health = values[-1]
        self.assertEquals('OK', health[4])

        # simulate failure
        requests_mock_get.side_effect= requests_mock_get.side_effect  = requests.exceptions.RequestException
        plugin = JupyterNotebook()
        values = plugin.runner("--jnbendpoint http://localhost", 'ERROR')
        health = values[-1]
        self.assertEquals('ERROR', health[4])


if __name__ == '__main__':
    unittest.main()
