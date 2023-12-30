import numpy as np

knowledge = np.load('Knowledge.npy', allow_pickle=True).item()

sorted_keys = list(knowledge.keys())
sorted_keys.sort()

for item in sorted_keys:
    print(item, '          ',knowledge[item])
    with open('Knowledge_View.txt', 'a') as f:
        f.write(str(item)+'          '+str(knowledge[item])+'\n')


while True:
    find = input()

    if find == 'list':
        for item in knowledge.keys():
            print(item)

    elif find == 'list+':
        for item in knowledge.keys():
            print(item, '          ',knowledge[item])

    elif find == 'key':
        find2 = input()
        print('items in ', find)
        try:
            for idx, item in enumerate(knowledge[find2]):
                print(idx, '          ', item)
        except KeyError:
            print('KEY ERROR')

    elif find == 'act':
        find2 = input()
        for val in knowledge[find2+'/2d']:
            print('Original Value:', val)
            try:
                for idx, item in enumerate(knowledge[find2+'/2d/'+str(val)]):
                    print(idx, '          ', item)
            except KeyError:
                print('KEY ERROR')

    else:
        print(knowledge[find])