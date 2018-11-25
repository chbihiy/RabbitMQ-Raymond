#!/usr/bin/env python
from Noeud import Noeud

if __name__ == '__main__':
    Noeud(
        self_id='%(self_id)s',
        holder_id='%(parent_id)s',
        neighbours={
%(neighbours)s
        },
        self_response_queue='%(message_id)s',
        self_messaging_queue='%(self_queue_id)s')
