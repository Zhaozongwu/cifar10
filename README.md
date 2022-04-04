# cifar10
##  使用pytorch搭建深度卷积神经网络，并且进行图像分类与识别
###  1、使用的数据集：Cifar10
 Cifar数据集总共有10类（意为10个lables），分别为：airplane，automobile，bird，cat，deer，dog，frog，horse，ship，truck。全部数据集总共有60000张彩色图片，图像大小是3（R，G，B）通道的32*32，即大小为32*32*3。数据分为测试集和训练集，训练集有50000张彩色图片，构成了5个训练批，每个训练批 10000张彩色图片，测试集10000张彩色图片，构成一个训练批。测试批的数据里，取自10类中的每一类，每一类随机取1000张，抽剩下的就随机排列组成了训练批。注意一个训练批中的各类图像并不一定数量相同，总的来看训练批，每一类都有5000张图。
 ![image](https://user-images.githubusercontent.com/40204192/161510819-f791ebed-b372-4cf1-b8b6-f2d7d0960b54.png)

### 2、网络模型
![image](https://user-images.githubusercontent.com/40204192/161510789-e1f202f7-427a-4da8-9e3b-b24f7701b8bc.png)
### 3、结果
在上述文件中，可以打印卷积核。
