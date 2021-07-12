from nsds_lab_to_nwb.components.stimulus.tokenizers.tone_tokenizer import ToneTokenizer
from nsds_lab_to_nwb.components.stimulus.tokenizers.timit_tokenizer import TIMITTokenizer
from nsds_lab_to_nwb.components.stimulus.tokenizers.wn_tokenizer import WNTokenizer


class MarkTokenizer():
    def __init__(self, block_name, stim_configs):
        self.block_name = block_name
        self.stim_configs = stim_configs

        self.tokenizable = True
        if self.stim_configs['type'] == 'continuous':
            self.tokenizable = False
            return

        stim_name = self.stim_configs['name']
        if 'tone' in stim_name:
            self.tokenizer = ToneTokenizer(self.block_name, self.stim_configs)
        elif 'timit' in stim_name:
            self.tokenizer = TIMITTokenizer(self.block_name, self.stim_configs)
        elif 'wn' in stim_name:
            self.tokenizer = WNTokenizer(self.block_name, self.stim_configs)
        else:
            raise ValueError(f"Unknown stimulus type '{stim_name}' for mark tokenizer")

    def tokenize(self, nwb_content, stim_vals):
        if not self.tokenizable:
            return
        self.tokenizer.tokenize(nwb_content, stim_vals)
