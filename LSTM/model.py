import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size1=50, hidden_size2=64, fc1_size=32, fc2_size=16, output_size=1):
        super(LSTMModel, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size1, batch_first=True)
        self.lstm2 = nn.LSTM(hidden_size1, hidden_size2, batch_first=True)
        self.fc1 = nn.Linear(hidden_size2, fc1_size)
        self.fc2 = nn.Linear(fc1_size, fc2_size)
        self.fc3 = nn.Linear(fc2_size, output_size)

    def forward(self, x):
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        x = self.fc1(x[:, -1, :])
        x = self.fc2(x)
        x = self.fc3(x)
        return x
