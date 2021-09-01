import logging

from nsds_lab_to_nwb.components.stimulus.tokenizers.tone_tokenizer import ToneTokenizer
from nsds_lab_to_nwb.components.stimulus.tokenizers.timit_tokenizer import TIMITTokenizer
from nsds_lab_to_nwb.components.stimulus.tokenizers.wn_tokenizer import WNTokenizer

logger = logging.getLogger(__name__)


class TrialsManager():
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

        self.custom_trial_columns = self.tokenizer.custom_trial_columns
        if self.custom_trial_columns is None:
            raise ValueError('self.custom_trial_columns should be set by the stim-specific tokenizer.')

    def add_trials(self, nwb_content, mark_onsets, stim_vals, mark_obj_name='recorded_mark'):
        if not self.tokenizable:
            return
        if self._already_tokenized(nwb_content):
            logger.info('Block has already been tokenized')
            return

        # tokenize to identify trials
        mark_time_series = self.read_mark(nwb_content, mark_obj_name)
        trial_list = self.tokenizer.tokenize(mark_onsets, mark_time_series, stim_vals)

        # add trial columns, then add trials
        for column_args in self.custom_trial_columns:
            nwb_content.add_trial_column(*column_args)
        for trial_kwargs in trial_list:
            nwb_content.add_trial(**trial_kwargs)

    def _already_tokenized(self, nwb_content):
        if not nwb_content.trials:
            return False
        if self.custom_trial_columns is None:
            return False
        has_custom_trial_columns = ((column_args[0] in nwb_content.trials.colnames)
                                    for column_args in self.custom_trial_columns)
        return all(has_custom_trial_columns)

    def read_mark(self, nwb_content, mark_obj_name):
        return nwb_content.stimulus[mark_obj_name]
