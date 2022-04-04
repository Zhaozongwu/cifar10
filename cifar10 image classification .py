import torch
import torchvision
import torchvision.transforms  as  transforms
import torch.nn as nn
import torch.optim as optim
import time
import matplotlib.pyplot as plt
from pylab import *
# 处理测试集和训练集上的图片
transform_train = transforms.Compose(
    [ transforms.RandomCrop(32,padding=4), #先四周填充0，裁剪成32*32
      transforms.RandomHorizontalFlip(),#图像一半的概率翻转，一半的概率不翻转
      transforms.ToTensor(),
      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])#进行归一化
transform_test = transforms.Compose(
    [ transforms.ToTensor(),
      transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)), ])#进行归一化
#数据集的加载
trainset = torchvision.datasets.CIFAR10(root='D:\python项目', train=True,
                                        download=False, transform=transform_train)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=50,
                                          shuffle=True, num_workers=0)
testset = torchvision.datasets.CIFAR10(root='D:\python项目', train=False,
                                       download=False, transform=transform_test)
testloader = torch.utils.data.DataLoader(testset, batch_size=50,
                                         shuffle=False, num_workers=0)
classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
#定义Net的初始化函数，这个函数定义了该神经网络的基本结构
class myNet(nn.Module):     #定义myNet的初始化函数，这个函数定义了该神经网络的基本结构
    def __init__(self):
        super(myNet, self).__init__()#复制并使用myNet的父类的初始化方法
        self.conv1=nn.Sequential(   #3*32*32
            nn.Conv2d(in_channels=3,out_channels=12, kernel_size=5,stride=1,padding=2),
            nn.ReLU(),  #(12,32,32)
            nn.MaxPool2d(kernel_size=2)#(12,16,16)
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(in_channels=12, out_channels=18, kernel_size=5,stride=1, padding=2),
            nn.ReLU()  #(18,16,16)
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(in_channels=18, out_channels=32, kernel_size=5,stride=1, padding=2),
            nn.ReLU(),#(32,16,16)
            nn.MaxPool2d(kernel_size=2)#(32,8,8)
        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=5,stride=1, padding=2),
            nn.ReLU()#(64,8,8)
        )
        self.conv5 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=5, stride=1, padding=2),
            nn.ReLU(),  # (128,8,8)
            nn.MaxPool2d(kernel_size=2)#(128*4*4)
        )
        self.fc1 = nn.Linear(128 * 4 * 4, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
    def forward(self, x):
         x = self.conv1(x)
         x = self.conv2(x)
         x = self.conv3(x)
         x = self.conv4(x)
         x = self.conv5(x)
         x = x.view(x.size(0),-1)
         x = self.fc1(x)
         x = self.fc2(x)
         x = self.fc3(x)
         return  x
net=myNet()
# print(net)
#将卷积核进行展示
def picture(z,x,y):
   plt.figure(num=3, figsize=(10, 10))
   for idx,filt in enumerate(z):
      plt.subplot(x,y,idx+1)
      plt.imshow (filt[0,:,:],cmap="gray")
      plt.axis('off')
   return  plt.show()
 # 定义是否使用GPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
net.to(device)
# print(net)
# 损失函数
criterion = nn.CrossEntropyLoss()#叉熵损失函数
#使用随机梯度下降优化，学习率为0.001，动量为0.9
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
if __name__ == "__main__":
   print('训练开始')
   EPOCH=150
   batch_size_start = time.time()
   train_loss=[]
   acc=[]
   for epoch in range(EPOCH):  #定义遍历数据集的次数
       running_loss = 0.0
       Correctpiture = 0  # 定义预测正确的图片数，初始化为0
       Totalpicture = 0  # 总共参与测试的图片数，也初始化为0
       for i, data in enumerate(trainloader, 0):  #遍历训练集，并且给出下标和数据
           inputs, labels = data
           inputs, labels = inputs.to(device), labels.to(device)
           optimizer.zero_grad()   #梯度初始化为0
           outputs = net(inputs)
           loss = criterion(outputs, labels) #计算损失值
           loss.backward()  #对损失值进行反向传递
           optimizer.step()   #用SGD更新参数
           # 每训练1个batch打印一次loss和准确率
           running_loss += loss.item()   #所有batch的损失和
           _, predicted = torch.max(outputs.data, 1)
           Totalpicture += labels.size(0)
           Correctpiture += (predicted == labels).sum().item()
           if i % 1000 == 999:   #每1000个Batch输出
               train_loss.append(running_loss / 1000)
               acc.append(100 * Correctpiture / Totalpicture)  #用列表存储下当前的损失值和精确率
               print('EPOCH [%d, %5d], train_loss: %.3f,accucy: %d %%, need time %.4f'
                  % (epoch + 1, i + 1, running_loss / 1000,(100 * Correctpiture / Totalpicture), time.time() - batch_size_start))
               running_loss = 0.0
   print('训练结束')

   #画出coss function的图像
   mpl.rcParams['font.sans-serif'] = ['SimHei']
   plt.figure(num=1,figsize=(8,5))
   plt.plot(train_loss,color='b')
   plt.ylabel('train_loss')
   plt.xlabel('EPOCH')
   plt.title('损失函数')
   plt.figure(num=2, figsize=(8, 5))
   plt.plot(acc,color='r')
   plt.ylabel('accuray')
   plt.xlabel('EPOCH')
   plt.title('训练集上预测准确率')
   plt.show()

   print('测试数据')
   Correctpiture = 0  # 定义预测正确的图片数，初始化为0
   Totalpicture  = 0   # 总共参与测试的图片数，也初始化为0
   with torch.no_grad():
       for data in testloader:
           inputs, labels = data
           inputs, labels = inputs.to(device), labels.to(device)
           outputs = net(inputs)
           _, predicted = torch.max(outputs.data, 1) #返回的列的第一个元素是image data，第二个元素是label
           Totalpicture += labels.size(0)  # 更新测试图片的数量
           Correctpiture += (predicted == labels).sum().item() # 更新正确分类的图片的数量

   print('Accuracy of the 10000 test picure: %d %%' % (100 * Correctpiture / Totalpicture))
   print('测试结束')
   #打印出5个卷积核
   X1 = picture(net.conv1[0].weight.data, 2, 6)
   X2 = picture(net.conv2[0].weight.data, 3, 6)
   X3 = picture(net.conv3[0].weight.data, 4, 8)
   X4 = picture(net.conv4[0].weight.data, 8, 8)
   X5 = picture(net.conv5[0].weight.data, 8, 16)

#此次模型以及数据结果的保存
   state = {'net': net.state_dict(), 'optimizer': optimizer.state_dict(), 'epoch': EPOCH}
   torch.save(state,'D:\python项目\modelpara.pth')
