"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/pipeline.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from functools import partial

from modstack.modules.flows import FlowBase, FlowData, RunFlow
from modstack.typing import Effect, Effects

class Flow(FlowBase):
    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowData]:
        return Effects.Sync(partial(self._invoke, data, **kwargs))

    def _invoke(self, data: RunFlow, **kwargs) -> FlowData:
        pass