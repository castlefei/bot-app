#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    QNA_KNOWLEDGEBASE_ID = os.environ.get("QnAKnowledgebaseId", "c2da8213-cef3-44e8-9696-3981b5c46556")
    QNA_ENDPOINT_KEY = os.environ.get("QnAEndpointKey", "45bfd31a-273d-4670-b292-5adc111b5740")
    QNA_ENDPOINT_HOST = os.environ.get("QnAEndpointHostName", "https://qnamaker-fei.azurewebsites.net/qnamaker")
