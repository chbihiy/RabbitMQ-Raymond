if __name__ == "__main__":
    arbre = open("config.txt").readlines()
    raymond = open("raymond.pyx").read()
    # print raymond % {"neighbours":"'A' : 'request_q_A'", "self_id":"A", "queue_id":"request_q_A", "parent_id":"A", "message_id": "message_q_A"}
    noeuds = arbre[0].replace("\n", "").split(" ")
    parents = arbre[1].replace("\n", "").split(" ")
    neighbours={}
    parents_dict={}
    for i in range(len(noeuds)):
        parents_dict[noeuds[i]]=parents[i]
        neighbours[noeuds[i]]=""
        if(noeuds[i] != parents[i]):
            neighbours[noeuds[i]]+="\t\t\t'%(noeud)s': 'request_q_%(noeud)s',\n" % {"noeud": parents[i]}
    for i in range(len(noeuds)):
        if(noeuds[i] != parents[i]):
            neighbours[parents[i]]+="\t\t\t'%(noeud)s': 'request_q_%(noeud)s',\n" % {"noeud": noeuds[i]}
    for i in range(len(noeuds)):
        f = open("Noeud_"+noeuds[i]+".py", "w+")
        f.write(raymond % {"self_id": noeuds[i],
                           "parent_id": noeuds[i] if parents[i]==noeuds[i] else "",
                           "self_queue_id": "request_q_"+ noeuds[i],
                           "message_id": "message_q_"+noeuds[i],
                           "neighbours": neighbours[noeuds[i]][:-2]
                           })
        f.close()
    print "Nodes generated succefully, please run each node on a separate terminal."
