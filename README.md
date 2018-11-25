# RabbitMQ-Raymond
The Raymond Algorithm implementation with RabbitMQ. This is a school project (IMT ATLANTIQUE).

### Setup
You need python 2.x and RabbitMQ installed

### Generate nodes for the Raymond Mutual Exclusion
Put all the files in the same directory, on the terminal execute this command
```
python generate.py
```
then open a terminal for each node, and execute the flowing command, for each node X
```
python Noeud_X.py
```
### Changing config.txt
The first line represents the node names

The second line represents their parents in the tree
```
A B C D E F
A A A A D D
```
![alt text](https://raw.githubusercontent.com/chbihiy/RabbitMQ-Raymond/master/exemple.png)
