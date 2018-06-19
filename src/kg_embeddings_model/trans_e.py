# -*- coding: utf-8 -*-
import torch
import torch.autograd
import torch.nn as nn

from utilities.constants import EMBEDDING_DIM, MARGIN_LOSS, NUM_ENTITIES, NUM_RELATIONS


class TransE(nn.Module):

    def __init__(self, config):
        super(TransE, self).__init__()
        # A simple lookup table that stores embeddings of a fixed dictionary and size

        num_entities = config[NUM_ENTITIES]
        num_relations = config[NUM_RELATIONS]
        embedding_dim = config[EMBEDDING_DIM]
        margin_loss = config[MARGIN_LOSS]

        self.entities_embeddings = nn.Embedding(num_entities, embedding_dim)
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)
        self.margin_loss = margin_loss
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # self.cuda = torch.device('cuda')


    def loss_fct(self, pos_score, neg_score):
        """

        :param pos_score:
        :param neg_score:
        :return:
        """
        criterion = nn.MarginRankingLoss(margin=self.margin_loss, size_average=False)
        # y == -1 indicates that second input to criterion should get a larger loss
        # y = torch.Tensor([-1]).cuda()
        y = torch.Tensor([-1],device=self.device)
        pos_score = pos_score.unsqueeze(0)
        neg_score = neg_score.unsqueeze(0)
        pos_score = torch.tensor(pos_score,device=self.device)
        neg_score = torch.tensor(neg_score, device=self.device)
        print(pos_score)
        print(neg_score)
        loss = criterion(pos_score, neg_score, y)

        return loss

    def calc_score(self, h_emb, r_emb, t_emb):
        """

        :param h_emb:
        :param r_emb:
        :param t_emb:
        :return:
        """
        # TODO: - torch.abs(h_emb + r_emb - t_emb)
        # Compute score and transform result to 1D tensor
        score = - torch.sum(torch.abs(h_emb + r_emb - t_emb))

        return score

    def predict(self, triple):
        """

        :param head:
        :param relation:
        :param tail:
        :return:
        """
        triple = torch.tensor(triple,dtype=torch.long)
        head, relation, tail = triple

        head_emb = self.entities_embeddings(head)
        relation_emb = self.relation_embeddings(relation)
        tail_emb = self.entities_embeddings(tail)

        score = self.calc_score(h_emb=head_emb, r_emb=relation_emb, t_emb=tail_emb)

        return score.detach().numpy()

    def forward(self, pos_exmpl, neg_exmpl):
        """

        :param pos_exmpl:
        :param neg_exmpl:
        :return:
        """

        pos_exmpl = torch.tensor(pos_exmpl,device=self.device)
        neg_exmpl = torch.tensor(neg_exmpl, device=self.device)
        pos_h, pos_r, pos_t = pos_exmpl
        neg_h, neg_r, neg_t, = neg_exmpl

        pos_h = torch.tensor(pos_h, dtype=torch.long, device=self.device)
        pos_r = torch.tensor(pos_r, dtype=torch.long, device=self.device)
        pos_t = torch.tensor(pos_t, dtype=torch.long, device=self.device)

        neg_h = torch.tensor(neg_h, dtype=torch.long, device=self.device)
        neg_r = torch.tensor(neg_r, dtype=torch.long, device=self.device)
        neg_t = torch.tensor(neg_t, dtype=torch.long, device=self.device)

        pos_h_emb = self.entities_embeddings(pos_h)
        pos_r_emb = self.relation_embeddings(pos_r)
        pos_t_emb = self.entities_embeddings(pos_t)

        neg_h_emb = self.entities_embeddings(neg_h)
        neg_r_emb = self.relation_embeddings(neg_r)
        neg_t_emb = self.entities_embeddings(neg_t)

        pos_score = self.calc_score(h_emb=pos_h_emb, r_emb=pos_r_emb, t_emb=pos_t_emb)
        neg_score = self.calc_score(h_emb=neg_h_emb, r_emb=neg_r_emb, t_emb=neg_t_emb)

        loss = self.loss_fct(pos_score=pos_score, neg_score=neg_score)

        return loss