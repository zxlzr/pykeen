# -*- coding: utf-8 -*-

"""Training KGE models based on the CWA."""

import numpy as np
import torch
from tqdm import trange

from .base import TrainingLoop
from .utils import split_list_in_batches
from ..instance_creation_factories.instances import Instances

__all__ = [
    'CWATrainingLoop',
]


class CWATrainingLoop(TrainingLoop):
    """A training loop that uses the closed world assumption."""

    def train(
            self,
            training_instances: Instances,
            num_epochs: int,
            batch_size: int,
            label_smoothing: bool = True,
            label_smoothing_epsilon: float = 0.1,
    ):
        """Train the model using the closed world assumption."""
        self.kge_model = self.kge_model.to(self.device)
        subject_relation_pairs = training_instances.instances
        labels = training_instances.labels
        num_entities = len(training_instances.entity_to_id)

        num_triples = subject_relation_pairs.shape[0]

        _tqdm_kwargs = dict(desc=f'Training epoch on {self.device}')
        for _ in trange(num_epochs, **_tqdm_kwargs):
            indices = np.arange(num_triples)
            np.random.shuffle(indices)
            subject_relation_pairs = subject_relation_pairs[indices]
            labels = [labels[i] for i in indices]
            batches = split_list_in_batches(input_list=subject_relation_pairs, batch_size=batch_size)
            labels_batches = split_list_in_batches(input_list=labels, batch_size=batch_size)
            current_epoch_loss = 0.

            for batch_pairs, batch_labels in zip(batches, labels_batches):
                current_batch_size = len(batch_pairs)
                batch_pairs = torch.tensor(batch_pairs, dtype=torch.long, device=self.device)

                batch_labels_full = torch.zeros((current_batch_size, num_entities), device=self.device)
                for i in range(current_batch_size):
                    batch_labels_full[i, batch_labels[i]] = 1

                if label_smoothing:
                    batch_labels_full = (batch_labels_full * (1.0 - label_smoothing_epsilon)) + \
                                        (label_smoothing_epsilon / (num_entities - 1))

                # Recall that torch *accumulates* gradients. Before passing in a
                # new instance, you need to zero out the gradients from the old instance
                self.optimizer.zero_grad()
                loss = self.kge_model(batch_pairs, batch_labels_full)
                current_epoch_loss += (loss.item() * current_batch_size)

                loss.backward()
                self.optimizer.step()

            # Track epoch loss
            self.losses_per_epochs.append(current_epoch_loss / len(subject_relation_pairs))

        return self.kge_model, self.losses_per_epochs