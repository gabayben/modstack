# SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.modules>
# SPDX-License-Identifier: Apache-2.0

import torch
from transformers import PreTrainedTokenizer, PreTrainedTokenizerFast, StoppingCriteria, TextStreamer

from modstack.typing import StreamingCallback

class StopWordsCriteria(StoppingCriteria):
    def __init__(
        self,
        tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast,
        stop_words: list[str],
        device: str | torch.device = 'cpu'
    ):
        if not tokenizer.pad_token:
            if tokenizer.eos_token:
                tokenizer.pad_token = tokenizer.eos_token
            else:
                tokenizer.add_special_tokens({'pad_token': '[PAD]'})
        encoded_stop_words = tokenizer(stop_words, padding=True, add_special_tokens=False, return_tensors='pt')
        self.stop_ids = encoded_stop_words.input_ids.to(device)

    def __call__(
        self,
        input_ids: torch.IntTensor,
        scores: torch.FloatTensor,
        **kwargs
    ) -> bool:
        for stop_id in self.stop_ids:
            if self.is_stop_word_found(input_ids, stop_id):
                return True
        return False

    @classmethod
    def is_stop_word_found(cls, generated_text_ids: torch.Tensor, stop_id: torch.Tensor) -> bool:
        generated_text_ids = generated_text_ids[-1]
        generated_text_size = generated_text_ids.size(0)
        stop_id_size = stop_id.size(0)
        return all(generated_text_ids[generated_text_size - stop_id_size:].eq(stop_id))

class TokenStreamingHandler(TextStreamer):
    def __init__(
        self,
        tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast,
        streaming_handler: StreamingCallback,
        stop_words: list[str] | None = None
    ):
        super().__init__(tokenizer=tokenizer, skip_prompt=True) #type: ignore[call-args]
        self.token_handler = streaming_handler
        self.stop_words = stop_words or []

    def on_finalized_text(self, text: str, stream_end: bool = False) -> None:
        word_to_send = text + '\n' if stream_end else text
        if word_to_send.strip() in self.stop_words:
            self.token_handler(word_to_send, {})