import torch
import torch.nn as nn
from torch.nn import TransformerEncoder, Linear, Dropout, LayerNorm, MultiheadAttention
from torch.nn import functional as F


class MLP(nn.Module):

    def __init__(self, out_dim=10, in_channel=1, img_sz=32, hidden_dim=256):
        super(MLP, self).__init__()
        self.in_dim = in_channel*img_sz*img_sz
        self.linear = nn.Sequential(
            nn.Linear(self.in_dim, hidden_dim),
            #nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim),
            #nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
        )
        self.last = nn.Linear(hidden_dim, out_dim)  # Subject to be replaced dependent on task

    def features(self, x):
        x = self.linear(x.view(-1,self.in_dim))
        return x

    def logits(self, x):
        x = self.last(x)
        return x

    def forward(self, x):
        x = self.features(x)
        x = self.logits(x)
        return x


class MyMLPMoreDomains(nn.Module):

    def __init__(self, input_size=32, num_classes=10):
        super(MyMLPMoreDomains, self).__init__()

        hidden_size = 100

        self.linear = nn.Sequential(
            nn.Linear(input_size * 256, hidden_size),   # 8192 -> 100
            nn.ReLU()
        )
        self.last = nn.Linear(hidden_size, num_classes)  # 100 -> 10

    def features(self, x):
        x = self.linear(x)
        return x

    def logits(self, x):
        x = self.last(x)
        return x

    def forward(self, x):
        x = self.features(x)
        x = self.logits(x)
        return x


class MyMLP(nn.Module):

    def __init__(self, input_size=32, num_classes=2):
        super(MyMLP, self).__init__()

        self.linear = nn.Sequential(
            nn.Linear(input_size * 256, input_size),   # 8192 -> 32
            nn.ReLU()
        )
        self.last = nn.Linear(input_size, num_classes)  # 32 -> 2

    def features(self, x):
        x = self.linear(x)
        return x

    def logits(self, x):
        x = self.last(x)
        return x

    def forward(self, x):
        x = torch.flatten(x, start_dim=1, end_dim=2)
        x = self.features(x)
        x = self.logits(x)
        return x


class MyTransformer(nn.Module):

    def __init__(self, input_size=32, num_heads=4, num_layers=1, dim_feedforward=1024, num_classes=2):
        super(MyTransformer, self).__init__()

        transformer_encoder_layer = MyTransformerEncoderLayer(input_size, num_heads, dim_feedforward, batch_first=True)
        self.transformer_encoder = TransformerEncoder(transformer_encoder_layer, num_layers)

        # self.mlp = nn.Sequential(
        #     nn.Linear(input_size * 256, input_size),   # 8192 -> 32
        #     nn.ReLU(),
        #     nn.Linear(input_size, num_classes),  # 32 -> 2
        # )

        self.linear = nn.Sequential(
            nn.Linear(input_size * 256, input_size),  # 8192 -> 32
            nn.ReLU()
        )
        self.last = nn.Linear(input_size, num_classes)  # 32 -> 2

    def features(self, x):
        x = self.linear(x)
        return x

    def logits(self, x):
        x = self.last(x)
        return x

    def forward(self, input, key_padding_mask=None):
        x = self.transformer_encoder(input, mask=None, src_key_padding_mask=key_padding_mask)
        x = torch.flatten(x, start_dim=1, end_dim=2)
        # output = self.mlp(x)   # feed through MLP
        x = self.features(x)
        x = self.logits(x)
        return x


class MyTransformerEncoderLayer(nn.Module):

    def __init__(self, input_size, num_heads, dim_feedforward, batch_first, dropout=0.0, activation=F.relu):
        super(MyTransformerEncoderLayer, self).__init__()

        self.self_attn = MultiheadAttention(input_size, num_heads, dropout=dropout, batch_first=batch_first)

        # implementation of feed-forward model
        self.linear1 = Linear(input_size, dim_feedforward)
        self.dropout = Dropout(dropout)
        self.linear2 = Linear(dim_feedforward, input_size)

        # # elementwise_affine=False means no trainable parameters (if True, there are 64 trainable parameters)
        # self.norm1 = LayerNorm(input_size, elementwise_affine=False)
        # self.norm2 = LayerNorm(input_size, elementwise_affine=False)

        self.layer_norm = LayerNorm(input_size, elementwise_affine=False)

        self.activation = activation

    def self_attention_block(self, input, key_padding_mask):
        x = self.self_attn(input, input, input, key_padding_mask=key_padding_mask, need_weights=False)[0]
        return self.dropout(x)

    def ff_block(self, input):
        x = self.linear2(self.dropout(self.activation(self.linear1(input))))
        return self.dropout(x)

    def forward(self, input, src_mask, src_key_padding_mask):
        x = self.layer_norm(input + self.self_attention_block(input, src_key_padding_mask))   # self.norm1
        x = self.layer_norm(x + self.ff_block(x))   # self.norm2
        return x



def myMLPmore_domains():
    return MyMLPMoreDomains()


def myMLP():
    return MyMLP()


def myTransformer():
    return MyTransformer()



def MLP100():
    return MLP(hidden_dim=100)


def MLP400():
    return MLP(hidden_dim=400)


def MLP1000():
    return MLP(hidden_dim=1000)


def MLP2000():
    return MLP(hidden_dim=2000)


def MLP5000():
    return MLP(hidden_dim=5000)
