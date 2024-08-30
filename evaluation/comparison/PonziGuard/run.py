import os
from turtle import shape
import torch
from torch.nn import Linear
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.nn import global_mean_pool
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.data import InMemoryDataset
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
import random

class MyOwnDataset(InMemoryDataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super().__init__(root, transform, pre_transform)
        self._data, self.slices = torch.load(self.processed_paths[0])
        print(self._data)
    @property
    def raw_file_names(self):
        return []
    @property
    def processed_file_names(self):
        return ['datas.pt']
    def download(self):
        # empty
        pass
    def process(self):
        data1 = Mydata().graphs
        data2 = Mydata(y=0, data_path = "path_to_dataset").graphs
        data_list = data1 + data2
        random.shuffle(data_list)
        if self.pre_filter is not None: # pre_filter
            data_list = [data for data in data_list if self.pre_filter(data)]
        if self.pre_transform is not None: # pre_transform
            data_list = [self.pre_transform(data) for data in data_list]
        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[0])

class Mydata():
    def __init__(self, y = 1, data_path = "path_to_dataset"):
        self.data_path = data_path
        self.y = y
        self._graphs = self.get_graphs()
        
    
    @property
    def graphs(self):
        return self._graphs
    
    def get_graphs(self):
        graphs = []
        filenames = os.listdir(self.data_path)
        for filename in filenames:
            y = self.y
            edge_index = []
            x = []
            src = []
            des = []
            edge_attr = []
            
            with open(self.data_path + filename,'r') as f:
                for line in f.readlines():
                    if line.startswith('['):
                        x.append(eval(line.replace(' ', ',')))

                    elif line.startswith('src'):
                        group = line.split(':')
                        src.append(int(group[1].split(' ')[0]))
                        des.append(int(group[2].split(' ')[0]))
                        edge_attr.append(eval(group[3].replace(' ', ',')))

                edge_index = [src, des]

                edge_index = torch.tensor(edge_index, dtype=torch.long)
                edge_attr = torch.tensor(edge_attr, dtype=torch.float)
                x = torch.tensor(x, dtype=torch.float)
                y = torch.tensor([y], dtype=torch.long)
            
            graph = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
            graphs.append(graph)
        return graphs

class GAT(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GATConv(72, 64)
        self.conv2 = GATConv(64, 64)
        self.fc = Linear(64, 2)
 
    def forward(self, data: Data):
        data.x = self.conv1(data.x, data.edge_index, data.edge_attr)
        data.x = F.leaky_relu(data.x)
        data.x = self.conv2(data.x, data.edge_index, data.edge_attr)
        data.x = global_mean_pool(data.x, data.batch)
        data.x = F.dropout(data.x, training=self.training)
        data.x = self.fc(data.x)

        return data.x

def main():
    device = torch.device('cuda')
    dataset = MyOwnDataset("path_to_dataset").to(device)
    n = int(0.2 * len(dataset)) # Rate: 20% data to train
    model = GAT().to(device)
    print(model)
    # 0-n train
    train_loader = DataLoader(dataset[:n], batch_size=32)
    
    # n-(-1) test
    test_loader = DataLoader(dataset[n:], batch_size=32)
    
    model.train()
    for epoch in range(200):
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', 0.1, 10, 1e-4, 'abs', 0, 1e-6)
        criterion = torch.nn.CrossEntropyLoss()
        for data in train_loader:  # Iterate in batches over the training dataset.
            optimizer.zero_grad()  # Clear gradients.
            out = model(data)  # Perform a single forward pass.
            loss = criterion(out, data.y)  # Compute the loss.
            loss.backward()  # Derive gradients.
            optimizer.step()
            scheduler.step(loss)  # Update parameters based on gradients.
    model.eval()
    correct = tp = tn = fp = fn = 0
    for data in test_loader:  # Iterate in batches over the training/test dataset.
        out = model(data)
        pred = out.argmax(dim=1)  # Use the class with highest probability.
        tp += (pred[data.y==1] == 1).sum().item()
        tn += (pred[data.y==0] == 0).sum().item()
        fp += (pred[data.y==0]!= 0).sum().item()
        fn += (pred[data.y==1]!= 1).sum().item()
    #     correct += int((pred == data.y).sum())  # Check against ground-truth labels.
    # test_acc = correct / len(test_loader.dataset)  # Derive ratio of correct predictions.
    tpr = tp / (tp + fn)
    tnr = tn / (tn + fp)
    test_bac = (tpr+tnr)/2

if __name__ == "__main__":
    main()
